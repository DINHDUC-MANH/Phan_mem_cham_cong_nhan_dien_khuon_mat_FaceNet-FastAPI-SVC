from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, LargeBinary, Time, Date, Boolean, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from dotenv import load_dotenv
from utils.date import *
import os
from datetime import datetime

load_dotenv()


value = os.getenv('DB_PASSWORD') 
# engine = create_engine('sqlite:///database.db')  

# 🔹 Tạo BaseModel
Base = declarative_base()

# 🔹 BaseModel cho các bảng có cột `created_at`
class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime, default=get_accruate)

# 🔹 Bảng Employee (Nhân viên)
class Employee(BaseModel):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    attendances = relationship('Attendance', back_populates='employee', lazy=True)
    complaints = relationship('Complaint', back_populates='employee', lazy=True)
    
# 🔹 Bảng Attendance (Chấm công)
class Attendance(BaseModel):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, default=get_date)
    shift = Column(String, nullable=False)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=True) #
    checkin = Column(Time, default=get_time)
    checkout = Column(Time, nullable=True)
    checkin_status = Column(String, nullable=True) #
    checkout_status = Column(String, nullable=True) #
    employee = relationship('Employee', back_populates='attendances')
    shift_info = relationship('Shift', foreign_keys=[shift_id], lazy='joined') #

# 🔹 Bảng Complaint (Khiếu nại)
class Complaint(BaseModel):
    __tablename__ = 'complaints'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    reason = Column(String, nullable=False)
    processed = Column(Boolean, default=False)
    approved = Column(Boolean, default=False) #
    status = Column(String, nullable=True) #
    # image = Column(LargeBinary, nullable=False) 
    image_data = Column(LargeBinary, nullable=False) #
    image_path = Column(String, nullable=True) #
    employee = relationship('Employee', back_populates='complaints')

# 🔹 Định nghĩa Model
class Embedding(Base):
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True)
    employee_id = Column(String, nullable=False) 
    embedding = Column(LargeBinary, nullable=False)

class Shift(Base):
    __tablename__ = 'shifts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    checkin = Column(Time, default=set_time("07:00"))
    checkout = Column(Time, default=set_time("12:00"))

psw = os.getenv('DB_PASSWORD')
engine = create_engine(f"sqlite+pysqlcipher://:{psw}@/database.db")

def forward_password(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute(f"PRAGMA key='{psw}'")
    cursor.execute("PRAGMA cipher_compatibility = 3")
    cursor.close()

event.listen(engine, "connect", forward_password)

# 🔹 Tạo database nếu chưa tồn tại
Base.metadata.create_all(engine)

# 🔹 Khởi tạo session
Session = sessionmaker(bind=engine)
session = Session()