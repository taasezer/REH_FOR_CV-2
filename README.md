# REH_FOR_CV-2
just a better human arcive 
**Tam fonksiyonlu, güvenli ve ölçeklenebilir bir kişi rehberi uygulaması.**
Kişileri ekleyin, düzenleyin, haritada görüntüleyin, filtreleyin ve e-posta verilerini toplayın.

---

## 📌 Proje Şeması
```bash
REH_FOR_CV-2/
│
├── backend/
│   ├── python/
│   │   ├── app.py                    
│   │   ├── email_data_collector.py    
│   │   ├── requirements.txt           # Python bağımlılıkları
│   │   └── Dockerfile                 
│   │
│   ├── csharp/
│   │   ├── KisiIslemleri.cs           
│   │   └── Dockerfile                 # C# Docker konfigürasyonu
│   │
│   └── cpp/
│       ├── kisi_islemleri.cpp        
│       └── Dockerfile                 # C++ Docker konfigürasyonu
│
├── frontend/
│   ├── index.html                     # HTML arayüzü
│   ├── style.css                      # CSS stilleri
│   └── script.js                      # JavaScript işlemleri
│
├── database/
│   └── init.sql                       # Veritabanı başlangıç scripti
│
├── docker-compose.yml                 
└── README.md                          # Kurulum ve kullanım talimatları
```
## 🚀 Kurulum
### 📋 Gereksinimler
- Docker 🐳
- Docker Compose
- Tarayıcı (Chrome, Firefox, vb.)

### 🛠 Kurulum Adımları
1. Projeyi Klonlayın veya İndirin
```bash
git clone https://github.com/kullaniciadi/rehber-projesi.git
cd rehber-projesi
```
2. Docker ile Projeyi Başlatın
```bash
docker-compose up --build
```
3. Uygulamayı Açın
Tarayıcınızda frontend/index.html dosyasını açın.

## 🎯 Kullanım
### 🔐 Kullanıcı Kaydı ve Girişi

Kayıt Ol butonuna tıklayın ve kullanıcı adı/şifre girin.
Giriş Yap butonuna tıklayın.

### 👤 Kişi İşlemleri

Kişi Ekle: Formu doldurun ve "Kişi Ekle" butonuna tıklayın.
Kişi Ara: Arama kutusuna isim girin ve "Ara" butonuna tıklayın.
Filtreleme: "Filtrele" butonuna tıklayarak kişileri sıralayın.

### 📧 E-posta Veri Toplama

E-posta Topla: Kişi eklerken veya düzenlerken e-posta adresleri otomatik olarak ***email_data_collector*** tarafından işlenir.
E-postaları Dışa Aktar: "E-postaları Dışa Aktar" butonuna tıklayarak tüm e-posta adreslerini bir dosyaya aktarabilirsiniz.

### 🗺 Harita Görüntüleme

Kişilerin adresleri otomatik olarak haritada işaretlenir.


## 🔧 Geliştirme
### 📦 Bağımlılıklar

Python Bağımlılıklarını Yükleme
```bash
pip install -r backend/python/requirements.txt
```

C# Bağımlılıklarını Yükleme
```bash
dotnet add package Npgsql
```
C++ Bağımlılıklarını Yükleme (Linux)
```bash
sudo apt-get install
```
# 🐳 Docker Komutları
## Projeyi Durdurma
 ```` bash
docker-compose down
````
## Veritabanını Sıfırlama
 ```` bash
docker-compose down -v
docker-compose up --build
````
# 🔍 Sorun Giderme
### PostgreSQL Bağlantı Hatası
```` bash
docker ps
````
PostgreSQL konteynerinin çalıştığından emin olun.
### Harita Görüntülenmiyor

- İnternet bağlantınızı kontrol edin.
- Tarayıcı konsolunda hata mesajlarını kontrol edin (F12 → Console).

## Geliştirme ve Katkı
Proje açık kaynak olarak geliştirilmekte olup, katkılarınızı memnuniyetle karşılarım.
Lütfen hata bildirmek veya özellik talep etmek için issue açınız. Pull request göndermekten çekinmeyiniz.

## İletişim
Herhangi bir soru veya destek talebi için aşağıdaki iletişim adresleri kullanılabilir:

## E-posta: [taha.sezer@istun.edu.tr]
