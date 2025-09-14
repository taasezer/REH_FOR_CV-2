from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from email_data_collector import export_emails_to_file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kullanici:sifre@db/rehber'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'sizin-gizli-anahtarınız'
jwt = JWTManager(app)
db = SQLAlchemy(app)

class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(80), unique=True, nullable=False)
    sifre_hash = db.Column(db.String(128), nullable=False)

class Kisi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(80), nullable=False)
    eposta = db.Column(db.String(120), unique=True, nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    adres = db.Column(db.String(200), nullable=False)
    enlem = db.Column(db.Float)
    boylam = db.Column(db.Float)

@app.route('/kayit', methods=['POST'])
def kayit():
    data = request.json
    sifre_hash = generate_password_hash(data['sifre'])
    yeni_kullanici = Kullanici(kullanici_adi=data['kullanici_adi'], sifre_hash=sifre_hash)
    db.session.add(yeni_kullanici)
    db.session.commit()
    return jsonify({"mesaj": "Kullanıcı başarıyla kaydedildi!"})

@app.route('/giris', methods=['POST'])
def giris():
    data = request.json
    kullanici = Kullanici.query.filter_by(kullanici_adi=data['kullanici_adi']).first()
    if kullanici and check_password_hash(kullanici.sifre_hash, data['sifre']):
        access_token = create_access_token(identity=kullanici.kullanici_adi)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"mesaj": "Geçersiz kullanıcı adı veya şifre!"}), 401

@app.route('/kisi/ekle', methods=['POST'])
@jwt_required()
def kisi_ekle():
    current_user = get_jwt_identity()
    data = request.json
    try:
        geolocator = Nominatim(user_agent="rehber_app", timeout=10)
        location = geolocator.geocode(data['adres'])
        yeni_kisi = Kisi(
            isim=data['isim'],
            eposta=data['eposta'],
            telefon=data['telefon'],
            adres=data['adres'],
            enlem=location.latitude if location else None,
            boylam=location.longitude if location else None
        )
        db.session.add(yeni_kisi)
        db.session.commit()
        return jsonify({"mesaj": "Kişi başarıyla eklendi!", "konum": {"enlem": location.latitude, "boylam": location.longitude}})
    except GeocoderTimedOut:
        return jsonify({"hata": "Adres bulunamadı."}), 400

@app.route('/kisi/ara', methods=['GET'])
@jwt_required()
def kisi_ara():
    isim = request.args.get('isim')
    kisi = Kisi.query.filter_by(isim=isim).first()
    if kisi:
        return jsonify({
            "isim": kisi.isim,
            "eposta": kisi.eposta,
            "telefon": kisi.telefon,
            "adres": kisi.adres,
            "enlem": kisi.enlem,
            "boylam": kisi.boylam
        })
    else:
        return jsonify({"mesaj": "Kişi bulunamadı."}), 404

@app.route('/kisiler', methods=['GET'])
@jwt_required()
def kisiler_listele():
    sorgu = Kisi.query
    isim = request.args.get('isim')
    if isim:
        sorgu = sorgu.filter(Kisi.isim.ilike(f'%{isim}%'))
    sirala = request.args.get('sirala')
    if sirala == 'isim':
        sorgu = sorgu.order_by(Kisi.isim)
    elif sirala == 'telefon':
        sorgu = sorgu.order_by(Kisi.telefon)
    kisiler = sorgu.all()
    return jsonify([{
        "isim": kisi.isim,
        "eposta": kisi.eposta,
        "telefon": kisi.telefon,
        "adres": kisi.adres,
        "enlem": kisi.enlem,
        "boylam": kisi.boylam
    } for kisi in kisiler])

@app.route('/emails/export', methods=['GET'])
@jwt_required()
def export_emails():
    filename = export_emails_to_file()
    return jsonify({"mesaj": f"E-posta adresleri {filename} dosyasına aktarıldı."})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5000)
