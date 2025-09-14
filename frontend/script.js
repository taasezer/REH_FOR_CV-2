let token = null;
const harita = L.map('harita').setView([39.9334, 32.8597], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(harita);

// Giriş/Kayıt İşlemleri
document.getElementById('kayitLink').addEventListener('click', () => {
    document.querySelector('.giris-formu').style.display = 'none';
    document.querySelector('.kayit-formu').style.display = 'block';
});

document.getElementById('kayitButton').addEventListener('click', async () => {
    const response = await fetch('http://localhost:5000/kayit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            kullanici_adi: document.getElementById('yeniKullaniciAdi').value,
            sifre: document.getElementById('yeniSifre').value
        })
    });
    const data = await response.json();
    alert(data.mesaj);
});

document.getElementById('girisButton').addEventListener('click', async () => {
    const response = await fetch('http://localhost:5000/giris', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            kullanici_adi: document.getElementById('kullaniciAdi').value,
            sifre: document.getElementById('sifre').value
        })
    });
    const data = await response.json();
    if (data.access_token) {
        token = data.access_token;
        alert("Giriş başarılı!");
        document.querySelector('.giris-formu').style.display = 'none';
        document.querySelector('.container').style.display = 'block';
    } else {
        alert("Giriş başarısız!");
    }
});

// Kişi Ekleme
document.getElementById('kisiForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:5000/kisi/ekle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            isim: document.getElementById('isim').value,
            eposta: document.getElementById('eposta').value,
            telefon: document.getElementById('telefon').value,
            adres: document.getElementById('adres').value
        })
    });
    const data = await response.json();
    alert(data.mesaj);
    document.getElementById('kisiForm').reset();
});

// Kişi Arama
document.getElementById('araButton').addEventListener('click', async () => {
    const isim = document.getElementById('ara').value;
    const response = await fetch(`http://localhost:5000/kisi/ara?isim=${isim}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    if (data.enlem && data.boylam) {
        harita.setView([data.enlem, data.boylam], 12);
        L.marker([data.enlem, data.boylam]).addTo(harita)
            .bindPopup(`<b>${data.isim}</b><br>${data.adres}`);
    }
    document.getElementById('sonuclar').innerHTML = `
        <h3>${data.isim}</h3>
        <p>E-posta: ${data.eposta}</p>
        <p>Telefon: ${data.telefon}</p>
        <p>Adres: ${data.adres}</p>
    `;
});

// Kişileri Listeleme
async function kisileriListele() {
    const sirala = document.getElementById('sirala').value;
    const response = await fetch(`http://localhost:5000/kisiler?sirala=${sirala}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const kisiler = await response.json();
    kisiler.forEach(kisi => {
        if (kisi.enlem && kisi.boylam) {
            L.marker([kisi.enlem, kisi.boylam]).addTo(harita)
                .bindPopup(`<b>${kisi.isim}</b><br>${kisi.adres}`);
        }
    });
}

document.getElementById('filtreleButton').addEventListener('click', kisileriListele);

// E-postaları Dışa Aktar
async function exportEmails() {
    const response = await fetch('http://localhost:5000/emails/export', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    alert(data.mesaj);
}

document.getElementById('exportEmailsButton').addEventListener('click', exportEmails);
