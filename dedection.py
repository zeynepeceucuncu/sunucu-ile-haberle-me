import sys
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import time
import cv2
import numpy as np
from collections import deque, defaultdict
import argparse

##sıtl veri alma
import asyncio
import json
from pymavlink import mavutil
import math
import httpx
import datetime
import threading

"""# Gazebo import (opsiyonel)
GAZEBO_AVAILABLE = False
try:
    from gz.transport13 import Node
    from gz.msgs10.image_pb2 import Image
    GAZEBO_AVAILABLE = True
except ImportError:
    pass"""

# Kamera Topic Adresi
CAMERA_TOPIC = "/world/runway/model/uav1/model/mini_talon_vtail_camera/link/base_link/sensor/camera/image"

# HSV Renk Aralıkları
# Kırmızı (HSV'de kırmızı 0 ve 180 civarında olduğu için iki aralık)
RED_LOWER1 = np.array([0, 120, 70])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([170, 120, 70])
RED_UPPER2 = np.array([180, 255, 255])

# Mavi
BLUE_LOWER = np.array([100, 150, 70])
BLUE_UPPER = np.array([130, 255, 255])

# Tespit parametreleri
DETECTION_THRESHOLD = 8  # Ardışık frame sayısı
MIN_CONTOUR_AREA = 500   # Minimum kontur alanı (piksel)
MAX_CONTOUR_AREA = 50000 # Maximum kontur alanı

# Tespit geçmişi: {(renk, şekil): sayaç}
detection_history = defaultdict(lambda: deque(maxlen=DETECTION_THRESHOLD))
confirmed_targets = {}  # {id: (renk, şekil, bbox, son_görülme)}

def take_data_from_iha(altitude_baundary,latitude_baundary,longtitude_boundary):

    print("mavlink bağlantısı kuruluyor")
    master=mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("mavlink bağlantısı  kuruldu")
    vehicle_state = {
        "lat": 0, "lon": 0, "alt": 0,
        "vx": 0, "vy": 0, "vz": 0,
        "pitch": 0, "roll": 0, "yaw": 0,
        "battery": 0, "mode": 0, "time_usec": 0
    }
    
    with httpx.Client() as client:
        while True:
            try:
                msg=master.recv_match(blocking=False)
                print("msg değerlerine erişildi")
                
                if msg:
                    print("veriler alındı")
                    msg_type = msg.get_type()
                    if msg_type == 'GLOBAL_POSITION_INT':
                        vehicle_state["lat"] = msg.lat / 1e7
                        vehicle_state["lon"] = msg.lon / 1e7
                        vehicle_state["alt"] = msg.alt / 1000.0
                        vehicle_state["vx"] = msg.vx
                        vehicle_state["vy"] = msg.vy
                        vehicle_state["vz"] = msg.vz
                        
                    elif msg_type == 'ATTITUDE':
                        vehicle_state["pitch"] = msg.pitch
                        vehicle_state["roll"] = msg.roll
                        vehicle_state["yaw"] = msg.yaw
                        
                    elif msg_type == 'BATTERY_STATUS':
                        vehicle_state["battery"] = msg.battery_remaining
                        
                    elif msg_type == 'HEARTBEAT':
                        vehicle_state["mode"] = msg.custom_mode
                        
                    elif msg_type == 'GPS_RAW_INT':
                        vehicle_state["time_usec"] = msg.time_usec

                    telemetry_data={
                        "type":"telemetry",
                        "takim_numarasi":12345,
                        "iha_enlem":vehicle_state["lat"],
                        "iha_boylam":vehicle_state["lon"],
                        "iha_irtifa":vehicle_state["alt"],
                        "iha_dikilme":vehicle_state["pitch"],
                        "iha_yonelme":vehicle_state["roll"],
                        "iha_yatis":vehicle_state["yaw"],
                        "iha_hiz":math.sqrt((vehicle_state["vx"]*vehicle_state["vx"])+(vehicle_state["vy"]*vehicle_state["vy"])+(vehicle_state["vz"]*vehicle_state["vz"])),
                        "iha_batarya":vehicle_state["battery"],
                        "iha_otonom":vehicle_state["mode"],
                        "gps_saati":vehicle_state["time_usec"]

                    }
                    count_of_crossing_the_altitude_border=0
                    count_of_crossing_the_longtitude_border=0
                    count_of_crossing_the_latitude_border=0
                    if telemetry_data["iha_enlem"]>latitude_baundary:
                        count_of_crossing_the_latitude_border+=1
                    elif telemetry_data["iha_boylam"] > longtitude_boundary:
                        count_of_crossing_the_longtitude_border+=1
                    elif telemetry_data["iha_irtifa"] < altitude_baundary:    
                        count_of_crossing_the_altitude_border+=1
                    
                    print(f"[SITL] Lat: {vehicle_state["lat"]}, Lon: {vehicle_state["lon"]}, Alt: {vehicle_state["alt"]}")

            except Exception as e:
                print(f"Telemetri Hatası: {e}")
                time.sleep(1)

