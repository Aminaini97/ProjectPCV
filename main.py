#mendekati benar

import cv2
import mediapipe as mp
import open3d as o3d
import time

# ==== PATH MODEL 3D ====
model_path = r"D:\body-tracker-project\frontend\model.glb"

# ==== LOAD MODEL GLB ====
print("[INFO] Loading model...")
# gunakan read_triangle_model agar dapat menampung meshes + material
try:
    model = o3d.io.read_triangle_model(model_path)
    meshes = [m for name, m in model.meshes.items()]
except Exception:
    # fallback ke read_triangle_mesh
    m = o3d.io.read_triangle_mesh(model_path)
    meshes = [m] if not m.is_empty() else []

# Debug info: tampilkan status mesh/texture
print("[DEBUG] loaded meshes:", len(meshes))
for i, m in enumerate(meshes):
    try:
        has_vc = m.has_vertex_colors()
    except Exception:
        has_vc = False
    tuv = len(m.triangle_uvs) if hasattr(m, "triangle_uvs") else "N/A"
    print(f"[DEBUG] mesh {i}: has_vertex_colors={has_vc}, triangle_uvs={tuv}")

for m in meshes:
    m.compute_vertex_normals()
    # jangan paint_uniform_color — biarkan warna/texture asli
    # m.paint_uniform_color([0.2, 0.6, 1.0])  # <-- hapus ini

# Hapus initialization/quit O3DVisualizer yang dapat memicu masalah di thread ini.
# Jika butuh tampilan material penuh, gunakan trimesh atau jalankan O3DVisualizer sebagai app terpisah.
# ==== SETUP VIEWER (kembali ke Visualizer untuk update realtime) ====
vis = o3d.visualization.Visualizer()
vis.create_window(window_name='3D Body Tracker', width=960, height=720)
for m in meshes:
    vis.add_geometry(m)
view_ctl = vis.get_view_control()
view_ctl.set_zoom(0.8)
vis.update_renderer()

# ==== SETUP MEDIAPIPE ====
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
print("[INFO] Camera started. Move your shoulders to test tracking...")

# ==== INISIAL POSISI MODEL ==== (ganti x_offset menjadi offsets untuk xyz + yaw)
x_offset = 0.0
y_offset = 0.0
z_offset = 0.0
yaw_offset = 0.0

try:
    while True:
        success, frame = cap.read()
        if not success:
            print("Kamera tidak terbaca.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # Ambil pergerakan X bahu kiri dan kanan
            # Mapping gerakan bahu ke transformasi model
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2.0
            shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2.0
            shoulder_dist = abs(right_shoulder.x - left_shoulder.x)  # makin besar = lebih dekat (rough)

            # map ke world coords (adjust scale sesuai kebutuhan)
            move_x = (shoulder_center_x - 0.5) * 2.0   # -1 .. +1
            move_y = (0.5 - shoulder_center_y) * 2.0   # atas/ bawah (invert Y)
            move_z = (0.25 - shoulder_dist) * 4.0      # coba ubah konstanta agar terasa baik

            # rotasi sederhana berdasarkan kemiringan bahu (roll) atau beda Y bahu
            shoulder_angle = (right_shoulder.y - left_shoulder.y)  # kecil -> radians approx after scale
            yaw = shoulder_angle * 2.0

            # terapkan perubahan relatif
            dx = move_x - x_offset
            dy = move_y - y_offset
            dz = move_z - z_offset
            dyaw = yaw - yaw_offset

            # terapkan translasi
            for m in meshes:
                m.translate((dx, dy, dz), relative=True)
                R = m.get_rotation_matrix_from_xyz((0.0, dyaw, 0.0))
                m.rotate(R, center=m.get_center())

            x_offset = move_x
            y_offset = move_y
            z_offset = move_z
            yaw_offset = yaw

            # Debug mapping values
            print(f"[DEBUG] move_x={move_x:.3f} move_y={move_y:.3f} move_z={move_z:.3f} yaw={yaw:.3f}")

            # update setiap mesh eksplisit
            for m in meshes:
                vis.update_geometry(m)
            vis.poll_events()
            vis.update_renderer()

        # ==== TAMPILKAN KAMERA ====
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow("Pose Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC untuk keluar
            break

        time.sleep(0.02)  # biar smooth, hindari flicker

except KeyboardInterrupt:
    print("Berhenti manual.")

cap.release()
cv2.destroyAllWindows()
vis.destroy_window()
