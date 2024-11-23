import os
import time
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Function to fetch and append candle data for a specific coin
def fetch_products():
    try:
        url = f"/api/v3/brokerage/products"

        products = client.get(url)

        # Check if products is received and it's not empty
        if not products:
            print("No products found.")
            return
        
        # Create a DataFrame from the products response
        df = pd.DataFrame(products)

        # If the 'products' column contains the JSON array, normalize it
        if 'products' in df.columns and df['products'].size > 0:
            # Extracting the JSON objects stored in the first cell of 'products'
            product_list = df['products']

            # Create a new DataFrame from the JSON data
            product_df = pd.json_normalize(product_list)

            # Display the first few rows of the parsed data
            print(product_df.head())

            # Save the product data to CSV
            product_df.to_csv('coinbase_products.csv', index=False)
        else:
            print("No product details found in 'products' column.")

    except Exception as e:
        print(f"An error occurred: {e}")



# Main loop to continually fetch data
if __name__ == "__main__":
    # while True:
    fetch_products()
    # time.sleep(60)  # Wait for 60 seconds before fetching again