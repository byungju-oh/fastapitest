# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime, timedelta
import jwt
import hashlib
import httpx
import asyncio
from io import BytesIO
import base64

# 로컬 모듈 임포트
from database import get_db, engine, Base
from models import User, SinkholeReport, LocationSearch
from schemas import UserCreate, UserLogin, LocationRequest, RouteRequest, VoiceQuery, ImageAnalysis
from azure_services import AzureOpenAI, AzureSpeech, AzureCustomVision
from utils import get_current_location, calculate_safe_route, validate_coordinates

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sinkhole Prediction Service",
    description="AI-powered sinkhole prediction and safety navigation service",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

# Azure 서비스 인스턴스
azure_openai = AzureOpenAI()
azure_speech = AzureSpeech()
azure_vision = AzureCustomVision()

# 임시 ML 모델 엔드포인트 (나중에 실제 모델로 교체)
ML_MODEL_ENDPOINT = "http://localhost:8001/predict"

# 인증 헬퍼 함수
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 회원가입 및 로그인 엔드포인트
@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 사용자 존재 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 비밀번호 해싱
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    
    # 새 사용자 생성
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "username": db_user.username,
            "full_name": db_user.full_name
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # 사용자 확인
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 비밀번호 확인
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    if db_user.hashed_password != hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "username": db_user.username,
            "full_name": db_user.full_name
        }
    }

# 현재 위치 기반 싱크홀 위험도 조회
@app.post("/api/location/risk")
async def get_location_risk(
    location: LocationRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        # 좌표 유효성 검사
        if not validate_coordinates(location.latitude, location.longitude):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        # ML 모델 API 호출 (임시로 더미 데이터 반환)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    ML_MODEL_ENDPOINT,
                    json={
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                        "radius": location.radius or 1000
                    },
                    timeout=10
                )
                risk_data = response.json()
            except httpx.RequestError:
                # ML 모델 서버가 없을 때 더미 데이터
                risk_data = {
                    "risk_level": "medium",
                    "probability": 0.35,
                    "factors": [
                        "Old water pipes in area",
                        "High rainfall last month",
                        "Subway construction nearby"
                    ],
                    "nearby_risks": [
                        {
                            "latitude": location.latitude + 0.001,
                            "longitude": location.longitude + 0.001,
                            "risk_level": "high",
                            "probability": 0.78
                        }
                    ]
                }
        
        # 검색 기록 저장
        search_record = LocationSearch(
            user_id=1,  # 임시로 1로 설정
            latitude=location.latitude,
            longitude=location.longitude,
            risk_probability=risk_data["probability"],
            searched_at=datetime.utcnow()
        )
        db.add(search_record)
        db.commit()
        
        return {
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "risk_assessment": risk_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

# 안전 경로 계산
@app.post("/api/navigation/safe-route")
async def get_safe_route(
    route_request: RouteRequest,
    current_user: str = Depends(verify_token)
):
    try:
        # 출발지와 목적지 좌표 유효성 검사
        if not validate_coordinates(route_request.start_lat, route_request.start_lng):
            raise HTTPException(status_code=400, detail="Invalid start coordinates")
        
        if not validate_coordinates(route_request.end_lat, route_request.end_lng):
            raise HTTPException(status_code=400, detail="Invalid destination coordinates")
        
        # 안전 경로 계산 (구현 예정)
        safe_route = await calculate_safe_route(
            start_lat=route_request.start_lat,
            start_lng=route_request.start_lng,
            end_lat=route_request.end_lat,
            end_lng=route_request.end_lng,
            avoid_high_risk=route_request.avoid_high_risk
        )
        
        return {
            "route": safe_route,
            "distance": safe_route.get("distance", 0),
            "duration": safe_route.get("duration", 0),
            "risk_areas_avoided": safe_route.get("avoided_risks", []),
            "warnings": safe_route.get("warnings", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {str(e)}")

# 음성 질의응답 (Azure OpenAI + TTS)
@app.post("/api/voice/query")
async def voice_query(
    audio_file: UploadFile = File(...),
    current_user: str = Depends(verify_token)
):
    try:
        # 음성 파일을 텍스트로 변환 (Azure Speech)
        audio_content = await audio_file.read()
        text_query = await azure_speech.speech_to_text(audio_content)
        
        # OpenAI로 질의 처리
        ai_response = await azure_openai.process_sinkhole_query(text_query)
        
        # 텍스트를 음성으로 변환
        audio_response = await azure_speech.text_to_speech(ai_response)
        
        return {
            "query": text_query,
            "text_response": ai_response,
            "audio_response": base64.b64encode(audio_response).decode(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice query failed: {str(e)}")

# 이미지 분석 (Azure Custom Vision)
@app.post("/api/image/analyze")
async def analyze_sinkhole_image(
    image: UploadFile = File(...),
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        # 이미지 파일 검증
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # 이미지 읽기
        image_content = await image.read()
        
        # Azure Custom Vision으로 분석
        analysis_result = await azure_vision.analyze_sinkhole_image(image_content)
        
        response_data = {
            "is_sinkhole": analysis_result["is_sinkhole"],
            "confidence": analysis_result["confidence"],
            "analysis": analysis_result["details"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 싱크홀로 판단되면 신고 방법 안내
        if analysis_result["is_sinkhole"] and analysis_result["confidence"] > 0.7:
            reporting_info = await azure_openai.get_sinkhole_reporting_guide()
            response_data["reporting_guide"] = reporting_info
            
            # 싱크홀 신고 기록 저장
            report = SinkholeReport(
                user_id=1,  # 임시로 1로 설정
                image_path=f"uploads/{uuid.uuid4()}.jpg",
                confidence=analysis_result["confidence"],
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(report)
            db.commit()
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

# 사용자 대시보드 데이터
@app.get("/api/user/dashboard")
async def get_user_dashboard(
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        # 사용자 정보 조회
        user = db.query(User).filter(User.email == current_user).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 최근 검색 기록
        recent_searches = db.query(LocationSearch).filter(
            LocationSearch.user_id == user.id
        ).order_by(LocationSearch.searched_at.desc()).limit(10).all()
        
        # 신고 기록
        reports = db.query(SinkholeReport).filter(
            SinkholeReport.user_id == user.id
        ).order_by(SinkholeReport.created_at.desc()).limit(5).all()
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat()
            },
            "recent_searches": [
                {
                    "id": search.id,
                    "latitude": search.latitude,
                    "longitude": search.longitude,
                    "risk_probability": search.risk_probability,
                    "searched_at": search.searched_at.isoformat()
                } for search in recent_searches
            ],
            "reports": [
                {
                    "id": report.id,
                    "confidence": report.confidence,
                    "status": report.status,
                    "created_at": report.created_at.isoformat()
                } for report in reports
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data failed: {str(e)}")

# 헬스체크
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)