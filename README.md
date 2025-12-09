# Laporan Project: Body Tracker 3D VTuber

## Pendahuluan

Project ini adalah implementasi sistem body tracker 3D yang menggunakan teknologi WebSocket untuk komunikasi real-time antara server Python dan klien web Three.js. Sistem ini memungkinkan tracking pose tubuh manusia melalui kamera dan memetakannya ke model 3D avatar dalam lingkungan web.

## Arsitektur Sistem

### Komponen Utama

1. **Server Python (pose_ws_server.py)**
   - Menggunakan MediaPipe untuk deteksi pose tubuh
   - OpenCV untuk pemrosesan video kamera
   - WebSocket server untuk komunikasi real-time
   - Mengirim data pose dalam format JSON

2. **Klien Web (index.html + main.js)**
   - Three.js untuk rendering 3D
   - WebSocket client untuk menerima data pose
   - GLTF loader untuk model 3D avatar
   - Sistem bone mapping untuk animasi avatar

### Alur Kerja Sistem

```
Kamera → MediaPipe Pose Detection → Data Pose → WebSocket → Three.js → Avatar 3D
```

## Implementasi Teknis

### Server Side (Python)

#### Dependencies
- `opencv-python`: Pemrosesan video dan kamera
- `mediapipe`: Deteksi pose tubuh
- `websockets`: Komunikasi WebSocket
- `numpy`: Operasi matematika

#### Fitur Utama
- Deteksi pose tubuh real-time menggunakan MediaPipe
- Tracking 33 landmark pose (tangan, kaki, tubuh, wajah)
- Komputasi sudut sendi untuk animasi
- WebSocket server pada port 8765
- Mirroring frame kamera untuk pengalaman natural

#### Struktur Data Pose
```json
{
  "type": "pose",
  "payload": {
    "timestamp": 1234567890.123,
    "root_position": {"x": 0.5, "y": 0.5},
    "hip": {"angle": 0.0},
    "left_shoulder": {"angle": 0.0},
    "right_shoulder": {"angle": 0.0},
    "left_hand": {"angle": 0.0},
    "right_hand": {"angle": 0.0},
    "head": {"pos": [0.5, 0.5], "angle": 0.0},
    "left_upper_arm": {"angle": 0.0},
    "left_lower_arm": {"angle": 0.0},
    "right_upper_arm": {"angle": 0.0},
    "right_lower_arm": {"angle": 0.0},
    "left_upper_leg": {"angle": 0.0},
    "left_lower_leg": {"angle": 0.0},
    "right_upper_leg": {"angle": 0.0},
    "right_lower_leg": {"angle": 0.0}
  }
}
```

### Client Side (JavaScript)

#### Dependencies
- `three.js`: Engine 3D
- `GLTFLoader`: Loader model 3D

#### Fitur Utama
- Rendering real-time 3D menggunakan WebGL
- Sistem bone mapping untuk model avatar
- Animasi smooth dengan quaternion interpolation
- Background color changing berdasarkan deteksi warna
- Responsive design untuk berbagai ukuran layar

#### Bone Mapping System
```javascript
const boneMap = {
    "hip": "CC_Base_Waist_033",
    "left_shoulder": "CC_Base_L_Clavicle_049",
    "right_shoulder": "CC_Base_R_Clavicle_077",
    "left_hand": "CC_Base_L_Hand_055",
    "left_upper_arm": "CC_Base_L_Upperarm_050",
    "left_lower_arm": "CC_Base_L_Forearm_051",
    "right_hand": "CC_Base_R_Hand_083",
    "right_upper_arm": "CC_Base_R_Upperarm_078",
    "right_lower_arm": "CC_Base_R_Forearm_079",
    "left_upper_leg": "CC_Base_L_Thigh_04",
    "left_lower_leg": "CC_Base_L_Calf_05",
    "right_upper_leg": "CC_Base_R_Thigh_018",
    "right_lower_leg": "CC_Base_R_Calf_019",
    "head": "CC_Base_Head_038"
};
```

## Fitur Khusus

### 1. Real-time Pose Tracking
- Deteksi pose dengan akurasi tinggi menggunakan MediaPipe
- Tracking 33 landmark tubuh
- Komputasi sudut sendi untuk animasi natural

### 2. 3D Avatar Animation
- Mapping pose ke bone structure avatar
- Smooth interpolation menggunakan quaternion
- Support untuk model GLTF/GLB

### 3. Background Color System
- Deteksi warna objek (Merah, Biru, Hijau, Kuning)
- Transisi halus background berdasarkan warna terdeteksi
- Integrasi dengan WebSocket data

### 4. Position Tracking
- Tracking posisi root body
- Movement mapping ke posisi avatar
- Smooth lerping untuk gerakan natural

## Cara Menjalankan

### Persiapan Environment
```bash
pip install opencv-python mediapipe websockets numpy
```

### Menjalankan Server
```bash
python pose_ws_server.py
```

### Mengakses Web Client
Buka `index.html` di browser web modern yang mendukung WebGL.

## Performa dan Optimisasi

### Optimisasi Server
- Pose detection pada frame asli untuk akurasi maksimal
- Asynchronous WebSocket handling
- Efficient data serialization dengan JSON

### Optimisasi Client
- Quaternion interpolation untuk smooth animation
- Linear interpolation untuk position tracking
- Efficient bone caching system

## Kesimpulan

Project body tracker 3D VTuber ini berhasil mengimplementasikan sistem tracking pose real-time yang dapat memetakan gerakan tubuh manusia ke avatar 3D. Dengan menggunakan teknologi MediaPipe dan Three.js, sistem ini mampu memberikan pengalaman interaktif yang smooth dan responsif.

### Pencapaian Utama
- ✅ Real-time pose tracking dengan akurasi tinggi
- ✅ Smooth 3D avatar animation
- ✅ WebSocket communication yang stabil
- ✅ Cross-platform compatibility
- ✅ Modular architecture untuk ekstensi future

### Potensi Pengembangan
- Integrasi dengan VR/AR
- Multiple avatar support
- Gesture recognition
- Voice integration
- Mobile device support

## Referensi

- MediaPipe Pose: https://google.github.io/mediapipe/solutions/pose.html
- Three.js: https://threejs.org/
- WebSocket Protocol: https://tools.ietf.org/html/rfc6455
