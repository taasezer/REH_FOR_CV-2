"""
REH_FOR_CV-2 OSINT Rehber - Social Media Lookup Module
Sosyal medya profil bulma ve doğrulama
"""

import re
import hashlib
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import quote


class SocialMediaLookup:
    """Sosyal medya profil arama sınıfı"""
    
    # Platform URL şablonları
    PLATFORMS = {
        'github': {
            'name': 'GitHub',
            'url_template': 'https://github.com/{username}',
            'api_url': 'https://api.github.com/users/{username}',
            'icon': '🐙'
        },
        'twitter': {
            'name': 'Twitter/X',
            'url_template': 'https://twitter.com/{username}',
            'icon': '🐦'
        },
        'linkedin': {
            'name': 'LinkedIn',
            'url_template': 'https://linkedin.com/in/{username}',
            'icon': '💼'
        },
        'instagram': {
            'name': 'Instagram',
            'url_template': 'https://instagram.com/{username}',
            'icon': '📷'
        },
        'facebook': {
            'name': 'Facebook',
            'url_template': 'https://facebook.com/{username}',
            'icon': '👤'
        },
        'reddit': {
            'name': 'Reddit',
            'url_template': 'https://reddit.com/user/{username}',
            'icon': '🤖'
        },
        'medium': {
            'name': 'Medium',
            'url_template': 'https://medium.com/@{username}',
            'icon': '✍️'
        },
        'dev': {
            'name': 'DEV.to',
            'url_template': 'https://dev.to/{username}',
            'icon': '👨‍💻'
        },
        'youtube': {
            'name': 'YouTube',
            'url_template': 'https://youtube.com/@{username}',
            'icon': '📺'
        },
        'tiktok': {
            'name': 'TikTok',
            'url_template': 'https://tiktok.com/@{username}',
            'icon': '🎵'
        },
        'pinterest': {
            'name': 'Pinterest',
            'url_template': 'https://pinterest.com/{username}',
            'icon': '📌'
        },
        'telegram': {
            'name': 'Telegram',
            'url_template': 'https://t.me/{username}',
            'icon': '✈️'
        }
    }
    
    # Request timeout
    TIMEOUT = 5
    
    # User agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    @staticmethod
    def extract_username_from_email(email: str) -> str:
        """E-postadan kullanıcı adı çıkar"""
        if not email or '@' not in email:
            return ''
        
        username = email.split('@')[0].lower()
        # Sayıları ve özel karakterleri kaldır
        clean = re.sub(r'[0-9._\-+]', '', username)
        
        # Eğer çok kısa kaldıysa orijinali kullan
        if len(clean) < 3:
            clean = re.sub(r'[._\-+]', '', username)
        
        return clean
    
    @staticmethod
    def generate_username_variations(base: str) -> List[str]:
        """Kullanıcı adı varyasyonları oluştur"""
        if not base:
            return []
        
        base = base.lower().strip()
        variations = [base]
        
        # Alt çizgi ve tire varyasyonları
        if '_' in base or '-' in base:
            # Birleştir
            variations.append(base.replace('_', '').replace('-', ''))
            # Değiştir
            variations.append(base.replace('_', '-'))
            variations.append(base.replace('-', '_'))
        
        # Kısa versiyon
        if len(base) > 5:
            variations.append(base[:5])
        
        # Unique list döndür
        return list(dict.fromkeys(variations))
    
    @classmethod
    def check_github(cls, username: str) -> Dict[str, Any]:
        """GitHub profili kontrol et"""
        try:
            api_url = cls.PLATFORMS['github']['api_url'].format(username=username)
            response = requests.get(
                api_url,
                headers={'User-Agent': cls.USER_AGENT},
                timeout=cls.TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'exists': True,
                    'platform': 'github',
                    'username': username,
                    'url': cls.PLATFORMS['github']['url_template'].format(username=username),
                    'profile': {
                        'name': data.get('name'),
                        'bio': data.get('bio'),
                        'company': data.get('company'),
                        'location': data.get('location'),
                        'blog': data.get('blog'),
                        'avatar_url': data.get('avatar_url'),
                        'public_repos': data.get('public_repos'),
                        'followers': data.get('followers'),
                        'following': data.get('following'),
                        'created_at': data.get('created_at')
                    }
                }
            elif response.status_code == 404:
                return {'exists': False, 'platform': 'github', 'username': username}
            else:
                return {'exists': None, 'platform': 'github', 'username': username, 'error': 'Rate limited or error'}
                
        except Exception as e:
            return {'exists': None, 'platform': 'github', 'username': username, 'error': str(e)}
    
    @classmethod
    def check_url_exists(cls, url: str) -> bool:
        """URL'in var olup olmadığını kontrol et"""
        try:
            response = requests.head(
                url,
                headers={'User-Agent': cls.USER_AGENT},
                timeout=cls.TIMEOUT,
                allow_redirects=True
            )
            # 200, 301, 302 başarılı kabul
            return response.status_code in [200, 301, 302]
        except:
            try:
                # HEAD başarısız olursa GET dene
                response = requests.get(
                    url,
                    headers={'User-Agent': cls.USER_AGENT},
                    timeout=cls.TIMEOUT,
                    allow_redirects=True
                )
                # 404 ve benzeri sayfalar body'de "not found" içerebilir
                if response.status_code == 200:
                    content = response.text.lower()
                    if 'not found' in content or 'doesn\'t exist' in content:
                        return False
                    return True
                return False
            except:
                return False
    
    @classmethod
    def check_platform(cls, platform: str, username: str) -> Dict[str, Any]:
        """Belirli bir platformda kullanıcı adını kontrol et"""
        if platform not in cls.PLATFORMS:
            return {'exists': None, 'error': 'Bilinmeyen platform'}
        
        platform_info = cls.PLATFORMS[platform]
        
        # GitHub için özel API kontrolü
        if platform == 'github':
            return cls.check_github(username)
        
        # Diğer platformlar için URL kontrolü
        url = platform_info['url_template'].format(username=username)
        exists = cls.check_url_exists(url)
        
        return {
            'exists': exists,
            'platform': platform,
            'platform_name': platform_info['name'],
            'icon': platform_info['icon'],
            'username': username,
            'url': url if exists else None
        }
    
    @classmethod
    def search_all_platforms(cls, username: str, platforms: List[str] = None) -> Dict[str, Any]:
        """Tüm platformlarda kullanıcı adını ara"""
        if not username:
            return {'error': 'Kullanıcı adı boş'}
        
        username = username.lower().strip()
        
        # Varsayılan platformlar
        if platforms is None:
            platforms = ['github', 'twitter', 'linkedin', 'instagram']
        
        results = {
            'username': username,
            'found_profiles': [],
            'not_found': [],
            'errors': [],
            'checked_at': datetime.utcnow().isoformat()
        }
        
        for platform in platforms:
            result = cls.check_platform(platform, username)
            
            if result.get('exists') is True:
                results['found_profiles'].append(result)
            elif result.get('exists') is False:
                results['not_found'].append(platform)
            else:
                results['errors'].append({
                    'platform': platform,
                    'error': result.get('error', 'Bilinmeyen hata')
                })
        
        results['total_found'] = len(results['found_profiles'])
        
        return results
    
    @classmethod
    def search_by_email(cls, email: str, platforms: List[str] = None) -> Dict[str, Any]:
        """E-postadan kullanıcı adı çıkarıp platformlarda ara"""
        username = cls.extract_username_from_email(email)
        
        if not username:
            return {'error': 'E-postadan kullanıcı adı çıkarılamadı'}
        
        variations = cls.generate_username_variations(username)
        
        all_results = {
            'email': email,
            'extracted_usernames': variations,
            'profiles': [],
            'checked_at': datetime.utcnow().isoformat()
        }
        
        # Her varyasyon için ara (ilk eşleşmede dur)
        found_platforms = set()
        
        for variant in variations[:3]:  # Max 3 varyasyon
            result = cls.search_all_platforms(variant, platforms)
            
            for profile in result.get('found_profiles', []):
                platform = profile.get('platform')
                if platform not in found_platforms:
                    all_results['profiles'].append(profile)
                    found_platforms.add(platform)
        
        all_results['total_found'] = len(all_results['profiles'])
        
        return all_results


