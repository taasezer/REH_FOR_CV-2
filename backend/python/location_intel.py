"""
REH_FOR_CV-2 OSINT Rehber - Location Intelligence Module
Konum analizi, proximity search, clustering
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Location:
    """Konum veri yapısı"""
    lat: float
    lng: float
    label: str = ""
    contact_id: int = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lng": self.lng,
            "label": self.label,
            "contact_id": self.contact_id
        }


class GeoUtils:
    """Coğrafi hesaplama yardımcıları"""
    
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        İki koordinat arası mesafe (km)
        Haversine formülü
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return GeoUtils.EARTH_RADIUS_KM * c
    
    @staticmethod
    def get_bounding_box(lat: float, lng: float, radius_km: float) -> Dict[str, float]:
        """
        Merkez ve yarıçaptan bounding box hesapla
        """
        lat_delta = radius_km / 111.0  # 1 derece ~ 111 km
        lng_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        return {
            "min_lat": lat - lat_delta,
            "max_lat": lat + lat_delta,
            "min_lng": lng - lng_delta,
            "max_lng": lng + lng_delta
        }
    
    @staticmethod
    def get_center(locations: List[Location]) -> Tuple[float, float]:
        """
        Konum listesinin merkez noktası
        """
        if not locations:
            return (0, 0)
        
        total_lat = sum(loc.lat for loc in locations)
        total_lng = sum(loc.lng for loc in locations)
        count = len(locations)
        
        return (total_lat / count, total_lng / count)
    
    @staticmethod
    def calculate_bounds(locations: List[Location]) -> Dict[str, float]:
        """
        Konum listesinin sınırlarını hesapla
        """
        if not locations:
            return {"min_lat": 0, "max_lat": 0, "min_lng": 0, "max_lng": 0}
        
        lats = [loc.lat for loc in locations]
        lngs = [loc.lng for loc in locations]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs)
        }


class ProximitySearch:
    """Yakınlık araması"""
    
    @staticmethod
    def find_nearby(
        center_lat: float, 
        center_lng: float, 
        locations: List[Location], 
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """
        Belirli bir yarıçap içindeki konumları bul
        """
        results = []
        
        for loc in locations:
            distance = GeoUtils.haversine_distance(
                center_lat, center_lng, loc.lat, loc.lng
            )
            
            if distance <= radius_km:
                results.append({
                    **loc.to_dict(),
                    "distance_km": round(distance, 2)
                })
        
        # Mesafeye göre sırala
        results.sort(key=lambda x: x["distance_km"])
        
        return results
    
    @staticmethod
    def find_within_bounds(
        locations: List[Location],
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float
    ) -> List[Location]:
        """
        Belirli sınırlar içindeki konumları bul
        """
        return [
            loc for loc in locations
            if min_lat <= loc.lat <= max_lat and min_lng <= loc.lng <= max_lng
        ]


class ClusterAnalysis:
    """Kümeleme analizi"""
    
    @staticmethod
    def simple_clustering(
        locations: List[Location], 
        cluster_radius_km: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Basit kümeleme algoritması
        Birbirine yakın konumları grupla
        """
        if not locations:
            return []
        
        clusters = []
        used = set()
        
        for i, loc in enumerate(locations):
            if i in used:
                continue
            
            # Bu konum için yeni küme oluştur
            cluster = {
                "center_lat": loc.lat,
                "center_lng": loc.lng,
                "locations": [loc.to_dict()],
                "count": 1
            }
            used.add(i)
            
            # Yakın konumları ekle
            for j, other in enumerate(locations):
                if j in used:
                    continue
                
                distance = GeoUtils.haversine_distance(
                    loc.lat, loc.lng, other.lat, other.lng
                )
                
                if distance <= cluster_radius_km:
                    cluster["locations"].append(other.to_dict())
                    cluster["count"] += 1
                    used.add(j)
            
            # Merkezi yeniden hesapla
            if cluster["count"] > 1:
                cluster["center_lat"] = sum(l["lat"] for l in cluster["locations"]) / cluster["count"]
                cluster["center_lng"] = sum(l["lng"] for l in cluster["locations"]) / cluster["count"]
            
            clusters.append(cluster)
        
        return clusters
    
    @staticmethod
    def calculate_density(
        locations: List[Location],
        grid_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Yoğunluk haritası için grid hesapla
        """
        if not locations:
            return []
        
        bounds = GeoUtils.calculate_bounds(locations)
        
        lat_step = (bounds["max_lat"] - bounds["min_lat"]) / grid_size
        lng_step = (bounds["max_lng"] - bounds["min_lng"]) / grid_size
        
        # Sıfır bölme hatası önleme
        if lat_step == 0:
            lat_step = 0.01
        if lng_step == 0:
            lng_step = 0.01
        
        grid = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                cell_min_lat = bounds["min_lat"] + i * lat_step
                cell_max_lat = cell_min_lat + lat_step
                cell_min_lng = bounds["min_lng"] + j * lng_step
                cell_max_lng = cell_min_lng + lng_step
                
                count = sum(
                    1 for loc in locations
                    if cell_min_lat <= loc.lat <= cell_max_lat and
                       cell_min_lng <= loc.lng <= cell_max_lng
                )
                
                if count > 0:
                    grid.append({
                        "lat": (cell_min_lat + cell_max_lat) / 2,
                        "lng": (cell_min_lng + cell_max_lng) / 2,
                        "count": count,
                        "intensity": count / len(locations)
                    })
        
        return grid


class HeatmapGenerator:
    """Heatmap veri üreteci"""
    
    @staticmethod
    def generate_heatmap_data(
        locations: List[Location],
        intensity_multiplier: float = 1.0
    ) -> List[List[float]]:
        """
        Leaflet.heat için heatmap verisi üret
        Format: [[lat, lng, intensity], ...]
        """
        if not locations:
            return []
        
        # Her konum için basit intensity
        return [
            [loc.lat, loc.lng, intensity_multiplier]
            for loc in locations
        ]
    
    @staticmethod
    def generate_weighted_heatmap(
        locations: List[Location],
        weights: Dict[int, float] = None
    ) -> List[List[float]]:
        """
        Ağırlıklı heatmap verisi
        weights: contact_id -> weight mapping
        """
        if not locations:
            return []
        
        if weights is None:
            weights = {}
        
        return [
            [loc.lat, loc.lng, weights.get(loc.contact_id, 1.0)]
            for loc in locations
        ]


class LocationIntelligence:
    """Ana konum istihbarat sınıfı"""
    
    def __init__(self, locations: List[Dict[str, Any]] = None):
        self.locations = []
        if locations:
            self.load_locations(locations)
    
    def load_locations(self, locations: List[Dict[str, Any]]):
        """Konum verilerini yükle"""
        self.locations = [
            Location(
                lat=loc.get("enlem") or loc.get("lat"),
                lng=loc.get("boylam") or loc.get("lng"),
                label=loc.get("label") or loc.get("tam_isim", ""),
                contact_id=loc.get("id") or loc.get("contact_id")
            )
            for loc in locations
            if (loc.get("enlem") or loc.get("lat")) and (loc.get("boylam") or loc.get("lng"))
        ]
    
    def get_heatmap_data(self) -> List[List[float]]:
        """Heatmap verisi al"""
        return HeatmapGenerator.generate_heatmap_data(self.locations)
    
    def get_clusters(self, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """Kümeleri al"""
        return ClusterAnalysis.simple_clustering(self.locations, radius_km)
    
    def get_density_grid(self, grid_size: int = 10) -> List[Dict[str, Any]]:
        """Yoğunluk grid'i al"""
        return ClusterAnalysis.calculate_density(self.locations, grid_size)
    
    def find_nearby(self, lat: float, lng: float, radius_km: float = 5.0) -> List[Dict[str, Any]]:
        """Yakın konumları bul"""
        return ProximitySearch.find_nearby(lat, lng, self.locations, radius_km)
    
    def get_bounds(self) -> Dict[str, float]:
        """Sınırları al"""
        return GeoUtils.calculate_bounds(self.locations)
    
    def get_center(self) -> Tuple[float, float]:
        """Merkezi al"""
        return GeoUtils.get_center(self.locations)
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri al"""
        if not self.locations:
            return {
                "total": 0,
                "clusters": 0,
                "center": None,
                "bounds": None
            }
        
        clusters = self.get_clusters()
        
        return {
            "total": len(self.locations),
            "clusters": len(clusters),
            "center": {
                "lat": self.get_center()[0],
                "lng": self.get_center()[1]
            },
            "bounds": self.get_bounds(),
            "analyzed_at": datetime.utcnow().isoformat()
        }


def analyze_locations(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Konum analizi ana fonksiyonu
    """
    intel = LocationIntelligence(locations)
    
    return {
        "heatmap": intel.get_heatmap_data(),
        "clusters": intel.get_clusters(),
        "statistics": intel.get_statistics()
    }
