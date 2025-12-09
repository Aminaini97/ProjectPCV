# server_tugas2.py
# FOKUS: Deteksi Multi Warna HSV + Trigger Background (Three.js Ready)

import asyncio
import json
import math
import time
import cv2
import mediapipe as mp
import numpy as np
import websockets

# --- KONFIGURASI ---
CAMERA_INDEX = 0
PORT = 8765

# --- KONFIGURASI MULTI WARNA HSV ---
COLOR_RANGES = {
    "BIRU":   (np.array([100, 150, 50]), np.array([140, 255, 255])),
    "MERAH":  (np.array([0, 150, 50]),   np.array([10, 255, 255])),
    "HIJAU":  (np.array([40, 70, 50]),    np.array([80, 255, 255])),
    "KUNING": (np.array([20, 100, 100]),  np.array([35, 255, 255]))
}

# --- SETUP MEDIAPIPE ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# --- LOGIKA DETEKSI MULTI WARNA ---
def detect_color_object(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    display_frame = frame.copy()

    detected_color = "NONE"

    for color_name, (lower, upper) in COLOR_RANGES.items():
        mask = cv2.inRange(hsv, lower, upper)

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, f"{color_name} DETECTED", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                detected_color = color_name
                return display_frame, detected_color

    return display_frame, detected_color


# --- FUNGSI TRACKING POSE ---
def to_pixel(lm, w, h): 
    return (lm.x * w, lm.y * h)

def angle_between(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))

def dist(p1, p2): 
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def compute_pose_data(landmarks, width, height, detected_color):
    lm = landmarks
    def norm(lm_item): return [lm_item.x, lm_item.y]

    pairs = {
        "left_sh": mp_pose.PoseLandmark.LEFT_SHOULDER,
        "right_sh": mp_pose.PoseLandmark.RIGHT_SHOULDER,
        "left_el": mp_pose.PoseLandmark.LEFT_ELBOW,
        "right_el": mp_pose.PoseLandmark.RIGHT_ELBOW,
        "left_wr": mp_pose.PoseLandmark.LEFT_WRIST,
        "right_wr": mp_pose.PoseLandmark.RIGHT_WRIST,
        "left_index": mp_pose.PoseLandmark.LEFT_INDEX,
        "right_index": mp_pose.PoseLandmark.RIGHT_INDEX,
        "left_hip": mp_pose.PoseLandmark.LEFT_HIP,
        "right_hip": mp_pose.PoseLandmark.RIGHT_HIP,
        "left_knee": mp_pose.PoseLandmark.LEFT_KNEE,
        "right_knee": mp_pose.PoseLandmark.RIGHT_KNEE,
        "left_ank": mp_pose.PoseLandmark.LEFT_ANKLE,
        "right_ank": mp_pose.PoseLandmark.RIGHT_ANKLE,
        "nose": mp_pose.PoseLandmark.NOSE
    }

    pix = {name: to_pixel(lm[idx], width, height) for name, idx in pairs.items()}
    norm_pos = {f"{name}_pos": norm(lm[idx]) for name, idx in pairs.items()}

    mid_sh = ((pix["left_sh"][0] + pix["right_sh"][0]) / 2,
              (pix["left_sh"][1] + pix["right_sh"][1]) / 2)

    mid_hip = ((pix["left_hip"][0] + pix["right_hip"][0]) / 2,
               (pix["left_hip"][1] + pix["right_hip"][1]) / 2)

    data = {
        "timestamp": time.time(),

        # --- DATA WARNA UNTUK THREE.JS ---
        "detected_color": detected_color,

        "root_position": { 
            "x": (lm[23].x + lm[24].x) / 2, 
            "y": (lm[23].y + lm[24].y) / 2 
        },

        "hip": { "angle": angle_between(mid_hip, mid_sh) },
        "left_shoulder": { "angle": angle_between(mid_sh, pix["left_sh"]) },
        "right_shoulder": { "angle": angle_between(mid_sh, pix["right_sh"]) },
        "left_hand": { "angle": angle_between(pix["left_wr"], pix["left_index"]) },
        "right_hand": { "angle": angle_between(pix["right_wr"], pix["right_index"]) },
        "head": { 
            "pos": list(pix["nose"]), 
            "angle": angle_between(pix["left_sh"], pix["right_sh"]) 
        },

        "left_upper_arm": { "angle": angle_between(pix["left_sh"], pix["left_el"]) },
        "left_lower_arm": { "angle": angle_between(pix["left_el"], pix["left_wr"]) },
        "right_upper_arm": { "angle": angle_between(pix["right_sh"], pix["right_el"]) },
        "right_lower_arm": { "angle": angle_between(pix["right_el"], pix["right_wr"]) },
        "left_upper_leg": { "angle": angle_between(pix["left_hip"], pix["left_knee"]) },
        "left_lower_leg": { "angle": angle_between(pix["left_knee"], pix["left_ank"]) },
        "right_upper_leg": { "angle": angle_between(pix["right_hip"], pix["right_knee"]) },
        "right_lower_leg": { "angle": angle_between(pix["right_knee"], pix["right_ank"]) }
    }

    data.update(norm_pos)
    return data


# --- WEBSOCKET ---
clients = set()

async def ws_handler(websocket):
    clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        clients.remove(websocket)


# --- MAIN LOOP ---
async def broadcast_pose_loop():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        while True:
            ret, raw_frame = cap.read()
            if not ret:
                await asyncio.sleep(0.5)
                continue

            frame = cv2.flip(raw_frame, 1)
            h, w, _ = frame.shape

            # --- DETEKSI WARNA ---
            display_frame, detected_color = detect_color_object(frame)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    display_frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )

                pose_data = compute_pose_data(
                    results.pose_landmarks.landmark,
                    w, h,
                    detected_color
                )

                msg = json.dumps({
                    "type": "pose",
                    "payload": pose_data
                })

                if clients:
                    await asyncio.gather(*(c.send(msg) for c in clients))

            cv2.imshow("Multi Color Detection (HSV)", display_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

            await asyncio.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()


async def main():
    print("Server Multi Color + Pose Tracking Running...")
    async with websockets.serve(ws_handler, "0.0.0.0", PORT):
        await broadcast_pose_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
