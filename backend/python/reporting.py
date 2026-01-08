"""
REH_FOR_CV-2 OSINT Rehber - Reporting Module
PDF rapor, CSV/vCard import/export
"""

import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ContactData:
    """Kişi verisi için dataclass"""
    id: int = None
    isim: str = ""
    soyisim: str = ""
    eposta: str = ""
    telefon: str = ""
    telefon_2: str = ""
    adres: str = ""
    sehir: str = ""
    ulke: str = ""
    notlar: str = ""
    etiketler: List[str] = None
    favori: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'isim': self.isim,
            'soyisim': self.soyisim,
            'eposta': self.eposta,
            'telefon': self.telefon,
            'telefon_2': self.telefon_2,
            'adres': self.adres,
            'sehir': self.sehir,
            'ulke': self.ulke,
            'notlar': self.notlar,
            'etiketler': self.etiketler or [],
            'favori': self.favori
        }


class CSVExporter:
    """CSV export işlemleri"""
    
    HEADERS = [
        'isim', 'soyisim', 'eposta', 'telefon', 'telefon_2',
        'adres', 'sehir', 'ulke', 'notlar', 'etiketler', 'favori'
    ]
    
    @classmethod
    def export_contacts(cls, contacts: List[Dict]) -> str:
        """Kişileri CSV formatına dönüştür"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cls.HEADERS, extrasaction='ignore')
        
        writer.writeheader()
        for contact in contacts:
            row = {
                'isim': contact.get('isim', ''),
                'soyisim': contact.get('soyisim', ''),
                'eposta': contact.get('eposta', ''),
                'telefon': contact.get('telefon', ''),
                'telefon_2': contact.get('telefon_2', ''),
                'adres': contact.get('adres', ''),
                'sehir': contact.get('sehir', ''),
                'ulke': contact.get('ulke', ''),
                'notlar': contact.get('notlar', ''),
                'etiketler': ','.join(contact.get('etiketler', []) or []),
                'favori': 'evet' if contact.get('favori') else 'hayir'
            }
            writer.writerow(row)
        
        return output.getvalue()


class CSVImporter:
    """CSV import işlemleri"""
    
    REQUIRED_FIELDS = ['isim']
    OPTIONAL_FIELDS = ['soyisim', 'eposta', 'telefon', 'telefon_2', 'adres', 'sehir', 'ulke', 'notlar', 'etiketler', 'favori']
    
    @classmethod
    def parse_csv(cls, csv_content: str) -> Dict[str, Any]:
        """CSV içeriğini parse et"""
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            
            contacts = []
            errors = []
            row_num = 1
            
            for row in reader:
                row_num += 1
                
                # Gerekli alanları kontrol et
                if not row.get('isim', '').strip():
                    errors.append(f"Satır {row_num}: 'isim' alanı boş olamaz")
                    continue
                
                contact = {
                    'isim': row.get('isim', '').strip(),
                    'soyisim': row.get('soyisim', '').strip(),
                    'eposta': row.get('eposta', '').strip(),
                    'telefon': row.get('telefon', '').strip(),
                    'telefon_2': row.get('telefon_2', '').strip(),
                    'adres': row.get('adres', '').strip(),
                    'sehir': row.get('sehir', '').strip(),
                    'ulke': row.get('ulke', '').strip(),
                    'notlar': row.get('notlar', '').strip(),
                    'etiketler': [t.strip() for t in row.get('etiketler', '').split(',') if t.strip()],
                    'favori': row.get('favori', '').lower() in ['evet', 'true', '1', 'yes']
                }
                
                contacts.append(contact)
            
            return {
                'success': True,
                'contacts': contacts,
                'errors': errors,
                'total_parsed': len(contacts),
                'total_errors': len(errors)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'contacts': [],
                'errors': [str(e)]
            }


class VCardExporter:
    """vCard export işlemleri"""
    
    @classmethod
    def export_single(cls, contact: Dict) -> str:
        """Tek kişiyi vCard formatına dönüştür"""
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
        ]
        
        # İsim
        isim = contact.get('isim', '')
        soyisim = contact.get('soyisim', '')
        tam_isim = f"{isim} {soyisim}".strip()
        
        lines.append(f"FN:{cls._escape(tam_isim)}")
        lines.append(f"N:{cls._escape(soyisim)};{cls._escape(isim)};;;")
        
        # E-posta
        eposta = contact.get('eposta', '')
        if eposta:
            lines.append(f"EMAIL;TYPE=INTERNET:{cls._escape(eposta)}")
        
        # Telefon
        telefon = contact.get('telefon', '')
        if telefon:
            lines.append(f"TEL;TYPE=CELL:{cls._escape(telefon)}")
        
        telefon_2 = contact.get('telefon_2', '')
        if telefon_2:
            lines.append(f"TEL;TYPE=WORK:{cls._escape(telefon_2)}")
        
        # Adres
        adres = contact.get('adres', '')
        sehir = contact.get('sehir', '')
        ulke = contact.get('ulke', '')
        
        if adres or sehir or ulke:
            adr_parts = ['', '', cls._escape(adres), cls._escape(sehir), '', '', cls._escape(ulke)]
            lines.append(f"ADR;TYPE=HOME:{';'.join(adr_parts)}")
        
        # Notlar
        notlar = contact.get('notlar', '')
        if notlar:
            lines.append(f"NOTE:{cls._escape(notlar)}")
        
        # Kategoriler (etiketler)
        etiketler = contact.get('etiketler', [])
        if etiketler:
            lines.append(f"CATEGORIES:{','.join(etiketler)}")
        
        # Oluşturma tarihi
        lines.append(f"REV:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        
        lines.append("END:VCARD")
        
        return "\r\n".join(lines)
    
    @classmethod
    def export_multiple(cls, contacts: List[Dict]) -> str:
        """Birden fazla kişiyi vCard formatına dönüştür"""
        vcards = [cls.export_single(contact) for contact in contacts]
        return "\r\n".join(vcards)
    
    @staticmethod
    def _escape(text: str) -> str:
        """vCard özel karakterlerini escape et"""
        if not text:
            return ""
        return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


class VCardImporter:
    """vCard import işlemleri"""
    
    @classmethod
    def parse_vcard(cls, vcard_content: str) -> Dict[str, Any]:
        """vCard içeriğini parse et"""
        try:
            contacts = []
            errors = []
            
            # vCard bloklarını ayır
            vcard_blocks = vcard_content.replace('\r\n', '\n').split('BEGIN:VCARD')
            
            for i, block in enumerate(vcard_blocks[1:], 1):  # İlk boş elemanı atla
                try:
                    contact = cls._parse_single_vcard(block)
                    if contact and contact.get('isim'):
                        contacts.append(contact)
                    else:
                        errors.append(f"vCard {i}: İsim alanı bulunamadı")
                except Exception as e:
                    errors.append(f"vCard {i}: {str(e)}")
            
            return {
                'success': True,
                'contacts': contacts,
                'errors': errors,
                'total_parsed': len(contacts),
                'total_errors': len(errors)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'contacts': [],
                'errors': [str(e)]
            }
    
    @classmethod
    def _parse_single_vcard(cls, block: str) -> Optional[Dict]:
        """Tek vCard bloğunu parse et"""
        contact = {}
        
        lines = block.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line == 'END:VCARD':
                continue
            
            # Property ve value'yu ayır
            if ':' not in line:
                continue
            
            prop_part, value = line.split(':', 1)
            prop = prop_part.split(';')[0].upper()  # TYPE parametresini görmezden gel
            
            value = cls._unescape(value)
            
            if prop == 'FN':
                # Tam ismi isim ve soyisim olarak ayır
                parts = value.split(' ', 1)
                contact['isim'] = parts[0]
                contact['soyisim'] = parts[1] if len(parts) > 1 else ''
                
            elif prop == 'N':
                # N:Soyisim;İsim;;;
                parts = value.split(';')
                if len(parts) >= 2:
                    contact['soyisim'] = parts[0]
                    contact['isim'] = parts[1]
                    
            elif prop == 'EMAIL':
                contact['eposta'] = value
                
            elif prop == 'TEL':
                if 'telefon' not in contact:
                    contact['telefon'] = value
                else:
                    contact['telefon_2'] = value
                    
            elif prop == 'ADR':
                # ADR:;;Adres;Şehir;;;Ülke
                parts = value.split(';')
                if len(parts) >= 7:
                    contact['adres'] = parts[2]
                    contact['sehir'] = parts[3]
                    contact['ulke'] = parts[6]
                    
            elif prop == 'NOTE':
                contact['notlar'] = value
                
            elif prop == 'CATEGORIES':
                contact['etiketler'] = [c.strip() for c in value.split(',')]
        
        return contact if contact else None
    
    @staticmethod
    def _unescape(text: str) -> str:
        """vCard escape karakterlerini geri dönüştür"""
        if not text:
            return ""
        return text.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


class JSONExporter:
    """JSON export işlemleri"""
    
    @classmethod
    def export_contacts(cls, contacts: List[Dict]) -> str:
        """Kişileri JSON formatına dönüştür"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'total_contacts': len(contacts),
            'contacts': contacts
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)


