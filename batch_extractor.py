from google.cloud import vision
import io
import os
import glob

def extract_text_from_image(image_path):
    """Extract text from handwritten image using Google Vision API"""
    client = vision.ImageAnnotatorClient()
    
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(f'{response.error.message}')
    
    if response.full_text_annotation:
        return response.full_text_annotation.text
    else:
        return "No text found in image"

def process_multiple_images(image_folder=".", output_file="extracted_text.txt"):
    """Process multiple images and save text to file"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(image_folder, ext)))
        image_files.extend(glob.glob(os.path.join(image_folder, ext.upper())))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for image_path in sorted(image_files):
            print(f"Processing: {os.path.basename(image_path)}")
            try:
                text = extract_text_from_image(image_path)
                f.write(f"\n{'='*50}\n")
                f.write(f"File: {os.path.basename(image_path)}\n")
                f.write(f"{'='*50}\n")
                f.write(text)
                f.write("\n")
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                f.write(f"\nError processing {os.path.basename(image_path)}: {e}\n")
    
    print(f"Text extracted to: {output_file}")

if __name__ == "__main__":
    # Process all images in current directory
    process_multiple_images()