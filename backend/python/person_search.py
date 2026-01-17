# REH_FOR_CV-2 OSINT Rehber - Person Search Module
# Kişi arama ve internet'te veri toplama

import re
import hashlib
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import urllib.parse


@dataclass
class PersonSearchResult:
    """Arama sonucu veri yapısı"""
    source: str  # Kaynak (gravatar, github, vb.)
    confidence: float  # Güven skoru (0-1)
    isim: Optional[str] = None
    soyisim: Optional[str] = None
    tam_isim: Optional[str] = None
    eposta: Optional[str] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None
    sehir: Optional[str] = None
    ulke: Optional[str] = None
    dogum_tarihi: Optional[str] = None
    profil_resmi: Optional[str] = None
    bio: Optional[str] = None
    sosyal_medya: Optional[Dict[str, str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class GravatarSearch:
    """Gravatar API ile profil arama"""
    
    BASE_URL = "https://www.gravatar.com"
    
    @staticmethod
    def get_email_hash(email: str) -> str:
        """E-posta MD5 hash'i"""
        return hashlib.md5(email.lower().strip().encode()).hexdigest()
    
    @classmethod
    def search(cls, email: str, timeout: int = 5) -> Optional[PersonSearchResult]:
        """Gravatar'da profil ara"""
        try:
            email_hash = cls.get_email_hash(email)
            
            # Profil JSON
            profile_url = f"{cls.BASE_URL}/{email_hash}.json"
            response = requests.get(profile_url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                entry = data.get('entry', [{}])[0]
                
                # İsmi parse et
                display_name = entry.get('displayName', '')
                name_parts = display_name.split(' ', 1)
                isim = name_parts[0] if name_parts else None
                soyisim = name_parts[1] if len(name_parts) > 1 else None
                
                # Konum
                location = entry.get('currentLocation', '')
                
                return PersonSearchResult(
                    source='gravatar',
                    confidence=0.8,
                    isim=isim,
                    soyisim=soyisim,
                    tam_isim=display_name or None,
                    eposta=email,
                    adres=location or None,
                    profil_resmi=f"{cls.BASE_URL}/avatar/{email_hash}?s=200",
                    bio=entry.get('aboutMe'),
                    sosyal_medya={
                        acc.get('shortname'): acc.get('url')
                        for acc in entry.get('accounts', [])
                        if acc.get('shortname') and acc.get('url')
                    } or None
                )
            
            # Profil bulunamadı ama avatar olabilir
            avatar_url = f"{cls.BASE_URL}/avatar/{email_hash}?d=404"
            avatar_response = requests.get(avatar_url, timeout=timeout)
            if avatar_response.status_code == 200:
                return PersonSearchResult(
                    source='gravatar',
                    confidence=0.3,
                    eposta=email,
                    profil_resmi=f"{cls.BASE_URL}/avatar/{email_hash}?s=200"
                )
                
        except Exception as e:
            print(f"Gravatar error: {e}")
        
        return None


class GitHubSearch:
    """GitHub API ile kullanıcı arama"""
    
    BASE_URL = "https://api.github.com"
    
    @classmethod
    def search_by_email(cls, email: str, timeout: int = 5) -> Optional[PersonSearchResult]:
        """E-posta ile GitHub kullanıcısı ara"""
        try:
            # E-posta ile commit arama
            search_url = f"{cls.BASE_URL}/search/users?q={urllib.parse.quote(email)}+in:email"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            response = requests.get(search_url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if items:
                    user = items[0]
                    username = user.get('login')
                    
                    # Detaylı profil al
                    user_url = f"{cls.BASE_URL}/users/{username}"
                    user_response = requests.get(user_url, headers=headers, timeout=timeout)
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        
                        # İsmi parse et
                        full_name = user_data.get('name', '')
                        name_parts = full_name.split(' ', 1) if full_name else []
                        
                        return PersonSearchResult(
                            source='github',
                            confidence=0.7,
                            isim=name_parts[0] if name_parts else None,
                            soyisim=name_parts[1] if len(name_parts) > 1 else None,
                            tam_isim=full_name or None,
                            eposta=user_data.get('email') or email,
                            adres=user_data.get('location'),
                            profil_resmi=user_data.get('avatar_url'),
                            bio=user_data.get('bio'),
                            sosyal_medya={
                                'github': user_data.get('html_url'),
                                'blog': user_data.get('blog') or None,
                                'twitter': f"https://twitter.com/{user_data.get('twitter_username')}" if user_data.get('twitter_username') else None
                            },
                            extra_data={
                                'company': user_data.get('company'),
                                'public_repos': user_data.get('public_repos'),
                                'followers': user_data.get('followers')
                            }
                        )
                        
        except Exception as e:
            print(f"GitHub error: {e}")
        
        return None
    
    @classmethod
    def search_by_name(cls, name: str, timeout: int = 5) -> List[PersonSearchResult]:
        """İsim ile GitHub kullanıcıları ara"""
        results = []
        try:
            search_url = f"{cls.BASE_URL}/search/users?q={urllib.parse.quote(name)}+in:name&per_page=5"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            response = requests.get(search_url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                for user in data.get('items', [])[:5]:
                    username = user.get('login')
                    
                    # Detaylı profil
                    user_url = f"{cls.BASE_URL}/users/{username}"
                    user_response = requests.get(user_url, headers=headers, timeout=timeout)
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        full_name = user_data.get('name', '')
                        name_parts = full_name.split(' ', 1) if full_name else []
                        
                        results.append(PersonSearchResult(
                            source='github',
                            confidence=0.5,
                            isim=name_parts[0] if name_parts else username,
                            soyisim=name_parts[1] if len(name_parts) > 1 else None,
                            tam_isim=full_name or username,
                            eposta=user_data.get('email'),
                            adres=user_data.get('location'),
                            profil_resmi=user_data.get('avatar_url'),
                            bio=user_data.get('bio'),
                            sosyal_medya={'github': user_data.get('html_url')}
                        ))
                        
        except Exception as e:
            print(f"GitHub search error: {e}")
        
        return results


class EmailDomainAnalyzer:
    """E-posta domain analizi"""
    
    PERSONAL_DOMAINS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'live.com', 'icloud.com', 'protonmail.com', 'mail.com',
        'yandex.com', 'aol.com', 'zoho.com'
    }
    
    @classmethod
    def analyze(cls, email: str) -> Dict[str, Any]:
        """E-posta domain analizi"""
        if '@' not in email:
            return {'valid': False, 'error': 'Geçersiz e-posta formatı'}
        
        domain = email.split('@')[1].lower()
        is_personal = domain in cls.PERSONAL_DOMAINS
        
        return {
            'valid': True,
            'domain': domain,
            'is_personal': is_personal,
            'is_corporate': not is_personal,
            'suspected_organization': domain.split('.')[0].title() if not is_personal else None
        }


class NominatimGeocoder:
    """OpenStreetMap Nominatim ile geocoding"""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    
    @classmethod
    def geocode(cls, address: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Adres → Koordinat"""
        try:
            url = f"{cls.BASE_URL}/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {'User-Agent': 'REH_FOR_CV-2 OSINT Rehber/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    address_details = result.get('address', {})
                    
                    return {
                        'lat': float(result.get('lat', 0)),
                        'lon': float(result.get('lon', 0)),
                        'display_name': result.get('display_name'),
                        'city': address_details.get('city') or address_details.get('town') or address_details.get('village'),
                        'country': address_details.get('country'),
                        'country_code': address_details.get('country_code', '').upper()
                    }
                    
        except Exception as e:
            print(f"Nominatim error: {e}")
        
        return None
    
    @classmethod
    def reverse_geocode(cls, lat: float, lon: float, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Koordinat → Adres"""
        try:
            url = f"{cls.BASE_URL}/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {'User-Agent': 'REH_FOR_CV-2 OSINT Rehber/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                return {
                    'display_name': data.get('display_name'),
                    'city': address.get('city') or address.get('town'),
                    'country': address.get('country'),
                    'country_code': address.get('country_code', '').upper()
                }
                
        except Exception as e:
            print(f"Nominatim reverse error: {e}")
        
        return None


class PersonSearchEngine:
    """Ana kişi arama motoru"""
    
    def __init__(self):
        self.gravatar = GravatarSearch()
        self.github = GitHubSearch()
        self.email_analyzer = EmailDomainAnalyzer()
        self.geocoder = NominatimGeocoder()
    
    def search(self, email: str = None, name: str = None) -> Dict[str, Any]:
        """
        Kişi arama - e-posta ve/veya isim ile
        Birden fazla kaynaktan sonuç toplar
        """
        results = []
        sources_checked = []
        
        # E-posta ile arama
        if email:
            # Domain analizi
            domain_info = self.email_analyzer.analyze(email)
            
            # Gravatar
            sources_checked.append('gravatar')
            gravatar_result = self.gravatar.search(email)
            if gravatar_result:
                results.append(gravatar_result)
            
            # GitHub
            sources_checked.append('github')
            github_result = self.github.search_by_email(email)
            if github_result:
                results.append(github_result)
        
        # İsim ile arama
        if name:
            sources_checked.append('github_name')
            name_results = self.github.search_by_name(name)
            results.extend(name_results)
        
        # Sonuçları güven skoruna göre sırala
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Sonuçları birleştir (aynı kişi farklı kaynaklardan gelebilir)
        merged_results = self._merge_results(results)
        
        return {
            'query': {
                'email': email,
                'name': name
            },
            'sources_checked': sources_checked,
            'total_results': len(merged_results),
            'results': [r.to_dict() for r in merged_results],
            'searched_at': datetime.utcnow().isoformat()
        }
    
    def _merge_results(self, results: List[PersonSearchResult]) -> List[PersonSearchResult]:
        """Aynı kişiye ait sonuçları birleştir"""
        if len(results) <= 1:
            return results
        
        # Şimdilik basit: ilk 10 sonucu döndür
        return results[:10]
    
    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Adres geocoding"""
        return self.geocoder.geocode(address)


# Singleton instance
person_search_engine = PersonSearchEngine()


def search_person(email: str = None, name: str = None) -> Dict[str, Any]:
    """Ana arama fonksiyonu"""
    return person_search_engine.search(email=email, name=name)


def geocode_address(address: str) -> Optional[Dict[str, Any]]:
    """Adres geocoding"""
    return person_search_engine.geocode_address(address)
