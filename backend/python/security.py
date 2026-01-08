"""
REH_FOR_CV-2 OSINT Rehber - Security & OPSEC Module
Güvenlik, şifreleme, proxy desteği ve API key yönetimi
"""

import os
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Veri şifreleme yönetimi"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv('ENCRYPTION_KEY', 'default-encryption-key-change-me')
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Fernet instance oluştur"""
        if self._fernet is None:
            # Key derivation
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'osint-rehber-salt',  # Production'da rastgele salt kullanılmalı
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """Veriyi şifrele"""
        if not data:
            return data
        try:
            encrypted = self._get_fernet().encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception:
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """Şifreli veriyi çöz"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._get_fernet().decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return encrypted_data
    
    def hash_sensitive_data(self, data: str) -> str:
        """Tek yönlü hash (geri dönüşümsüz)"""
        if not data:
            return ""
        return hashlib.sha256(data.encode()).hexdigest()


class APIKeyManager:
    """API key yönetimi"""
    
    def __init__(self, encryption_manager: EncryptionManager = None):
        self.encryption = encryption_manager or EncryptionManager()
        self._api_keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self) -> str:
        """Yeni API key oluştur"""
        return secrets.token_urlsafe(32)
    
    def store_api_key(self, service: str, api_key: str, user_id: int) -> Dict[str, Any]:
        """API key'i şifreleyerek sakla"""
        encrypted_key = self.encryption.encrypt(api_key)
        key_hash = self.encryption.hash_sensitive_data(api_key)[:16]  # Tanımlama için kısa hash
        
        key_data = {
            'service': service,
            'encrypted_key': encrypted_key,
            'key_preview': f"{api_key[:4]}...{api_key[-4:]}",
            'key_hash': key_hash,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None
        }
        
        self._api_keys[f"{user_id}:{service}"] = key_data
        return {
            'service': service,
            'key_preview': key_data['key_preview'],
            'created_at': key_data['created_at']
        }
    
    def get_api_key(self, service: str, user_id: int) -> Optional[str]:
        """API key'i çöz ve döndür"""
        key_id = f"{user_id}:{service}"
        if key_id in self._api_keys:
            key_data = self._api_keys[key_id]
            key_data['last_used'] = datetime.utcnow().isoformat()
            return self.encryption.decrypt(key_data['encrypted_key'])
        return None
    
    def list_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """Kullanıcının API key'lerini listele (şifresiz)"""
        keys = []
        for key_id, key_data in self._api_keys.items():
            if key_data['user_id'] == user_id:
                keys.append({
                    'service': key_data['service'],
                    'key_preview': key_data['key_preview'],
                    'created_at': key_data['created_at'],
                    'last_used': key_data['last_used']
                })
        return keys
    
    def delete_api_key(self, service: str, user_id: int) -> bool:
        """API key'i sil"""
        key_id = f"{user_id}:{service}"
        if key_id in self._api_keys:
            del self._api_keys[key_id]
            return True
        return False


