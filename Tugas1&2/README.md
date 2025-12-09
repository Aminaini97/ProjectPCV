Tugas 1 & 2:

Implementasi smoothing, blurring, dan deteksi warna HSV pada project body tracker yang sudah ada, menggunakan MediaPipe untuk tracking pose tubuh dan OpenCV untuk pemrosesan video. Kedua file berjalan sebagai server WebSocket yang mengirim data pose ke klien.

## Tugas 1: Smoothing & Blurring

Tugas ini fokus pada penerapan filter smoothing dan blurring pada feed kamera dengan kontrol keyboard.

### Fitur:
- Tracking pose tubuh menggunakan MediaPipe
- Penerapan filter real-time:
  - Mode 0: Normal (tanpa filter)
  - Mode 1: Average Blur 5x5
  - Mode 2: Average Blur 9x9
  - Mode 3: Gaussian Blur (kernel manual)
  - Mode 4: Sharpening
- Kontrol via keyboard (tekan 0-4 untuk ganti mode)
- Kirim data pose via WebSocket ke port 8765

### Cara Menjalankan:
1. Pastikan dependencies terinstall: `pip install opencv-python mediapipe websockets numpy`
2. Jalankan: `python tugas1.py`
3. Tekan ESC atau 'q' untuk keluar

## Tugas 2: Deteksi Multi Warna HSV + Trigger Background

Tugas ini fokus pada deteksi objek berwarna menggunakan ruang warna HSV dan integrasi dengan tracking pose.

### Fitur:
- Deteksi warna: Biru, Merah, Hijau, Kuning
- Tracking pose tubuh menggunakan MediaPipe
- Kirim data pose + warna terdeteksi via WebSocket ke port 8765
- Siap untuk integrasi dengan Three.js

### Cara Menjalankan:
1. Pastikan dependencies terinstall: `pip install opencv-python mediapipe websockets numpy`
2. Jalankan: `python tugas2.py`
3. Tekan ESC untuk keluar

## Dependencies:
- Python 3.x
- OpenCV (cv2)
- MediaPipe
- WebSockets
- NumPy

## Struktur Data WebSocket:
Server mengirim JSON dengan format:
```json
{
  "type": "pose",
  "payload": {
    "timestamp": 1234567890.123,
    "detected_color": "BIRU", // hanya di tugas 2
    "root_position": {"x": 0.5, "y": 0.5},
    "hip": {"angle": 0.0},
    // ... data pose lainnya
  }
}
```

## Catatan:
- Kedua server menggunakan kamera indeks 0 secara default
- Frame kamera di-mirror untuk pengalaman yang lebih natural
- Pose tracking diproses pada frame asli untuk akurasi tinggi
