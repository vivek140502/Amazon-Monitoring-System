from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import os
import uvicorn  # ✅ Added missing import
from dotenv import load_dotenv
from gcs_util import upload_to_gcs, download_excel
from amazon_api import check_amazon_product_updates
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# Load environment variables
load_dotenv()
SERVICE_ACCOUNT_FILE = "/secrets/GCS_KEY_FILE"

# Set the environment variable for authentication
if os.path.exists(SERVICE_ACCOUNT_FILE):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
else:
    raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")

# Initialize Google Cloud Storage client
client = storage.Client()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to your frontend domain if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_FILE_NAME = "Master_Catalogue.xlsx"

# Upload Excel file endpoint
@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    try:
        gcs_url = upload_to_gcs(file.file, EXCEL_FILE_NAME)
        return JSONResponse(content={"message": "Excel uploaded successfully!", "url": gcs_url}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Process Excel file and fetch updates
@app.get("/process-excel/")
async def process_excel():
    try:
        file_path = download_excel(EXCEL_FILE_NAME)
        df = pd.read_excel(file_path, sheet_name="PRICING DATA")

        # ✅ Ensure required columns exist
        required_columns = {"Amazon ASIN", "Amazon URL"}
        if not required_columns.issubset(df.columns):
            return JSONResponse(content={"error": "Missing required columns in Excel"}, status_code=400)

        updated_products = []
        for _, row in df.iterrows():
            asin = row["Amazon ASIN"]
            url = row["Amazon URL"]

            update = check_amazon_product_updates(asin)  # ✅ Add `await` if async

            if update:
                updated_products.append({
                    "asin": asin,
                    "url": url,
                    "update": update
                })

        return JSONResponse(content={"products": updated_products}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Cloud Run"}

# ✅ Corrected Uvicorn execution for Cloud Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Default to 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
