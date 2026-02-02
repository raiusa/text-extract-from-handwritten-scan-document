import os
from google.cloud import vision

def test_credentials():
    """Test if Google Cloud credentials are properly set up"""
    try:
        # Check if credentials environment variable is set
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path:
            print(f"✓ GOOGLE_APPLICATION_CREDENTIALS set to: {creds_path}")
            if os.path.exists(creds_path):
                print("✓ Credentials file exists")
            else:
                print("✗ Credentials file not found")
                return False
        else:
            print("✗ GOOGLE_APPLICATION_CREDENTIALS not set")
            return False
        
        # Try to create client
        client = vision.ImageAnnotatorClient()
        print("✓ Vision API client created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    if test_credentials():
        print("\n✓ Authentication setup is correct!")
    else:
        print("\n✗ Please set up authentication:")
        print("export GOOGLE_APPLICATION_CREDENTIALS='path/to/your/service-account-key.json'")