def is_square(contour, epsilon_factor=0.03):
    """Konturun kare olup olmadığını kontrol et"""
    # Kontur çevresini hesapla
    perimeter = cv2.arcLength(contour, True)
    # Poligon yaklaşımı (daha hassas)
    approx = cv2.approxPolyDP(contour, epsilon_factor * perimeter, True)
    
    # Kare: tam 4 köşe olmalı
    if len(approx) != 4:
        return False, None
    
    # Konveks olmalı
    if not cv2.isContourConvex(approx):
        return False, None
    
    # Bounding box kontrolü - En-boy oranı
    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = float(w) / h
    
    # Daha katı en-boy oranı (0.75-1.33 arası)
    if not (0.75 <= aspect_ratio <= 1.33):
        return False, None
    
    # Kenar uzunluklarını hesapla
    def distance(p1, p2):
        return np.sqrt((p1[0][0] - p2[0][0])**2 + (p1[0][1] - p2[0][1])**2)
    
    sides = []
    for i in range(4):
        side_length = distance(approx[i], approx[(i + 1) % 4])
        sides.append(side_length)
    
    # Kenar uzunluklarının standart sapması (kenarlar benzer uzunlukta olmalı)
    sides_array = np.array(sides)
    mean_side = np.mean(sides_array)
    std_side = np.std(sides_array)
    
    # Standart sapma ortalamaya göre %25'ten az olmalı (kenarlar birbirine yakın)
    if std_side > mean_side * 0.25:
        return False, None
    
    # Açı kontrolü - köşe açıları 90 dereceye yakın olmalı
    def angle_between_vectors(v1, v2):
        """İki vektör arasındaki açıyı derece cinsinden döndür"""
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Numerik hata düzeltmesi
        angle = np.arccos(cos_angle)
        return np.degrees(angle)
    
    angles = []
    for i in range(4):
        p1 = approx[i][0]
        p2 = approx[(i + 1) % 4][0]
        p3 = approx[(i + 2) % 4][0]
        
        # İki vektör oluştur
        v1 = p1 - p2
        v2 = p3 - p2
        
        angle = angle_between_vectors(v1, v2)
        angles.append(angle)
    
    # 1. Her açı 85-95 derece arasında olmalı (daha dar tolerans)
    for angle in angles:
        if not (85 <= angle <= 95):
            return False, None
    
    # 2. Açıların ortalaması 90 dereceye yakın olmalı (88-92 arası)
    angles_array = np.array(angles)
    mean_angle = np.mean(angles_array)
    if not (88 <= mean_angle <= 92):
        return False, None
    
    # 3. Açıların standart sapması düşük olmalı (açılar birbirine yakın)
    std_angle = np.std(angles_array)
    if std_angle > 5.0:  # Açılar arasında max 5 derece fark
        return False, None
    
    return True, approx

def detect_shapes(frame):
    """Frame'de kırmızı ve mavi kareleri tespit et"""
    # HSV'ye çevir
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Blur uygula (gürültüyü azalt)
    hsv = cv2.GaussianBlur(hsv, (5, 5), 0)
    
    detections = []
    
    # Kırmızı maskeler (iki aralık)
    mask_red1 = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1)
    mask_red2 = cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Mavi maske
    mask_blue = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    
    # Morfolojik işlemler (gürültü temizleme)
    kernel = np.ones((5, 5), np.uint8)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
    
    # Her renk için kontur bul ve analiz et
    for mask, color_name, color_bgr in [
        (mask_red, "RED", (0, 0, 255)),
        (mask_blue, "BLUE", (255, 0, 0))
    ]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Alan kontrolü
            if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
                # Kare kontrolü
                is_sq, approx = is_square(contour)
                
                if is_sq:
                    # Merkez nokta
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                    else:
                        cx, cy = 0, 0
                    
                    # Bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    detections.append({
                        'color': color_name,
                        'shape': 'SQUARE',
                        'center': (cx, cy),
                        'bbox': (x, y, w, h),
                        'contour': contour,
                        'approx': approx,
                        'area': area,
                        'color_bgr': color_bgr
                    })
    
    return detections

def update_tracking(detections):
    """Tespit geçmişini güncelle ve onaylanmış hedefleri döndür"""
    current_time = time.time()
    
    # Renk+Şekil bazında grupla (grid yok!)
    detection_groups = defaultdict(list)
    
    for det in detections:
        color = det['color']
        shape = det['shape']
        key = (color, shape)
        detection_groups[key].append(det)
    
    # Her renk+şekil kombinasyonu için işle
    for key, dets in detection_groups.items():
        color, shape = key
        
        # Eğer birden fazla tespit varsa, en büyük alanı olanı seç
        if len(dets) > 1:
            best_det = max(dets, key=lambda d: d['area'])
        else:
            best_det = dets[0]
        
        # Geçmişe ekle
        detection_history[key].append(current_time)
        
        # Ardışık tespit kontrolü
        if len(detection_history[key]) >= DETECTION_THRESHOLD:
            # Son N frame'de hep görüldü mü kontrol et
            time_window = current_time - 2.0  # 2 saniye pencere
            recent_detections = [t for t in detection_history[key] if t >= time_window]
            
            if len(recent_detections) >= DETECTION_THRESHOLD:
                # Onaylanmış hedef - her renk+şekil için TEK ID
                target_id = f"{color}_{shape}"
                confirmed_targets[target_id] = {
                    'color': color,
                    'shape': shape,
                    'bbox': best_det['bbox'],
                    'center': best_det['center'],
                    'last_seen': current_time,
                    'color_bgr': best_det['color_bgr']
                }
    
    # Mevcut frame'de görülmeyen renk+şekil kombinasyonları için
    current_keys = set(detection_groups.keys())
    
    # Confirmed targets'ı güncelle
    to_remove = []
    for target_id, target in list(confirmed_targets.items()):
        target_key = (target['color'], target['shape'])
        
        # Eğer bu frame'de görüldüyse, zaten güncellendi
        # Eğer görülmediyse, timeout kontrolü yap
        if target_key not in current_keys:
            if current_time - target['last_seen'] > 1.0:  # 1 saniye görülmezse sil
                to_remove.append(target_id)
    
    for target_id in to_remove:
        del confirmed_targets[target_id]
    
    # Geçmişi temizle
    for key in list(detection_history.keys()):
        if key not in current_keys:
            if len(detection_history[key]) > 0:
                if current_time - detection_history[key][-1] > 2.0:
                    del detection_history[key]

