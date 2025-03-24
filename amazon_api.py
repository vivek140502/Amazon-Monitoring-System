import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()




# Amazon LWA Credentials (No AWS needed)
CLIENT_ID = os.getenv("AMAZON_CLIENT_ID")
CLIENT_SECRET = os.getenv("AMAZON_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("AMAZON_REFRESH_TOKEN")

# Amazon API Endpoint
API_HOST = "https://sellingpartnerapi-na.amazon.com"

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to Get Amazon SP-API Access Token
def get_access_token():
    """
    Retrieves an access token from Amazon SP-API using the refresh token.
    """
    url = "https://api.amazon.com/auth/o2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        logger.error(f"Error getting access token: {response.text}")
        return None

# Function to Check Amazon Product Updates
def check_amazon_product_updates(asin):
    """
    Fetches product details from Amazon SP-API and checks for updates.
    """
    access_token = get_access_token()
    if not access_token:
        return None

    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }

    url = f"{API_HOST}/catalog/v0/items/{asin}?marketplaceIds=A1PA6795UKMFR9"  # Change marketplace ID as needed

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        logger.info(f"Product Data: {data}")

        # Check for badges (Amazon Choice, Best Seller)
        if "bestseller" in str(data).lower():
            return "New Best Seller Badge Added"
        if "amazon choice" in str(data).lower():
            return "New Amazon Choice Badge Added"
        return "No updates"
    
    logger.error(f"Error fetching product data: {response.text}")
    return None

# Test function
if __name__ == "__main__":
    test_asin = "B09G3HRMVB"  # Example ASIN
    result = check_amazon_product_updates(test_asin)
    print("Update:", result)
