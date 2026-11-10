-- ==============================================================================
-- Schema Migration: Smart Complaint System (SCS) - Kota Bandar Lampung
-- Compliant with PRD Section 11, 12, & 13
-- PostgreSQL 16 + PostGIS
-- ==============================================================================

-- 1. Enable PostGIS Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- 2. Users Table (PRD 13)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(25),
    nik VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Roles Table (PRD 13)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(100) NOT NULL
);

-- 4. User Roles Join Table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 5. Departments (OPD) Table (PRD 13)
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    area_code VARCHAR(20) DEFAULT '1871', -- Kota Bandar Lampung
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. Categories Table (PRD 13)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    default_priority VARCHAR(20) DEFAULT 'SEDANG',
    icon VARCHAR(50) DEFAULT 'report_problem',
    default_dept_id INT REFERENCES departments(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- 7. Reports Table (PRD 13 & FR-04, FR-05)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_no VARCHAR(50) UNIQUE NOT NULL,
    reporter_id UUID NOT NULL REFERENCES users(id),
    category_id INT NOT NULL REFERENCES categories(id),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    address_text TEXT NOT NULL,
    district VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    priority VARCHAR(20) NOT NULL DEFAULT 'SEDANG',
    rejection_reason TEXT,
    clarification_request TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Spatial GiST Index for PostGIS Location Queries (PRD 11.2, 11.3)
CREATE INDEX IF NOT EXISTS idx_reports_location_gist ON reports USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);

-- 8. Report Media Table (PRD 13 & NFR-05)
CREATE TABLE IF NOT EXISTS report_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    storage_key VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    phase VARCHAR(20) DEFAULT 'INITIAL', -- INITIAL or RESOLUTION
    checksum VARCHAR(64),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Report Assignments Table (PRD 13)
CREATE TABLE IF NOT EXISTS report_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    department_id INT NOT NULL REFERENCES departments(id),
    assignee_id UUID REFERENCES users(id),
    assigned_by UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT
);

-- 10. Report Status History Table (Append-only audit, PRD 13)
CREATE TABLE IF NOT EXISTS report_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    old_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    note TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_status_history_report ON report_status_history(report_id);

-- 11. Comments Table (PRD 13)
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    body TEXT NOT NULL,
    visibility VARCHAR(20) DEFAULT 'PUBLIC', -- PUBLIC or INTERNAL
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. In-App Notifications Table (PRD 13 & FR-10)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
    channel VARCHAR(30) DEFAULT 'IN_APP',
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, read_at);

-- 13. Audit Logs Table (PRD 13 & FR-12)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID,
    actor_name VARCHAR(150),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. Feedback Table (PRD 13 & FR-13)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- Initial Seeding
-- ==============================================================================
INSERT INTO roles (role_code, role_name) VALUES
('MASYARAKAT', 'Masyarakat / Pelapor Warga'),
('ADMIN', 'Admin / Verifikator Pengaduan'),
('PETUGAS', 'Petugas / Unit Pelaksana Lapangan OPD'),
('PIMPINAN', 'Pimpinan / Pengawas Pemerintah Kota'),
('SUPERADMIN', 'Super Admin Konfigurasi Sistem')
ON CONFLICT (role_code) DO NOTHING;

INSERT INTO departments (name, code, area_code, description) VALUES
('Dinas Bina Marga & Bina Konstruksi (PUPR)', 'PUPR', '1871', 'Penanganan jalan rusak, jembatan, dan trotoar'),
('Dinas Lingkungan Hidup (DLH)', 'DLH', '1871', 'Pengelolaan sampah, TPS, dan kebersihan ruang terbuka'),
('Dinas Perhubungan (Dishub)', 'DISHUB', '1871', 'Pengendalian lalu lintas, rambu, dan Penerangan Jalan Umum (PJU)'),
('Badan Penanggulangan Bencana Daerah (BPBD)', 'BPBD', '1871', 'Pohon tumbang, evakuasi genangan, dan darurat bencana daerah')
ON CONFLICT (code) DO NOTHING;

INSERT INTO categories (name, code, description, default_priority, icon, default_dept_id) VALUES
('Jalan Rusak & Berlubang', 'ROAD_DAMAGE', 'Aspal amblas, lubang jalan protokol & jalan lingkungan', 'TINGGI', 'alt_route', 1),
('Lampu Penerangan Jalan (PJU) Mati', 'STREET_LIGHT', 'Lampu PJU padam, tiang miring, korsleting kabel PJU', 'SEDANG', 'lightbulb', 3),
('Sampah Menumpuk & Liar', 'GARBAGE', 'Penumpukan sampah liar di tepi jalan & TPS meluap', 'SEDANG', 'delete', 2),
('Drainase Tersumbat & Genangan', 'DRAINAGE', 'Saluran air tertutup sedimen, selokan tersumbat sampah', 'TINGGI', 'water_drop', 1),
('Pohon Tumbang & Ranting Rawan', 'FALLEN_TREE', 'Pohon roboh menghalangi jalan atau ranting rapuh membahayakan', 'DARURAT', 'nature', 4)
ON CONFLICT (code) DO NOTHING;

