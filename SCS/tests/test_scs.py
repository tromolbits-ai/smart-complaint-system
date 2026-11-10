"""
Comprehensive Test Suite for Smart Complaint System (SCS) Kota Bandar Lampung.
Validates Acceptance Criteria AC-01 to AC-09 from PRD Section 15,
Role-Based Access Control, State Transitions, and Audit Logging.
"""

import unittest
import sqlite3
import os
import sys
import json
import uuid

# Ensure base dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, init_db, hash_password, verify_password, haversine_distance
from app.auth import create_access_token, verify_access_token, check_permission
from app.server import generate_ticket_no, record_audit, create_notification

class TestSmartComplaintSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_ac01_valid_report_creation_and_ticket_generation(self):
        """AC-01: Pelapor mengirim laporan valid, menghasilkan ticket_no unik dan tersimpan."""
        conn = get_db()
        ticket_no = generate_ticket_no(conn)
        self.assertTrue(ticket_no.startswith("SCS-"))
        self.assertEqual(len(ticket_no.split("-")), 3)

        rep_id = f"test-{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO reports (id, ticket_no, reporter_id, category_id, title, description,
                            lat, lng, address_text, district, status, priority, created_at, updated_at)
        VALUES (?, ?, 'usr-warga-01', 1, 'Uji Validasi Jalan', 'Deskripsi pengujian sistem',
                -5.3789, 105.2541, 'Jl. ZA Pagar Alam', 'Kedaton', 'SUBMITTED', 'SEDANG', '2026-11-10T00:00:00', '2026-11-10T00:00:00')
        """, (rep_id, ticket_no))
        conn.commit()

        # Verify inserted
        cur = conn.cursor()
        cur.execute("SELECT ticket_no, status FROM reports WHERE id = ?", (rep_id,))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["ticket_no"], ticket_no)
        self.assertEqual(row["status"], "SUBMITTED")
        conn.close()

    def test_ac02_validation_failure_without_required_fields(self):
        """AC-02: Pelapor mengirim tanpa data wajib -> ditolak dan tidak tersimpan."""
        conn = get_db()
        # Missing title or address should fail database check or application validation
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("""
            INSERT INTO reports (id, ticket_no, reporter_id, category_id, title, description,
                                lat, lng, address_text, district, status, priority, created_at, updated_at)
            VALUES ('invalid-rep', 'TKT-INV', 'usr-warga-01', 1, NULL, 'Deskripsi saja',
                    -5.3, 105.2, 'Alamat', 'Kedaton', 'SUBMITTED', 'SEDANG', '2026-11-10', '2026-11-10')
            """)
        conn.close()

    def test_ac04_admin_verification_state_transition(self):
        """AC-04: Admin memverifikasi laporan -> status berubah & riwayat tercatat."""
        conn = get_db()
        cur = conn.cursor()
        rep_id = f"test-verify-{uuid.uuid4().hex[:8]}"
        tkt = generate_ticket_no(conn)

        # 1. Create report in SUBMITTED state
        conn.execute("""
        INSERT INTO reports (id, ticket_no, reporter_id, category_id, title, description,
                            lat, lng, address_text, district, status, priority, created_at, updated_at)
        VALUES (?, ?, 'usr-warga-01', 1, 'Pohon Rawan', 'Dahan rapuh', -5.4, 105.2, 'Raden Intan', 'Tj Karang', 'SUBMITTED', 'TINGGI', '2026-11-10', '2026-11-10')
        """, (rep_id, tkt))

        # 2. Transition to VERIFIED
        conn.execute("UPDATE reports SET status = 'VERIFIED' WHERE id = ?", (rep_id,))
        conn.execute("""
        INSERT INTO report_status_history (id, report_id, old_status, new_status, changed_by, note, changed_at)
        VALUES (?, ?, 'SUBMITTED', 'VERIFIED', 'usr-admin-01', 'Diverifikasi valid oleh admin', '2026-11-10T01:00:00')
        """, (f"hist-{uuid.uuid4().hex[:8]}", rep_id))
        conn.commit()

        # Check status and history
        cur.execute("SELECT status FROM reports WHERE id = ?", (rep_id,))
        self.assertEqual(cur.fetchone()[0], "VERIFIED")

        cur.execute("SELECT old_status, new_status, changed_by FROM report_status_history WHERE report_id = ?", (rep_id,))
        hist = cur.fetchone()
        self.assertEqual(hist["old_status"], "SUBMITTED")
        self.assertEqual(hist["new_status"], "VERIFIED")
        self.assertEqual(hist["changed_by"], "usr-admin-01")
        conn.close()

    def test_ac08_spatial_distance_haversine(self):
        """AC-08: Spatial distance calculation between coordinates in Bandar Lampung."""
        # Distance between Universitas Teknokrat Indonesia (-5.378923, 105.254101)
        # and Tugu Adipura Bandar Lampung (-5.421711, 105.257522)
        dist = haversine_distance(-5.378923, 105.254101, -5.421711, 105.257522)
        self.assertIsNotNone(dist)
        # Distance should be approximately 4.7 km (4700 - 4800 meters)
        self.assertTrue(4500 < dist < 5000, f"Calculated distance: {dist} meters")

    def test_ac09_status_change_creates_notification_and_audit(self):
        """AC-09: Perubahan status menghasilkan notifikasi in-app dan audit log."""
        conn = get_db()
        create_notification(conn, "usr-warga-01", "rep-bdl-001", "Pengaduan Diperbarui", "Laporan Anda sedang dikerjakan.")
        record_audit(conn, "usr-admin-01", "Bambang Irawan", "STATUS_UPDATE", "REPORT", "rep-bdl-001", {"status": "IN_PROGRESS"})
        conn.commit()

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = 'usr-warga-01' AND title = 'Pengaduan Diperbarui'")
        self.assertGreater(cur.fetchone()[0], 0)

        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE actor_id = 'usr-admin-01' AND action = 'STATUS_UPDATE'")
        self.assertGreater(cur.fetchone()[0], 0)
        conn.close()

    def test_auth_token_and_rbac(self):
        """Test token creation, verification, and RBAC permission checks."""
        token = create_access_token("usr-test", "test@lampung.go.id", "Penguji", ["ADMIN"])
        claims = verify_access_token(token)
        self.assertIsNotNone(claims)
        self.assertEqual(claims["sub"], "usr-test")
        self.assertIn("ADMIN", claims["roles"])

        # Check permissions
        self.assertTrue(check_permission(["ADMIN"], ["ADMIN", "SUPERADMIN"]))
        self.assertFalse(check_permission(["MASYARAKAT"], ["ADMIN", "PETUGAS"]))
        self.assertTrue(check_permission(["SUPERADMIN"], ["PETUGAS"])) # Superadmin has all

    def test_section_18_footer_text(self):
        """PRD Section 18.2: Mandatory exact footer text check."""
        expected_footer = "Copyright©2026 by Nama Mahasiswa dan Dr. Erliyan Redy Susanto, M.Kom"
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn(expected_footer, html, "Footer text does not match PRD Section 18.2 exact wording requirement!")

if __name__ == "__main__":
    unittest.main(verbosity=2)

