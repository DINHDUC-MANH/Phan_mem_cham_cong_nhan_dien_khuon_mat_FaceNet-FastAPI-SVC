from database import session, Employee, Attendance, Complaint
from fastapi import Form, Path, APIRouter
from ai import refresh_train

router = APIRouter()


@router.post("/employee", tags=["Employee"])
async def add_employee(name: str = Form(...),position: str = Form(...)):
    new_employee = Employee(name=name, position=position)
    session.add(new_employee)
    session.commit()
    session.refresh(new_employee)

    # Gọi hàm train AI
    employee_id = new_employee.id

    return {"employee_id": employee_id,}

@router.get("/employee", tags=["Employee"])
async def employees():
    employees = session.query(Employee).all()
    employee_list = [{"id": emp.id, "name": emp.name, "position": emp.position} for emp in employees]
    return {"employees": employee_list}

@router.get("/employee/{employee_id}", tags=["Employee"])
async def get_employee(employee_id: int):
    """Lấy thông tin một nhân viên theo ID"""
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return {"success": False, "message": "Không tìm thấy nhân viên"}
    
    return {
        "success": True,
        "id": employee.id,
        "name": employee.name,
        "position": employee.position
    }
    
