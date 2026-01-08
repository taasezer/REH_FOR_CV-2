"""
REH_FOR_CV-2 OSINT Rehber - External API Integrations Module
HaveIBeenPwned, Hunter.io, Shodan, VirusTotal entegrasyonları
"""

import os
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests


class RateLimiter:
    """Basit rate limiter"""
    
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.call_times: List[float] = []
    
    def wait_if_needed(self):
        """Gerekirse bekle"""
        now = time.time()
        # Son 1 dakikadaki çağrıları filtrele
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        if len(self.call_times) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.call_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.call_times.append(time.time())


class HaveIBeenPwnedAPI:
    """
    HaveIBeenPwned API entegrasyonu
    Veri ihlali kontrolü
    https://haveibeenpwned.com/API/v3
    """
    
    BASE_URL = "https://haveibeenpwned.com/api/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HAVEIBEENPWNED_API_KEY')
        self.rate_limiter = RateLimiter(calls_per_minute=10)
        self.headers = {
            'hibp-api-key': self.api_key,
            'User-Agent': 'OSINT-Rehber'
        }
    
    def check_email_breaches(self, email: str) -> Dict[str, Any]:
        """
        E-postanın veri ihlallerini kontrol et
        """
        if not self.api_key:
            return {
                'checked': False,
                'error': 'API key gerekli',
                'email': email
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.BASE_URL}/breachedaccount/{email}"
            response = requests.get(
                url,
                headers=self.headers,
                params={'truncateResponse': 'false'},
                timeout=10
            )
            
            if response.status_code == 200:
                breaches = response.json()
                return {
                    'checked': True,
                    'email': email,
                    'pwned': True,
                    'breach_count': len(breaches),
                    'breaches': [
                        {
                            'name': b.get('Name'),
                            'title': b.get('Title'),
                            'domain': b.get('Domain'),
                            'breach_date': b.get('BreachDate'),
                            'added_date': b.get('AddedDate'),
                            'pwn_count': b.get('PwnCount'),
                            'data_classes': b.get('DataClasses', []),
                            'is_verified': b.get('IsVerified'),
                            'is_sensitive': b.get('IsSensitive')
                        }
                        for b in breaches
                    ],
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'checked': True,
                    'email': email,
                    'pwned': False,
                    'breach_count': 0,
                    'breaches': [],
                    'message': 'E-posta bilinen ihlallerde bulunamadı',
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 401:
                return {
                    'checked': False,
                    'error': 'Geçersiz API anahtarı',
                    'email': email
                }
            elif response.status_code == 429:
                return {
                    'checked': False,
                    'error': 'Rate limit aşıldı',
                    'email': email
                }
            else:
                return {
                    'checked': False,
                    'error': f'API hatası: {response.status_code}',
                    'email': email
                }
                
        except requests.exceptions.Timeout:
            return {
                'checked': False,
                'error': 'Bağlantı zaman aşımı',
                'email': email
            }
        except Exception as e:
            return {
                'checked': False,
                'error': str(e),
                'email': email
            }
    
    def check_password_pwned(self, password: str) -> Dict[str, Any]:
        """
        Şifrenin veri ihlallerinde olup olmadığını kontrol et
        k-Anonymity yöntemi kullanır (şifre sunucuya gönderilmez)
        """
        # SHA-1 hash hesapla
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Suffix'i ara
                hashes = response.text.split('\r\n')
                for h in hashes:
                    parts = h.split(':')
                    if len(parts) == 2 and parts[0] == suffix:
                        return {
                            'checked': True,
                            'pwned': True,
                            'count': int(parts[1]),
                            'message': f'Bu şifre {parts[1]} kez ihlallerde görülmüş'
                        }
                
                return {
                    'checked': True,
                    'pwned': False,
                    'count': 0,
                    'message': 'Bu şifre bilinen ihlallerde bulunamadı'
                }
            else:
                return {
                    'checked': False,
                    'error': f'API hatası: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'checked': False,
                'error': str(e)
            }


class HunterIOAPI:
    """
    Hunter.io API entegrasyonu
    E-posta doğrulama ve domain araması
    https://hunter.io/api-documentation/v2
    """
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HUNTER_API_KEY')
        self.rate_limiter = RateLimiter(calls_per_minute=15)
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        E-posta adresini doğrula
        """
        if not self.api_key:
            return {
                'verified': False,
                'error': 'API key gerekli',
                'email': email
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.BASE_URL}/email-verifier"
            response = requests.get(
                url,
                params={'email': email, 'api_key': self.api_key},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'verified': True,
                    'email': email,
                    'result': data.get('result'),  # deliverable, undeliverable, risky, unknown
                    'score': data.get('score'),
                    'status': data.get('status'),
                    'regexp': data.get('regexp'),
                    'gibberish': data.get('gibberish'),
                    'disposable': data.get('disposable'),
                    'webmail': data.get('webmail'),
                    'mx_records': data.get('mx_records'),
                    'smtp_server': data.get('smtp_server'),
                    'smtp_check': data.get('smtp_check'),
                    'accept_all': data.get('accept_all'),
                    'block': data.get('block'),
                    'sources': data.get('sources', []),
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 401:
                return {
                    'verified': False,
                    'error': 'Geçersiz API anahtarı',
                    'email': email
                }
            else:
                return {
                    'verified': False,
                    'error': f'API hatası: {response.status_code}',
                    'email': email
                }
                
        except Exception as e:
            return {
                'verified': False,
                'error': str(e),
                'email': email
            }
    
    def domain_search(self, domain: str) -> Dict[str, Any]:
        """
        Domain'deki e-posta adreslerini ara
        """
        if not self.api_key:
            return {
                'searched': False,
                'error': 'API key gerekli',
                'domain': domain
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.BASE_URL}/domain-search"
            response = requests.get(
                url,
                params={'domain': domain, 'api_key': self.api_key},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'searched': True,
                    'domain': domain,
                    'organization': data.get('organization'),
                    'pattern': data.get('pattern'),
                    'email_count': len(data.get('emails', [])),
                    'emails': [
                        {
                            'value': e.get('value'),
                            'type': e.get('type'),
                            'confidence': e.get('confidence'),
                            'first_name': e.get('first_name'),
                            'last_name': e.get('last_name'),
                            'position': e.get('position'),
                            'department': e.get('department')
                        }
                        for e in data.get('emails', [])[:20]  # İlk 20
                    ],
                    'checked_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'searched': False,
                    'error': f'API hatası: {response.status_code}',
                    'domain': domain
                }
                
        except Exception as e:
            return {
                'searched': False,
                'error': str(e),
                'domain': domain
            }


class ShodanAPI:
    """
    Shodan API entegrasyonu
    IP ve domain bilgisi
    https://developer.shodan.io/api
    """
    
    BASE_URL = "https://api.shodan.io"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SHODAN_API_KEY')
        self.rate_limiter = RateLimiter(calls_per_minute=1)  # Free plan çok sınırlı
    
    def lookup_ip(self, ip: str) -> Dict[str, Any]:
        """
        IP adresi hakkında bilgi al
        """
        if not self.api_key:
            return {
                'found': False,
                'error': 'API key gerekli',
                'ip': ip
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.BASE_URL}/shodan/host/{ip}"
            response = requests.get(
                url,
                params={'key': self.api_key},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'found': True,
                    'ip': ip,
                    'ip_str': data.get('ip_str'),
                    'asn': data.get('asn'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'city': data.get('city'),
                    'region_code': data.get('region_code'),
                    'country_code': data.get('country_code'),
                    'country_name': data.get('country_name'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'os': data.get('os'),
                    'ports': data.get('ports', []),
                    'hostnames': data.get('hostnames', []),
                    'domains': data.get('domains', []),
                    'vulns': list(data.get('vulns', {}).keys()) if data.get('vulns') else [],
                    'last_update': data.get('last_update'),
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'found': False,
                    'ip': ip,
                    'message': 'IP adresi Shodan veritabanında bulunamadı'
                }
            elif response.status_code == 401:
                return {
                    'found': False,
                    'error': 'Geçersiz API anahtarı',
                    'ip': ip
                }
            else:
                return {
                    'found': False,
                    'error': f'API hatası: {response.status_code}',
                    'ip': ip
                }
                
        except Exception as e:
            return {
                'found': False,
                'error': str(e),
                'ip': ip
            }
    
    def dns_resolve(self, hostnames: List[str]) -> Dict[str, Any]:
        """
        Hostname'leri IP'lere çözümle
        """
        if not self.api_key:
            return {
                'resolved': False,
                'error': 'API key gerekli'
            }
        
        try:
            url = f"{self.BASE_URL}/dns/resolve"
            response = requests.get(
                url,
                params={'key': self.api_key, 'hostnames': ','.join(hostnames)},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'resolved': True,
                    'results': response.json()
                }
            else:
                return {
                    'resolved': False,
                    'error': f'API hatası: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'resolved': False,
                'error': str(e)
            }


class VirusTotalAPI:
    """
    VirusTotal API entegrasyonu
    URL ve domain analizi
    https://developers.virustotal.com/reference
    """
    
    BASE_URL = "https://www.virustotal.com/api/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        self.rate_limiter = RateLimiter(calls_per_minute=4)  # Free: 4/min
        self.headers = {
            'x-apikey': self.api_key
        }
    
    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """
        Domain analizi
        """
        if not self.api_key:
            return {
                'analyzed': False,
                'error': 'API key gerekli',
                'domain': domain
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.BASE_URL}/domains/{domain}"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                attributes = data.get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'analyzed': True,
                    'domain': domain,
                    'id': data.get('id'),
                    'registrar': attributes.get('registrar'),
                    'creation_date': attributes.get('creation_date'),
                    'last_modification_date': attributes.get('last_modification_date'),
                    'reputation': attributes.get('reputation'),
                    'categories': attributes.get('categories', {}),
                    'last_analysis_stats': {
                        'harmless': stats.get('harmless', 0),
                        'malicious': stats.get('malicious', 0),
                        'suspicious': stats.get('suspicious', 0),
                        'undetected': stats.get('undetected', 0),
                        'timeout': stats.get('timeout', 0)
                    },
                    'total_votes': {
                        'harmless': attributes.get('total_votes', {}).get('harmless', 0),
                        'malicious': attributes.get('total_votes', {}).get('malicious', 0)
                    },
                    'whois': attributes.get('whois'),
                    'last_dns_records': attributes.get('last_dns_records', [])[:10],
                    'is_malicious': stats.get('malicious', 0) > 0,
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'analyzed': False,
                    'domain': domain,
                    'message': 'Domain VirusTotal veritabanında bulunamadı'
                }
            elif response.status_code == 401:
                return {
                    'analyzed': False,
                    'error': 'Geçersiz API anahtarı',
                    'domain': domain
                }
            else:
                return {
                    'analyzed': False,
                    'error': f'API hatası: {response.status_code}',
                    'domain': domain
                }
                
        except Exception as e:
            return {
                'analyzed': False,
                'error': str(e),
                'domain': domain
            }
    
    def analyze_url(self, url_to_check: str) -> Dict[str, Any]:
        """
        URL analizi (scan başlat)
        """
        if not self.api_key:
            return {
                'analyzed': False,
                'error': 'API key gerekli',
                'url': url_to_check
            }
        
        self.rate_limiter.wait_if_needed()
        
        try:
            # URL'i base64 encode et
            import base64
            url_id = base64.urlsafe_b64encode(url_to_check.encode()).decode().strip('=')
            
            url = f"{self.BASE_URL}/urls/{url_id}"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                attributes = data.get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'analyzed': True,
                    'url': url_to_check,
                    'final_url': attributes.get('last_final_url'),
                    'title': attributes.get('title'),
                    'last_analysis_stats': {
                        'harmless': stats.get('harmless', 0),
                        'malicious': stats.get('malicious', 0),
                        'suspicious': stats.get('suspicious', 0),
                        'undetected': stats.get('undetected', 0)
                    },
                    'reputation': attributes.get('reputation'),
                    'is_malicious': stats.get('malicious', 0) > 0,
                    'checked_at': datetime.utcnow().isoformat()
                }
            elif response.status_code == 404:
                # URL henüz taranmamış, yeni scan başlat
                return self._submit_url_scan(url_to_check)
            else:
                return {
                    'analyzed': False,
                    'error': f'API hatası: {response.status_code}',
                    'url': url_to_check
                }
                
        except Exception as e:
            return {
                'analyzed': False,
                'error': str(e),
                'url': url_to_check
            }
    
    def _submit_url_scan(self, url_to_check: str) -> Dict[str, Any]:
        """URL scan başlat"""
        try:
            url = f"{self.BASE_URL}/urls"
            response = requests.post(
                url,
                headers=self.headers,
                data={'url': url_to_check},
                timeout=15
            )
            
            if response.status_code == 200:
                return {
                    'analyzed': False,
                    'scan_submitted': True,
                    'url': url_to_check,
                    'message': 'URL tarama için gönderildi, sonuçlar için birkaç dakika bekleyin'
                }
            else:
                return {
                    'analyzed': False,
                    'error': f'Scan gönderilemedi: {response.status_code}',
                    'url': url_to_check
                }
                
        except Exception as e:
            return {
                'analyzed': False,
                'error': str(e),
                'url': url_to_check
            }


class ExternalAPIManager:
    """Tüm harici API'leri yöneten ana sınıf"""
    
    def __init__(self):
        self.hibp = HaveIBeenPwnedAPI()
        self.hunter = HunterIOAPI()
        self.shodan = ShodanAPI()
        self.virustotal = VirusTotalAPI()
    
    def check_email_comprehensive(self, email: str) -> Dict[str, Any]:
        """E-posta için kapsamlı kontrol"""
        results = {
            'email': email,
            'checked_at': datetime.utcnow().isoformat()
        }
        
        # HaveIBeenPwned
        results['breach_check'] = self.hibp.check_email_breaches(email)
        
        # Hunter.io
        results['verification'] = self.hunter.verify_email(email)
        
        # Domain analizi (VirusTotal)
        domain = email.split('@')[1] if '@' in email else None
        if domain:
            results['domain_analysis'] = self.virustotal.analyze_domain(domain)
        
        return results
    
    def check_domain_comprehensive(self, domain: str) -> Dict[str, Any]:
        """Domain için kapsamlı kontrol"""
        results = {
            'domain': domain,
            'checked_at': datetime.utcnow().isoformat()
        }
        
        # Hunter.io domain search
        results['email_search'] = self.hunter.domain_search(domain)
        
        # VirusTotal
        results['security_analysis'] = self.virustotal.analyze_domain(domain)
        
        return results
    
    def get_api_status(self) -> Dict[str, bool]:
        """API anahtarlarının durumu"""
        return {
            'haveibeenpwned': bool(self.hibp.api_key),
            'hunter': bool(self.hunter.api_key),
            'shodan': bool(self.shodan.api_key),
            'virustotal': bool(self.virustotal.api_key)
        }
