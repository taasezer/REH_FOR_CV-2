"""
REH_FOR_CV-2 OSINT Rehber - Data Enrichment Module
E-posta ve telefon analizi, domain bilgisi
"""

import re
import socket
import hashlib
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Disposable email domains listesi
DISPOSABLE_DOMAINS = {
    'tempmail.com', 'throwaway.email', 'guerrillamail.com', 'mailinator.com',
    'temp-mail.org', '10minutemail.com', 'fakeinbox.com', 'trashmail.com',
    'tempmail.net', 'disposablemail.com', 'yopmail.com', 'maildrop.cc',
    'getairmail.com', 'mohmal.com', 'emailondeck.com', 'tempr.email',
    'dispostable.com', 'tempail.com', 'fakemailgenerator.com', 'guerrillamail.info'
}

# Popüler kurumsal domain'ler
CORPORATE_DOMAINS = {
    'google.com', 'microsoft.com', 'apple.com', 'amazon.com', 'facebook.com',
    'meta.com', 'linkedin.com', 'twitter.com', 'x.com', 'instagram.com',
    'netflix.com', 'spotify.com', 'uber.com', 'airbnb.com', 'salesforce.com'
}

# Kişisel email provider'ları
PERSONAL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com',
    'icloud.com', 'me.com', 'mac.com', 'aol.com', 'protonmail.com',
    'proton.me', 'mail.com', 'zoho.com', 'yandex.com', 'yandex.ru',
    'gmx.com', 'gmx.de', 'web.de', 'mail.ru', 'qq.com', '163.com'
}

# Türkiye operatörleri (prefix bazlı)
TR_MOBILE_PREFIXES = {
    '530': 'Turkcell', '531': 'Turkcell', '532': 'Turkcell', '533': 'Turkcell',
    '534': 'Turkcell', '535': 'Turkcell', '536': 'Turkcell', '537': 'Turkcell',
    '538': 'Turkcell', '539': 'Turkcell',
    '540': 'Vodafone', '541': 'Vodafone', '542': 'Vodafone', '543': 'Vodafone',
    '544': 'Vodafone', '545': 'Vodafone', '546': 'Vodafone', '547': 'Vodafone',
    '548': 'Vodafone', '549': 'Vodafone',
    '550': 'Turk Telekom', '551': 'Turk Telekom', '552': 'Turk Telekom', 
    '553': 'Turk Telekom', '554': 'Turk Telekom', '555': 'Turk Telekom',
    '556': 'Turk Telekom', '557': 'Turk Telekom', '558': 'Turk Telekom', 
    '559': 'Turk Telekom',
    '501': 'Turk Telekom', '505': 'Vodafone', '506': 'Vodafone', '507': 'Vodafone'
}


class EmailEnricher:
    """E-posta zenginleştirme sınıfı"""
    
    @staticmethod
    def validate_format(email: str) -> bool:
        """E-posta format doğrulaması"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.lower().strip()))
    
    @staticmethod
    def extract_parts(email: str) -> Tuple[str, str]:
        """E-postadan username ve domain çıkar"""
        if not email or '@' not in email:
            return '', ''
        parts = email.lower().strip().split('@')
        return parts[0], parts[1]
    
    @staticmethod
    def get_email_type(domain: str) -> str:
        """E-posta tipini belirle (corporate, personal, disposable)"""
        domain = domain.lower()
        
        if domain in DISPOSABLE_DOMAINS:
            return 'disposable'
        if domain in PERSONAL_DOMAINS:
            return 'personal'
        if domain in CORPORATE_DOMAINS:
            return 'corporate'
        
        # Bilinmeyen domain'ler için TLD bazlı tahmin
        if domain.endswith('.edu') or domain.endswith('.edu.tr'):
            return 'educational'
        if domain.endswith('.gov') or domain.endswith('.gov.tr'):
            return 'government'
        if domain.endswith('.org'):
            return 'organization'
        
        # Özel domain = muhtemelen kurumsal
        return 'corporate'
    
    @staticmethod
    def check_mx_record(domain: str) -> bool:
        """Domain'in MX kaydı var mı kontrol et"""
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(list(mx_records)) > 0
        except:
            # DNS resolver yoksa veya hata varsa, socket ile dene
            try:
                socket.gethostbyname(domain)
                return True
            except:
                return False
    
    @staticmethod
    def get_gravatar_url(email: str, size: int = 200) -> str:
        """Gravatar URL'i oluştur"""
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=404"
    
    @staticmethod
    def check_gravatar_exists(email: str) -> bool:
        """Gravatar profili var mı kontrol et"""
        import requests
        try:
            url = EmailEnricher.get_gravatar_url(email)
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def extract_possible_name(email: str) -> Dict[str, str]:
        """E-postadan olası isim çıkar"""
        username, _ = EmailEnricher.extract_parts(email)
        
        # Sayıları ve özel karakterleri temizle
        clean = re.sub(r'[0-9_.\-]', ' ', username)
        parts = [p.strip() for p in clean.split() if len(p) > 1]
        
        result = {'username': username}
        
        if len(parts) >= 2:
            result['possible_first_name'] = parts[0].capitalize()
            result['possible_last_name'] = parts[-1].capitalize()
        elif len(parts) == 1:
            result['possible_name'] = parts[0].capitalize()
        
        return result
    
    @classmethod
    def enrich(cls, email: str) -> Dict[str, Any]:
        """E-posta için tam zenginleştirme"""
        if not email:
            return {'valid': False, 'error': 'E-posta boş'}
        
        email = email.lower().strip()
        
        if not cls.validate_format(email):
            return {'valid': False, 'error': 'Geçersiz format'}
        
        username, domain = cls.extract_parts(email)
        email_type = cls.get_email_type(domain)
        has_mx = cls.check_mx_record(domain)
        name_info = cls.extract_possible_name(email)
        
        # Gravatar kontrolü (opsiyonel - request gerektirir)
        has_gravatar = False
        gravatar_url = None
        try:
            has_gravatar = cls.check_gravatar_exists(email)
            if has_gravatar:
                gravatar_url = cls.get_gravatar_url(email)
        except:
            pass
        
        return {
            'valid': True,
            'email': email,
            'username': username,
            'domain': domain,
            'email_type': email_type,
            'has_mx_record': has_mx,
            'is_disposable': email_type == 'disposable',
            'has_gravatar': has_gravatar,
            'gravatar_url': gravatar_url,
            'name_extraction': name_info,
            'enriched_at': datetime.utcnow().isoformat()
        }


