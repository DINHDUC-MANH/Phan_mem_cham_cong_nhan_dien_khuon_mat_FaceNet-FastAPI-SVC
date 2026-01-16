from fastapi import File, Form, UploadFile
from database import Complaint, session, Employee, Attendance
from fastapi import APIRouter
from tools import checkin
from camera import generate_complaint_camera
from pydantic import BaseModel
from typing import Optional
import base64
import time

class ComplaintProcessRequest(BaseModel):
    complaint_id: int
    action: str  # 'approve' hoặc 'reject'
    employee_id: Optional[int] = None
    complaint_date: Optional[str] = None
    complaint_time: Optional[str] = None


router = APIRouter()

# @router.get("/complaint_image", tags=["Complaint"])
# async def get_complaint_image():
#     return {"image": generate_complaint_camera()}

@router.get("/complaint_image", tags=["Complaint"])
async def get_complaint_image(path: str = None):
    """Lấy ảnh khiếu nại hoặc tạo ảnh mới từ camera nếu không có path"""
    try:
        if not path:
            # Không có path, tạo ảnh mới từ camera
            return {"image": generate_complaint_camera()}
        
        # Có path, lấy ảnh từ database
        complaint = session.query(Complaint).filter(Complaint.image_path == path).first()
        if not complaint:
            return {"success": False, "message": "Không tìm thấy ảnh"}
            
        # Trả về ảnh dạng base64
        image_base64 = base64.b64encode(complaint.image_data).decode('utf-8')
        return {"success": True, "image": image_base64}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi lấy ảnh: {str(e)}"}
