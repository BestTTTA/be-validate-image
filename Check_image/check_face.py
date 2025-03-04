import sys
import os
import base64
from io import BytesIO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from utils.face_encoding_manager import load_face_encodings, search_face

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
            # Ensure img_path is absolute and points to the correct location
            img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Selected_Images", os.path.basename(img_path))
            print(f" - {img_path}")
            try:
                base64_img = convert_image_to_base64(img_path)
                base64_images.append(base64_img)
            except Exception as e:
                print(f"Error converting image to base64: {e}")
    else:
        print("❌ ไม่พบภาพที่ตรงกันในฐานข้อมูล")
    
    return base64_images

if __name__ == "__main__":
    input_image = "1 (43).jpg"  
    check_face(input_image)