# Google Vision API Text Extraction

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud authentication:
   - Create a Google Cloud project
   - Enable Vision API
   - Create service account and download JSON key
   - Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/Users/p2269263/Documents/Personal/projects/vision-api-key.json"
```

## Usage

**Single image:**
```python
from text_extractor import extract_text_from_image

text = extract_text_from_image("your_handwritten_image.jpg")
print(text)
```

**Multiple images:**
```python
from text_extractor import process_multiple_images

# Process all images in current directory
process_multiple_images()

# Process images in specific folder
process_multiple_images("path/to/images", "output.txt")
```

**Command line:**
```bash
python3 text_extractor.py
```