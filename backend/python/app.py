"""
REH_FOR_CV-2 OSINT Rehber - Flask Backend API
Tam CRUD operasyonları, JWT authentication, rate limiting ve CORS desteği
"""

import os
import re
from datetime import timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from models import db, Kullanici, Kisi, AuditLog


# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = Flask(__name__)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://kullanici:sifre@db/rehber'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300
}

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'osint-rehber-gizli-anahtar-2026')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# CORS - Tüm originlere izin ver (development için)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*", "file://*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_email(email):
    """E-posta formatı doğrulama"""
    if not email:
        return True  # Opsiyonel alan
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Telefon formatı doğrulama"""
    if not phone:
        return True  # Opsiyonel alan
    # Sadece rakam, +, -, boşluk ve parantez kabul et
    pattern = r'^[\d\s\+\-\(\)]+$'
    return re.match(pattern, phone) is not None and len(re.sub(r'\D', '', phone)) >= 7


def geocode_address(address):
    """Adres geocoding - enlem/boylam bul"""
    if not address:
        return None, None
    try:
        geolocator = Nominatim(user_agent="osint_rehber_v2", timeout=10)
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderServiceError):
        pass
    return None, None


def log_action(action, entity_type, entity_id=None, details=None):
    """Audit log kaydı oluştur"""
    try:
        kullanici_id = None
        try:
            identity = get_jwt_identity()
            if identity:
                kullanici = Kullanici.query.filter_by(kullanici_adi=identity).first()
                if kullanici:
                    kullanici_id = kullanici.id
        except:
            pass
        
        log = AuditLog(
            kullanici_id=kullanici_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Audit log error: {e}")


def get_current_user():
    """JWT'den mevcut kullanıcıyı al"""
    identity = get_jwt_identity()
    return Kullanici.query.filter_by(kullanici_adi=identity).first()


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Geçersiz istek", "message": str(error)}), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Yetkisiz erişim", "message": "Giriş yapmanız gerekiyor"}), 401


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Bulunamadı", "message": str(error)}), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Çok fazla istek", "message": "Lütfen biraz bekleyin"}), 429


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Sunucu hatası", "message": "Bir hata oluştu"}), 500


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "osint-rehber"})


@app.route('/kayit', methods=['POST'])
@limiter.limit("5 per hour")
def kayit():
    """Yeni kullanıcı kaydı"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Veri bulunamadı"}), 400
    
    kullanici_adi = data.get('kullanici_adi', '').strip()
    sifre = data.get('sifre', '')
    email = data.get('email', '').strip() if data.get('email') else None
    
    # Validasyonlar
    if not kullanici_adi or len(kullanici_adi) < 3:
        return jsonify({"error": "Kullanıcı adı en az 3 karakter olmalı"}), 400
    
    if not sifre or len(sifre) < 6:
        return jsonify({"error": "Şifre en az 6 karakter olmalı"}), 400
    
    if email and not validate_email(email):
        return jsonify({"error": "Geçersiz e-posta formatı"}), 400
    
    # Kullanıcı adı kontrolü
    if Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first():
        return jsonify({"error": "Bu kullanıcı adı zaten kullanılıyor"}), 400
    
    # Email kontrolü
    if email and Kullanici.query.filter_by(email=email).first():
        return jsonify({"error": "Bu e-posta zaten kullanılıyor"}), 400
    
    # Kullanıcı oluştur
    sifre_hash = generate_password_hash(sifre)
    yeni_kullanici = Kullanici(
        kullanici_adi=kullanici_adi,
        sifre_hash=sifre_hash,
        email=email
    )
    
    db.session.add(yeni_kullanici)
    db.session.commit()
    
    log_action('CREATE', 'Kullanici', yeni_kullanici.id, {'kullanici_adi': kullanici_adi})
    
    return jsonify({
        "mesaj": "Kullanıcı başarıyla kaydedildi!",
        "kullanici": yeni_kullanici.to_dict()
    }), 201


@app.route('/giris', methods=['POST'])
@limiter.limit("10 per minute")
def giris():
    """Kullanıcı girişi - JWT token döndürür"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Veri bulunamadı"}), 400
    
    kullanici_adi = data.get('kullanici_adi', '').strip()
    sifre = data.get('sifre', '')
    
    if not kullanici_adi or not sifre:
        return jsonify({"error": "Kullanıcı adı ve şifre gerekli"}), 400
    
    kullanici = Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first()
    
    if not kullanici or not check_password_hash(kullanici.sifre_hash, sifre):
        log_action('LOGIN_FAILED', 'Kullanici', details={'kullanici_adi': kullanici_adi})
        return jsonify({"error": "Geçersiz kullanıcı adı veya şifre"}), 401
    
    if not kullanici.is_active:
        return jsonify({"error": "Hesabınız devre dışı"}), 401
    
    # Token oluştur
    access_token = create_access_token(identity=kullanici_adi)
    refresh_token = create_refresh_token(identity=kullanici_adi)
    
    log_action('LOGIN', 'Kullanici', kullanici.id)
    
    return jsonify({
        "mesaj": "Giriş başarılı!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "kullanici": kullanici.to_dict()
    })


