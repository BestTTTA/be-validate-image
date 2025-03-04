from PIL import Image
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.face_encoding_manager import encode_image_directory, save_face_encodings, search_face

IMAGE_DATABASE_DIR = "../Selected_Images"

# Encode and save face data
print("📥 กำลังโหลดและบันทึกข้อมูลใบหน้า...")
face_encodings, image_paths = encode_image_directory(IMAGE_DATABASE_DIR)
save_face_encodings(face_encodings, image_paths)

# ทดสอบอัปโหลดภาพเพื่อค้นหา
input_image_path = "1 (1).jpeg"  
print(f"🔍 กำลังค้นหาภาพที่ตรงกับ {input_image_path}...")

matched_images = search_face(input_image_path)

# แสดงผลลัพธ์
if matched_images:
    print("✅ พบภาพที่ตรงกัน:")
    for img in matched_images:
        print(f" - {img}")
        image = Image.open(img)
        image.show()
else:
    print("❌ ไม่พบภาพที่ตรงกันในฐานข้อมูล")