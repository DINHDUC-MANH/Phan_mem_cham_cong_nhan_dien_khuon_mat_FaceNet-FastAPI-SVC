import os
import cv2
import joblib
import numpy as np
import random
import mediapipe as mp
import onnxruntime as ort
from tools import augmentate
from sklearn.svm import LinearSVC
from database import session, Embedding
from sklearn.calibration import CalibratedClassifierCV

model_dir = os.path.join(os.path.dirname(__file__), 'models')
rec_path = os.path.join(model_dir, 'quantized_model.onnx')
cls_path = os.path.join(model_dir, 'face_classifier.pkl')
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,  # False để sử dụng video (dynamic)
    max_num_faces=1,  # Số lượng khuôn mặt tối đa có thể phát hiện trong mỗi khung hình
    refine_landmarks=True,  # Lọc landmarks (điểm mốc) để có độ chính xác cao hơn
    min_detection_confidence=0.5,  # Mức độ tin cậy tối thiểu để phát hiện khuôn mặt
)

def load_model():
    #Kiểm tra sự tồn tại của các thư mục cần thiết
    if not os.path.exists('models'):
        os.makedirs('models')

    #Kiểm tra File ONNX
    rec_model = ort.InferenceSession(rec_path)
    print("Model ONNX sẵn sàng")

    #Kiểm tra File SVC
    if not os.path.exists(cls_path):
        cls_model = None
    else:
        cls_model = joblib.load(cls_path)
        print("Model SVC sẵn sàng")
    return rec_model, cls_model

rec_model, cls_model = load_model()
cls_ready = True
if cls_model == None:
    cls_ready = False

def detect_face(image):
    """
    Phát hiện khuôn mặt trong ảnh và trích xuất vùng mặt.
    - Tham số: ảnh gốc
    - Trả về: ảnh khuôn mặt đã cắt và tọa độ bounding box
    """
    global mp_face_mesh, face_mesh
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)
    if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
        face_landmarks = results.multi_face_landmarks[0].landmark
        
        # Lấy các điểm landmark của mắt trái và mắt phải
        left_eye = [face_landmarks[i] for i in range(33, 133)]  # Landmark của mắt trái (index có thể thay đổi)
        right_eye = [face_landmarks[i] for i in range(362, 463)]  # Landmark của mắt phải (index có thể thay đổi)
        
        # Kiểm tra xem cả hai mắt có được phát hiện không
        if left_eye and right_eye:
            img_h, img_w, _ = image.shape
            # Tính các điểm bounding box
            x_coords = [int(landmark.x * img_w) for landmark in face_landmarks]
            y_coords = [int(landmark.y * img_h) for landmark in face_landmarks]
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            bbox_width, bbox_height = x2 - x1, y2 - y1
            if min(bbox_width, bbox_height) < 70:
                return None, None
            
            bbox = np.array([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], dtype=np.int32)
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(img_w, x2), min(img_h, y2)
            return image[y1:y2, x1:x2], bbox

    return None, None

def train(saved_face, employee_id, N_SAMPLE=30):
    """
    Huấn luyện model với tập ảnh.
    - Tham số: danh sách ảnh và mã nhân viên
    - Kết quả: trả về huấn luyện thành công
    """
    global cls_model, cls_path, rec_model, cls_ready, labels
    cls_ready = True
    images = saved_face
    n = len(images)
    if n < N_SAMPLE:
        samples = random.choices(images, k=N_SAMPLE - n) 
        images.extend(samples)
    elif n > N_SAMPLE:
        images = random.sample(images, N_SAMPLE)
    session.query(Embedding).filter_by(employee_id=employee_id).delete()
    session.commit()
    embeddings, labels = [], []

    # 🔹 Load tất cả embeddings cũ từ database trước khi train
    data = session.query(Embedding).all()
    for item in data:
        embeddings.append(np.frombuffer(item.embedding, dtype=np.float32).tolist())
        labels.append(item.employee_id)
    
    # 🔹 Thêm embeddings mới vào
    count = 0
    instances = []
    for image in images:
        face = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face = cv2.resize(face, (160, 160))
        augmented_faces = augmentate(face)
        all_images = [face] + augmented_faces
        
        for img in all_images:
            count += 1
            img = img.astype('float32') / 255.0
            img = np.transpose(img, (2, 0, 1))
            img = np.expand_dims(img, axis=0)
            output = rec_model.run(None, {rec_model.get_inputs()[0].name: img})
            embedding = output[0][0].tobytes()

            instance = Embedding(embedding=embedding, employee_id=employee_id)
            instances.append(instance)

            embeddings.append(np.frombuffer(embedding, dtype=np.float32).tolist())
            labels.append(employee_id)
    
    session.add_all(instances)
    session.commit()
    previous_labels = len(set(labels))
    if previous_labels < 2:
        dummy_embedding = np.random.rand(len(embeddings[0])).tolist()
        embeddings.append(dummy_embedding)
        embeddings.append(dummy_embedding)
        labels.append("unknown")
        labels.append("unknown")
    cls_model = LinearSVC(random_state=42)
    cls_model = CalibratedClassifierCV(cls_model, cv=2)
    cls_model.fit(embeddings, labels)
    joblib.dump(cls_model, cls_path)
    del images, embeddings, labels
    return {'status': 'Thành công'}

def refresh_train(employee_id):
    global cls_model, cls_path, rec_model, cls_ready, labels
    cls_ready = True
    session.query(Embedding).filter_by(employee_id=employee_id).delete()
    session.commit()
    embeddings, labels = [], []

    # 🔹 Load tất cả embeddings cũ từ database trước khi train
    data = session.query(Embedding).all()
    for item in data:
        embeddings.append(np.frombuffer(item.embedding, dtype=np.float32).tolist())
        labels.append(item.employee_id)

    previous_labels = len(set(labels))
    if previous_labels < 2:
        dummy_embedding = np.random.rand(len(embeddings[0])).tolist()
        embeddings.append(dummy_embedding)
        embeddings.append(dummy_embedding)
        labels.append("unknown")
        labels.append("unknown")
    cls_model = LinearSVC(random_state=42)
    cls_model = CalibratedClassifierCV(cls_model, cv=2)
    cls_model.fit(embeddings, labels)
    joblib.dump(cls_model, cls_path)
    return {'status': 'Thành công'}

def predict(face, threshold=0.6):
    """
    Dự đoán danh tính khuôn mặt từ ảnh.
    - Đầu vào: ảnh khuôn mặt đã cắt
    - Trả về: employee_id đáp ứng ngưỡng
    """
    global cls_model, rec_model, cls_ready
    if not cls_ready: return ''

    # Tiền xử lí ảnh cho mô hình Facenet
    img = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (160, 160))
    img = img.astype('float32') / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    outputs = rec_model.run(None, {rec_model.get_inputs()[0].name: img})
    predicted_probs = cls_model.predict_proba(outputs[0])
    confidence = np.max(predicted_probs)
    predicted_index = np.argmax(predicted_probs, axis=1)[0]
    if confidence >= threshold:
        predicted_label = cls_model.classes_[predicted_index]
    else:
        predicted_label = ""
    return predicted_label
#capnhat