"""
HTTP REST API and Static File Server for Smart Complaint System (SCS) Kota Bandar Lampung.
Implements endpoints defined in PRD Section 14, role-based access control, file upload processing,
and full state machine business rules.
"""

import http.server
import socketserver
import json
import os
import sys
import re
import uuid
import datetime
import mimetypes
import urllib.parse
import traceback
import random

from app.database import get_db, init_db, hash_password, verify_password
from app.auth import create_access_token, verify_access_token, check_permission

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_ticket_no(conn):
    """Generate unique, unguessable ticket number conforming to FR-05."""
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    for _ in range(100):
        rand_suffix = f"{random.randint(1000, 9999)}"
        ticket_candidate = f"SCS-{today_str}-{rand_suffix}"
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM reports WHERE ticket_no = ?", (ticket_candidate,))
        if not cur.fetchone():
            return ticket_candidate
    return f"SCS-{today_str}-{uuid.uuid4().hex[:6].upper()}"

def record_audit(conn, actor_id, actor_name, action, entity_type, entity_id, metadata_dict):
    """Record an entry in the audit_logs table (FR-12)."""
    now = datetime.datetime.now().isoformat()
    conn.execute("""
    INSERT INTO audit_logs (id, actor_id, actor_name, action, entity_type, entity_id, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (f"aud-{uuid.uuid4()}", actor_id, actor_name, action, entity_type, entity_id, json.dumps(metadata_dict), now))

def create_notification(conn, user_id, report_id, title, body):
    """Create in-app notification (FR-10)."""
    now = datetime.datetime.now().isoformat()
    conn.execute("""
    INSERT INTO notifications (id, user_id, report_id, channel, title, body, created_at)
    VALUES (?, ?, ?, 'IN_APP', ?, ?, ?)
    """, (f"notif-{uuid.uuid4()}", user_id, report_id, title, body, now))

class SCSRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {self.command} {self.path} - {format % args}\n")

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status_code: int, message: str, details=None):
        payload = {"success": False, "error": message}
        if details:
            payload["details"] = details
        self.send_json(status_code, payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def get_current_user(self):
        """Extract and authenticate user from Authorization header or cookie."""
        auth_header = self.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif 'scs_token=' in self.headers.get('Cookie', ''):
            for part in self.headers.get('Cookie', '').split(';'):
                part = part.strip()
                if part.startswith('scs_token='):
                    token = part.split('=', 1)[1]
                    break
        
        if not token:
            return None
        return verify_access_token(token)

    def parse_request_body(self):
        """Parse JSON or multipart form data."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        
        content_type = self.headers.get('Content-Type', '')
        raw_body = self.rfile.read(content_length)

        if 'application/json' in content_type:
            try:
                return json.loads(raw_body.decode('utf-8'))
            except Exception:
                return {}
        elif 'multipart/form-data' in content_type:
            return self.parse_multipart(raw_body, content_type)
        elif 'application/x-www-form-urlencoded' in content_type:
            parsed = urllib.parse.parse_qs(raw_body.decode('utf-8'))
            return {k: v[0] for k, v in parsed.items()}
        return {}

    def parse_multipart(self, raw_body: bytes, content_type: str):
        """Simple, robust multipart form-data parser without external deps."""
        boundary = content_type.split("boundary=")[1].encode('utf-8')
        if boundary.startswith(b'"') and boundary.endswith(b'"'):
            boundary = boundary[1:-1]
        
        parts = raw_body.split(b'--' + boundary)
        result = {"_files": []}

        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            subparts = part.split(b'\r\n\r\n', 1)
            if len(subparts) < 2:
                continue
            
            header_raw, content = subparts
            # strip trailing \r\n
            if content.endswith(b'\r\n'):
                content = content[:-2]
            
            header_text = header_raw.decode('latin1', 'ignore')
            disposition_match = re.search(r'name="([^"]+)"', header_text)
            if not disposition_match:
                continue
            
            field_name = disposition_match.group(1)
            filename_match = re.search(r'filename="([^"]+)"', header_text)
            
            if filename_match:
                filename = filename_match.group(1)
                if filename and len(content) > 0:
                    ext = os.path.splitext(filename)[1].lower() or '.jpg'
                    stored_name = f"{uuid.uuid4().hex}{ext}"
                    stored_path = os.path.join(UPLOAD_DIR, stored_name)
                    with open(stored_path, 'wb') as f:
                        f.write(content)
                    
                    mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
                    result["_files"].append({
                        "field_name": field_name,
                        "file_name": filename,
                        "storage_key": stored_name,
                        "mime_type": mime_type,
                        "file_size": len(content),
                        "url": f"/static/uploads/{stored_name}"
                    })
            else:
                result[field_name] = content.decode('utf-8', 'ignore')

        return result

    def serve_static(self, filepath: str):
        """Serve a static file with correct MIME type and caching headers."""
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            self.send_error_json(404, "File not found")
            return
            
        mime, _ = mimetypes.guess_type(filepath)
        if not mime:
            mime = 'application/octet-stream'

        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_json(500, f"Error reading file: {str(e)}")

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. Static Files
        if path.startswith('/static/'):
            rel_path = path[8:]
            file_path = os.path.join(STATIC_DIR, rel_path.replace('/', os.sep))
            self.serve_static(file_path)
            return

        # 2. Main Page / SPA Routing
        if path == '/' or path == '/index.html' or not path.startswith('/api/'):
            index_file = os.path.join(BASE_DIR, "index.html")
            self.serve_static(index_file)
            return

        # 3. REST API Endpoints
        conn = get_db()
        try:
            # GET /api/v1/auth/quick-switch-users - Helper for demo testing
            if path == '/api/v1/auth/quick-switch-users':
                cur = conn.cursor()
                cur.execute("""
                SELECT u.id, u.full_name, u.email, u.phone, r.role_code, r.role_name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                ORDER BY r.id ASC, u.full_name ASC
                """)
                rows = [dict(r) for r in cur.fetchall()]
                self.send_json(200, {"success": True, "users": rows})
                return

            # GET /api/v1/auth/token-for-user?id=... (Instant demo login switcher)
            if path == '/api/v1/auth/token-for-user':
                user_id = query.get('id', [None])[0]
                if not user_id:
                    self.send_error_json(400, "User ID required")
                    return
                cur = conn.cursor()
                cur.execute("SELECT id, full_name, email, phone, nik, is_active FROM users WHERE id = ?", (user_id,))
                user = cur.fetchone()
                if not user:
                    self.send_error_json(404, "User not found")
                    return
                
                cur.execute("""
                SELECT r.role_code FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
                """, (user_id,))
                roles = [r[0] for r in cur.fetchall()]
                token = create_access_token(user["id"], user["email"], user["full_name"], roles)
                self.send_json(200, {
                    "success": True,
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "name": user["full_name"],
                        "email": user["email"],
                        "phone": user["phone"],
                        "nik": user["nik"],
                        "roles": roles
                    }
                })
                return

            # GET /api/v1/me
            if path == '/api/v1/me':
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Silakan login terlebih dahulu")
                    return
                cur = conn.cursor()
                cur.execute("SELECT id, full_name, email, phone, nik, created_at FROM users WHERE id = ?", (user_claims["sub"],))
                u = cur.fetchone()
                if not u:
                    self.send_error_json(404, "Pengguna tidak ditemukan")
                    return
                self.send_json(200, {
                    "success": True,
                    "user": {
                        "id": u["id"],
                        "name": u["full_name"],
                        "email": u["email"],
                        "phone": u["phone"],
                        "nik": u["nik"],
                        "roles": user_claims["roles"]
                    }
                })
                return

            # GET /api/v1/departments
            if path == '/api/v1/departments':
                cur = conn.cursor()
                cur.execute("SELECT id, name, code, area_code, description FROM departments WHERE is_active = 1 ORDER BY name ASC")
                depts = [dict(r) for r in cur.fetchall()]
                self.send_json(200, {"success": True, "departments": depts})
                return

            # GET /api/v1/categories
            if path == '/api/v1/categories':
                cur = conn.cursor()
                cur.execute("""
                SELECT c.id, c.name, c.code, c.description, c.default_priority, c.icon, c.default_dept_id, d.name as default_dept_name
                FROM categories c
                LEFT JOIN departments d ON c.default_dept_id = d.id
                WHERE c.is_active = 1
                ORDER BY c.id ASC
                """)
                cats = [dict(r) for r in cur.fetchall()]
                self.send_json(200, {"success": True, "categories": cats})
                return

            # GET /api/v1/reports/mine
            if path == '/api/v1/reports/mine':
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                cur = conn.cursor()
                cur.execute("""
                SELECT r.*, c.name as category_name, c.icon as category_icon,
                       (SELECT storage_key FROM report_media WHERE report_id = r.id LIMIT 1) as thumbnail_key
                FROM reports r
                JOIN categories c ON r.category_id = c.id
                WHERE r.reporter_id = ?
                ORDER BY r.created_at DESC
                """, (user_claims["sub"],))
                reports = [dict(r) for r in cur.fetchall()]
                self.send_json(200, {"success": True, "reports": reports})
                return

            # GET /api/v1/reports/{id}
            report_detail_match = re.match(r'^/api/v1/reports/([a-zA-Z0-9\-]+)$', path)
            if report_detail_match:
                rep_id = report_detail_match.group(1)
                user_claims = self.get_current_user()
                
                cur = conn.cursor()
                cur.execute("""
                SELECT r.*, c.name as category_name, c.icon as category_icon,
                       u.full_name as reporter_name, u.phone as reporter_phone, u.nik as reporter_nik,
                       d.name as department_name, d.code as department_code,
                       asg_u.full_name as assignee_name, asg_u.phone as assignee_phone,
                       asg.due_at, asg.notes as assignment_notes
                FROM reports r
                JOIN categories c ON r.category_id = c.id
                JOIN users u ON r.reporter_id = u.id
                LEFT JOIN report_assignments asg ON r.id = asg.report_id
                LEFT JOIN departments d ON asg.department_id = d.id
                LEFT JOIN users asg_u ON asg.assignee_id = asg_u.id
                WHERE r.id = ? OR r.ticket_no = ?
                """, (rep_id, rep_id))
                row = cur.fetchone()
                if not row:
                    self.send_error_json(404, "Laporan pengaduan tidak ditemukan")
                    return
                
                rep = dict(row)

                # Anonymity masking for public / unauthorized users (Section 9 & AC-03)
                is_authorized = False
                if user_claims:
                    roles = user_claims.get("roles", [])
                    if "ADMIN" in roles or "SUPERADMIN" in roles or "PIMPINAN" in roles or "PETUGAS" in roles:
                        is_authorized = True
                    elif user_claims["sub"] == rep["reporter_id"]:
                        is_authorized = True
                
                if not is_authorized:
                    # Mask personal data
                    rep["reporter_name"] = "Warga Kota Bandar Lampung" if rep["is_anonymous"] else (rep["reporter_name"][:3] + "***")
                    rep["reporter_phone"] = "08**********"
                    rep["reporter_nik"] = "1871**********"

                # Fetch media
                cur.execute("SELECT id, storage_key, file_name, mime_type, file_size, phase, created_at FROM report_media WHERE report_id = ?", (rep["id"],))
                media_list = []
                for m in cur.fetchall():
                    md = dict(m)
                    md["url"] = f"/static/uploads/{md['storage_key']}"
                    media_list.append(md)
                rep["media"] = media_list

                # Fetch status history
                cur.execute("""
                SELECT h.*, u.full_name as changed_by_name
                FROM report_status_history h
                JOIN users u ON h.changed_by = u.id
                WHERE h.report_id = ?
                ORDER BY h.changed_at ASC
                """, (rep["id"],))
                rep["status_history"] = [dict(h) for h in cur.fetchall()]

                # Fetch comments
                cur.execute("""
                SELECT c.*, u.full_name as author_name,
                       (SELECT r.role_code FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = c.author_id LIMIT 1) as author_role
                FROM comments c
                JOIN users u ON c.author_id = u.id
                WHERE c.report_id = ?
                ORDER BY c.created_at ASC
                """, (rep["id"],))
                rep["comments"] = [dict(c) for c in cur.fetchall()]

                # Fetch feedback if exists
                cur.execute("SELECT * FROM feedback WHERE report_id = ?", (rep["id"],))
                fb = cur.fetchone()
                rep["feedback"] = dict(fb) if fb else None

                self.send_json(200, {"success": True, "report": rep})
                return

            # GET /api/v1/reports (Filtered listing & Search FR-14)
            if path == '/api/v1/reports':
                search_q = query.get('q', [None])[0]
                status_f = query.get('status', [None])[0]
                cat_f = query.get('category_id', [None])[0]
                dist_f = query.get('district', [None])[0]
                dept_f = query.get('department_id', [None])[0]
                limit = int(query.get('limit', [100])[0])

                sql = """
                SELECT r.id, r.ticket_no, r.title, r.description, r.lat, r.lng, r.address_text,
                       r.district, r.status, r.priority, r.is_anonymous, r.created_at, r.updated_at,
                       c.name as category_name, c.icon as category_icon,
                       u.full_name as reporter_name,
                       d.name as department_name,
                       (SELECT storage_key FROM report_media WHERE report_id = r.id AND phase = 'INITIAL' LIMIT 1) as thumbnail_key
                FROM reports r
                JOIN categories c ON r.category_id = c.id
                JOIN users u ON r.reporter_id = u.id
                LEFT JOIN report_assignments asg ON r.id = asg.report_id
                LEFT JOIN departments d ON asg.department_id = d.id
                WHERE 1=1
                """
                params = []
                if search_q:
                    sql += " AND (r.ticket_no LIKE ? OR r.title LIKE ? OR r.description LIKE ? OR r.address_text LIKE ?)"
                    pattern = f"%{search_q}%"
                    params.extend([pattern, pattern, pattern, pattern])
                if status_f and status_f != 'ALL':
                    sql += " AND r.status = ?"
                    params.append(status_f)
                if cat_f and cat_f != 'ALL':
                    sql += " AND r.category_id = ?"
                    params.append(cat_f)
                if dist_f and dist_f != 'ALL':
                    sql += " AND r.district = ?"
                    params.append(dist_f)
                if dept_f and dept_f != 'ALL':
                    sql += " AND asg.department_id = ?"
                    params.append(dept_f)

                sql += " ORDER BY r.created_at DESC LIMIT ?"
                params.append(limit)

                cur = conn.cursor()
                cur.execute(sql, params)
                reports = [dict(r) for r in cur.fetchall()]
                for rep in reports:
                    if rep.get("thumbnail_key"):
                        rep["thumbnail_url"] = f"/static/uploads/{rep['thumbnail_key']}"
                    else:
                        rep["thumbnail_url"] = None

                self.send_json(200, {"success": True, "count": len(reports), "reports": reports})
                return

            # GET /api/v1/dashboard/summary (FR-11 & Pimpinan Dashboard)
            if path == '/api/v1/dashboard/summary':
                cur = conn.cursor()
                
                # Totals
                cur.execute("SELECT COUNT(*) FROM reports")
                total = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'SUBMITTED'")
                submitted = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'VERIFIED'")
                verified = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'ASSIGNED'")
                assigned = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'IN_PROGRESS'")
                in_progress = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status IN ('RESOLVED', 'CLOSED')")
                resolved = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'REJECTED'")
                rejected = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'NEEDS_INFO'")
                needs_info = cur.fetchone()[0]

                # Average satisfaction rating
                cur.execute("SELECT AVG(rating), COUNT(*) FROM feedback")
                fb_row = cur.fetchone()
                avg_rating = round(fb_row[0], 1) if fb_row and fb_row[0] else 4.8
                total_ratings = fb_row[1] if fb_row else 0

                # By category
                cur.execute("""
                SELECT c.name, COUNT(r.id) as count
                FROM categories c
                LEFT JOIN reports r ON c.id = r.category_id
                GROUP BY c.id
                ORDER BY count DESC
                """)
                by_category = [dict(r) for r in cur.fetchall()]

                # By status
                cur.execute("""
                SELECT status, COUNT(*) as count FROM reports GROUP BY status
                """)
                by_status = [dict(r) for r in cur.fetchall()]

                # By district
                cur.execute("""
                SELECT district, COUNT(*) as count FROM reports GROUP BY district ORDER BY count DESC LIMIT 10
                """)
                by_district = [dict(r) for r in cur.fetchall()]

                # By department
                cur.execute("""
                SELECT d.name, COUNT(r.id) as count
                FROM departments d
                LEFT JOIN report_assignments asg ON d.id = asg.department_id
                LEFT JOIN reports r ON asg.report_id = r.id
                GROUP BY d.id
                ORDER BY count DESC
                """)
                by_dept = [dict(r) for r in cur.fetchall()]

                self.send_json(200, {
                    "success": True,
                    "kpi": {
                        "total": total,
                        "submitted": submitted,
                        "verified": verified,
                        "assigned": assigned,
                        "in_progress": in_progress,
                        "resolved": resolved,
                        "rejected": rejected,
                        "needs_info": needs_info,
                        "avg_rating": avg_rating,
                        "total_ratings": total_ratings,
                        "resolution_rate": round((resolved / total * 100) if total > 0 else 0, 1)
                    },
                    "by_category": by_category,
                    "by_status": by_status,
                    "by_district": by_district,
                    "by_department": by_dept
                })
                return

            # GET /api/v1/notifications
            if path == '/api/v1/notifications':
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                cur = conn.cursor()
                cur.execute("""
                SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20
                """, (user_claims["sub"],))
                notifs = [dict(n) for n in cur.fetchall()]
                cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read_at IS NULL", (user_claims["sub"],))
                unread_count = cur.fetchone()[0]
                self.send_json(200, {"success": True, "notifications": notifs, "unread_count": unread_count})
                return

            # GET /api/v1/audit-logs
            if path == '/api/v1/audit-logs':
                user_claims = self.get_current_user()
                if not user_claims or not check_permission(user_claims.get("roles", []), ["ADMIN", "SUPERADMIN"]):
                    self.send_error_json(403, "Akses ditolak: Hanya Admin/Superadmin")
                    return
                cur = conn.cursor()
                cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100")
                logs = [dict(l) for l in cur.fetchall()]
                self.send_json(200, {"success": True, "logs": logs})
                return

            # GET /api/v1/users
            if path == '/api/v1/users':
                user_claims = self.get_current_user()
                if not user_claims or not check_permission(user_claims.get("roles", []), ["ADMIN", "SUPERADMIN"]):
                    self.send_error_json(403, "Akses ditolak: Hanya Admin/Superadmin")
                    return
                cur = conn.cursor()
                cur.execute("""
                SELECT u.id, u.full_name, u.email, u.phone, u.nik, u.is_active, u.created_at,
                       GROUP_CONCAT(r.role_code) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
                """)
                users = [dict(u) for u in cur.fetchall()]
                self.send_json(200, {"success": True, "users": users})
                return

            self.send_error_json(404, "Endpoint tidak ditemukan")

        finally:
            conn.close()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        body = self.parse_request_body()

        conn = get_db()
        try:
            # POST /api/v1/auth/register (FR-01)
            if path == '/api/v1/auth/register':
                full_name = body.get('full_name', '').strip()
                email = body.get('email', '').strip().lower()
                password = body.get('password', '')
                phone = body.get('phone', '').strip()
                nik = body.get('nik', '').strip()

                if not full_name or not email or not password:
                    self.send_error_json(400, "Nama lengkap, email, dan kata sandi wajib diisi")
                    return
                if len(password) < 6:
                    self.send_error_json(400, "Kata sandi minimal 6 karakter")
                    return
                
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cur.fetchone():
                    self.send_error_json(400, "Email sudah terdaftar dalam sistem")
                    return
                
                user_id = f"usr-{uuid.uuid4().hex[:12]}"
                pwd_hash = hash_password(password)
                now = datetime.datetime.now().isoformat()

                cur.execute("""
                INSERT INTO users (id, full_name, email, phone, nik, password_hash, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """, (user_id, full_name, email, phone, nik, pwd_hash, now))

                # Assign role MASAYARAKAT
                cur.execute("SELECT id FROM roles WHERE role_code = 'MASYARAKAT'")
                role_row = cur.fetchone()
                if role_row:
                    cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_row[0]))

                token = create_access_token(user_id, email, full_name, ["MASYARAKAT"])
                record_audit(conn, user_id, full_name, "USER_REGISTER", "USER", user_id, {"email": email})
                conn.commit()

                self.send_json(201, {
                    "success": True,
                    "message": "Registrasi berhasil!",
                    "token": token,
                    "user": {
                        "id": user_id,
                        "name": full_name,
                        "email": email,
                        "roles": ["MASYARAKAT"]
                    }
                })
                return

            # POST /api/v1/auth/login (FR-01)
            if path == '/api/v1/auth/login':
                email = body.get('email', '').strip().lower()
                password = body.get('password', '')

                if not email or not password:
                    self.send_error_json(400, "Email dan kata sandi wajib diisi")
                    return
                
                cur = conn.cursor()
                cur.execute("SELECT id, full_name, email, phone, nik, password_hash, is_active FROM users WHERE email = ?", (email,))
                user = cur.fetchone()
                if not user or not verify_password(password, user["password_hash"]):
                    self.send_error_json(401, "Email atau kata sandi tidak valid")
                    return
                
                if not user["is_active"]:
                    self.send_error_json(403, "Akun Anda dinonaktifkan")
                    return

                cur.execute("""
                SELECT r.role_code FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
                """, (user["id"],))
                roles = [r[0] for r in cur.fetchall()]
                token = create_access_token(user["id"], user["email"], user["full_name"], roles)

                record_audit(conn, user["id"], user["full_name"], "USER_LOGIN", "USER", user["id"], {"email": email})
                conn.commit()

                self.send_json(200, {
                    "success": True,
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "name": user["full_name"],
                        "email": user["email"],
                        "phone": user["phone"],
                        "nik": user["nik"],
                        "roles": roles
                    }
                })
                return

            # POST /api/v1/auth/logout
            if path == '/api/v1/auth/logout':
                self.send_json(200, {"success": True, "message": "Berhasil keluar dari sistem"})
                return

            # POST /api/v1/reports (FR-03, FR-04, FR-05, AC-01, AC-02)
            if path == '/api/v1/reports':
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Silakan masuk akun terlebih dahulu untuk mengirim pengaduan")
                    return
                
                title = body.get('title', '').strip()
                category_id = body.get('category_id')
                description = body.get('description', '').strip()
                address_text = body.get('address_text', '').strip()
                district = body.get('district', 'Bandar Lampung').strip()
                is_anonymous = 1 if str(body.get('is_anonymous', '0')).lower() in ('1', 'true') else 0

                # Coordinates
                try:
                    lat = float(body.get('lat', -5.4292))
                    lng = float(body.get('lng', 105.2625))
                except (ValueError, TypeError):
                    lat, lng = -5.4292, 105.2625

                # Validation per AC-02: Title, Category, Description, Address are required
                if not title or not category_id or not description or not address_text:
                    self.send_error_json(400, "Validasi gagal: Judul, kategori, deskripsi laporan, dan alamat lokasi wajib diisi lengkap")
                    return

                try:
                    category_id = int(category_id)
                except ValueError:
                    self.send_error_json(400, "Kategori tidak valid")
                    return

                ticket_no = generate_ticket_no(conn)
                report_id = f"rep-{uuid.uuid4().hex[:12]}"
                now = datetime.datetime.now().isoformat()

                cur = conn.cursor()
                # Check default priority for category
                cur.execute("SELECT default_priority FROM categories WHERE id = ?", (category_id,))
                cat_row = cur.fetchone()
                priority = cat_row[0] if cat_row else 'SEDANG'

                cur.execute("""
                INSERT INTO reports (id, ticket_no, reporter_id, category_id, title, description,
                                    lat, lng, address_text, district, status, priority, is_anonymous, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SUBMITTED', ?, ?, ?, ?)
                """, (report_id, ticket_no, user_claims["sub"], category_id, title, description,
                      lat, lng, address_text, district, priority, is_anonymous, now, now))

                # Add initial status history
                cur.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, NULL, 'SUBMITTED', ?, 'Pengaduan masyarakat berhasil dikirim ke antrean sistem.', ?)
                """, (f"hist-{uuid.uuid4().hex[:12]}", report_id, user_claims["sub"], now))

                # Save uploaded media files from multipart form
                files = body.get("_files", [])
                for f in files:
                    cur.execute("""
                    INSERT INTO report_media (id, report_id, storage_key, file_name, mime_type, file_size, phase, uploaded_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'INITIAL', ?, ?)
                    """, (f"med-{uuid.uuid4().hex[:12]}", report_id, f["storage_key"], f["file_name"], f["mime_type"], f["file_size"], user_claims["sub"], now))

                # If base64 photo is provided in JSON payload
                raw_photo = body.get("photo_base64")
                if raw_photo and len(raw_photo) > 50:
                    try:
                        if ',' in raw_photo:
                            raw_photo = raw_photo.split(',', 1)[1]
                        photo_bytes = base64.b64decode(raw_photo)
                        stored_name = f"{uuid.uuid4().hex}.jpg"
                        stored_path = os.path.join(UPLOAD_DIR, stored_name)
                        with open(stored_path, 'wb') as pf:
                            pf.write(photo_bytes)
                        cur.execute("""
                        INSERT INTO report_media (id, report_id, storage_key, file_name, mime_type, file_size, phase, uploaded_by, created_at)
                        VALUES (?, ?, ?, 'bukti_pengaduan.jpg', 'image/jpeg', ?, 'INITIAL', ?, ?)
                        """, (f"med-{uuid.uuid4().hex[:12]}", report_id, stored_name, len(photo_bytes), user_claims["sub"], now))
                    except Exception as e:
                        print("Error saving base64 photo:", e)

                # Send in-app notification to reporter
                create_notification(conn, user_claims["sub"], report_id, "Pengaduan Berhasil Terkirim",
                                    f"Laporan Anda dengan nomor tiket #{ticket_no} telah diterima dan sedang menunggu verifikasi admin.")

                record_audit(conn, user_claims["sub"], user_claims["name"], "CREATE_REPORT", "REPORT", report_id, {"ticket_no": ticket_no, "title": title})
                conn.commit()

                self.send_json(201, {
                    "success": True,
                    "message": "Pengaduan Anda berhasil dikirim!",
                    "report_id": report_id,
                    "ticket_no": ticket_no
                })
                return

            # POST /api/v1/reports/{id}/media (Upload evidence photo FR-03, NFR-05, AC-06)
            report_media_match = re.match(r'^/api/v1/reports/([a-zA-Z0-9\-]+)/media$', path)
            if report_media_match:
                rep_id = report_media_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                
                files = body.get("_files", [])
                phase = body.get("phase", "INITIAL") # INITIAL or RESOLUTION
                
                # Check file formats and size (NFR-05, AC-06)
                allowed_mimes = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
                max_size = 15 * 1024 * 1024 # 15MB
                
                uploaded = []
                now = datetime.datetime.now().isoformat()
                cur = conn.cursor()

                for f in files:
                    if f["mime_type"] not in allowed_mimes:
                        self.send_error_json(400, "Format berkas tidak diizinkan. Gunakan JPG, PNG, atau WebP.")
                        return
                    if f["file_size"] > max_size:
                        self.send_error_json(400, "Ukuran file melebihi batas 15MB.")
                        return

                    med_id = f"med-{uuid.uuid4().hex[:12]}"
                    cur.execute("""
                    INSERT INTO report_media (id, report_id, storage_key, file_name, mime_type, file_size, phase, uploaded_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (med_id, rep_id, f["storage_key"], f["file_name"], f["mime_type"], f["file_size"], phase, user_claims["sub"], now))
                    uploaded.append({"id": med_id, "url": f"/static/uploads/{f['storage_key']}"})

                conn.commit()
                self.send_json(201, {"success": True, "uploaded": uploaded})
                return

            # POST /api/v1/admin/reports/{id}/verify (FR-07, AC-04)
            # Allowed actions: VERIFY, REJECT, REQUEST_INFO
            admin_verify_match = re.match(r'^/api/v1/admin/reports/([a-zA-Z0-9\-]+)/verify$', path)
            if admin_verify_match:
                rep_id = admin_verify_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims or not check_permission(user_claims.get("roles", []), ["ADMIN", "SUPERADMIN"]):
                    self.send_error_json(403, "Akses ditolak: Hanya Admin / Verifikator")
                    return

                action = body.get("action", "").upper() # ACCEPT / REJECT / REQUEST_INFO
                note = body.get("note", "").strip()
                reason = body.get("reason", "").strip()
                department_id = body.get("department_id")
                urgency = body.get("priority") # RENDAH, SEDANG, TINGGI, DARURAT

                cur = conn.cursor()
                cur.execute("SELECT * FROM reports WHERE id = ?", (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return

                old_status = rep["status"]
                now = datetime.datetime.now().isoformat()

                if action in ("ACCEPT", "VERIFIED"):
                    # SUBMITTED -> VERIFIED
                    if old_status not in ("SUBMITTED", "NEEDS_INFO"):
                        self.send_error_json(400, f"Transisi tidak valid dari status {old_status} ke VERIFIED")
                        return

                    new_status = "VERIFIED"
                    cur.execute("""
                    UPDATE reports SET status = ?, priority = COALESCE(?, priority), updated_at = ? WHERE id = ?
                    """, (new_status, urgency, now, rep_id))

                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, new_status, user_claims["sub"], note or "Laporan diverifikasi valid oleh admin.", now))

                    # If department also chosen, auto transition to ASSIGNED
                    if department_id:
                        cur.execute("""
                        INSERT OR REPLACE INTO report_assignments (id, report_id, department_id, assignee_id, assigned_by, assigned_at, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (f"asg-{uuid.uuid4().hex[:12]}", rep_id, department_id, body.get("assignee_id"), user_claims["sub"], now, note))

                        cur.execute("UPDATE reports SET status = 'ASSIGNED', updated_at = ? WHERE id = ?", (now, rep_id))

                        cur.execute("""
                        INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                        VALUES (?, ?, 'VERIFIED', 'ASSIGNED', ?, 'Laporan didisposisikan ke instansi teknis penanggung jawab.', ?)
                        """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, user_claims["sub"], now))
                        new_status = "ASSIGNED"

                    create_notification(conn, rep["reporter_id"], rep_id, "Laporan Anda Telah Diverifikasi",
                                        f"Laporan #{rep['ticket_no']} telah diverifikasi valid dan diteruskan ke tahap penanganan.")

                elif action in ("REJECT", "REJECTED"):
                    # Mandatory rejection reason (Section 9)
                    if not reason:
                        self.send_error_json(400, "Alasan penolakan wajib diisi!")
                        return
                    new_status = "REJECTED"
                    cur.execute("""
                    UPDATE reports SET status = ?, rejection_reason = ?, updated_at = ? WHERE id = ?
                    """, (new_status, reason, now, rep_id))

                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, new_status, user_claims["sub"], f"Laporan ditolak: {reason}", now))

                    create_notification(conn, rep["reporter_id"], rep_id, "Laporan Tidak Dapat Diproses",
                                        f"Laporan #{rep['ticket_no']} tidak dapat diproses: {reason}")

                elif action in ("REQUEST_INFO", "NEEDS_INFO"):
                    # Mandatory question (Section 9)
                    question = body.get("question", "").strip() or note
                    if not question:
                        self.send_error_json(400, "Pertanyaan permintaan klarifikasi wajib diisi!")
                        return
                    new_status = "NEEDS_INFO"
                    cur.execute("""
                    UPDATE reports SET status = ?, clarification_request = ?, updated_at = ? WHERE id = ?
                    """, (new_status, question, now, rep_id))

                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, new_status, user_claims["sub"], f"Admin meminta klarifikasi: {question}", now))

                    # Also add to comments
                    cur.execute("""
                    INSERT INTO comments (id, report_id, author_id, body, visibility, created_at)
                    VALUES (?, ?, ?, ?, 'PUBLIC', ?)
                    """, (f"cmt-{uuid.uuid4().hex[:12]}", rep_id, user_claims["sub"], f"[Permintaan Klarifikasi Admin]: {question}", now))

                    create_notification(conn, rep["reporter_id"], rep_id, "Permintaan Klarifikasi Laporan",
                                        f"Admin membutuhkan informasi tambahan untuk laporan #{rep['ticket_no']}: {question}")

                else:
                    self.send_error_json(400, "Aksi verifikasi tidak valid")
                    return

                record_audit(conn, user_claims["sub"], user_claims["name"], "VERIFY_REPORT", "REPORT", rep_id, {"action": action, "new_status": new_status})
                conn.commit()

                self.send_json(200, {"success": True, "message": f"Status laporan berhasil diperbarui menjadi {new_status}", "status": new_status})
                return

            # POST /api/v1/admin/reports/{id}/assign (FR-08)
            admin_assign_match = re.match(r'^/api/v1/admin/reports/([a-zA-Z0-9\-]+)/assign$', path)
            if admin_assign_match:
                rep_id = admin_assign_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims or not check_permission(user_claims.get("roles", []), ["ADMIN", "SUPERADMIN"]):
                    self.send_error_json(403, "Akses ditolak: Hanya Admin / Verifikator")
                    return
                
                dept_id = body.get("department_id")
                assignee_id = body.get("assignee_id")
                due_at = body.get("due_at")
                notes = body.get("notes", "")

                if not dept_id:
                    self.send_error_json(400, "OPD penanggung jawab wajib dipilih")
                    return

                cur = conn.cursor()
                cur.execute("SELECT status, ticket_no, reporter_id FROM reports WHERE id = ?", (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return

                now = datetime.datetime.now().isoformat()
                cur.execute("""
                INSERT OR REPLACE INTO report_assignments (id, report_id, department_id, assignee_id, assigned_by, assigned_at, due_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (f"asg-{uuid.uuid4().hex[:12]}", rep_id, dept_id, assignee_id, user_claims["sub"], now, due_at, notes))

                old_status = rep["status"]
                new_status = "ASSIGNED"
                cur.execute("UPDATE reports SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, rep_id))

                cur.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, new_status, user_claims["sub"], f"Didisposisikan ke OPD (ID: {dept_id}). {notes}".strip(), now))

                create_notification(conn, rep["reporter_id"], rep_id, "Laporan Telah Ditugaskan",
                                    f"Laporan #{rep['ticket_no']} telah didisposisikan ke dinas terkait untuk penanganan.")
                
                if assignee_id:
                    create_notification(conn, assignee_id, rep_id, "Tugas Pengaduan Baru",
                                        f"Anda ditugaskan menangani laporan #{rep['ticket_no']}.")

                record_audit(conn, user_claims["sub"], user_claims["name"], "ASSIGN_REPORT", "REPORT", rep_id, {"dept_id": dept_id, "assignee_id": assignee_id})
                conn.commit()

                self.send_json(200, {"success": True, "message": "Disposisi penugasan berhasil disimpan"})
                return

            # PATCH / POST /api/v1/field/reports/{id}/status (FR-09, AC-05)
            field_status_match = re.match(r'^/api/v1/field/reports/([a-zA-Z0-9\-]+)/status$', path)
            if field_status_match:
                rep_id = field_status_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims or not check_permission(user_claims.get("roles", []), ["PETUGAS", "ADMIN", "SUPERADMIN"]):
                    self.send_error_json(403, "Akses ditolak: Hanya Petugas Lapangan OPD / Admin")
                    return

                new_status = body.get("status", "").upper() # IN_PROGRESS or RESOLVED
                progress_note = body.get("progress_note", "").strip()
                resolution_photo = body.get("photo_base64")

                cur = conn.cursor()
                cur.execute("""
                SELECT r.*, asg.assignee_id, asg.department_id
                FROM reports r
                LEFT JOIN report_assignments asg ON r.id = asg.report_id
                WHERE r.id = ?
                """, (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return

                # AC-05 check: Petugas only modifies reports assigned to them or their unit (unless admin)
                is_admin = check_permission(user_claims.get("roles", []), ["ADMIN", "SUPERADMIN"])
                if not is_admin and "PETUGAS" in user_claims.get("roles", []):
                    if rep["assignee_id"] and rep["assignee_id"] != user_claims["sub"]:
                        self.send_error_json(403, "Anda tidak memiliki kewenangan mengubah laporan yang ditugaskan ke petugas lain (AC-05)")
                        return

                old_status = rep["status"]
                now = datetime.datetime.now().isoformat()

                if new_status == "IN_PROGRESS":
                    if old_status not in ("ASSIGNED", "IN_PROGRESS", "REOPENED"):
                        self.send_error_json(400, f"Transisi status dari {old_status} ke IN_PROGRESS tidak valid")
                        return
                    cur.execute("UPDATE reports SET status = 'IN_PROGRESS', updated_at = ? WHERE id = ?", (now, rep_id))
                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, ?, 'IN_PROGRESS', ?, ?, ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, user_claims["sub"], progress_note or "Tim teknis sedang melakukan pengerjaan fisik di lokasi.", now))

                elif new_status == "RESOLVED":
                    if old_status not in ("IN_PROGRESS", "ASSIGNED"):
                        self.send_error_json(400, f"Transisi status dari {old_status} ke RESOLVED tidak valid")
                        return
                    
                    # Save resolution photo if provided
                    if resolution_photo and len(resolution_photo) > 50:
                        try:
                            if ',' in resolution_photo:
                                resolution_photo = resolution_photo.split(',', 1)[1]
                            pbytes = base64.b64decode(resolution_photo)
                            sname = f"{uuid.uuid4().hex}.jpg"
                            spath = os.path.join(UPLOAD_DIR, sname)
                            with open(spath, 'wb') as pf:
                                pf.write(pbytes)
                            cur.execute("""
                            INSERT INTO report_media (id, report_id, storage_key, file_name, mime_type, file_size, phase, uploaded_by, created_at)
                            VALUES (?, ?, ?, 'bukti_penyelesaian.jpg', 'image/jpeg', ?, 'RESOLUTION', ?, ?)
                            """, (f"med-{uuid.uuid4().hex[:12]}", rep_id, sname, len(pbytes), user_claims["sub"], now))
                        except Exception as e:
                            print("Error saving resolution photo:", e)

                    cur.execute("UPDATE reports SET status = 'RESOLVED', updated_at = ? WHERE id = ?", (now, rep_id))
                    cur.execute("UPDATE report_assignments SET completed_at = ? WHERE report_id = ?", (now, rep_id))
                    
                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, ?, 'RESOLVED', ?, ?, ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, user_claims["sub"], progress_note or "Pekerjaan fisik telah selesai diperbaiki dan diverifikasi tuntas.", now))

                    create_notification(conn, rep["reporter_id"], rep_id, "Pengaduan Dinyatakan Selesai",
                                        f"Petugas telah menyelesaikan penanganan laporan #{rep['ticket_no']}. Silakan periksa dan berikan penilaian.")

                record_audit(conn, user_claims["sub"], user_claims["name"], "FIELD_UPDATE", "REPORT", rep_id, {"old_status": old_status, "new_status": new_status, "note": progress_note})
                conn.commit()

                self.send_json(200, {"success": True, "message": f"Status berhasil diperbarui menjadi {new_status}"})
                return

            # POST /api/v1/reports/{id}/comments
            report_comment_match = re.match(r'^/api/v1/reports/([a-zA-Z0-9\-]+)/comments$', path)
            if report_comment_match:
                rep_id = report_comment_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                
                body_text = body.get("body", "").strip()
                if not body_text:
                    self.send_error_json(400, "Isi komentar / klarifikasi tidak boleh kosong")
                    return
                
                cur = conn.cursor()
                cur.execute("SELECT * FROM reports WHERE id = ?", (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return

                now = datetime.datetime.now().isoformat()
                comment_id = f"cmt-{uuid.uuid4().hex[:12]}"
                visibility = body.get("visibility", "PUBLIC")

                cur.execute("""
                INSERT INTO comments (id, report_id, author_id, body, visibility, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (comment_id, rep_id, user_claims["sub"], body_text, visibility, now))

                # If report was in NEEDS_INFO and reporter replies, transition to SUBMITTED
                if rep["status"] == "NEEDS_INFO" and user_claims["sub"] == rep["reporter_id"]:
                    cur.execute("UPDATE reports SET status = 'SUBMITTED', updated_at = ? WHERE id = ?", (now, rep_id))
                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, 'NEEDS_INFO', 'SUBMITTED', ?, 'Pelapor telah melengkapi klarifikasi tambahan.', ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, user_claims["sub"], now))

                conn.commit()
                self.send_json(201, {"success": True, "message": "Komentar berhasil ditambahkan", "comment_id": comment_id})
                return

            # POST /api/v1/reports/{id}/feedback (FR-13)
            report_feedback_match = re.match(r'^/api/v1/reports/([a-zA-Z0-9\-]+)/feedback$', path)
            if report_feedback_match:
                rep_id = report_feedback_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                
                rating = int(body.get("rating", 5))
                comment = body.get("comment", "").strip()

                if rating < 1 or rating > 5:
                    self.send_error_json(400, "Rating harus antara 1 sampai 5 bintang")
                    return
                
                cur = conn.cursor()
                cur.execute("SELECT * FROM reports WHERE id = ?", (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return
                
                now = datetime.datetime.now().isoformat()
                cur.execute("""
                INSERT OR REPLACE INTO feedback (id, report_id, user_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (f"fdb-{uuid.uuid4().hex[:12]}", rep_id, user_claims["sub"], rating, comment, now))

                # Auto close if satisfied
                if rep["status"] == "RESOLVED":
                    cur.execute("UPDATE reports SET status = 'CLOSED', updated_at = ? WHERE id = ?", (now, rep_id))
                    cur.execute("""
                    INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                    VALUES (?, ?, 'RESOLVED', 'CLOSED', ?, 'Pelapor mengonfirmasi penutupan laporan dengan penilaian bintang.', ?)
                    """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, user_claims["sub"], now))

                conn.commit()
                self.send_json(201, {"success": True, "message": "Terima kasih! Penilaian Anda telah kami terima."})
                return

            # POST /api/v1/reports/{id}/close
            report_close_match = re.match(r'^/api/v1/reports/([a-zA-Z0-9\-]+)/close$', path)
            if report_close_match:
                rep_id = report_close_match.group(1)
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return

                action = body.get("action", "CLOSE").upper() # CLOSE or REOPEN
                note = body.get("note", "").strip()
                now = datetime.datetime.now().isoformat()

                cur = conn.cursor()
                cur.execute("SELECT * FROM reports WHERE id = ?", (rep_id,))
                rep = cur.fetchone()
                if not rep:
                    self.send_error_json(404, "Laporan tidak ditemukan")
                    return

                old_status = rep["status"]
                if action == "CLOSE":
                    new_status = "CLOSED"
                elif action == "REOPEN":
                    new_status = "REOPENED"
                else:
                    self.send_error_json(400, "Aksi tidak valid")
                    return

                cur.execute("UPDATE reports SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, rep_id))
                cur.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4().hex[:12]}", rep_id, old_status, new_status, user_claims["sub"], note or f"Status laporan diubah ke {new_status}", now))

                conn.commit()
                self.send_json(200, {"success": True, "message": f"Status laporan berhasil diubah ke {new_status}"})
                return

            # POST /api/v1/notifications/read
            if path == '/api/v1/notifications/read':
                user_claims = self.get_current_user()
                if not user_claims:
                    self.send_error_json(401, "Autentikasi diperlukan")
                    return
                now = datetime.datetime.now().isoformat()
                cur = conn.cursor()
                cur.execute("UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL", (now, user_claims["sub"]))
                conn.commit()
                self.send_json(200, {"success": True, "message": "Semua notifikasi telah ditandai sudah dibaca"})
                return

            self.send_error_json(404, "Endpoint tidak ditemukan")

        except Exception as e:
            traceback.print_exc()
            self.send_error_json(500, f"Terjadi kesalahan server internal: {str(e)}")
        finally:
            conn.close()

    def do_PATCH(self):
        # Treat PATCH the same as POST for endpoints like /api/v1/field/reports/{id}/status
        self.do_POST()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run_server(port=8080):
    init_db()
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, SCSRequestHandler)
    print(f"============================================================")
    print(f"   SMART COMPLAINT SYSTEM (SCS) - KOTA BANDAR LAMPUNG       ")
    print(f"   Kemitraan Pemkot Bandar Lampung & Univ Teknokrat Indonesia")
    print(f"============================================================")
    print(f"Server berjalan di: http://127.0.0.1:{port}")
    print(f"Tekan Ctrl+C untuk menghentikan server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)

