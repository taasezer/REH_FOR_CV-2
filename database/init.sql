-- REH_FOR_CV-2 OSINT Rehber - Database Schema
-- PostgreSQL initialization script

-- Kullanıcı tablosu
CREATE TABLE IF NOT EXISTS kullanici (
    id SERIAL PRIMARY KEY,
    kullanici_adi VARCHAR(80) UNIQUE NOT NULL,
    sifre_hash VARCHAR(256) NOT NULL,
    email VARCHAR(120) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Kişi tablosu
CREATE TABLE IF NOT EXISTS kisi (
    id SERIAL PRIMARY KEY,
    kullanici_id INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE CASCADE,
    
    -- Temel bilgiler
    isim VARCHAR(100) NOT NULL,
    soyisim VARCHAR(100),
    eposta VARCHAR(120),
    telefon VARCHAR(20),
    telefon_2 VARCHAR(20),
    adres VARCHAR(500),
    
    -- Konum bilgileri
    enlem FLOAT,
    boylam FLOAT,
    sehir VARCHAR(100),
    ulke VARCHAR(100),
    
    -- OSINT alanları (Phase 3)
    email_valid BOOLEAN,
    email_type VARCHAR(20),
    phone_country VARCHAR(10),
    phone_carrier VARCHAR(50),
    phone_type VARCHAR(20),
    social_profiles JSONB,
    
    -- Meta bilgiler
    notlar TEXT,
    etiketler JSONB,
    favori BOOLEAN DEFAULT FALSE,
    
    -- Zaman damgaları
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enriched_at TIMESTAMP
);

-- Audit log tablosu
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    kullanici_id INTEGER REFERENCES kullanici(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_kisi_kullanici_id ON kisi(kullanici_id);
CREATE INDEX IF NOT EXISTS idx_kisi_isim ON kisi(isim);
CREATE INDEX IF NOT EXISTS idx_kisi_eposta ON kisi(eposta);
CREATE INDEX IF NOT EXISTS idx_kisi_telefon ON kisi(telefon);
CREATE INDEX IF NOT EXISTS idx_kisi_created_at ON kisi(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_kullanici_id ON audit_log(kullanici_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);

-- Updated_at trigger fonksiyonu
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Updated_at trigger'ları
DROP TRIGGER IF EXISTS update_kullanici_updated_at ON kullanici;
CREATE TRIGGER update_kullanici_updated_at
    BEFORE UPDATE ON kullanici
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_kisi_updated_at ON kisi;
CREATE TRIGGER update_kisi_updated_at
    BEFORE UPDATE ON kisi
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PHASE 5: İLİŞKİ TABLOSU
-- =============================================================================

CREATE TABLE IF NOT EXISTS iliski (
    id SERIAL PRIMARY KEY,
    kullanici_id INTEGER NOT NULL REFERENCES kullanici(id) ON DELETE CASCADE,
    kisi_1_id INTEGER NOT NULL REFERENCES kisi(id) ON DELETE CASCADE,
    kisi_2_id INTEGER NOT NULL REFERENCES kisi(id) ON DELETE CASCADE,
    iliski_tipi VARCHAR(50) NOT NULL DEFAULT 'diger',
    guc INTEGER DEFAULT 1 CHECK (guc >= 1 AND guc <= 10),
    yonlu BOOLEAN DEFAULT FALSE,
    otomatik BOOLEAN DEFAULT FALSE,
    tespit_nedeni VARCHAR(100),
    notlar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Aynı çift için tek ilişki
    CONSTRAINT unique_relationship UNIQUE (kullanici_id, kisi_1_id, kisi_2_id),
    
    -- Kendisiyle ilişki olamaz
    CONSTRAINT no_self_relationship CHECK (kisi_1_id != kisi_2_id)
);

-- İlişki indeksleri
CREATE INDEX IF NOT EXISTS idx_iliski_kullanici_id ON iliski(kullanici_id);
CREATE INDEX IF NOT EXISTS idx_iliski_kisi_1_id ON iliski(kisi_1_id);
CREATE INDEX IF NOT EXISTS idx_iliski_kisi_2_id ON iliski(kisi_2_id);
CREATE INDEX IF NOT EXISTS idx_iliski_tipi ON iliski(iliski_tipi);

-- İlişki updated_at trigger
DROP TRIGGER IF EXISTS update_iliski_updated_at ON iliski;
CREATE TRIGGER update_iliski_updated_at
    BEFORE UPDATE ON iliski
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
