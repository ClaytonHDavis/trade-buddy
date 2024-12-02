import os
import uuid
from coinbase.rest import RESTClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

def place_market_order(product_id, size, transaction_type='BUY'):
    try:
        # Create a unique client order ID
        client_order_id = str(uuid.uuid4())

        # Define the order parameters
        order_data = {
            "client_order_id": client_order_id,
            "product_id": product_id,
            "side": transaction_type,
            "order_configuration": {
                "market_market_ioc": {
                    "base_size": str(size)  # `size` amount of base asset
                }
            }
        }

        # Place the market order
        response = client.post('/api/v3/brokerage/orders', data=order_data)

        # Check for error in response
        if 'error' in response:
            print(f"Error placing order: {response['error']}")
        else:
            print("Order placed successfully. Response:", response)

    except Exception as e:
        print(f"Encountered an exception: {e}")
