from fastapi import Form
from database import Shift, session
from fastapi import APIRouter
from utils.date import set_time, time_to_string
from pydantic import BaseModel
from typing import Dict, Any

class ShiftConfig(BaseModel):
    shift1: Dict[str, str]
    shift2: Dict[str, str]

router = APIRouter()

@router.post("/shift", tags=["Shift"])
async def add_shift(
    name: str = Form(...),
    checkin: str = Form(...),
    checkout: str = Form(...)):
    new_shift = Shift(name=name, checkin=set_time(checkin), checkout=set_time(checkout))
    session.add(new_shift)
    session.commit()
    session.refresh(new_shift)
    return {"success": True, "shift_id": new_shift.id, "name":new_shift.name, "checkin":new_shift.checkin, "checkout":new_shift.checkout}

@router.delete("/shift", tags=["Shift"])
async def delete_shift():
    session.query(Shift).delete()
    session.commit()
    return session.query(Shift).all()

@router.get("/shift", tags=["shift"])
async def get_shifts():
    """lấy danh sách tất cả ca làm việc"""
    shifts = session.query(Shift).all()
    result = []
    for shift in shifts:
        result.append({
            "id": shift.id,
            "name":shift.name, 
            "checkin": time_to_string(shift.checkin),
            "checkout": time_to_string(shift.checkout),
        })
    return {"shifts": result}