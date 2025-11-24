# pose_ws_server.py (FINAL COMPLETE VERSION)
import asyncio
import json
import math
import time
import cv2
import mediapipe as mp
import numpy as np
import websockets

# -------------------------------------------------------
# Mediapipe setup
# -------------------------------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# -------------------------------------------------------
# Helper functions
# -------------------------------------------------------
def to_pixel(lm, w, h):
    return (lm.x * w, lm.y * h)

def angle_between(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))

def dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def compute_pose_data(landmarks, width, height):
    lm = landmarks

    def norm(lm_item):
        return [lm_item.x, lm_item.y]

    # Key joints
    pairs = {
        "left_sh": mp_pose.PoseLandmark.LEFT_SHOULDER,
        "right_sh": mp_pose.PoseLandmark.RIGHT_SHOULDER,
        "left_el": mp_pose.PoseLandmark.LEFT_ELBOW,
        "right_el": mp_pose.PoseLandmark.RIGHT_ELBOW,
        "left_wr": mp_pose.PoseLandmark.LEFT_WRIST,
        "right_wr": mp_pose.PoseLandmark.RIGHT_WRIST,
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

    data = {
        "timestamp": time.time(),
        "head": {
            "pos": list(pix["nose"]),
            "pos_norm": norm(lm[pairs["nose"]]),
            "angle": angle_between(pix["left_sh"], pix["right_sh"])
        },

        "left_upper_arm": {
            "angle": angle_between(pix["left_sh"], pix["left_el"]),
            "length": dist(pix["left_sh"], pix["left_el"])
        },
        "left_lower_arm": {
            "angle": angle_between(pix["left_el"], pix["left_wr"]),
            "length": dist(pix["left_el"], pix["left_wr"])
        },

        "right_upper_arm": {
            "angle": angle_between(pix["right_sh"], pix["right_el"]),
            "length": dist(pix["right_sh"], pix["right_el"])
        },
        "right_lower_arm": {
            "angle": angle_between(pix["right_el"], pix["right_wr"]),
            "length": dist(pix["right_el"], pix["right_wr"])
        },

        "left_upper_leg": {
            "angle": angle_between(pix["left_hip"], pix["left_knee"]),
            "length": dist(pix["left_hip"], pix["left_knee"])
        },
        "left_lower_leg": {
            "angle": angle_between(pix["left_knee"], pix["left_ank"]),
            "length": dist(pix["left_knee"], pix["left_ank"])
        },

        "right_upper_leg": {
            "angle": angle_between(pix["right_hip"], pix["right_knee"]),
            "length": dist(pix["right_hip"], pix["right_knee"])
        },
        "right_lower_leg": {
            "angle": angle_between(pix["right_knee"], pix["right_ank"]),
            "length": dist(pix["right_knee"], pix["right_ank"])
        }
    }

    # Add normalized joint positions
    data.update(norm_pos)
    return data


# -------------------------------------------------------
# WebSocket server
# -------------------------------------------------------
clients = set()

async def ws_handler(websocket):
    print("Client connected")
    clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        print("Client disconnected")


# -------------------------------------------------------
# Pose loop + camera window
# -------------------------------------------------------
async def broadcast_pose_loop(cap_index=0):
    cap = cv2.VideoCapture(cap_index)
    print(f"[SERVER] Opening camera index {cap_index} -> isOpened={cap.isOpened()}")

    with mp_pose.Pose(
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[SERVER] frame read failed")
                await asyncio.sleep(0.5)
                continue

            frame = cv2.flip(frame, 1)

            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            # Draw the pose landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )

                # Compute pose data
                pose_data = compute_pose_data(results.pose_landmarks.landmark, w, h)
                msg = json.dumps({"type": "pose", "payload": pose_data})

                if clients:
                    await asyncio.gather(*(c.send(msg) for c in clients))

            # Show camera window
            cv2.imshow("MediaPipe Pose Feed", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC exit
                break

            await asyncio.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()


# -------------------------------------------------------
# Main entry
# -------------------------------------------------------
async def main():
    print("Starting WebSocket server...")
    await websockets.serve(ws_handler, "0.0.0.0", 8765)
    print("WebSocket server running at ws://0.0.0.0:8765")
    await broadcast_pose_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")
