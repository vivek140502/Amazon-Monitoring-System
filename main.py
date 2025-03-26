import json
import asyncio
import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from gcs_util import upload_to_gcs, download_excel
from amazon_api import check_amazon_product_updates
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_FILE_NAME = "Master_Catalogue.xlsx"
RESULT_FILE = "/tmp/updated_products.json"  # ✅ Store results in a temporary file


@app.get("/process-excel/")
async def process_excel(background_tasks: BackgroundTasks):
    """Start processing the Excel file in the background."""
    background_tasks.add_task(process_excel_background)
    return JSONResponse(content={"message": "Processing started in background!"}, status_code=202)


async def process_excel_background():
    """Background task to process the Excel file."""
    try:
        file_path = download_excel(EXCEL_FILE_NAME)
        df = pd.read_excel(file_path, sheet_name="PRICING DATA")

        required_columns = {"Amazon ASIN", "Amazon URL"}
        if not required_columns.issubset(df.columns):
            return

        updated_products = []
        for _, row in df.iterrows():
            asin = row["Amazon ASIN"]
            url = row["Amazon URL"]

            update = await check_amazon_product_updates(asin)  # ✅ Use `await` if function is async

            if update:
                updated_products.append({
                    "asin": asin,
                    "url": url,
                    "update": update
                })

        # ✅ Store results in a file
        with open(RESULT_FILE, "w") as f:
            json.dump(updated_products, f)

    except Exception as e:
        with open(RESULT_FILE, "w") as f:
            json.dump({"error": str(e)}, f)


@app.get("/get-results/")
async def get_results():
    """Fetch processed results."""
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            updated_products = json.load(f)
        return JSONResponse(content={"products": updated_products}, status_code=200)
    else:
        return JSONResponse(content={"message": "Processing not completed yet."}, status_code=202)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Cloud Run"}
