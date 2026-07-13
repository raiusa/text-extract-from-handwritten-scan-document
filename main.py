from flask import Flask, request, render_template_string, jsonify, send_from_directory
import os
import uuid
import io
from datetime import datetime
from google.cloud import vision
from google.cloud import translate_v2 as translate

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Local storage directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
EXTRACTED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted')
TRANSLATED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translated')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_locally(file_content, filename, folder):
    """Save file locally and return the download URL"""
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as f:
        f.write(file_content) if isinstance(file_content, bytes) else f.write(file_content.encode('utf-8'))
    # Return a local download route URL
    folder_name = os.path.basename(folder)
    return f'/download/{folder_name}/{filename}'

def extract_text_from_image(image_content):
    """Extract text from image using Google Vision API with position-based ordering"""
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_content)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'Vision API Error: {response.error.message}')
        
        if not response.full_text_annotation:
            return "No text found"
        
        # Extract words with their positions for proper ordering
        words_with_positions = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_confidence = word.confidence if word.confidence else 0
                        if word_confidence < 0.6:
                            continue
                        
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        
                        # Skip single characters (spiral hole noise)
                        if len(word_text.strip()) <= 1:
                            continue
                        
                        # Get the top-left Y and X position of the word
                        vertices = word.bounding_box.vertices
                        y_pos = vertices[0].y
                        x_pos = vertices[0].x
                        
                        words_with_positions.append((y_pos, x_pos, word_text))
        
        if not words_with_positions:
            return "No text found"
        
        # Group words into lines based on Y position (words within similar Y are on same line)
        words_with_positions.sort(key=lambda w: (w[0], w[1]))
        
        lines = []
        current_line = [words_with_positions[0]]
        line_threshold = 20  # pixels tolerance for same line
        
        for word in words_with_positions[1:]:
            # If Y position is close to current line, it's the same line
            if abs(word[0] - current_line[0][0]) < line_threshold:
                current_line.append(word)
            else:
                # Sort current line by X position (left to right)
                current_line.sort(key=lambda w: w[1])
                lines.append(' '.join([w[2] for w in current_line]))
                current_line = [word]
        
        # Don't forget the last line
        current_line.sort(key=lambda w: w[1])
        lines.append(' '.join([w[2] for w in current_line]))
        
        result = '\n'.join(lines)
        return result if result.strip() else "No text found"
    
    except Exception as e:
        raise Exception(f'Text extraction error: {str(e)}')