class GravatarLookup:
    """Gravatar profil arama"""
    
    @staticmethod
    def get_hash(email: str) -> str:
        """E-posta için Gravatar hash'i"""
        return hashlib.md5(email.lower().strip().encode()).hexdigest()
    
    @staticmethod
    def get_avatar_url(email: str, size: int = 200, default: str = '404') -> str:
        """Gravatar avatar URL'i"""
        email_hash = GravatarLookup.get_hash(email)
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"
    
    @staticmethod
    def get_profile_url(email: str) -> str:
        """Gravatar profil URL'i"""
        email_hash = GravatarLookup.get_hash(email)
        return f"https://www.gravatar.com/{email_hash}.json"
    
    @classmethod
    def check_exists(cls, email: str) -> bool:
        """Gravatar profili var mı"""
        try:
            url = cls.get_avatar_url(email, default='404')
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @classmethod
    def get_profile(cls, email: str) -> Dict[str, Any]:
        """Gravatar profil bilgilerini al"""
        try:
            url = cls.get_profile_url(email)
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                entry = data.get('entry', [{}])[0]
                
                return {
                    'exists': True,
                    'email_hash': cls.get_hash(email),
                    'display_name': entry.get('displayName'),
                    'preferred_username': entry.get('preferredUsername'),
                    'profile_url': entry.get('profileUrl'),
                    'avatar_url': cls.get_avatar_url(email),
                    'photos': entry.get('photos', []),
                    'about': entry.get('aboutMe'),
                    'location': entry.get('currentLocation'),
                    'accounts': entry.get('accounts', [])
                }
            else:
                return {
                    'exists': False,
                    'email_hash': cls.get_hash(email)
                }
                
        except Exception as e:
            return {
                'exists': None,
                'error': str(e)
            }


def lookup_social_profiles(email: str = None, username: str = None, 
                           platforms: List[str] = None) -> Dict[str, Any]:
    """Sosyal medya profil araması yap"""
    results = {
        'gravatar': None,
        'social_profiles': None,
        'checked_at': datetime.utcnow().isoformat()
    }
    
    # Gravatar kontrolü
    if email:
        results['gravatar'] = GravatarLookup.get_profile(email)
    
    # Sosyal medya araması
    if username:
        results['social_profiles'] = SocialMediaLookup.search_all_platforms(username, platforms)
    elif email:
        results['social_profiles'] = SocialMediaLookup.search_by_email(email, platforms)
    
    return results
