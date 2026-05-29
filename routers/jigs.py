# routers/jigs.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

import models
from database import SessionLocal

router = APIRouter(prefix="/jigs", tags=["jigs"])

# Hàm kết nối database cho mỗi request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schema kiểm tra dữ liệu đầu vào (Pydantic)
class JigCreate(BaseModel):
    name: str
    qty: int
    desc: str
    photo_url: Optional[str] = ""

class JigInspectIn(BaseModel):
    status: str
    missing_detail: Optional[str] = ""
    photo_url: Optional[str] = ""
    inspector: str


# 1. API lấy danh sách JIGs (GET /jigs)
@router.get("/")
def get_all_jigs(db: Session = Depends(get_db)):
    return db.query(models.Jig).order_by(models.Jig.created_at.desc()).all()


# 2. API thêm mới JIG (POST /jigs)
@router.post("/")
def create_jig(payload: JigCreate, db: Session = Depends(get_db)):
    new_jig = models.Jig(
        name=payload.name,
        qty=payload.qty,
        desc=payload.desc,
        photo_url=payload.photo_url,
        status="FULL"
    )
    db.add(new_jig)
    db.commit()
    db.refresh(new_jig)
    return new_jig


# 3. API cập nhật trạng thái kiểm tra JIG (POST /jigs/{jig_id}/inspect)
@router.post("/{jig_id}/inspect")
def inspect_jig(jig_id: int, payload: JigInspectIn, db: Session = Depends(get_db)):
    jig = db.query(models.Jig).filter(models.Jig.id == jig_id).first()
    if not jig:
        raise HTTPException(status_code=404, detail="JIG not found")
    
    jig.status = payload.status
    jig.missing_detail = payload.missing_detail if payload.status == "MISSING" else ""
    if payload.photo_url:
        jig.photo_url = payload.photo_url
    jig.last_inspector = payload.inspector
    jig.last_inspected_at = datetime.utcnow()
    
    db.commit()
    db.refresh(jig)
    return jig