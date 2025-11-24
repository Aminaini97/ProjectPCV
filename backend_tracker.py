# Simpan sebagai: backend_tracker.py

import cv2
import mediapipe as mp
import json
from flask import Flask, jsonify, send_from_directory
import time

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
cap = cv2.VideoCapture(0) 

app = Flask(__name__, static_folder='frontend')

def get_pose_data():
    success, image = cap.read()
    if not success:
        return {}
    image = cv2.flip(image, 1) 
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = pose.process(image_rgb)
    image_rgb.flags.writeable = True

    landmarks_data = {}
    
    if results.pose_world_landmarks:
        for idx, landmark in enumerate(results.pose_world_landmarks.landmark):
            key = str(mp_pose.PoseLandmark(idx)).split('.')[-1]
            landmarks_data[key] = {
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z
            }
        
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(
            image_bgr,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS)
            
        cv2.imshow('MediaPipe Pose Tracking (ESC to exit)', image_bgr)
        
    
    if cv2.waitKey(5) & 0xFF == 27:
        return {"EXIT": True} 
    
    return landmarks_data

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/pose_api')
def pose_api():
    data = get_pose_data()
    return jsonify(data)

if __name__ == '__main__':
    print("Akses aplikasi di: http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000, debug=False)

cap.release()
cv2.destroyAllWindows()