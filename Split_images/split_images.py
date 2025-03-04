import os
import random
import shutil

# Define source and destination directories
SOURCE_DIR = "../Humans"
DEST_DIR = "Selected_Images"
NUM_IMAGES = 1000

# Create destination directory if it doesn't exist
if not os.path.exists(DEST_DIR):
    os.makedirs(DEST_DIR)
    print(f"✅ Created destination directory: {DEST_DIR}")

# Get list of all image files
image_files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'))]

# Randomly select images
if len(image_files) < NUM_IMAGES:
    print(f"⚠️ Warning: Only {len(image_files)} images available in source directory")
    selected_images = image_files
else:
    selected_images = random.sample(image_files, NUM_IMAGES)

# Copy selected images to destination directory
for image in selected_images:
    source_path = os.path.join(SOURCE_DIR, image)
    dest_path = os.path.join(DEST_DIR, image)
    
    try:
        shutil.copy2(source_path, dest_path)
        print(f"✅ Copied: {image}")
    except Exception as e:
        print(f"❌ Error copying {image}: {e}")

print(f"\n✨ Process completed! {len(selected_images)} images copied to {DEST_DIR}")