@app.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def token_refresh():
    """Access token yenileme"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


@app.route('/profil', methods=['GET'])
@jwt_required()
def profil():
    """Mevcut kullanıcı profili"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404
    
    kisi_sayisi = Kisi.query.filter_by(kullanici_id=kullanici.id).count()
    
    return jsonify({
        "kullanici": kullanici.to_dict(),
        "istatistikler": {
            "toplam_kisi": kisi_sayisi
        }
    })


# =============================================================================
# KISI CRUD ENDPOINTS
# =============================================================================

@app.route('/kisi', methods=['POST'])
@jwt_required()
@limiter.limit("30 per hour")
def kisi_ekle():
    """Yeni kişi ekle"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Veri bulunamadı"}), 400
    
    # Zorunlu alan kontrolü
    isim = data.get('isim', '').strip()
    if not isim:
        return jsonify({"error": "İsim alanı zorunludur"}), 400
    
    # Opsiyonel alanlar
    eposta = data.get('eposta', '').strip() if data.get('eposta') else None
    telefon = data.get('telefon', '').strip() if data.get('telefon') else None
    adres = data.get('adres', '').strip() if data.get('adres') else None
    
    # Validasyonlar
    if eposta and not validate_email(eposta):
        return jsonify({"error": "Geçersiz e-posta formatı"}), 400
    
    if telefon and not validate_phone(telefon):
        return jsonify({"error": "Geçersiz telefon formatı"}), 400
    
    # Geocoding
    enlem, boylam = geocode_address(adres)
    
    # Kişi oluştur
    yeni_kisi = Kisi(
        kullanici_id=kullanici.id,
        isim=isim,
        soyisim=data.get('soyisim', '').strip() if data.get('soyisim') else None,
        eposta=eposta,
        telefon=telefon,
        telefon_2=data.get('telefon_2', '').strip() if data.get('telefon_2') else None,
        adres=adres,
        enlem=enlem,
        boylam=boylam,
        sehir=data.get('sehir', '').strip() if data.get('sehir') else None,
        ulke=data.get('ulke', '').strip() if data.get('ulke') else None,
        notlar=data.get('notlar', '').strip() if data.get('notlar') else None,
        etiketler=data.get('etiketler') if isinstance(data.get('etiketler'), list) else None,
        favori=bool(data.get('favori', False))
    )
    
    db.session.add(yeni_kisi)
    db.session.commit()
    
    log_action('CREATE', 'Kisi', yeni_kisi.id, {'isim': isim})
    
    return jsonify({
        "mesaj": "Kişi başarıyla eklendi!",
        "kisi": yeni_kisi.to_dict()
    }), 201


@app.route('/kisi/<int:kisi_id>', methods=['GET'])
@jwt_required()
def kisi_detay(kisi_id):
    """Kişi detayı getir"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisi = Kisi.query.filter_by(id=kisi_id, kullanici_id=kullanici.id).first()
    if not kisi:
        return jsonify({"error": "Kişi bulunamadı"}), 404
    
    log_action('READ', 'Kisi', kisi_id)
    
    return jsonify({"kisi": kisi.to_dict()})