def translate_text(text, target_language='en'):
    """Translate text to target language using Google Translate API"""
    try:
        translate_client = translate.Client()
        
        # Detect source language
        detection = translate_client.detect_language(text)
        source_language = detection['language']
        
        # Skip translation if already in target language
        if source_language == target_language:
            return text, source_language, target_language
        
        # Translate text
        result = translate_client.translate(text, target_language=target_language)
        translated_text = result['translatedText']
        
        return translated_text, source_language, target_language
    
    except Exception as e:
        raise Exception(f'Translation error: {str(e)}')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Text Extractor - Google Vision API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: transparent;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            opacity: 1;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .header .feature-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 15px;
            font-size: 0.9em;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .content {
            padding: 40px;
        }
        .upload-section {
            background: #f8f9ff;
            border: 3px dashed #4facfe;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        .upload-section:hover {
            border-color: #00f2fe;
            background: #f0f4ff;
        }
        .file-input {
            display: none;
        }
        .file-label {
            display: inline-block;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1.1em;
            transition: transform 0.3s ease;
            margin: 20px 0;
        }
        .file-label:hover {
            transform: translateY(-2px);
        }
        .extract-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.3s ease;
            margin-top: 20px;
        }
        .extract-btn:hover {
            transform: translateY(-2px);
        }
        .extract-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .result-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .result-text {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        .download-links {
            margin-top: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .download-btn {
            background: #28a745;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        .download-btn:hover {
            background: #218838;
        }
        .new-upload {
            background: #6c757d;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        .new-upload:hover {
            background: #5a6268;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            background: #f8f9ff;
            border: 3px solid #4facfe;
            border-radius: 15px;
        }
        .loading h3 {
            color: #4facfe;
            margin-bottom: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4facfe;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Text Extractor</h1>
            <div class="feature-badge">✍️ Handwritten Text Recognition Enabled</div>
        </div>
        
        <div class="content">
            {% if not result %}
            <form action="/extract" method="post" enctype="multipart/form-data" id="uploadForm">
                <div class="upload-section">
                    <h3>📸 Upload Your Image</h3>
                    <p>Supports: PNG, JPG, JPEG, GIF, BMP, TIFF (Max 16MB)</p>
                    <p style="margin-top: 10px; color: #667eea; font-weight: 600;">✍️ Handwritten text extraction supported!</p>
                    
                    <input type="file" name="file" accept="image/*" required class="file-input" id="fileInput">
                    <label for="fileInput" class="file-label">Choose Image File</label>
                    
                    <div id="fileName" style="margin-top: 15px; font-weight: bold;"></div>
                    
                    <div style="margin: 20px 0;">
                        <label style="display: flex; align-items: center; justify-content: center; gap: 10px;">
                            <input type="checkbox" name="translate" value="true" id="translateCheck">
                            <span>🌐 Translate to English (if text is in another language)</span>
                        </label>
                    </div>
                    
                    <button type="submit" class="extract-btn" id="extractBtn" disabled>
                        🔍 Extract Text
                    </button>
                </div>
            </form>
            
            <div class="loading" id="loading">
                <h3>⏳ Processing Your Image</h3>
                <div class="spinner"></div>
                <p><strong>Please wait...</strong></p>
                <p>Extracting text with Google Vision AI</p>
                <p style="margin-top: 10px; font-size: 0.9em; color: #666;">This may take a few seconds</p>
            </div>
            {% endif %}
            
            {% if result %}
            <div class="result-section">
                <div class="result-header">
                    <h3>📝 Extracted Text</h3>
                    <small>{{ timestamp }}</small>
                </div>
                
                {% if result.startswith('Error:') %}
                <div class="error">
                    {{ result }}
                </div>
                {% else %}
                <div class="success">
                    ✅ Text extraction completed successfully!
                    {% if translation_info %}
                    <br>🌐 Translated from {{ translation_info.source }} to {{ translation_info.target }}
                    {% endif %}
                </div>
                
                {% if original_text and translated_text %}
                <div style="margin: 20px 0;">
                    <h4>📜 Original Text ({{ translation_info.source_name }}):</h4>
                    <div class="result-text">{{ original_text }}</div>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>🌐 Translated Text (English):</h4>
                    <div class="result-text">{{ translated_text }}</div>
                </div>
                {% else %}
                <div class="result-text">{{ result }}</div>
                {% endif %}
                
                <!-- Always show download links if they exist -->
                {% if download_links %}
                <div class="download-links">
                    {% if download_links.image %}
                    <a href="{{ download_links.image }}" class="download-btn" download>
                        📷 Download Original Image
                    </a>
                    {% endif %}
                    {% if download_links.original_text %}
                    <a href="{{ download_links.original_text }}" class="download-btn" download>
                        📄 Download Extracted Text
                    </a>
                    {% endif %}
                    {% if download_links.translated_text %}
                    <a href="{{ download_links.translated_text }}" class="download-btn" download>
                        🌐 Download Translated Text
                    </a>
                    {% endif %}
                </div>
                {% endif %}
                {% endif %}
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="/" class="new-upload">🔄 Extract from New Image</a>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const extractBtn = document.getElementById('extractBtn');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                fileName.textContent = '📁 ' + e.target.files[0].name;
                extractBtn.disabled = false;
            }
        });
        
        if (uploadForm) {
            uploadForm.addEventListener('submit', function(e) {
                // Disable submit button to prevent double submission
                extractBtn.disabled = true;
                extractBtn.textContent = '⏳ Processing...';
                
                // Show loading, hide form
                uploadForm.style.display = 'none';
                loading.style.display = 'block';
                
                // Keep the page visible during server processing
                document.body.style.opacity = '1';
                
                // Form will submit normally after this
            });
        }
        
        // Prevent blank page on navigation
        window.addEventListener('beforeunload', function() {
            document.body.style.opacity = '1';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract_text():
    try:
        file = request.files['file']
        translate_option = request.form.get('translate') == 'true'
        
        if not file or not allowed_file(file.filename):
            return render_template_string(HTML_TEMPLATE, 
                result='Error: Invalid file type. Please upload an image file.',
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        text_filename = unique_filename.rsplit('.', 1)[0]
        
        # Read file content
        file_content = file.read()
        
        # Save image locally
        image_url = save_file_locally(file_content, unique_filename, UPLOAD_FOLDER)
        
        # Extract text
        extracted_text = extract_text_from_image(file_content)
        
        if extracted_text == "No text found":
            return render_template_string(HTML_TEMPLATE, 
                result=extracted_text,
                download_links={'image': image_url},
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Save original extracted text locally
        original_text_url = save_file_locally(extracted_text, f"{text_filename}_original.txt", EXTRACTED_FOLDER)
        
        download_links = {
            'image': image_url,
            'original_text': original_text_url
        }
        
        # Handle translation if requested
        if translate_option:
            try:
                translated_text, source_lang, target_lang = translate_text(extracted_text)
                
                # Language code to name mapping
                lang_names = {
                    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
                    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
                    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
                    'th': 'Thai', 'vi': 'Vietnamese', 'tr': 'Turkish', 'pl': 'Polish'
                }
                
                source_name = lang_names.get(source_lang, source_lang.upper())
                
                if source_lang != target_lang:
                    # Save translated text locally
                    translated_text_url = save_file_locally(translated_text, f"{text_filename}_translated.txt", TRANSLATED_FOLDER)
                    download_links['translated_text'] = translated_text_url
                    
                    translation_info = {
                        'source': source_lang.upper(),
                        'target': target_lang.upper(),
                        'source_name': source_name
                    }
                    
                    return render_template_string(HTML_TEMPLATE,
                        result="Translation completed",  # Add this so template logic works
                        original_text=extracted_text,
                        translated_text=translated_text,
                        translation_info=translation_info,
                        download_links=download_links,
                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    return render_template_string(HTML_TEMPLATE, 
                        result=f"{extracted_text}\n\n🌐 Text is already in English - no translation needed.",
                        download_links=download_links,
                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        
            except Exception as e:
                return render_template_string(HTML_TEMPLATE, 
                    result=f"{extracted_text}\n\n⚠️ Translation failed: {str(e)}",
                    download_links=download_links,
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            # No translation requested
            return render_template_string(HTML_TEMPLATE, 
                result=extracted_text,
                download_links=download_links,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, 
            result=f'Error: {str(e)}',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    """Serve files for download"""
    folder_map = {
        'uploads': UPLOAD_FOLDER,
        'extracted': EXTRACTED_FOLDER,
        'translated': TRANSLATED_FOLDER,
    }
    directory = folder_map.get(folder)
    if not directory:
        return 'Not found', 404
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)