def draw_detections(frame, detections):
    """Tespitleri frame üzerine çiz"""
    # Önce tüm tespitleri ince çizgilerle göster (onaylanmamış)
    for det in detections:
        x, y, w, h = det['bbox']
        cv2.rectangle(frame, (x, y), (x + w, y + h), (128, 128, 128), 1)
    
    # Onaylanmış hedefleri kalın çizgi ve etiketle göster
    for target_id, target in confirmed_targets.items():
        x, y, w, h = target['bbox']
        color_bgr = target['color_bgr']
        
        # Kalın bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 3)
        
        # Etiket
        label = f"{target['color']} {target['shape']}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        # Etiket arka planı
        cv2.rectangle(frame, (x, y - label_size[1] - 10), 
                     (x + label_size[0], y), color_bgr, -1)
        
        # Etiket metni
        cv2.putText(frame, label, (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Merkez noktası
        cv2.circle(frame, target['center'], 5, color_bgr, -1)
    
    # İstatistik bilgisi
    info_text = f"Confirmed Targets: {len(confirmed_targets)}"
    cv2.putText(frame, info_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

def process_stream(data_packet):
    try:
        w = data_packet.width
        h = data_packet.height
        raw_bytes = np.frombuffer(data_packet.data, dtype=np.uint8)
        total_size = len(data_packet.data)

        current_frame = None

        if total_size == w * h * 3:
            # RGB -> BGR
            current_frame = cv2.cvtColor(raw_bytes.reshape((h, w, 3)), cv2.COLOR_RGB2BGR)
        elif total_size == w * h * 4:
            # RGBA -> BGR
            current_frame = cv2.cvtColor(raw_bytes.reshape((h, w, 4)), cv2.COLOR_RGBA2BGR)
        elif total_size == w * h:
            # Grayscale -> BGR
            current_frame = cv2.cvtColor(raw_bytes.reshape((h, w)), cv2.COLOR_GRAY2BGR)
        else:
            return

        # Görüntü işleme pipeline
        detections = detect_shapes(current_frame)
        update_tracking(detections)
        draw_detections(current_frame, detections)

        # Ekrana bas
        cv2.imshow("UAV Feed - Target Detection", current_frame)
        cv2.waitKey(1)

    except Exception as e:
        pass

def process_webcam_frame(frame):
    """Webcam frame'ini işle"""
    try:
        # Görüntü işleme pipeline
        detections = detect_shapes(frame)
        update_tracking(detections)
        draw_detections(frame, detections)
        
        return frame
    except Exception as e:
        print(f"Frame işleme hatası: {e}")
        return frame

def start_webcam(camera_id=0):
    """Webcam modunda çalış"""
    print(f"Webcam başlatılıyor (ID: {camera_id})...")
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print("Webcam açılamadı!")
        return
    
    print("Webcam başlatıldı. Çıkmak için 'q' tuşuna basın.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame okunamadı!")
                break
            
            # Frame'i işle
            processed_frame = process_webcam_frame(frame)
            
            # Ekrana göster
            cv2.imshow("Webcam - Target Detection", processed_frame)
            
            # 'q' tuşu ile çık
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\nDurduruldu.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

"""def start_gazebo():
    #Gazebo modunda çalış
    if not GAZEBO_AVAILABLE:
        print("Gazebo transport kütüphanesi bulunamadı!")
        print("Lütfen gz.transport13 yükleyin veya webcam modunu kullanın.")
        return
    
    print("Gazebo kamera topic'ine bağlanılıyor...")
    gz_handler = Node()
    gz_handler.subscribe(Image, CAMERA_TOPIC, process_stream)
    
    print(f"Bağlantı başarılı: {CAMERA_TOPIC}")
    print("Çıkmak için Ctrl+C tuşlarına basın.")
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDurduruldu.")
        cv2.destroyAllWindows()"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hedef tespit sistemi - Webcam veya Gazebo')
    parser.add_argument('--mode', type=str, default='gazebo', choices=['webcam', 'gazebo'],
                       help='Kamera modu: webcam veya gazebo (varsayılan: gazebo)')
    parser.add_argument('--camera-id', type=int, default=0,
                       help='Webcam ID (varsayılan: 0)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  HEDEF TESPİT SİSTEMİ - Kırmızı ve Mavi Kare Tespiti")
    print("=" * 60)
    print(f"Mod: {args.mode.upper()}")
    print(f"Tespit Eşiği: {DETECTION_THRESHOLD} ardışık frame")
    print(f"Min Alan: {MIN_CONTOUR_AREA}, Max Alan: {MAX_CONTOUR_AREA} piksel")
    print("=" * 60)
    print()

    telemetry_thread = threading.Thread(target=take_data_from_iha, args=(20, 50, 70))
    telemetry_thread.daemon = True 
    telemetry_thread.start()
    
    #if args.mode == 'webcam':
    start_webcam(args.camera_id)
    #else:
       # start_gazebo()
