# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 데이터베이스 URL (SQLite 사용, 나중에 PostgreSQL로 변경 가능)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sinkhole_service.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    location_searches = relationship("LocationSearch", back_populates="user")
    sinkhole_reports = relationship("SinkholeReport", back_populates="user")

class LocationSearch(Base):
    __tablename__ = "location_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    risk_probability = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="location_searches")

class SinkholeReport(Base):
    __tablename__ = "sinkhole_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String, default="pending")  # pending, verified, false_positive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="sinkhole_reports")

class RiskArea(Base):
    __tablename__ = "risk_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)  # low, medium, high, critical
    risk_probability = Column(Float, nullable=False)
    radius = Column(Float, default=100)  # 위험 반경 (미터)
    factors = Column(Text, nullable=True)  # JSON 형태로 위험 요소들 저장
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# backend/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# 사용자 관련 스키마
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# 위치 관련 스키마
class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[float] = 1000

class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    avoid_high_risk: bool = True

# 음성 쿼리 스키마
class VoiceQuery(BaseModel):
    audio_data: str  # base64 encoded audio
    format: str = "wav"

# 이미지 분석 스키마
class ImageAnalysis(BaseModel):
    image_data: str  # base64 encoded image
    include_location: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# 응답 스키마
class RiskAssessment(BaseModel):
    risk_level: str
    probability: float
    factors: List[str]
    recommendations: List[str]

class SafeRoute(BaseModel):
    waypoints: List[dict]
    distance: float
    duration: int
    risk_areas_avoided: List[dict]
    warnings: List[str]