class PhoneEnricher:
    """Telefon numarası zenginleştirme sınıfı"""
    
    # Ülke kodları
    COUNTRY_CODES = {
        '90': {'country': 'Türkiye', 'code': 'TR'},
        '1': {'country': 'ABD/Kanada', 'code': 'US'},
        '44': {'country': 'Birleşik Krallık', 'code': 'GB'},
        '49': {'country': 'Almanya', 'code': 'DE'},
        '33': {'country': 'Fransa', 'code': 'FR'},
        '39': {'country': 'İtalya', 'code': 'IT'},
        '34': {'country': 'İspanya', 'code': 'ES'},
        '31': {'country': 'Hollanda', 'code': 'NL'},
        '7': {'country': 'Rusya', 'code': 'RU'},
        '86': {'country': 'Çin', 'code': 'CN'},
        '81': {'country': 'Japonya', 'code': 'JP'},
        '82': {'country': 'Güney Kore', 'code': 'KR'},
        '91': {'country': 'Hindistan', 'code': 'IN'},
        '61': {'country': 'Avustralya', 'code': 'AU'},
        '55': {'country': 'Brezilya', 'code': 'BR'},
        '52': {'country': 'Meksika', 'code': 'MX'},
        '20': {'country': 'Mısır', 'code': 'EG'},
        '971': {'country': 'BAE', 'code': 'AE'},
        '966': {'country': 'Suudi Arabistan', 'code': 'SA'},
        '994': {'country': 'Azerbaycan', 'code': 'AZ'},
        '995': {'country': 'Gürcistan', 'code': 'GE'},
    }
    
    @staticmethod
    def normalize(phone: str) -> str:
        """Telefon numarasını normalize et (sadece rakamlar)"""
        if not phone:
            return ''
        # Sadece rakamları al
        return re.sub(r'\D', '', phone)
    
    @staticmethod
    def validate_format(phone: str) -> bool:
        """Telefon format doğrulaması"""
        normalized = PhoneEnricher.normalize(phone)
        # En az 7, en fazla 15 rakam
        return 7 <= len(normalized) <= 15
    
    @staticmethod
    def detect_country(phone: str) -> Dict[str, str]:
        """Ülke kodunu tespit et"""
        normalized = PhoneEnricher.normalize(phone)
        
        # + ile başlıyorsa veya uzunsa ülke kodu var demek
        if len(normalized) >= 10:
            # 3 haneli ülke kodları
            for code_len in [3, 2, 1]:
                prefix = normalized[:code_len]
                if prefix in PhoneEnricher.COUNTRY_CODES:
                    return PhoneEnricher.COUNTRY_CODES[prefix]
        
        # Varsayılan olarak Türkiye kabul et (90 ile başlamıyorsa)
        if normalized.startswith('0'):
            return {'country': 'Türkiye', 'code': 'TR'}
        
        return {'country': 'Bilinmiyor', 'code': 'XX'}
    
    @staticmethod
    def detect_carrier_tr(phone: str) -> Optional[str]:
        """Türkiye için operatör tespiti"""
        normalized = PhoneEnricher.normalize(phone)
        
        # 90 ülke kodunu kaldır
        if normalized.startswith('90'):
            normalized = normalized[2:]
        # Başındaki 0'ı kaldır
        if normalized.startswith('0'):
            normalized = normalized[1:]
        
        # İlk 3 hane prefix
        if len(normalized) >= 3:
            prefix = normalized[:3]
            return TR_MOBILE_PREFIXES.get(prefix)
        
        return None
    
    @staticmethod
    def detect_phone_type(phone: str) -> str:
        """Telefon tipini tespit et (mobile/landline)"""
        normalized = PhoneEnricher.normalize(phone)
        
        # Türkiye için
        if normalized.startswith('90') or normalized.startswith('0'):
            # 90 veya 0'ı kaldır
            local = normalized.lstrip('90').lstrip('0')
            
            # 5 ile başlayan numaralar mobil
            if local.startswith('5'):
                return 'mobile'
            # 2, 3, 4 ile başlayanlar sabit hat
            if local.startswith(('2', '3', '4')):
                return 'landline'
            # 8 ile başlayanlar özel servisler
            if local.startswith('8'):
                return 'special'
        
        # Diğer ülkeler için genellikle mobil kabul et
        return 'mobile'
    
    @staticmethod
    def format_international(phone: str, country_code: str = '90') -> str:
        """Uluslararası formata çevir"""
        normalized = PhoneEnricher.normalize(phone)
        
        # Zaten ülke kodu varsa
        if normalized.startswith(country_code):
            return f'+{normalized}'
        
        # Başındaki 0'ı kaldır ve ülke kodu ekle
        if normalized.startswith('0'):
            normalized = normalized[1:]
        
        return f'+{country_code}{normalized}'
    
    @staticmethod
    def format_local(phone: str) -> str:
        """Yerel formata çevir (Türkiye için)"""
        normalized = PhoneEnricher.normalize(phone)
        
        # Ülke kodunu kaldır
        if normalized.startswith('90'):
            normalized = normalized[2:]
        if not normalized.startswith('0'):
            normalized = '0' + normalized
        
        # Format: 0XXX XXX XX XX
        if len(normalized) == 11:
            return f'{normalized[:4]} {normalized[4:7]} {normalized[7:9]} {normalized[9:11]}'
        
        return normalized
    
    @classmethod
    def enrich(cls, phone: str) -> Dict[str, Any]:
        """Telefon için tam zenginleştirme"""
        if not phone:
            return {'valid': False, 'error': 'Telefon boş'}
        
        normalized = cls.normalize(phone)
        
        if not cls.validate_format(phone):
            return {'valid': False, 'error': 'Geçersiz format'}
        
        country_info = cls.detect_country(phone)
        phone_type = cls.detect_phone_type(phone)
        carrier = None
        
        # Türkiye için operatör tespiti
        if country_info.get('code') == 'TR':
            carrier = cls.detect_carrier_tr(phone)
        
        return {
            'valid': True,
            'original': phone,
            'normalized': normalized,
            'international_format': cls.format_international(phone),
            'local_format': cls.format_local(phone),
            'country': country_info.get('country'),
            'country_code': country_info.get('code'),
            'phone_type': phone_type,
            'carrier': carrier,
            'digit_count': len(normalized),
            'enriched_at': datetime.utcnow().isoformat()
        }


