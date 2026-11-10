"""
Database module for Smart Complaint System (SCS) Kota Bandar Lampung.
Implements the conceptual schema from PRD Section 13 using SQLite with spatial calculation support,
ACID transactions, audit logging, and seed data.
"""

import sqlite3
import os
import uuid
import datetime
import math
import hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "scs.db")

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates (Haversine formula)."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_db():
    """Get database connection with row factory and spatial distance function."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Register spatial function for SQLite
    conn.create_function("st_distance", 4, haversine_distance)
    return conn

def hash_password(password: str) -> str:
    """Adaptive password hashing using PBKDF2-HMAC-SHA256 (NFR-02)."""
    salt = "scs_bandarlampung_salt_2026"
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def init_db():
    """Create all tables conforming to PRD Section 13 and populate seed data."""
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        nik TEXT,
        password_hash TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Roles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_code TEXT UNIQUE NOT NULL,
        role_name TEXT NOT NULL
    );
    """)

    # 3. User Roles join table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    );
    """)

    # 4. Departments (OPD) table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        area_code TEXT DEFAULT '1871',
        description TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)

    # 5. Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        default_priority TEXT DEFAULT 'SEDANG',
        icon TEXT DEFAULT 'report_problem',
        default_dept_id INTEGER,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (default_dept_id) REFERENCES departments(id)
    );
    """)

    # 6. Reports (Pengaduan) table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        ticket_no TEXT UNIQUE NOT NULL,
        reporter_id TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        address_text TEXT NOT NULL,
        district TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'SUBMITTED',
        priority TEXT NOT NULL DEFAULT 'SEDANG',
        rejection_reason TEXT,
        clarification_request TEXT,
        is_anonymous INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (reporter_id) REFERENCES users(id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );
    """)

    # 7. Report Media table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report_media (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        storage_key TEXT NOT NULL,
        file_name TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        phase TEXT DEFAULT 'INITIAL', -- INITIAL (pelapor) or RESOLUTION (petugas)
        checksum TEXT,
        uploaded_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    );
    """)

    # 8. Report Assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report_assignments (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        assignee_id TEXT,
        assigned_by TEXT NOT NULL,
        assigned_at TEXT NOT NULL,
        due_at TEXT,
        completed_at TEXT,
        notes TEXT,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES departments(id),
        FOREIGN KEY (assignee_id) REFERENCES users(id),
        FOREIGN KEY (assigned_by) REFERENCES users(id)
    );
    """)

    # 9. Report Status History table (Append-only audit trail)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report_status_history (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        changed_by TEXT NOT NULL,
        note TEXT,
        changed_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users(id)
    );
    """)

    # 10. Comments / Klarifikasi table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        author_id TEXT NOT NULL,
        body TEXT NOT NULL,
        visibility TEXT DEFAULT 'PUBLIC', -- PUBLIC or INTERNAL
        created_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id)
    );
    """)

    # 11. In-App Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        report_id TEXT,
        channel TEXT DEFAULT 'IN_APP',
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        read_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE SET NULL
    );
    """)

    # 12. Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        actor_name TEXT,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        metadata TEXT, -- JSON string
        created_at TEXT NOT NULL
    );
    """)

    # 13. Feedback / Rating table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        report_id TEXT UNIQUE NOT NULL,
        user_id TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # Create Indexes for high performance query matching PRD Section 11 & 13
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_district ON reports(district);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_history_report ON report_status_history(report_id);")

    conn.commit()

    # Seed initial roles, departments, categories, and test users if empty
    seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    """Seed system roles, OPDs, categories, demo users, and demo complaints."""
    cursor = conn.cursor()
    
    # Check if roles exist
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        roles = [
            ("MASYARAKAT", "Masyarakat / Pelapor Warga"),
            ("ADMIN", "Admin / Verifikator Pengaduan"),
            ("PETUGAS", "Petugas / Unit Pelaksana Lapangan OPD"),
            ("PIMPINAN", "Pimpinan / Pengawas Pemerintah Kota"),
            ("SUPERADMIN", "Super Admin Konfigurasi Sistem")
        ]
        cursor.executemany("INSERT INTO roles (role_code, role_name) VALUES (?, ?)", roles)
    
    # Check if departments exist
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        depts = [
            ("Dinas Bina Marga & Bina Konstruksi (PUPR)", "PUPR", "1871", "Penanganan jalan rusak, jembatan, dan trotoar"),
            ("Dinas Lingkungan Hidup (DLH)", "DLH", "1871", "Pengelolaan sampah, TPS, dan kebersihan ruang terbuka"),
            ("Dinas Perhubungan (Dishub)", "DISHUB", "1871", "Pengendalian lalu lintas, rambu, dan Penerangan Jalan Umum (PJU)"),
            ("Badan Penanggulangan Bencana Daerah (BPBD)", "BPBD", "1871", "Pohon tumbang, evakuasi genangan, dan darurat bencana daerah"),
            ("Dinas Pemadam Kebakaran & Penyelamatan", "DAMKAR", "1871", "Penyelamatan darurat non-kebakaran & evakuasi hewan berbisa"),
            ("Satuan Polisi Pamong Praja (Satpol PP)", "SATPOLPP", "1871", "Penertiban ketertiban umum dan gangguan fasilitas publik"),
            ("Dinas Perumahan & Kawasan Permukiman", "PERKIM", "1871", "Saluran drainase pemukiman dan sanitasi lingkungan")
        ]
        cursor.executemany("INSERT INTO departments (name, code, area_code, description) VALUES (?, ?, ?, ?)", depts)

    # Check if categories exist
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cats = [
            ("Jalan Rusak & Berlubang", "ROAD_DAMAGE", "Aspal amblas, lubang jalan protokol & jalan lingkungan", "TINGGI", "alt_route", 1),
            ("Lampu Penerangan Jalan (PJU) Mati", "STREET_LIGHT", "Lampu PJU padam, tiang miring, korsleting kabel PJU", "SEDANG", "lightbulb", 3),
            ("Sampah Menumpuk & Liar", "GARBAGE", "Penumpukan sampah liar di tepi jalan & TPS meluap", "SEDANG", "delete", 2),
            ("Drainase Tersumbat & Genangan", "DRAINAGE", "Saluran air tertutup sedimen, selokan tersumbat sampah", "TINGGI", "water_drop", 1),
            ("Pohon Tumbang & Ranting Rawan", "FALLEN_TREE", "Pohon roboh menghalangi jalan atau ranting rapuh membahayakan", "DARURAT", "nature", 4),
            ("Kerusakan Fasilitas Umum", "PUBLIC_FACILITY", "Halte bus rusak, rambu roboh, trotoar hancur, taman kota rusak", "RENDAH", "domain", 6)
        ]
        cursor.executemany("INSERT INTO categories (name, code, description, default_priority, icon, default_dept_id) VALUES (?, ?, ?, ?, ?, ?)", cats)

    # Check if users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().isoformat()
        
        users_data = [
            # id, full_name, email, phone, nik, role_code
            ("usr-superadmin-01", "Gilang Ramadan", "superadmin@lampung.go.id", "08127110001", "1871040101990001", "SUPERADMIN"),
            ("usr-admin-01", "Bambang Irawan, S.STP", "admin@lampung.go.id", "08127110002", "1871040202850002", "ADMIN"),
            ("usr-petugas-pupr-01", "Ir. Hendra Saputra (PUPR)", "petugas.pupr@lampung.go.id", "08127110003", "1871040303880003", "PETUGAS"),
            ("usr-petugas-dlh-01", "Agus Setiawan (DLH)", "petugas.dlh@lampung.go.id", "08127110004", "1871040404900004", "PETUGAS"),
            ("usr-pimpinan-01", "Dr. H. Zulkifli, M.M.", "pimpinan@lampung.go.id", "08127110005", "1871040505700005", "PIMPINAN"),
            ("usr-warga-01", "Dra. Rahayu", "warga@lampung.go.id", "08127110006", "1871040606820006", "MASYARAKAT"),
            ("usr-warga-02", "Budi Santoso", "warga2@lampung.go.id", "08127110007", "1871040707950007", "MASYARAKAT")
        ]

        default_pwd_hash = hash_password("password123")
        for uid, name, email, phone, nik, role_code in users_data:
            cursor.execute("""
            INSERT INTO users (id, full_name, email, phone, nik, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (uid, name, email, phone, nik, default_pwd_hash, now))
            
            cursor.execute("SELECT id FROM roles WHERE role_code = ?", (role_code,))
            role_row = cursor.fetchone()
            if role_row:
                cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (uid, role_row[0]))

        # Seed sample reports across Bandar Lampung districts
        sample_reports = [
            {
                "id": "rep-bdl-001",
                "ticket_no": "SCS-20261110-8842",
                "reporter_id": "usr-warga-01",
                "category_id": 1, # Jalan Rusak
                "title": "Aspal Ambles dan Retak Lebar di Jalan ZA Pagar Alam",
                "description": "Terdapat lubang berdiameter sekitar 1,5 meter dengan kedalaman 15 cm di lajur kiri arah Rajabasa persis di depan Universitas Teknokrat Indonesia. Sangat membahayakan pengendara sepeda motor terutama pada malam hari.",
                "lat": -5.378923,
                "lng": 105.254101,
                "address_text": "Jl. ZA Pagar Alam No. 9-11, Labuhan Ratu, Kec. Kedaton",
                "district": "Kedaton",
                "status": "IN_PROGRESS",
                "priority": "TINGGI",
                "dept_id": 1,
                "assignee_id": "usr-petugas-pupr-01"
            },
            {
                "id": "rep-bdl-002",
                "ticket_no": "SCS-20261110-9012",
                "reporter_id": "usr-warga-02",
                "category_id": 5, # Pohon Tumbang
                "title": "Pohon Trembesi Rawan Roboh Menimpa Kabel PLN di Raden Intan",
                "description": "Dahan pohon pelindung jalan berukuran besar patah dan tersangkut kabel listrik dan optik di dekat perempatan Jl. Raden Intan dan Jl. Ahmad Yani.",
                "lat": -5.412432,
                "lng": 105.259104,
                "address_text": "Jl. Raden Intan, Kel. Enggal, Kec. Tanjung Karang Pusat",
                "district": "Tanjung Karang Pusat",
                "status": "SUBMITTED",
                "priority": "DARURAT",
                "dept_id": None,
                "assignee_id": None
            },
            {
                "id": "rep-bdl-003",
                "ticket_no": "SCS-20261109-7719",
                "reporter_id": "usr-warga-01",
                "category_id": 3, # Sampah
                "title": "Tumpukan Sampah Liar Meluber ke Bahu Jalan di Pasar Koga",
                "description": "TPS liar di gang samping Pasar Koga sudah 4 hari tidak diangkut sehingga menimbulkan aroma menyengat dan mengganggu aktivitas warga.",
                "lat": -5.395120,
                "lng": 105.263840,
                "address_text": "Jl. Teuku Umar No. 45, Sidodadi, Kec. Kedaton",
                "district": "Kedaton",
                "status": "RESOLVED",
                "priority": "SEDANG",
                "dept_id": 2,
                "assignee_id": "usr-petugas-dlh-01"
            },
            {
                "id": "rep-bdl-004",
                "ticket_no": "SCS-20261108-6531",
                "reporter_id": "usr-warga-02",
                "category_id": 2, # Lampu Jalan
                "title": "Lampu PJU Padam Sepanjang 300 Meter di Jalan Sultan Agung",
                "description": "5 titik tiang lampu penerangan jalan mati berturut-turut dari arah jalur dua flyover Mall Boemi Kedaton menuju Way Halim. Kawasan menjadi sangat gelap saat malam.",
                "lat": -5.383120,
                "lng": 105.268950,
                "address_text": "Jl. Sultan Agung, Sepang Jaya, Kec. Way Halim",
                "district": "Way Halim",
                "status": "ASSIGNED",
                "priority": "SEDANG",
                "dept_id": 3,
                "assignee_id": None
            },
            {
                "id": "rep-bdl-005",
                "ticket_no": "SCS-20261107-5120",
                "reporter_id": "usr-warga-01",
                "category_id": 4, # Drainase
                "title": "Drainase Tersumbat Menimbulkan Banjir Genangan di Teluk Betung",
                "description": "Gorong-gorong pembuangan air tersumbat endapan lumpur dan sampah padat menyebabkan air meluap setinggi 30 cm setiap hujan deras.",
                "lat": -5.441200,
                "lng": 105.271100,
                "address_text": "Jl. Ikan Hiu, Pesawahan, Kec. Teluk Betung Selatan",
                "district": "Teluk Betung Selatan",
                "status": "CLOSED",
                "priority": "TINGGI",
                "dept_id": 1,
                "assignee_id": "usr-petugas-pupr-01"
            }
        ]

        for rep in sample_reports:
            cursor.execute("""
            INSERT INTO reports (id, ticket_no, reporter_id, category_id, title, description,
                                lat, lng, address_text, district, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rep["id"], rep["ticket_no"], rep["reporter_id"], rep["category_id"], rep["title"], rep["description"],
                  rep["lat"], rep["lng"], rep["address_text"], rep["district"], rep["status"], rep["priority"], now, now))
            
            # Status history
            cursor.execute("""
            INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"hist-{uuid.uuid4()}", rep["id"], None, "SUBMITTED", rep["reporter_id"], "Laporan baru diajukan oleh masyarakat via web portal.", now))

            if rep["status"] in ("ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"):
                cursor.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4()}", rep["id"], "SUBMITTED", "VERIFIED", "usr-admin-01", "Laporan telah diverifikasi keabsahan data lokasi dan foto bukti.", now))

                cursor.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4()}", rep["id"], "VERIFIED", "ASSIGNED", "usr-admin-01", f"Laporan didisposisikan ke OPD terkait.", now))

            if rep["status"] in ("IN_PROGRESS", "RESOLVED", "CLOSED"):
                cursor.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4()}", rep["id"], "ASSIGNED", "IN_PROGRESS", rep["assignee_id"] or "usr-petugas-pupr-01", "Tim teknis lapangan telah berada di lokasi dan memulai pengerjaan fisik.", now))

            if rep["status"] in ("RESOLVED", "CLOSED"):
                cursor.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4()}", rep["id"], "IN_PROGRESS", "RESOLVED", rep["assignee_id"] or "usr-petugas-pupr-01", "Penanganan selesai sesuai SOP. Pembersihan area telah tuntas.", now))

            if rep["status"] == "CLOSED":
                cursor.execute("""
                INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"hist-{uuid.uuid4()}", rep["id"], "RESOLVED", "CLOSED", "usr-warga-01", "Pelapor telah mengonfirmasi bahwa penanganan telah tuntas memuaskan.", now))

            # Assignment record if applicable
            if rep["dept_id"]:
                cursor.execute("""
                INSERT INTO report_assignments (id, report_id, department_id, assignee_id, assigned_by, assigned_at, due_at, completed_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (f"asg-{uuid.uuid4()}", rep["id"], rep["dept_id"], rep["assignee_id"], "usr-admin-01", now, None, None, "Harap ditindaklanjuti sesuai instruksi kerja standar OPD."))

            # Add feedback for closed report
            if rep["status"] == "CLOSED":
                cursor.execute("""
                INSERT INTO feedback (id, report_id, user_id, rating, comment, created_at)
                VALUES (?, ?, ?, 5, 'Respon cepat dan hasil perbaikan gorong-gorong sangat rapi. Terima kasih Pemkot Bandar Lampung!', ?)
                """, (f"fdb-{uuid.uuid4()}", rep["id"], rep["reporter_id"], now))

            # Sample notification
            cursor.execute("""
            INSERT INTO notifications (id, user_id, report_id, channel, title, body, created_at)
            VALUES (?, ?, ?, 'IN_APP', 'Status Laporan Diperbarui', 'Laporan #' || ? || ' saat ini berstatus ' || ?, ?)
            """, (f"notif-{uuid.uuid4()}", rep["reporter_id"], rep["id"], rep["ticket_no"], rep["status"], now))

        # Sample initial audit log
        cursor.execute("""
        INSERT INTO audit_logs (id, actor_id, actor_name, action, entity_type, entity_id, metadata, created_at)
        VALUES (?, 'usr-superadmin-01', 'Gilang Ramadan', 'SYSTEM_INITIALIZATION', 'SYSTEM', 'GLOBAL', '{"status":"ready", "city":"Bandar Lampung"}', ?)
        """, (f"aud-{uuid.uuid4()}", now))

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)