@app.route('/kisi/<int:kisi_id>', methods=['PUT'])
@jwt_required()
def kisi_guncelle(kisi_id):
    """Kişi güncelle"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisi = Kisi.query.filter_by(id=kisi_id, kullanici_id=kullanici.id).first()
    if not kisi:
        return jsonify({"error": "Kişi bulunamadı"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Veri bulunamadı"}), 400
    
    # Güncellenecek alanlar
    guncellemeler = {}
    
    if 'isim' in data:
        isim = data['isim'].strip()
        if not isim:
            return jsonify({"error": "İsim boş olamaz"}), 400
        kisi.isim = isim
        guncellemeler['isim'] = isim
    
    if 'soyisim' in data:
        kisi.soyisim = data['soyisim'].strip() if data['soyisim'] else None
    
    if 'eposta' in data:
        eposta = data['eposta'].strip() if data['eposta'] else None
        if eposta and not validate_email(eposta):
            return jsonify({"error": "Geçersiz e-posta formatı"}), 400
        kisi.eposta = eposta
        guncellemeler['eposta'] = eposta
    
    if 'telefon' in data:
        telefon = data['telefon'].strip() if data['telefon'] else None
        if telefon and not validate_phone(telefon):
            return jsonify({"error": "Geçersiz telefon formatı"}), 400
        kisi.telefon = telefon
    
    if 'telefon_2' in data:
        kisi.telefon_2 = data['telefon_2'].strip() if data['telefon_2'] else None
    
    if 'adres' in data:
        adres = data['adres'].strip() if data['adres'] else None
        if adres != kisi.adres:  # Adres değiştiyse yeniden geocode
            kisi.adres = adres
            kisi.enlem, kisi.boylam = geocode_address(adres)
    
    if 'sehir' in data:
        kisi.sehir = data['sehir'].strip() if data['sehir'] else None
    
    if 'ulke' in data:
        kisi.ulke = data['ulke'].strip() if data['ulke'] else None
    
    if 'notlar' in data:
        kisi.notlar = data['notlar'].strip() if data['notlar'] else None
    
    if 'etiketler' in data:
        kisi.etiketler = data['etiketler'] if isinstance(data['etiketler'], list) else None
    
    if 'favori' in data:
        kisi.favori = bool(data['favori'])
    
    db.session.commit()
    
    log_action('UPDATE', 'Kisi', kisi_id, guncellemeler)
    
    return jsonify({
        "mesaj": "Kişi başarıyla güncellendi!",
        "kisi": kisi.to_dict()
    })


@app.route('/kisi/<int:kisi_id>', methods=['DELETE'])
@jwt_required()
def kisi_sil(kisi_id):
    """Kişi sil"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisi = Kisi.query.filter_by(id=kisi_id, kullanici_id=kullanici.id).first()
    if not kisi:
        return jsonify({"error": "Kişi bulunamadı"}), 404
    
    isim = kisi.isim
    db.session.delete(kisi)
    db.session.commit()
    
    log_action('DELETE', 'Kisi', kisi_id, {'isim': isim})
    
    return jsonify({"mesaj": f"'{isim}' başarıyla silindi!"})


