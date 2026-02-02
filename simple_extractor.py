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

def process_with_translation_ready(image_folder=".", output_file="hindi_text_for_translation.txt"):
    """Process multiple images and prepare text for translation"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(image_folder, ext)))
        image_files.extend(glob.glob(os.path.join(image_folder, ext.upper())))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("EXTRACTED HINDI TEXT - READY FOR TRANSLATION\n")
        f.write("=" * 60 + "\n\n")
        f.write("Instructions:\n")
        f.write("1. Copy the Hindi text below\n")
        f.write("2. Paste into Google Translate (translate.google.com)\n")
        f.write("3. Set source: Hindi, target: English\n")
        f.write("4. Get instant translation\n\n")
        f.write("=" * 60 + "\n\n")
        
        for image_path in sorted(image_files):
            print(f"Processing: {os.path.basename(image_path)}")
            try:
                hindi_text = extract_text_from_image(image_path)
                
                f.write(f"FILE: {os.path.basename(image_path)}\n")
                f.write("-" * 40 + "\n")
                f.write(hindi_text)
                f.write("\n\n" + "=" * 60 + "\n\n")
                
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                f.write(f"Error processing {os.path.basename(image_path)}: {e}\n\n")
    
    print(f"Hindi text extracted to: {output_file}")
    print("Copy text from file and paste into Google Translate for English translation")

if __name__ == "__main__":
    process_with_translation_ready()