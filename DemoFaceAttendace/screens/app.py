import sys, cv2
from PyQt6.QtWidgets import *
from screens.attendance import Attendance
from screens.register import Register
from screens.reset import Reset
from screens.history import History
from database.schema import init_db

# Thiết lập thông số cài đặt dự án, có thể sửa thoải mái
WIDTH, HEIGHT = 1280, 720                               # Độ phân giải
MAX_CAPTURES = 5                                        # Số embedding nhận để đăng ký mặt
FPS = 30                                                # FPS camera
RATIO = 0.8                                             # Tỷ lệ nhãn hợp lệ trong 1 lần kiểm tra mặt
THRESHOLD = 0.5                                         # Ngưỡng chấm điểm
TIME_CONSUMING = 3                                      # Thời gian duy trì kiểm tra mặt
COOLDOWN_SECONDS = 2                                    # Thời gian camera nghỉ sau khi đăng ký
EMB_PATH = "embeddings/embeddings.npz"                  # Nơi lưu trữ các bộ (embedding, label)

# Nếu camera bị đen, đổi lại là: cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)


class MainApp(QWidget):
    """Class chính điều khiển menu và chuyển màn hình"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phần mềm chấm công khuôn mặt")
        
        # Khởi tạo các màn hình với đầy đủ tham số
        self.attendance_screen = Attendance(cap, FPS, WIDTH, HEIGHT, EMB_PATH, THRESHOLD, RATIO, TIME_CONSUMING, COOLDOWN_SECONDS)
        self.register_screen = Register(cap, FPS, WIDTH, HEIGHT, EMB_PATH, MAX_CAPTURES)
        self.clear_screen = Reset(EMB_PATH)
        self.history_screen = History()
        
        self.init_ui()
        
        # Mặc định hiển thị màn hình chấm công
        self.show_screen(self.attendance_screen)
    
    def init_ui(self):
        """Khởi tạo giao diện chính"""
        self.main_layout = QVBoxLayout()
        
        # Container để chứa các màn hình
        self.screen_container = QStackedWidget()
        self.screen_container.addWidget(self.attendance_screen)
        self.screen_container.addWidget(self.register_screen)
        self.screen_container.addWidget(self.clear_screen)
        self.screen_container.addWidget(self.history_screen)
        self.main_layout.addWidget(self.screen_container)
        
        # Menu buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        buttons_data = [
            {"text": "Chấm công", "callback": lambda: self.show_screen(self.attendance_screen)},
            {"text": "Đăng ký khuôn mặt", "callback": lambda: self.show_screen(self.register_screen)},
            {"text": "Xóa dữ liệu", "callback": lambda: self.show_screen(self.clear_screen)},
            {"text": "Kho dữ liệu", "callback": lambda: self.show_screen(self.history_screen)},
        ]
        
        for btn_data in buttons_data:
            btn = QPushButton(btn_data["text"])
            btn.clicked.connect(btn_data["callback"])
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(150)
            button_layout.addWidget(btn)
        
        button_layout.addStretch()
        self.main_layout.addLayout(button_layout)
        
        self.setLayout(self.main_layout)
    
    def show_screen(self, screen):
        """Chuyển đổi màn hình"""
        # Dừng timer của màn hình hiện tại
        current_widget = self.screen_container.currentWidget()
        if current_widget:
            current_widget.stop()
        
        # Chuyển sang màn hình mới
        self.screen_container.setCurrentWidget(screen)
        screen.start()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())