class JSONImporter:
    """JSON import işlemleri"""
    
    @classmethod
    def parse_json(cls, json_content: str) -> Dict[str, Any]:
        """JSON içeriğini parse et"""
        try:
            data = json.loads(json_content)
            
            # contacts dizisini bul
            if isinstance(data, list):
                contacts = data
            elif isinstance(data, dict) and 'contacts' in data:
                contacts = data['contacts']
            else:
                return {
                    'success': False,
                    'error': "Geçersiz JSON yapısı. 'contacts' dizisi bulunamadı.",
                    'contacts': []
                }
            
            # Kişileri doğrula
            valid_contacts = []
            errors = []
            
            for i, contact in enumerate(contacts):
                if not isinstance(contact, dict):
                    errors.append(f"Kişi {i+1}: Geçersiz format")
                    continue
                
                if not contact.get('isim'):
                    errors.append(f"Kişi {i+1}: 'isim' alanı gerekli")
                    continue
                
                valid_contacts.append({
                    'isim': contact.get('isim', ''),
                    'soyisim': contact.get('soyisim', ''),
                    'eposta': contact.get('eposta', ''),
                    'telefon': contact.get('telefon', ''),
                    'telefon_2': contact.get('telefon_2', ''),
                    'adres': contact.get('adres', ''),
                    'sehir': contact.get('sehir', ''),
                    'ulke': contact.get('ulke', ''),
                    'notlar': contact.get('notlar', ''),
                    'etiketler': contact.get('etiketler', []),
                    'favori': contact.get('favori', False)
                })
            
            return {
                'success': True,
                'contacts': valid_contacts,
                'errors': errors,
                'total_parsed': len(valid_contacts),
                'total_errors': len(errors)
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"JSON parse hatası: {str(e)}",
                'contacts': []
            }


