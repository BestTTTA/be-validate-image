import sys
import os
import base64
from io import BytesIO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from utils.face_encoding_manager import load_face_encodings, search_face
from minio import Minio

# MinIO configuration
MINIO_ENDPOINT = "119.59.99.192:9000"
MINIO_ACCESS_KEY = "sut-skin"
MINIO_SECRET_KEY = "sut-skin-2024"
BUCKET_NAME = "where-my-images"

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def convert_image_to_base64(image_path):
    """Convert an image file to base64 string."""
    with Image.open(image_path) as img:
        # Convert to RGB if image is in RGBA mode
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

def check_face(input_image_path):
    input_image_path = os.path.abspath(input_image_path)
    print(f"🔍 กำลังค้นหาภาพที่ตรงกับ {input_image_path}...")
    
    matched_images = search_face(input_image_path)
    
    if matched_images == "NO_FACE_FOUND":
        print("❌ ไม่พบใบหน้าในภาพที่อัปโหลด")
        return "NO_FACE_FOUND"
    
    base64_images = []
    if matched_images:
        print("✅ พบภาพที่ตรงกัน:")
        for img_path in matched_images:
            print(f" - {img_path}")
            try:
                # Get the original filename (without _face_N suffix)
                original_filename = '_'.join(img_path.split('_')[:-2])  # Remove _face_N
                temp_file_path = f"temp_minio_{original_filename}"
                
                # Try to get the original image directly
                try:
                    print(f"Trying path: {original_filename}")
                    minio_client.fget_object(BUCKET_NAME, original_filename, temp_file_path)
                    base64_img = convert_image_to_base64(temp_file_path)
                    base64_images.append(base64_img)
                    print(f"✅ Successfully downloaded from path: {original_filename}")
                except Exception as e:
                    print(f"Failed to download image: {str(e)}")
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    continue

                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            except Exception as e:
                print(f"Error processing MinIO image: {e}")
    else:
        print("❌ ไม่พบภาพที่ตรงกันในฐานข้อมูล")
    
    return base64_images

if __name__ == "__main__":
    input_image = "1 (43).jpg"  
    check_face(input_image)