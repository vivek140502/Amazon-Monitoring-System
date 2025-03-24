from google.cloud import storage
import os

# Google Cloud Storage settings
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Initialize Storage Client
try:
    storage_client = storage.Client()  # Uses default credentials
    bucket = storage_client.bucket(BUCKET_NAME)
except Exception as e:
    print(f"Error initializing GCS client: {e}")
    bucket = None  # Avoids errors if credentials are missing

def upload_to_gcs(file, filename):
    """Uploads a file to Google Cloud Storage."""
    if not bucket:
        raise ValueError("GCS bucket not initialized. Check your credentials.")

    try:
        blob = bucket.blob(filename)
        blob.upload_from_filename(file)  # Use upload_from_filename for files
        return f"https://storage.googleapis.com/amazon-monitoring-assets/Master_Catalogue.xlsx"
    except Exception as e:
        print(f"Error uploading file to GCS: {e}")
        return None

def download_excel(filename):
    """Downloads an Excel file from Google Cloud Storage."""
    if not bucket:
        raise ValueError("GCS bucket not initialized. Check your credentials.")

    try:
        blob = bucket.blob(filename)
        local_path = f"/tmp/{filename}"
        blob.download_to_filename(local_path)
        return local_path
    except Exception as e:
        print(f"Error downloading file from GCS: {e}")
        return None