@app.route('/kisi/<int:kisi_id>/favori', methods=['POST'])
@jwt_required()
def kisi_favori_toggle(kisi_id):
    """Kişi favori durumunu değiştir"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisi = Kisi.query.filter_by(id=kisi_id, kullanici_id=kullanici.id).first()
    if not kisi:
        return jsonify({"error": "Kişi bulunamadı"}), 404
    
    kisi.favori = not kisi.favori
    db.session.commit()
    
    return jsonify({
        "mesaj": "Favori durumu güncellendi",
        "favori": kisi.favori
    })


# =============================================================================
# KISI LISTELEME & ARAMA
# =============================================================================

@app.route('/kisiler', methods=['GET'])
@jwt_required()
def kisiler_listele():
    """Tüm kişileri listele (filtreleme ve sıralama destekli)"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    # Base query - sadece kullanıcının kişileri
    sorgu = Kisi.query.filter_by(kullanici_id=kullanici.id)
    
    # Filtreleme
    arama = request.args.get('arama', '').strip()
    if arama:
        sorgu = sorgu.filter(
            db.or_(
                Kisi.isim.ilike(f'%{arama}%'),
                Kisi.soyisim.ilike(f'%{arama}%'),
                Kisi.eposta.ilike(f'%{arama}%'),
                Kisi.telefon.ilike(f'%{arama}%'),
                Kisi.adres.ilike(f'%{arama}%')
            )
        )
    
    # Etiket filtresi
    etiket = request.args.get('etiket', '').strip()
    if etiket:
        sorgu = sorgu.filter(Kisi.etiketler.contains([etiket]))
    
    # Favori filtresi
    favori = request.args.get('favori', '').lower()
    if favori == 'true':
        sorgu = sorgu.filter(Kisi.favori == True)
    
    # Sıralama
    sirala = request.args.get('sirala', 'isim')
    sira_yonu = request.args.get('sira_yonu', 'asc')
    
    if sirala == 'isim':
        order_col = Kisi.isim
    elif sirala == 'eposta':
        order_col = Kisi.eposta
    elif sirala == 'telefon':
        order_col = Kisi.telefon
    elif sirala == 'created_at':
        order_col = Kisi.created_at
    elif sirala == 'updated_at':
        order_col = Kisi.updated_at
    else:
        order_col = Kisi.isim
    
    if sira_yonu == 'desc':
        sorgu = sorgu.order_by(order_col.desc())
    else:
        sorgu = sorgu.order_by(order_col.asc())
    
    # Sayfalama
    sayfa = request.args.get('sayfa', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 100)  # Max 100
    
    toplam = sorgu.count()
    kisiler = sorgu.offset((sayfa - 1) * limit).limit(limit).all()
    
    return jsonify({
        "kisiler": [kisi.to_dict_basic() for kisi in kisiler],
        "sayfalama": {
            "mevcut_sayfa": sayfa,
            "toplam_sayfa": (toplam + limit - 1) // limit,
            "toplam_kayit": toplam,
            "limit": limit
        }
    })


@app.route('/kisi/ara', methods=['GET'])
@jwt_required()
def kisi_ara():
    """Kişi arama (tek sonuç)"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    isim = request.args.get('isim', '').strip()
    if not isim:
        return jsonify({"error": "Arama terimi gerekli"}), 400
    
    kisi = Kisi.query.filter(
        Kisi.kullanici_id == kullanici.id,
        db.or_(
            Kisi.isim.ilike(f'%{isim}%'),
            Kisi.soyisim.ilike(f'%{isim}%')
        )
    ).first()
    
    if not kisi:
        return jsonify({"error": "Kişi bulunamadı"}), 404
    
    return jsonify({"kisi": kisi.to_dict()})


@app.route('/kisiler/harita', methods=['GET'])
@jwt_required()
def kisiler_harita():
    """Harita için konum verileri"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisiler = Kisi.query.filter(
        Kisi.kullanici_id == kullanici.id,
        Kisi.enlem.isnot(None),
        Kisi.boylam.isnot(None)
    ).all()
    
    return jsonify({
        "markers": [{
            "id": kisi.id,
            "isim": kisi.isim,
            "soyisim": kisi.soyisim,
            "tam_isim": f"{kisi.isim} {kisi.soyisim}" if kisi.soyisim else kisi.isim,
            "adres": kisi.adres,
            "enlem": kisi.enlem,
            "boylam": kisi.boylam,
            "etiketler": kisi.etiketler
        } for kisi in kisiler],
        "toplam": len(kisiler)
    })


@app.route('/kisiler/etiketler', methods=['GET'])
@jwt_required()
def etiketler_listele():
    """Tüm etiketleri listele"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisiler = Kisi.query.filter_by(kullanici_id=kullanici.id).all()
    
    tum_etiketler = set()
    for kisi in kisiler:
        if kisi.etiketler:
            tum_etiketler.update(kisi.etiketler)
    
    return jsonify({"etiketler": sorted(list(tum_etiketler))})


@app.route('/kisiler/istatistikler', methods=['GET'])
@jwt_required()
def istatistikler():
    """Kişi istatistikleri"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    toplam = Kisi.query.filter_by(kullanici_id=kullanici.id).count()
    favori = Kisi.query.filter_by(kullanici_id=kullanici.id, favori=True).count()
    konumlu = Kisi.query.filter(
        Kisi.kullanici_id == kullanici.id,
        Kisi.enlem.isnot(None)
    ).count()
    epostali = Kisi.query.filter(
        Kisi.kullanici_id == kullanici.id,
        Kisi.eposta.isnot(None)
    ).count()
    
    return jsonify({
        "toplam_kisi": toplam,
        "favori_kisi": favori,
        "konumlu_kisi": konumlu,
        "epostali_kisi": epostali
    })


