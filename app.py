from flask import Flask, render_template, Response, request, redirect, url_for, flash
import cv2
import face_recognition
import os
import numpy as np
import pandas as pd
from datetime import datetime
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Cấu hình Flask-Mail (điền email & mật khẩu của bạn)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tanbao2608@gmail.com'
app.config['MAIL_PASSWORD'] = 'ondq gpxj klbf lfqj'
    
mail = Mail(app)

# Folder chứa ảnh khuôn mặt đã biết
face_dir = 'faces'
supported_formats = ('.jpg', '.jpeg', '.png')

known_face_encodings = []
known_face_names = []

def load_faces():
    known_face_encodings.clear()
    known_face_names.clear()
    for filename in os.listdir(face_dir):
        if filename.lower().endswith(supported_formats):
            path = os.path.join(face_dir, filename)
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                known_face_encodings.append(encoding[0])
                known_face_names.append(os.path.splitext(filename)[0])


load_faces()

attendance_file = 'attendance.csv'
today_str = datetime.now().strftime('%Y-%m-%d')

# Tạo set chứa tên đã điểm danh hôm nay
marked_today = set()
if os.path.exists(attendance_file):
    try:
        df = pd.read_csv(attendance_file)
        if 'Date' in df.columns and 'Name' in df.columns:
            marked_today = set(df[df['Date'] == today_str]['Name'].tolist())
    except pd.errors.EmptyDataError:
        # File rỗng chưa có dữ liệu
        marked_today = set()

# Hàm ghi điểm danh và gửi email thông báo
def mark_attendance(name):
    if name in marked_today:
        return
    now = datetime.now()
    with open(attendance_file, 'a') as f:
        f.write(f"{name},{now.strftime('%Y-%m-%d')},{now.strftime('%H:%M:%S')}\n")
    marked_today.add(name)

    # Gửi email thông báo điểm danh thành công
    try:
        if os.path.exists('students.csv'):
            df_students = pd.read_csv('students.csv')
            email_row = df_students[df_students['Name'] == name]
            if not email_row.empty:
                email = email_row.iloc[0]['Email']
                msg = Message(
                    subject='Thông báo điểm danh thành công',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.body = f"Chào {name},\nBạn đã điểm danh thành công vào lúc {now.strftime('%H:%M:%S')} ngày {today_str}."
                
                #  Đây là cách sửa lỗi
                with app.app_context():
                    mail.send(msg)
    except Exception as e:
        print(f"Lỗi gửi email cho {name}: {e}")

# Biến global giữ camera
camera = None
tolerance = 0.45

@app.route('/')
def index():
    # Đọc dữ liệu điểm danh hôm nay để hiển thị
    records = []
    if os.path.exists(attendance_file):
        try:
            df = pd.read_csv(attendance_file)
            df_today = df[df['Date'] == today_str]
            records = df_today.values.tolist()
        except pd.errors.EmptyDataError:
            records = []
    return render_template('index.html', records=records)

@app.route('/start_camera')
def start_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return redirect(url_for('index'))

@app.route('/stop_camera')
def stop_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None
    return redirect(url_for('index'))

def gen_frames():
    global camera
    while camera is not None and camera.isOpened():
        success, frame = camera.read()
        if not success:
            break

        # Resize frame để tăng tốc xử lý
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(distances) == 0:
                continue
            best_index = np.argmin(distances)
            if distances[best_index] < tolerance:
                name = known_face_names[best_index]
                mark_attendance(name)
            else:
                name = "Unknown"

            # Vẽ hình chữ nhật và tên
            y1, x2, y2, x1 = [v * 2 for v in face_location]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame, name, (x1+6, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def history():
    query = request.args.get('q', '').strip().lower()
    history_records = []
    if os.path.exists(attendance_file):
        try:
            d= pd.read_csv(attendance_file)
            if query:
                df = df[df['Name'].str.lower().str.contains(query)]
            df.sort_values(by=['Date', 'Time'], ascending=[False, False], inplace=True)
            history_records = df.values.tolist()
        except pd.errors.EmptyDataError:
            history_records = []
    return render_template('history.html', records=history_records, search_query=query)


if __name__ == '__main__':
    app.run(debug=True)

