from google.cloud import vision
import io

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

# Usage example
if __name__ == "__main__":
    image_path = "history1.jpg"  # Replace with your image path
    extracted_text = extract_text_from_image(image_path)
    print(extracted_text)