class ReportGenerator:
    """Rapor oluşturucu (HTML tabanlı, PDF'e dönüştürülebilir)"""
    
    @classmethod
    def generate_html_report(cls, 
                             contacts: List[Dict],
                             title: str = "OSINT Rehber Raporu",
                             include_stats: bool = True) -> str:
        """HTML rapor oluştur"""
        
        # İstatistikler
        total = len(contacts)
        with_email = sum(1 for c in contacts if c.get('eposta'))
        with_phone = sum(1 for c in contacts if c.get('telefon'))
        with_location = sum(1 for c in contacts if c.get('sehir') or c.get('ulke'))
        favorites = sum(1 for c in contacts if c.get('favori'))
        
        html = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 40px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #8B0A1A;
        }}
        .header h1 {{
            color: #8B0A1A;
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .header .date {{
            color: #888;
            font-size: 0.9rem;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #8B0A1A;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 5px;
        }}
        .contacts-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .contacts-table th,
        .contacts-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        .contacts-table th {{
            background: #1a1a1a;
            color: #8B0A1A;
            font-weight: 600;
        }}
        .contacts-table tr:hover {{
            background: #1a1a1a;
        }}
        .tag {{
            display: inline-block;
            background: #2c2c2c;
            color: #8B0A1A;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            margin: 2px;
        }}
        .favorite {{
            color: #FFD700;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 0.8rem;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .stat-card {{ border-color: #ccc; }}
            .contacts-table th {{ background: #f0f0f0; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 {title}</h1>
        <div class="date">Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
    </div>
"""
        
        if include_stats:
            html += f"""
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Toplam Kişi</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{with_email}</div>
            <div class="stat-label">E-posta</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{with_phone}</div>
            <div class="stat-label">Telefon</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{with_location}</div>
            <div class="stat-label">Konum</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{favorites}</div>
            <div class="stat-label">Favori</div>
        </div>
    </div>
"""
        
        html += """
    <table class="contacts-table">
        <thead>
            <tr>
                <th>#</th>
                <th>İsim</th>
                <th>E-posta</th>
                <th>Telefon</th>
                <th>Şehir</th>
                <th>Etiketler</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for i, contact in enumerate(contacts, 1):
            tam_isim = f"{contact.get('isim', '')} {contact.get('soyisim', '')}".strip()
            star = ' <span class="favorite">★</span>' if contact.get('favori') else ''
            
            tags_html = ''.join(
                f'<span class="tag">{tag}</span>' 
                for tag in (contact.get('etiketler') or [])
            )
            
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{tam_isim}{star}</td>
                <td>{contact.get('eposta', '-')}</td>
                <td>{contact.get('telefon', '-')}</td>
                <td>{contact.get('sehir', '-')}</td>
                <td>{tags_html or '-'}</td>
            </tr>
"""
        
        html += f"""
        </tbody>
    </table>
    
    <div class="footer">
        OSINT Rehber - {datetime.now().year} | Bu rapor otomatik olarak oluşturulmuştur.
    </div>
</body>
</html>
"""
        
        return html


class ExportManager:
    """Export işlemlerini yöneten ana sınıf"""
    
    def __init__(self):
        self.csv_exporter = CSVExporter
        self.vcard_exporter = VCardExporter
        self.json_exporter = JSONExporter
        self.report_generator = ReportGenerator
    
    def export_to_csv(self, contacts: List[Dict]) -> Dict[str, Any]:
        """CSV export"""
        try:
            content = self.csv_exporter.export_contacts(contacts)
            return {
                'success': True,
                'format': 'csv',
                'content': content,
                'filename': f'kisiler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                'mime_type': 'text/csv',
                'count': len(contacts)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_vcard(self, contacts: List[Dict]) -> Dict[str, Any]:
        """vCard export"""
        try:
            content = self.vcard_exporter.export_multiple(contacts)
            return {
                'success': True,
                'format': 'vcf',
                'content': content,
                'filename': f'kisiler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.vcf',
                'mime_type': 'text/vcard',
                'count': len(contacts)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_json(self, contacts: List[Dict]) -> Dict[str, Any]:
        """JSON export"""
        try:
            content = self.json_exporter.export_contacts(contacts)
            return {
                'success': True,
                'format': 'json',
                'content': content,
                'filename': f'kisiler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                'mime_type': 'application/json',
                'count': len(contacts)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_html(self, contacts: List[Dict], title: str = "OSINT Rehber Raporu") -> Dict[str, Any]:
        """HTML rapor export"""
        try:
            content = self.report_generator.generate_html_report(contacts, title)
            return {
                'success': True,
                'format': 'html',
                'content': content,
                'filename': f'rapor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html',
                'mime_type': 'text/html',
                'count': len(contacts)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ImportManager:
    """Import işlemlerini yöneten ana sınıf"""
    
    def __init__(self):
        self.csv_importer = CSVImporter
        self.vcard_importer = VCardImporter
        self.json_importer = JSONImporter
    
    def import_from_csv(self, content: str) -> Dict[str, Any]:
        """CSV import"""
        return self.csv_importer.parse_csv(content)
    
    def import_from_vcard(self, content: str) -> Dict[str, Any]:
        """vCard import"""
        return self.vcard_importer.parse_vcard(content)
    
    def import_from_json(self, content: str) -> Dict[str, Any]:
        """JSON import"""
        return self.json_importer.parse_json(content)
    
    def detect_format_and_import(self, content: str, filename: str = None) -> Dict[str, Any]:
        """Formatı otomatik algıla ve import et"""
        content = content.strip()
        
        # Dosya adından algıla
        if filename:
            ext = filename.lower().split('.')[-1]
            if ext == 'csv':
                return self.import_from_csv(content)
            elif ext in ['vcf', 'vcard']:
                return self.import_from_vcard(content)
            elif ext == 'json':
                return self.import_from_json(content)
        
        # İçerikten algıla
        if content.startswith('BEGIN:VCARD'):
            return self.import_from_vcard(content)
        elif content.startswith('{') or content.startswith('['):
            return self.import_from_json(content)
        else:
            # CSV varsayılan
            return self.import_from_csv(content)
