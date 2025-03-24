from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
import pandas as pd
import os
from dotenv import load_dotenv
from gcs_util import upload_to_gcs, download_excel
from amazon_api import check_amazon_product_updates
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ["GOOGLE_APPLICATION_CREDENTIALS"]) 

# Manually set if not loaded
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\GCP\\amazon-monitoring-453611-4761414aad79.json"

print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to specific frontend domain if needed
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

        updated_products = []
        for _, row in df.iterrows():
            asin = row.get("Amazon ASIN")
            url = row.get("Amazon URL")

            update = check_amazon_product_updates(asin)  # Real API call

            if update:
                updated_products.append({
                    "asin": asin,
                    "url": url,
                    "update": update
                })

        return JSONResponse(content={"products": updated_products}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/test-env")
def test_env():
    return {"GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")}

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Cloud Run"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # Use PORT 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