# =============================================================================
# EMAIL EXPORT (Legacy endpoint - eski uyumluluk için)
# =============================================================================

@app.route('/emails/export', methods=['GET'])
@jwt_required()
def export_emails():
    """E-posta adreslerini dışa aktar"""
    kullanici = get_current_user()
    if not kullanici:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    
    kisiler = Kisi.query.filter(
        Kisi.kullanici_id == kullanici.id,
        Kisi.eposta.isnot(None)
    ).all()
    
    emails = [kisi.eposta for kisi in kisiler if kisi.eposta]
    
    return jsonify({
        "mesaj": f"{len(emails)} e-posta adresi bulundu",
        "emails": emails,
        "toplam": len(emails)
    })


# =============================================================================
# PHASE 3: DATA ENRICHMENT ENDPOINTS
# =============================================================================

@app.route('/enrich/email', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def enrich_email():
    """E-posta zenginleştirme"""
    try:
        from enrichment import EmailEnricher
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "E-posta adresi gerekli"}), 400
        
        result = EmailEnricher.enrich(email)
        
        return jsonify({
            "mesaj": "E-posta analiz edildi",
            "sonuc": result
        })
        
    except ImportError:
        return jsonify({"error": "Enrichment modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/enrich/phone', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def enrich_phone():
    """Telefon zenginleştirme"""
    try:
        from enrichment import PhoneEnricher
        
        data = request.get_json()
        phone = data.get('phone') or data.get('telefon')
        
        if not phone:
            return jsonify({"error": "Telefon numarası gerekli"}), 400
        
        result = PhoneEnricher.enrich(phone)
        
        return jsonify({
            "mesaj": "Telefon analiz edildi",
            "sonuc": result
        })
        
    except ImportError:
        return jsonify({"error": "Enrichment modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/enrich/social', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def enrich_social():
    """Sosyal medya profil araması"""
    try:
        from social_lookup import lookup_social_profiles
        
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        platforms = data.get('platforms')  # Opsiyonel liste
        
        if not email and not username:
            return jsonify({"error": "E-posta veya kullanıcı adı gerekli"}), 400
        
        result = lookup_social_profiles(
            email=email,
            username=username,
            platforms=platforms
        )
        
        return jsonify({
            "mesaj": "Sosyal medya araması tamamlandı",
            "sonuc": result
        })
        
    except ImportError:
        return jsonify({"error": "Social lookup modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/kisi/<int:kisi_id>/enrich', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def enrich_contact(kisi_id):
    """Kişi için tam zenginleştirme"""
    try:
        from enrichment import EmailEnricher, PhoneEnricher
        from social_lookup import lookup_social_profiles
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        kisi = Kisi.query.filter_by(id=kisi_id, kullanici_id=kullanici.id).first()
        if not kisi:
            return jsonify({"error": "Kişi bulunamadı"}), 404
        
        result = {
            "kisi_id": kisi.id,
            "tam_isim": kisi.tam_isim,
            "email_enrichment": None,
            "phone_enrichment": None,
            "social_profiles": None
        }
        
        # E-posta analizi
        if kisi.eposta:
            email_result = EmailEnricher.enrich(kisi.eposta)
            result["email_enrichment"] = email_result
            
            # Veritabanına kaydet
            if email_result.get('valid'):
                kisi.email_valid = True
                kisi.email_type = email_result.get('email_type')
        
        # Telefon analizi
        if kisi.telefon:
            phone_result = PhoneEnricher.enrich(kisi.telefon)
            result["phone_enrichment"] = phone_result
            
            # Veritabanına kaydet
            if phone_result.get('valid'):
                kisi.phone_country = phone_result.get('country_code')
                kisi.phone_carrier = phone_result.get('carrier')
                kisi.phone_type = phone_result.get('phone_type')
        
        # Sosyal medya araması
        if kisi.eposta:
            social_result = lookup_social_profiles(email=kisi.eposta)
            result["social_profiles"] = social_result
            
            # Bulunan profilleri kaydet
            if social_result.get('social_profiles', {}).get('found_profiles'):
                profiles = {}
                for profile in social_result['social_profiles']['found_profiles']:
                    platform = profile.get('platform')
                    url = profile.get('url')
                    if platform and url:
                        profiles[platform] = url
                
                if profiles:
                    kisi.social_profiles = profiles
        
        # Enriched timestamp güncelle
        from datetime import datetime
        kisi.enriched_at = datetime.utcnow()
        
        db.session.commit()
        
        # Audit log
        log_action('enrich', 'kisi', kisi_id, kullanici.id, f"Kişi zenginleştirildi")
        
        return jsonify({
            "mesaj": "Kişi zenginleştirme tamamlandı",
            "sonuc": result
        })
        
    except ImportError as e:
        return jsonify({"error": f"Modül yüklenemedi: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/kisiler/enrich-all', methods=['POST'])
@jwt_required()
@limiter.limit("1 per minute")
def enrich_all_contacts():
    """Tüm kişileri zenginleştir (rate limited)"""
    try:
        from enrichment import EmailEnricher, PhoneEnricher
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        # Sadece henüz zenginleştirilmemiş kişileri al
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enriched_at.is_(None)
        ).limit(10).all()  # Maksimum 10 kişi
        
        enriched_count = 0
        errors = []
        
        for kisi in kisiler:
            try:
                # E-posta analizi
                if kisi.eposta:
                    email_result = EmailEnricher.enrich(kisi.eposta)
                    if email_result.get('valid'):
                        kisi.email_valid = True
                        kisi.email_type = email_result.get('email_type')
                
                # Telefon analizi
                if kisi.telefon:
                    phone_result = PhoneEnricher.enrich(kisi.telefon)
                    if phone_result.get('valid'):
                        kisi.phone_country = phone_result.get('country_code')
                        kisi.phone_carrier = phone_result.get('carrier')
                        kisi.phone_type = phone_result.get('phone_type')
                
                from datetime import datetime
                kisi.enriched_at = datetime.utcnow()
                enriched_count += 1
                
            except Exception as e:
                errors.append({"kisi_id": kisi.id, "error": str(e)})
        
        db.session.commit()
        
        # Kalan kişi sayısı
        remaining = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enriched_at.is_(None)
        ).count()
        
        return jsonify({
            "mesaj": f"{enriched_count} kişi zenginleştirildi",
            "zenginlestirilen": enriched_count,
            "hatalar": errors,
            "kalan": remaining
        })
        
    except ImportError:
        return jsonify({"error": "Enrichment modülü yüklenemedi"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =============================================================================
# PHASE 4: LOCATION INTELLIGENCE ENDPOINTS
# =============================================================================

@app.route('/kisiler/heatmap', methods=['GET'])
@jwt_required()
def get_heatmap_data():
    """Heatmap verisi"""
    try:
        from location_intel import LocationIntelligence
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enlem.isnot(None),
            Kisi.boylam.isnot(None)
        ).all()
        
        locations = [
            {
                "id": kisi.id,
                "enlem": kisi.enlem,
                "boylam": kisi.boylam,
                "tam_isim": kisi.tam_isim
            }
            for kisi in kisiler
        ]
        
        intel = LocationIntelligence(locations)
        
        return jsonify({
            "mesaj": f"{len(locations)} konum için heatmap verisi",
            "heatmap": intel.get_heatmap_data(),
            "bounds": intel.get_bounds(),
            "center": {
                "lat": intel.get_center()[0],
                "lng": intel.get_center()[1]
            }
        })
        
    except ImportError:
        return jsonify({"error": "Location intel modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/kisiler/clusters', methods=['GET'])
@jwt_required()
def get_clusters():
    """Kümeleme verisi"""
    try:
        from location_intel import LocationIntelligence
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        radius = request.args.get('radius', 10, type=float)
        
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enlem.isnot(None),
            Kisi.boylam.isnot(None)
        ).all()
        
        locations = [
            {
                "id": kisi.id,
                "enlem": kisi.enlem,
                "boylam": kisi.boylam,
                "tam_isim": kisi.tam_isim
            }
            for kisi in kisiler
        ]
        
        intel = LocationIntelligence(locations)
        clusters = intel.get_clusters(radius)
        
        return jsonify({
            "mesaj": f"{len(clusters)} küme bulundu",
            "clusters": clusters,
            "radius_km": radius,
            "toplam_konum": len(locations)
        })
        
    except ImportError:
        return jsonify({"error": "Location intel modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/kisiler/proximity', methods=['GET'])
@jwt_required()
def proximity_search():
    """Yakınlık araması"""
    try:
        from location_intel import LocationIntelligence
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 5, type=float)
        
        if lat is None or lng is None:
            return jsonify({"error": "lat ve lng parametreleri gerekli"}), 400
        
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enlem.isnot(None),
            Kisi.boylam.isnot(None)
        ).all()
        
        locations = [
            {
                "id": kisi.id,
                "enlem": kisi.enlem,
                "boylam": kisi.boylam,
                "tam_isim": kisi.tam_isim
            }
            for kisi in kisiler
        ]
        
        intel = LocationIntelligence(locations)
        nearby = intel.find_nearby(lat, lng, radius)
        
        return jsonify({
            "mesaj": f"{len(nearby)} kişi {radius} km içinde bulundu",
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius,
            "results": nearby
        })
        
    except ImportError:
        return jsonify({"error": "Location intel modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/kisiler/location-stats', methods=['GET'])
@jwt_required()
def get_location_stats():
    """Konum istatistikleri"""
    try:
        from location_intel import LocationIntelligence
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enlem.isnot(None),
            Kisi.boylam.isnot(None)
        ).all()
        
        locations = [
            {
                "id": kisi.id,
                "enlem": kisi.enlem,
                "boylam": kisi.boylam,
                "tam_isim": kisi.tam_isim
            }
            for kisi in kisiler
        ]
        
        intel = LocationIntelligence(locations)
        
        # Şehir bazlı dağılım
        city_distribution = {}
        for kisi in Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.sehir.isnot(None)
        ).all():
            city = kisi.sehir
            city_distribution[city] = city_distribution.get(city, 0) + 1
        
        # Ülke bazlı dağılım
        country_distribution = {}
        for kisi in Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.ulke.isnot(None)
        ).all():
            country = kisi.ulke
            country_distribution[country] = country_distribution.get(country, 0) + 1
        
        stats = intel.get_statistics()
        stats["city_distribution"] = city_distribution
        stats["country_distribution"] = country_distribution
        
        return jsonify({
            "mesaj": "Konum istatistikleri",
            "istatistikler": stats
        })
        
    except ImportError:
        return jsonify({"error": "Location intel modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/kisiler/density', methods=['GET'])
@jwt_required()
def get_density_grid():
    """Yoğunluk grid'i"""
    try:
        from location_intel import LocationIntelligence
        
        kullanici = get_current_user()
        if not kullanici:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 401
        
        grid_size = request.args.get('grid_size', 10, type=int)
        
        kisiler = Kisi.query.filter(
            Kisi.kullanici_id == kullanici.id,
            Kisi.enlem.isnot(None),
            Kisi.boylam.isnot(None)
        ).all()
        
        locations = [
            {
                "id": kisi.id,
                "enlem": kisi.enlem,
                "boylam": kisi.boylam
            }
            for kisi in kisiler
        ]
        
        intel = LocationIntelligence(locations)
        
        return jsonify({
            "mesaj": "Yoğunluk grid verisi",
            "density": intel.get_density_grid(grid_size),
            "grid_size": grid_size
        })
        
    except ImportError:
        return jsonify({"error": "Location intel modülü yüklenemedi"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    app.run(host='0.0.0.0', debug=True, port=5000)


