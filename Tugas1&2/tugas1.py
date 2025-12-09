# server_tugas1.py
# FOKUS: Smoothing & Blurring (Sesuai Request Keyboard Control Kamu)

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
filter_mode = '0' # Default Normal

# --- SETUP MEDIAPIPE ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# --- FUNGSI BANTUAN LOGIKA ---
def to_pixel(lm, w, h): return (lm.x * w, lm.y * h)
def angle_between(p1, p2):
    dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))
def dist(p1, p2): return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

# --- LOGIKA FILTER (Disesuaikan dengan Kontrol Kamu) ---
def apply_filters(frame, mode):
    # Mode 1: Average Blur Kecil (5x5) - Sesuai syarat tugas poin 1 
    if mode == '1': 
        return cv2.blur(frame, (5, 5)) 
    
    # Mode 2: Average Blur Besar (9x9) - Sesuai syarat tugas poin 1 
    elif mode == '2':
        return cv2.blur(frame, (9, 9)) 
    
    # Mode 3: Gaussian Blur (Manual Kernel) - Sesuai syarat tugas poin 2 [cite: 35]
    elif mode == '3':
        # Kernel 1D
        gaussian_kernel_1d = cv2.getGaussianKernel(5, 1.5)
        # Kernel 2D (Outer Product)
        gaussian_kernel_2d = np.outer(gaussian_kernel_1d, gaussian_kernel_1d.transpose())
        return cv2.filter2D(frame, -1, gaussian_kernel_2d)
    
    # Mode 4: Sharpening - Sesuai syarat tugas poin 3 [cite: 36]
    elif mode == '4':
        sharpen_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        return cv2.filter2D(frame, -1, sharpen_kernel)
    
    # Mode 0: Normal
    return frame

def compute_pose_data(landmarks, width, height):
    lm = landmarks
    def norm(lm_item): return [lm_item.x, lm_item.y]

    # Mapping Tulang
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

    # Hitung Titik Tengah
    mid_sh = ((pix["left_sh"][0] + pix["right_sh"][0]) / 2, (pix["left_sh"][1] + pix["right_sh"][1]) / 2)
    mid_hip = ((pix["left_hip"][0] + pix["right_hip"][0]) / 2, (pix["left_hip"][1] + pix["right_hip"][1]) / 2)

    data = {
        "timestamp": time.time(),
        "root_position": { "x": (lm[23].x + lm[24].x) / 2, "y": (lm[23].y + lm[24].y) / 2 },
        "hip": { "angle": angle_between(mid_hip, mid_sh) },
        "left_shoulder": { "angle": angle_between(mid_sh, pix["left_sh"]) },
        "right_shoulder": { "angle": angle_between(mid_sh, pix["right_sh"]) },
        "left_hand": { "angle": angle_between(pix["left_wr"], pix["left_index"]) },
        "right_hand": { "angle": angle_between(pix["right_wr"], pix["right_index"]) },
        "head": { "pos": list(pix["nose"]), "angle": angle_between(pix["left_sh"], pix["right_sh"]) },
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

# --- WEBSOCKET & MAIN LOOP ---
clients = set()
async def ws_handler(websocket):
    clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    except:
        pass
    finally:
        clients.remove(websocket)

async def broadcast_pose_loop():
    global filter_mode
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, raw_frame = cap.read()
            if not ret: await asyncio.sleep(0.5); continue

            # Mirroring
            frame = cv2.flip(raw_frame, 1)
            h, w, _ = frame.shape
            
            # --- PROSES FILTER (TUGAS 1) ---
            display_frame = apply_filters(frame, filter_mode)

            # Proses Tracking (Pakai frame asli agar akurasi tetap tinggi)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    display_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

                pose_data = compute_pose_data(results.pose_landmarks.landmark, w, h)
                msg = json.dumps({"type": "pose", "payload": pose_data})
                if clients: await asyncio.gather(*(c.send(msg) for c in clients))

            # UI Text (Menampilkan mode yang aktif)
            mode_text = "Normal"
            if filter_mode == '1': mode_text = "Average Blur 5x5"
            elif filter_mode == '2': mode_text = "Average Blur 9x9"
            elif filter_mode == '3': mode_text = "Gaussian Blur"
            elif filter_mode == '4': mode_text = "Sharpening"

            cv2.putText(display_frame, f"Mode: {mode_text} (Tekan 0-4)", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Tugas 1: Filtering", display_frame)
            
            # --- KEYBOARD CONTROL SESUAI REQUEST ---
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'): break # ESC atau q untuk keluar
            elif key == ord('0'): filter_mode = '0' # Normal
            elif key == ord('1'): filter_mode = '1' # Avg 5x5
            elif key == ord('2'): filter_mode = '2' # Avg 9x9
            elif key == ord('3'): filter_mode = '3' # Gaussian
            elif key == ord('4'): filter_mode = '4' # Sharpen

            await asyncio.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()

async def main():
    print("Server Tugas 1 Running...")
    print("Controls:")
    print(" 0: Normal")
    print(" 1: Average Blur 5x5")
    print(" 2: Average Blur 9x9")
    print(" 3: Gaussian Blur")
    print(" 4: Sharpening")
    print(" q: Quit")
    async with websockets.serve(ws_handler, "0.0.0.0", PORT):
        await broadcast_pose_loop()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass