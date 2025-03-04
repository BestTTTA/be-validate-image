import os
import pickle
import face_recognition
from PIL import Image
import numpy as np

ENCODINGS_DIR = "Encoded_Faces"
ENCODINGS_FILE = os.path.join(ENCODINGS_DIR, "face_encodings.pkl")
VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
FACE_SIMILARITY_THRESHOLD = 0.6  #ปรับค่าไกล้ 0.1 มีความแม่นมาก

def ensure_encodings_dir():
    if not os.path.exists(ENCODINGS_DIR):
        os.makedirs(ENCODINGS_DIR)
        print(f"✅ สร้างโฟลเดอร์สำหรับเก็บข้อมูลใบหน้า: {ENCODINGS_DIR}")

def save_face_encodings(face_encodings, image_paths):
    ensure_encodings_dir()
    data = {
        'face_encodings': face_encodings,
        'image_paths': image_paths
    }
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(data, f)
    print(f"✅ บันทึกข้อมูลใบหน้าสำเร็จ: {len(face_encodings)} ใบหน้า")

def load_face_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        print("❌ ไม่พบไฟล์ข้อมูลใบหน้าที่บันทึกไว้")
        return [], []
    
    with open(ENCODINGS_FILE, 'rb') as f:
        data = pickle.load(f)
    print(f"✅ โหลดข้อมูลใบหน้าสำเร็จ: {len(data['face_encodings'])} ใบหน้า")
    return data['face_encodings'], data['image_paths']

def encode_image_directory(image_dir):
    face_encodings = []
    image_paths = []
    # Convert image_dir to absolute path
    image_dir = os.path.abspath(image_dir)
    total_files = len([f for f in os.listdir(image_dir) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)])
    processed = 0
    success = 0
    failed = 0
    skipped = 0

    print(f"📊 พบไฟล์รูปภาพทั้งหมด: {total_files} ไฟล์")

    for file_name in os.listdir(image_dir):
        file_path = os.path.join(image_dir, file_name)

        if not file_name.lower().endswith(VALID_IMAGE_EXTENSIONS):
            print(f"❌ ข้ามไฟล์ที่ไม่ใช่รูปภาพ: {file_name}")
            skipped += 1
            continue

        try:
            processed += 1
            percent = (processed / total_files) * 100
            print(f"⏳ กำลังประมวลผล ({processed}/{total_files} - {percent:.1f}%): {file_name}")

            image = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:
                face_encodings.append(encodings[0])
                # Store absolute path
                image_paths.append(os.path.abspath(file_path))
                success += 1
                print(f"✅ โหลดสำเร็จ: {file_name}")
            else:
                print(f"⚠️ ไม่พบใบหน้าในภาพ: {file_name}")
                failed += 1

        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการโหลด {file_name}: {e}")
            failed += 1

    print(f"\n📊 สรุปผลการโหลด:")
    print(f"✅ สำเร็จ: {success} ไฟล์")
    print(f"❌ ล้มเหลว: {failed} ไฟล์")
    print(f"⏭️ ข้าม: {skipped} ไฟล์")

    return face_encodings, image_paths

def search_face(input_image_path, face_encodings=None, image_paths=None):
    if face_encodings is None or image_paths is None:
        face_encodings, image_paths = load_face_encodings()
        if not face_encodings:
            print("❌ ไม่พบข้อมูลใบหน้าที่บันทึกไว้")
            return []
    
    try:
        input_image = face_recognition.load_image_file(input_image_path)
        input_encodings = face_recognition.face_encodings(input_image)

        if not input_encodings:
            print("❌ ไม่พบใบหน้าในภาพที่อัปโหลด")
            return "NO_FACE_FOUND"

        input_encoding = input_encodings[0]
        matched_images = []
        distances = []

        # Calculate face distances and find matches
        for i, known_encoding in enumerate(face_encodings):
            distance = face_recognition.face_distance([known_encoding], input_encoding)[0]
            if distance <= FACE_SIMILARITY_THRESHOLD:
                matched_images.append(image_paths[i])
                distances.append(distance)

        # Sort matches by similarity (lower distance = more similar)
        if matched_images:
            matched_pairs = sorted(zip(matched_images, distances), key=lambda x: x[1])
            matched_images = [pair[0] for pair in matched_pairs[:7]]  

        return matched_images

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการค้นหาใบหน้า: {e}")
        return []