class DomainEnricher:
    """Domain zenginleştirme sınıfı"""
    
    @staticmethod
    def get_whois_info(domain: str) -> Dict[str, Any]:
        """WHOIS bilgilerini al (python-whois gerektirir)"""
        try:
            import whois
            w = whois.whois(domain)
            return {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'name_servers': w.name_servers,
                'status': w.status,
                'org': w.org,
                'country': w.country
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_dns_records(domain: str) -> Dict[str, Any]:
        """DNS kayıtlarını al"""
        records = {}
        
        try:
            import dns.resolver
            
            # A records
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                records['A'] = [str(r) for r in a_records]
            except:
                records['A'] = []
            
            # MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                records['MX'] = [str(r.exchange) for r in mx_records]
            except:
                records['MX'] = []
            
            # TXT records
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                records['TXT'] = [str(r) for r in txt_records]
            except:
                records['TXT'] = []
            
        except ImportError:
            # dnspython yüklü değilse basit kontrol
            try:
                ip = socket.gethostbyname(domain)
                records['A'] = [ip]
            except:
                records['A'] = []
        
        return records
    
    @classmethod
    def enrich(cls, domain: str) -> Dict[str, Any]:
        """Domain için tam zenginleştirme"""
        if not domain:
            return {'valid': False, 'error': 'Domain boş'}
        
        domain = domain.lower().strip()
        
        # @ içeriyorsa e-postadır, domain'i çıkar
        if '@' in domain:
            domain = domain.split('@')[1]
        
        dns_records = cls.get_dns_records(domain)
        whois_info = cls.get_whois_info(domain)
        
        return {
            'valid': True,
            'domain': domain,
            'has_website': len(dns_records.get('A', [])) > 0,
            'has_email': len(dns_records.get('MX', [])) > 0,
            'dns_records': dns_records,
            'whois': whois_info,
            'enriched_at': datetime.utcnow().isoformat()
        }


def enrich_contact(email: str = None, phone: str = None) -> Dict[str, Any]:
    """Kişi bilgilerini zenginleştir"""
    result = {
        'email_enrichment': None,
        'phone_enrichment': None,
        'enriched_at': datetime.utcnow().isoformat()
    }
    
    if email:
        result['email_enrichment'] = EmailEnricher.enrich(email)
    
    if phone:
        result['phone_enrichment'] = PhoneEnricher.enrich(phone)
    
    return result
