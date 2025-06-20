# backend/utils.py
import math
import httpx
import asyncio
from typing import Dict, List, Tuple, Any
import os

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """좌표 유효성 검사"""
    # 서울시 대략적인 경계
    if not (37.4 <= latitude <= 37.8):
        return False
    if not (126.7 <= longitude <= 127.3):
        return False
    return True

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 지점 간 거리 계산 (하버사인 공식)"""
    R = 6371  # 지구 반지름 (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c * 1000  # 미터 단위로 반환

async def get_current_location() -> Dict[str, float]:
    """현재 위치 조회 (IP 기반 또는 GPS)"""
    try:
        # IP 기반 위치 조회 (실제로는 클라이언트에서 GPS 사용)
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ip-api.com/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "latitude": data.get("lat", 37.5665),
                    "longitude": data.get("lon", 126.9780)
                }
    except:
        pass
    
    # 기본값: 서울시청
    return {"latitude": 37.5665, "longitude": 126.9780}

async def calculate_safe_route(
    start_lat: float, start_lng: float, 
    end_lat: float, end_lng: float,
    avoid_high_risk: bool = True
) -> Dict[str, Any]:
    """안전 경로 계산"""
    
    # 임시 위험지역 데이터 (실제로는 DB에서 조회)
    high_risk_areas = [
        {"lat": 37.5510, "lng": 126.9882, "radius": 200, "risk": 0.8},
        {"lat": 37.5660, "lng": 126.9784, "radius": 150, "risk": 0.7},
        {"lat": 37.5400, "lng": 127.0000, "radius": 300, "risk": 0.9}
    ]
    
    try:
        # Google Maps Directions API 사용 (실제 구현 시)
        # 여기서는 더미 데이터 반환
        
        # 직선 거리 계산
        distance = calculate_distance(start_lat, start_lng, end_lat, end_lng)
        estimated_duration = int(distance / 50 * 60)  # 50m/분으로 가정
        
        # 경로상 위험지역 확인
        avoided_risks = []
        warnings = []
        
        if avoid_high_risk:
            for risk_area in high_risk_areas:
                # 경로가 위험지역을 지나는지 간단히 확인
                risk_distance_start = calculate_distance(
                    start_lat, start_lng, 
                    risk_area["lat"], risk_area["lng"]
                )
                risk_distance_end = calculate_distance(
                    end_lat, end_lng,
                    risk_area["lat"], risk_area["lng"]
                )
                
                if min(risk_distance_start, risk_distance_end) < risk_area["radius"]:
                    avoided_risks.append({
                        "location": {"lat": risk_area["lat"], "lng": risk_area["lng"]},
                        "risk_level": risk_area["risk"],
                        "reason": "싱크홀 위험지역"
                    })
                    warnings.append(f"위험지역을 우회합니다. (위험도: {risk_area['risk']:.1%})")
        
        # 경로 포인트 생성 (단순화)
        waypoints = [
            {"lat": start_lat, "lng": start_lng, "type": "start"},
            {"lat": (start_lat + end_lat) / 2, "lng": (start_lng + end_lng) / 2, "type": "waypoint"},
            {"lat": end_lat, "lng": end_lng, "type": "end"}
        ]
        
        return {
            "waypoints": waypoints,
            "distance": distance,
            "duration": estimated_duration,
            "avoided_risks": avoided_risks,
            "warnings": warnings,
            "route_type": "safe" if avoid_high_risk else "direct"
        }
        
    except Exception as e:
        print(f"경로 계산 실패: {e}")
        return {
            "waypoints": [
                {"lat": start_lat, "lng": start_lng, "type": "start"},
                {"lat": end_lat, "lng": end_lng, "type": "end"}
            ],
            "distance": calculate_distance(start_lat, start_lng, end_lat, end_lng),
            "duration": 0,
            "avoided_risks": [],
            "warnings": ["경로 계산에 실패했습니다."],
            "route_type": "direct"
        }

async def geocode_address(address: str) -> Dict[str, Any]:
    """주소를 좌표로 변환"""
    try:
        # Google Geocoding API 또는 Kakao Map API 사용
        # 여기서는 더미 데이터 반환
        seoul_addresses = {
            "서울시청": {"lat": 37.5665, "lng": 126.9780},
            "강남역": {"lat": 37.4979, "lng": 127.0276},
            "홍대입구역": {"lat": 37.5563, "lng": 126.9236},
            "종로": {"lat": 37.5694, "lng": 126.9769}
        }
        
        for key, coords in seoul_addresses.items():
            if key in address:
                return {
                    "latitude": coords["lat"],
                    "longitude": coords["lng"],
                    "formatted_address": f"서울특별시 {key}",
                    "success": True
                }
        
        # 기본값
        return {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "formatted_address": "서울특별시 중구 태평로1가 31",
            "success": False,
            "message": "정확한 주소를 찾을 수 없습니다."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"주소 변환 실패: {str(e)}"
        }

def format_risk_level(probability: float) -> str:
    """위험도를 문자열로 변환"""
    if probability >= 0.8:
        return "매우높음"
    elif probability >= 0.6:
        return "높음"
    elif probability >= 0.4:
        return "중간"
    elif probability >= 0.2:
        return "낮음"
    else:
        return "매우낮음"

def get_risk_color(probability: float) -> str:
    """위험도에 따른 색상 반환"""
    if probability >= 0.8:
        return "#FF0000"  # 빨간색
    elif probability >= 0.6:
        return "#FF8000"  # 주황색
    elif probability >= 0.4:
        return "#FFFF00"  # 노란색
    elif probability >= 0.2:
        return "#80FF00"  # 연두색
    else:
        return "#00FF00"  # 초록색

