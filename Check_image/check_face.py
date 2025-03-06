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
BUCKET_NAME = "test-where-my-images"

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
    """Check if a face in the input image matches any faces in the database.
    
    Args:
        input_image_path (str): Path to the input image to check
        
    Returns:
        list or str: List of base64 encoded images, empty if no matches found,
                     'NO_FACE_FOUND' if no faces detected in input image
    """
    # Convert input path to absolute path if it's relative
    input_image_path = os.path.abspath(input_image_path)
    print(f"🔍 กำลังค้นหาภาพที่ตรงกับ {input_image_path}...")
    
    # Search for matching faces using pre-encoded data
    matched_images = search_face(input_image_path)
    
    # If no faces were detected in the input image
    if matched_images == "NO_FACE_FOUND":
        print("❌ ไม่พบใบหน้าในภาพที่อัปโหลด")
        return "NO_FACE_FOUND"
    
    # Convert matched images to base64
    base64_images = []
    if matched_images:
        print("✅ พบภาพที่ตรงกัน:")
        for img_path in matched_images:
            print(f" - {img_path}")
            try:
                # Create a temporary file to store the MinIO object
                temp_file_path = f"temp_minio_{os.path.basename(img_path)}"
                try:
                    # Download the image from MinIO
                    minio_client.fget_object(BUCKET_NAME, img_path, temp_file_path)
                    
                    # Convert the downloaded image to base64
                    base64_img = convert_image_to_base64(temp_file_path)
                    base64_images.append(base64_img)
                finally:
                    # Clean up the temporary file
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