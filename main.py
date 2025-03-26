from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd
import os
import uvicorn
from dotenv import load_dotenv
from gcs_util import upload_to_gcs, download_excel
from amazon_api import check_amazon_product_updates
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
import asyncio  # ✅ Added for async batch processing

# Load environment variables
load_dotenv()
SERVICE_ACCOUNT_FILE = "/secrets/GCS_KEY_FILE/amazon-monitoring-453611-99dccfb3bece.json"

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
BATCH_SIZE = 50  # ✅ Process 50 ASINs at a time

# Upload Excel file endpoint
@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    try:
        gcs_url = upload_to_gcs(file.file, EXCEL_FILE_NAME)
        return JSONResponse(content={"message": "Excel uploaded successfully!", "url": gcs_url}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 🔄 Function to process ASINs in the background
async def process_asins_background():
    try:
        file_path = download_excel(EXCEL_FILE_NAME)
        df = pd.read_excel(file_path, sheet_name="PRICING DATA", usecols=["Amazon ASIN", "Amazon URL"])

        updated_products = []
        asin_list = df["Amazon ASIN"].tolist()

        # Process ASINs in batches
        for i in range(0, len(asin_list), BATCH_SIZE):
            batch = asin_list[i:i + BATCH_SIZE]
            updates = await asyncio.gather(*[check_amazon_product_updates(asin) for asin in batch])

            for asin, update in zip(batch, updates):
                if update:
                    updated_products.append({"asin": asin, "update": update})

        # ✅ Save results to a file (optional: store in GCS or DB)
        result_path = "/tmp/updated_products.json"
        with open(result_path, "w") as f:
            f.write(str(updated_products))

        print("✅ Processing completed successfully!")
    except Exception as e:
        print(f"❌ Error processing ASINs: {str(e)}")

# API to trigger background processing
@app.get("/process-excel/")
async def process_excel(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_asins_background)
    return JSONResponse(content={"message": "Processing started in background!"}, status_code=202)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Cloud Run"}

# ✅ Corrected Uvicorn execution for Cloud Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Default to 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
