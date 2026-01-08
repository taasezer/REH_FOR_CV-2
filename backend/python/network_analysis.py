"""
REH_FOR_CV-2 OSINT Rehber - Network Analysis Module
İlişki ağı analizi ve otomatik bağlantı tespiti
"""

from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict


@dataclass
class Node:
    """Graf düğümü"""
    id: int
    label: str
    email: str = None
    phone: str = None
    city: str = None
    country: str = None
    company: str = None  # email domain'den çıkarılabilir
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            'country': self.country,
            'company': self.company
        }


@dataclass
class Edge:
    """Graf kenarı (ilişki)"""
    source: int
    target: int
    relation_type: str
    strength: int = 1
    auto_detected: bool = False
    detection_reason: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'type': self.relation_type,
            'strength': self.strength,
            'auto_detected': self.auto_detected,
            'detection_reason': self.detection_reason
        }


class NetworkGraph:
    """İlişki ağı grafı"""
    
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency: Dict[int, Set[int]] = defaultdict(set)
    
    def add_node(self, node: Node):
        """Düğüm ekle"""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: Edge):
        """Kenar ekle"""
        self.edges.append(edge)
        self.adjacency[edge.source].add(edge.target)
        self.adjacency[edge.target].add(edge.source)
    
    def get_neighbors(self, node_id: int) -> List[int]:
        """Komşu düğümleri getir"""
        return list(self.adjacency.get(node_id, set()))
    
    def get_degree(self, node_id: int) -> int:
        """Düğüm derecesi (bağlantı sayısı)"""
        return len(self.adjacency.get(node_id, set()))
    
    def to_d3_format(self) -> Dict[str, Any]:
        """D3.js force-directed graph formatı"""
        return {
            'nodes': [
                {
                    'id': node.id,
                    'label': node.label,
                    'email': node.email,
                    'city': node.city,
                    'degree': self.get_degree(node.id)
                }
                for node in self.nodes.values()
            ],
            'links': [edge.to_dict() for edge in self.edges]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Ağ istatistikleri"""
        if not self.nodes:
            return {
                'node_count': 0,
                'edge_count': 0,
                'avg_degree': 0,
                'density': 0
            }
        
        node_count = len(self.nodes)
        edge_count = len(self.edges)
        
        degrees = [self.get_degree(n) for n in self.nodes]
        avg_degree = sum(degrees) / node_count if node_count > 0 else 0
        
        # Graf yoğunluğu (0-1 arası)
        max_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_edges if max_edges > 0 else 0
        
        return {
            'node_count': node_count,
            'edge_count': edge_count,
            'avg_degree': round(avg_degree, 2),
            'max_degree': max(degrees) if degrees else 0,
            'density': round(density, 4)
        }


class RelationshipDetector:
    """Otomatik ilişki tespiti"""
    
    @staticmethod
    def extract_email_domain(email: str) -> str:
        """E-postadan domain çıkar"""
        if not email or '@' not in email:
            return None
        return email.split('@')[1].lower()
    
    @staticmethod
    def is_corporate_domain(domain: str) -> bool:
        """Kurumsal domain mi?"""
        if not domain:
            return False
        
        # Kişisel e-posta sağlayıcıları
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'live.com', 'icloud.com', 'protonmail.com', 'mail.com'
        }
        
        return domain.lower() not in personal_domains
    
    @staticmethod
    def detect_same_domain(contacts: List[Dict]) -> List[Tuple[int, int, str]]:
        """Aynı e-posta domain'ine sahip kişileri tespit et"""
        domain_groups = defaultdict(list)
        
        for contact in contacts:
            email = contact.get('eposta')
            if email:
                domain = RelationshipDetector.extract_email_domain(email)
                if domain and RelationshipDetector.is_corporate_domain(domain):
                    domain_groups[domain].append(contact['id'])
        
        connections = []
        for domain, contact_ids in domain_groups.items():
            if len(contact_ids) >= 2:
                # Tüm çiftleri bağla
                for i in range(len(contact_ids)):
                    for j in range(i + 1, len(contact_ids)):
                        connections.append((
                            contact_ids[i],
                            contact_ids[j],
                            f'same_domain:{domain}'
                        ))
        
        return connections
    
    @staticmethod
    def detect_same_city(contacts: List[Dict]) -> List[Tuple[int, int, str]]:
        """Aynı şehirdeki kişileri tespit et"""
        city_groups = defaultdict(list)
        
        for contact in contacts:
            city = contact.get('sehir')
            if city:
                city_groups[city.lower().strip()].append(contact['id'])
        
        connections = []
        for city, contact_ids in city_groups.items():
            if len(contact_ids) >= 2:
                for i in range(len(contact_ids)):
                    for j in range(i + 1, len(contact_ids)):
                        connections.append((
                            contact_ids[i],
                            contact_ids[j],
                            f'same_city:{city}'
                        ))
        
        return connections
    
    @staticmethod
    def detect_same_country(contacts: List[Dict]) -> List[Tuple[int, int, str]]:
        """Aynı ülkedeki kişileri tespit et"""
        country_groups = defaultdict(list)
        
        for contact in contacts:
            country = contact.get('ulke')
            if country:
                country_groups[country.lower().strip()].append(contact['id'])
        
        connections = []
        for country, contact_ids in country_groups.items():
            if len(contact_ids) >= 2:
                for i in range(len(contact_ids)):
                    for j in range(i + 1, len(contact_ids)):
                        connections.append((
                            contact_ids[i],
                            contact_ids[j],
                            f'same_country:{country}'
                        ))
        
        return connections
    
    @staticmethod
    def detect_same_phone_prefix(contacts: List[Dict]) -> List[Tuple[int, int, str]]:
        """Aynı telefon prefix'ine sahip kişileri tespit et (aynı şirket/aile olabilir)"""
        prefix_groups = defaultdict(list)
        
        for contact in contacts:
            phone = contact.get('telefon')
            if phone:
                # İlk 7 haneyi al (alan kodu + prefix)
                normalized = ''.join(filter(str.isdigit, phone))
                if len(normalized) >= 7:
                    prefix = normalized[:7]
                    prefix_groups[prefix].append(contact['id'])
        
        connections = []
        for prefix, contact_ids in prefix_groups.items():
            if len(contact_ids) >= 2:
                for i in range(len(contact_ids)):
                    for j in range(i + 1, len(contact_ids)):
                        connections.append((
                            contact_ids[i],
                            contact_ids[j],
                            f'same_phone_prefix:{prefix}'
                        ))
        
        return connections
    
    @staticmethod
    def detect_name_similarity(contacts: List[Dict]) -> List[Tuple[int, int, str]]:
        """Benzer soyisimleri tespit et (aile olabilir)"""
        surname_groups = defaultdict(list)
        
        for contact in contacts:
            surname = contact.get('soyisim')
            if surname and len(surname) > 2:
                surname_groups[surname.lower().strip()].append(contact['id'])
        
        connections = []
        for surname, contact_ids in surname_groups.items():
            if len(contact_ids) >= 2:
                for i in range(len(contact_ids)):
                    for j in range(i + 1, len(contact_ids)):
                        connections.append((
                            contact_ids[i],
                            contact_ids[j],
                            f'same_surname:{surname}'
                        ))
        
        return connections
    
    @classmethod
    def detect_all(cls, contacts: List[Dict], existing_pairs: Set[Tuple[int, int]] = None) -> List[Dict]:
        """Tüm otomatik ilişkileri tespit et"""
        if existing_pairs is None:
            existing_pairs = set()
        
        all_connections = []
        
        # Domain bazlı (iş ilişkisi)
        for c1, c2, reason in cls.detect_same_domain(contacts):
            pair = tuple(sorted([c1, c2]))
            if pair not in existing_pairs:
                all_connections.append({
                    'kisi_1_id': c1,
                    'kisi_2_id': c2,
                    'iliski_tipi': 'is',
                    'guc': 5,
                    'tespit_nedeni': reason
                })
                existing_pairs.add(pair)
        
        # Soyisim bazlı (aile ilişkisi)
        for c1, c2, reason in cls.detect_name_similarity(contacts):
            pair = tuple(sorted([c1, c2]))
            if pair not in existing_pairs:
                all_connections.append({
                    'kisi_1_id': c1,
                    'kisi_2_id': c2,
                    'iliski_tipi': 'aile',
                    'guc': 7,
                    'tespit_nedeni': reason
                })
                existing_pairs.add(pair)
        
        # Şehir bazlı (tanıdık)
        for c1, c2, reason in cls.detect_same_city(contacts):
            pair = tuple(sorted([c1, c2]))
            if pair not in existing_pairs:
                all_connections.append({
                    'kisi_1_id': c1,
                    'kisi_2_id': c2,
                    'iliski_tipi': 'tanidik',
                    'guc': 2,
                    'tespit_nedeni': reason
                })
                existing_pairs.add(pair)
        
        return all_connections


class NetworkAnalyzer:
    """Ağ analizi"""
    
    @staticmethod
    def find_central_nodes(graph: NetworkGraph, top_n: int = 5) -> List[Dict]:
        """En merkezi düğümleri bul (degree centrality)"""
        centrality = []
        
        for node_id, node in graph.nodes.items():
            degree = graph.get_degree(node_id)
            centrality.append({
                'id': node_id,
                'label': node.label,
                'degree': degree
            })
        
        centrality.sort(key=lambda x: x['degree'], reverse=True)
        return centrality[:top_n]
    
    @staticmethod
    def find_communities(graph: NetworkGraph) -> List[List[int]]:
        """Basit topluluk tespiti (bağlı bileşenler)"""
        if not graph.nodes:
            return []
        
        visited = set()
        communities = []
        
        def dfs(node_id: int, community: List[int]):
            visited.add(node_id)
            community.append(node_id)
            for neighbor in graph.get_neighbors(node_id):
                if neighbor not in visited:
                    dfs(neighbor, community)
        
        for node_id in graph.nodes:
            if node_id not in visited:
                community = []
                dfs(node_id, community)
                communities.append(community)
        
        return communities
    
    @staticmethod
    def get_relationship_distribution(edges: List[Edge]) -> Dict[str, int]:
        """İlişki tipi dağılımı"""
        distribution = defaultdict(int)
        for edge in edges:
            distribution[edge.relation_type] += 1
        return dict(distribution)


def build_network_from_contacts(contacts: List[Dict], relationships: List[Dict]) -> NetworkGraph:
    """Kişi ve ilişkilerden ağ oluştur"""
    graph = NetworkGraph()
    
    # Düğümleri ekle
    for contact in contacts:
        node = Node(
            id=contact['id'],
            label=contact.get('tam_isim') or contact.get('isim', ''),
            email=contact.get('eposta'),
            phone=contact.get('telefon'),
            city=contact.get('sehir'),
            country=contact.get('ulke')
        )
        graph.add_node(node)
    
    # Kenarları ekle
    for rel in relationships:
        edge = Edge(
            source=rel['kisi_1_id'],
            target=rel['kisi_2_id'],
            relation_type=rel.get('iliski_tipi', 'diger'),
            strength=rel.get('guc', 1),
            auto_detected=rel.get('otomatik', False),
            detection_reason=rel.get('tespit_nedeni')
        )
        graph.add_edge(edge)
    
    return graph


def analyze_network(contacts: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """Tam ağ analizi"""
    graph = build_network_from_contacts(contacts, relationships)
    
    return {
        'd3_data': graph.to_d3_format(),
        'statistics': graph.get_statistics(),
        'central_nodes': NetworkAnalyzer.find_central_nodes(graph),
        'communities': NetworkAnalyzer.find_communities(graph),
        'relationship_distribution': NetworkAnalyzer.get_relationship_distribution(graph.edges),
        'analyzed_at': datetime.utcnow().isoformat()
    }
