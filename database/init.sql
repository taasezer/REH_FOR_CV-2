CREATE TABLE kullanici (
    id SERIAL PRIMARY KEY,
    kullanici_adi VARCHAR(80) UNIQUE NOT NULL,
    sifre_hash VARCHAR(128) NOT NULL
);

CREATE TABLE kisi (
    id SERIAL PRIMARY KEY,
    isim VARCHAR(80) NOT NULL,
    eposta VARCHAR(120) UNIQUE NOT NULL,
    telefon VARCHAR(20) NOT NULL,
    adres VARCHAR(200) NOT NULL,
    enlem FLOAT,
    boylam FLOAT
);
