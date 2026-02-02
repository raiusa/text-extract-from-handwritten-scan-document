from google.cloud import vision
import io
import os
import sys

def extract_text_from_image(image_path, credentials_path=None):
    """Extract text from handwritten image using Google Vision API"""
    
    # Set credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
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

if __name__ == "__main__":
    image_path = "history1.jpg"
    
    # Check if credentials are set
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Please provide your service account key file path:")
        creds_path = input("Path to JSON key file: ").strip()
        if creds_path and os.path.exists(creds_path):
            extracted_text = extract_text_from_image(image_path, creds_path)
        else:
            print("Invalid credentials file path")
            sys.exit(1)
    else:
        extracted_text = extract_text_from_image(image_path)
    
    print("Extracted Text:")
    print("-" * 50)
    print(extracted_text)