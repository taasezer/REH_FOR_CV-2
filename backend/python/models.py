"""
REH_FOR_CV-2 OSINT Rehber - Database Models
Kullanıcı ve Kişi modelleri
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Kullanici(db.Model):
    """Kullanıcı modeli - Sisteme giriş yapan kullanıcılar"""
    __tablename__ = 'kullanici'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(80), unique=True, nullable=False, index=True)
    sifre_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # İlişki: Bir kullanıcının birden fazla kişisi olabilir
    kisiler = db.relationship('Kisi', backref='sahip', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'kullanici_adi': self.kullanici_adi,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class Kisi(db.Model):
    """Kişi modeli - Rehbere eklenen kişiler"""
    __tablename__ = 'kisi'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False, index=True)
    
    # Temel bilgiler
    isim = db.Column(db.String(100), nullable=False, index=True)
    soyisim = db.Column(db.String(100), nullable=True)
    eposta = db.Column(db.String(120), nullable=True, index=True)
    telefon = db.Column(db.String(20), nullable=True, index=True)
    telefon_2 = db.Column(db.String(20), nullable=True)
    adres = db.Column(db.String(500), nullable=True)
    
    # Konum bilgileri
    enlem = db.Column(db.Float, nullable=True)
    boylam = db.Column(db.Float, nullable=True)
    sehir = db.Column(db.String(100), nullable=True)
    ulke = db.Column(db.String(100), nullable=True)
    
    # OSINT alanları (Phase 3'te doldurulacak)
    email_valid = db.Column(db.Boolean, nullable=True)
    email_type = db.Column(db.String(20), nullable=True)  # corporate, personal, disposable
    phone_country = db.Column(db.String(10), nullable=True)
    phone_carrier = db.Column(db.String(50), nullable=True)
    phone_type = db.Column(db.String(20), nullable=True)  # mobile, landline
    social_profiles = db.Column(db.JSON, nullable=True)
    
    # Meta bilgiler
    notlar = db.Column(db.Text, nullable=True)
    etiketler = db.Column(db.JSON, nullable=True)  # ["aile", "iş", "arkadaş"]
    favori = db.Column(db.Boolean, default=False)
    
    # Zaman damgaları
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enriched_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'kullanici_id': self.kullanici_id,
            'isim': self.isim,
            'soyisim': self.soyisim,
            'tam_isim': f"{self.isim} {self.soyisim}" if self.soyisim else self.isim,
            'eposta': self.eposta,
            'telefon': self.telefon,
            'telefon_2': self.telefon_2,
            'adres': self.adres,
            'enlem': self.enlem,
            'boylam': self.boylam,
            'sehir': self.sehir,
            'ulke': self.ulke,
            'email_valid': self.email_valid,
            'email_type': self.email_type,
            'phone_country': self.phone_country,
            'phone_carrier': self.phone_carrier,
            'phone_type': self.phone_type,
            'social_profiles': self.social_profiles,
            'notlar': self.notlar,
            'etiketler': self.etiketler,
            'favori': self.favori,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'enriched_at': self.enriched_at.isoformat() if self.enriched_at else None
        }
    
    def to_dict_basic(self):
        """Harita ve liste görünümü için minimal veri"""
        return {
            'id': self.id,
            'isim': self.isim,
            'soyisim': self.soyisim,
            'tam_isim': f"{self.isim} {self.soyisim}" if self.soyisim else self.isim,
            'eposta': self.eposta,
            'telefon': self.telefon,
            'adres': self.adres,
            'enlem': self.enlem,
            'boylam': self.boylam,
            'favori': self.favori,
            'etiketler': self.etiketler
        }


class AuditLog(db.Model):
    """Audit log modeli - Tüm işlemlerin kaydı (Phase 8)"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    entity_type = db.Column(db.String(50), nullable=False)  # Kisi, Kullanici
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'kullanici_id': self.kullanici_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
