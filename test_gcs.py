import os
from google.cloud import storage

# Check if credentials are set
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    print("Error: GOOGLE_APPLICATION_CREDENTIALS is not set!")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS is set to:", os.environ["GOOGLE_APPLICATION_CREDENTIALS"])

# Try to connect to GCS
try:
    client = storage.Client()
    buckets = list(client.list_buckets())
    print("✅ Successfully connected to GCS!")
except Exception as e:
    print("❌ Error connecting to GCS:", e)
