from google.cloud import vision
from googletrans import Translator
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

def translate_text_free(text, target_language='en', source_language='hi'):
    """Translate text using free googletrans library"""
    translator = Translator()
    result = translator.translate(text, src=source_language, dest=target_language)
    return result.text

def process_with_free_translation(image_folder=".", output_file="translated_text.txt"):
    """Process multiple images, extract text and translate to English using free library"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(image_folder, ext)))
        image_files.extend(glob.glob(os.path.join(image_folder, ext.upper())))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for image_path in sorted(image_files):
            print(f"Processing: {os.path.basename(image_path)}")
            try:
                # Extract text
                hindi_text = extract_text_from_image(image_path)
                
                # Translate to English
                english_text = translate_text_free(hindi_text)
                
                # Write both versions
                f.write(f"\n{'='*60}\n")
                f.write(f"File: {os.path.basename(image_path)}\n")
                f.write(f"{'='*60}\n\n")
                
                f.write("ORIGINAL HINDI TEXT:\n")
                f.write("-" * 30 + "\n")
                f.write(hindi_text)
                f.write("\n\n")
                
                f.write("ENGLISH TRANSLATION:\n")
                f.write("-" * 30 + "\n")
                f.write(english_text)
                f.write("\n\n")
                
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                f.write(f"\nError processing {os.path.basename(image_path)}: {e}\n\n")
    
    print(f"Translated text saved to: {output_file}")

if __name__ == "__main__":
    process_with_free_translation()