class ProxyManager:
    """Proxy ve Tor desteği"""
    
    SUPPORTED_TYPES = ['http', 'https', 'socks5']
    
    def __init__(self):
        self.proxies: Dict[str, str] = {}
        self.tor_enabled = False
        self.tor_port = 9050
    
    def set_proxy(self, proxy_type: str, proxy_url: str) -> bool:
        """Proxy ayarla"""
        if proxy_type not in self.SUPPORTED_TYPES:
            return False
        
        self.proxies[proxy_type] = proxy_url
        return True
    
    def get_proxies(self) -> Dict[str, str]:
        """Aktif proxy'leri döndür"""
        if self.tor_enabled:
            return {
                'http': f'socks5://127.0.0.1:{self.tor_port}',
                'https': f'socks5://127.0.0.1:{self.tor_port}'
            }
        return self.proxies if self.proxies else None
    
    def enable_tor(self, port: int = 9050) -> Dict[str, Any]:
        """Tor bağlantısını etkinleştir"""
        self.tor_enabled = True
        self.tor_port = port
        return {
            'enabled': True,
            'port': port,
            'message': 'Tor proxy aktif. Tor servisinin çalıştığından emin olun.'
        }
    
    def disable_tor(self) -> Dict[str, Any]:
        """Tor bağlantısını devre dışı bırak"""
        self.tor_enabled = False
        return {
            'enabled': False,
            'message': 'Tor proxy devre dışı.'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Proxy bağlantısını test et"""
        import requests
        
        try:
            proxies = self.get_proxies()
            
            # IP kontrolü
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                ip_data = response.json()
                return {
                    'success': True,
                    'ip': ip_data.get('ip'),
                    'proxy_active': proxies is not None,
                    'tor_active': self.tor_enabled
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class AuditLogViewer:
    """Audit log görüntüleme ve analiz"""
    
    @staticmethod
    def format_log_entry(log: Dict) -> Dict[str, Any]:
        """Log kaydını formatla"""
        return {
            'id': log.get('id'),
            'action': log.get('action'),
            'entity_type': log.get('entity_type'),
            'entity_id': log.get('entity_id'),
            'details': log.get('details'),
            'ip_address': log.get('ip_address'),
            'user_agent': log.get('user_agent'),
            'created_at': log.get('created_at'),
            'formatted_time': AuditLogViewer._format_time(log.get('created_at'))
        }
    
    @staticmethod
    def _format_time(timestamp) -> str:
        """Zamanı okunabilir formatta göster"""
        if not timestamp:
            return "-"
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        except:
            return str(timestamp)
    
    @staticmethod
    def get_action_icon(action: str) -> str:
        """Aksiyona göre ikon döndür"""
        icons = {
            'create': '➕',
            'read': '👁️',
            'update': '✏️',
            'delete': '🗑️',
            'login': '🔐',
            'logout': '🚪',
            'export': '📤',
            'import': '📥',
            'check': '🔍',
            'enrich': '💡'
        }
        return icons.get(action, '●')
    
    @staticmethod
    def get_statistics(logs: List[Dict]) -> Dict[str, Any]:
        """Log istatistikleri"""
        if not logs:
            return {'total': 0}
        
        action_counts = {}
        entity_counts = {}
        hourly_activity = [0] * 24
        
        for log in logs:
            # Action sayıları
            action = log.get('action', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
            
            # Entity sayıları
            entity = log.get('entity_type', 'unknown')
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
            
            # Saatlik aktivite
            try:
                created = log.get('created_at')
                if created:
                    if isinstance(created, str):
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    else:
                        dt = created
                    hourly_activity[dt.hour] += 1
            except:
                pass
        
        return {
            'total': len(logs),
            'by_action': action_counts,
            'by_entity': entity_counts,
            'hourly_activity': hourly_activity,
            'most_common_action': max(action_counts, key=action_counts.get) if action_counts else None
        }


class SecurityConfig:
    """Güvenlik yapılandırması"""
    
    DEFAULT_CONFIG = {
        'session_timeout_minutes': 60,
        'max_login_attempts': 5,
        'lockout_duration_minutes': 15,
        'require_strong_password': True,
        'min_password_length': 8,
        'log_all_requests': False,
        'mask_sensitive_data': True,
        'enable_2fa': False
    }
    
    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default=None):
        """Yapılandırma değeri al"""
        return self.config.get(key, default)
    
    def set(self, key: str, value) -> bool:
        """Yapılandırma değeri ayarla"""
        if key in self.DEFAULT_CONFIG:
            self.config[key] = value
            return True
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """Tüm yapılandırmayı döndür"""
        return self.config.copy()
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Şifre gücünü kontrol et"""
        issues = []
        score = 0
        
        if len(password) >= self.config['min_password_length']:
            score += 1
        else:
            issues.append(f"En az {self.config['min_password_length']} karakter olmalı")
        
        if any(c.isupper() for c in password):
            score += 1
        else:
            issues.append("En az bir büyük harf içermeli")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            issues.append("En az bir küçük harf içermeli")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            issues.append("En az bir rakam içermeli")
        
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 1
        else:
            issues.append("En az bir özel karakter içermeli")
        
        strength = 'weak'
        if score >= 5:
            strength = 'strong'
        elif score >= 3:
            strength = 'medium'
        
        return {
            'valid': len(issues) == 0,
            'score': score,
            'max_score': 5,
            'strength': strength,
            'issues': issues
        }


class DataMasker:
    """Hassas veri maskeleme"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """E-postayı maskele"""
        if not email or '@' not in email:
            return email
        
        parts = email.split('@')
        local = parts[0]
        domain = parts[1]
        
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Telefon numarasını maskele"""
        if not phone:
            return phone
        
        # Sadece rakamları al
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) < 4:
            return '*' * len(phone)
        
        return '*' * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def mask_api_key(key: str) -> str:
        """API key'i maskele"""
        if not key or len(key) < 8:
            return '********'
        
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
    
    @staticmethod
    def mask_ip(ip: str) -> str:
        """IP adresini maskele"""
        if not ip:
            return ip
        
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.**"
        return ip


class SessionManager:
    """Oturum güvenliği yönetimi"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.active_sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Yeni oturum oluştur"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=self.config.get('session_timeout_minutes'))
        
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        self.active_sessions[session_id] = session
        return session
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Oturumu doğrula"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        expires_at = datetime.fromisoformat(session['expires_at'])
        
        if datetime.utcnow() > expires_at:
            del self.active_sessions[session_id]
            return None
        
        # Aktiviteyi güncelle
        session['last_activity'] = datetime.utcnow().isoformat()
        return session
    
    def end_session(self, session_id: str) -> bool:
        """Oturumu sonlandır"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def check_login_attempts(self, ip_address: str) -> Dict[str, Any]:
        """Giriş denemelerini kontrol et"""
        now = datetime.utcnow()
        lockout_duration = timedelta(minutes=self.config.get('lockout_duration_minutes'))
        
        # Eski denemeleri temizle
        if ip_address in self.failed_attempts:
            self.failed_attempts[ip_address] = [
                t for t in self.failed_attempts[ip_address]
                if now - t < lockout_duration
            ]
        
        attempts = len(self.failed_attempts.get(ip_address, []))
        max_attempts = self.config.get('max_login_attempts')
        
        if attempts >= max_attempts:
            oldest = min(self.failed_attempts[ip_address])
            unlock_at = oldest + lockout_duration
            remaining = (unlock_at - now).seconds
            
            return {
                'locked': True,
                'attempts': attempts,
                'max_attempts': max_attempts,
                'unlock_in_seconds': remaining
            }
        
        return {
            'locked': False,
            'attempts': attempts,
            'max_attempts': max_attempts,
            'remaining_attempts': max_attempts - attempts
        }
    
    def record_failed_attempt(self, ip_address: str):
        """Başarısız giriş denemesini kaydet"""
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        self.failed_attempts[ip_address].append(datetime.utcnow())
    
    def clear_failed_attempts(self, ip_address: str):
        """Başarılı girişte denemeleri temizle"""
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]


# Global instances
security_config = SecurityConfig()
encryption_manager = EncryptionManager()
api_key_manager = APIKeyManager(encryption_manager)
proxy_manager = ProxyManager()
session_manager = SessionManager(security_config)
data_masker = DataMasker()
audit_viewer = AuditLogViewer()
