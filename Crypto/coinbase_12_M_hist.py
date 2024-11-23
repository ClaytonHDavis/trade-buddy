import os
import time
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient
import matplotlib.pyplot as plt

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Function to fetch and append candle data for a specific coin
def fetch_products():
    all_candles = pd.DataFrame(columns=columns)  # DataFrame to hold candles data for all products

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
            #print(product_df.head())

            # Save the product data to CSV
            product_df.to_csv('coinbase_products.csv', index=False)

            isFetch = False

            if isFetch:
                # Loop through the product_id column and call fetch_and_append_candles for each product
                for product_id in product_df['product_id']:
                    new_symbol_candle = fetch_and_append_candles(product_id, 'ONE_DAY', 90)
                    all_candles = pd.concat([all_candles, new_symbol_candle]).drop_duplicates(subset=['start', 'product_id']).reset_index(drop=True)
                    print(new_symbol_candle)
            else:
                # Load all_candles from the existing CSV file
                if os.path.exists('coinbase_candles.csv'):
                    all_candles = pd.read_csv('coinbase_candles.csv')
                    all_candles['start'] = pd.to_datetime(all_candles['start'])  # Ensure 'start' column is in datetime format
                else:
                    print("coinbase_candles.csv not found.")

            # Filter out all product_id rows containing 'USDC'
            all_candles = all_candles[~all_candles['product_id'].str.contains('USDC')]

            # Group the candles data by product_id and sort desc by start date
            all_candles = all_candles.groupby('product_id').apply(lambda x: x.sort_values('start', ascending=False)).reset_index(drop=True)

            # Create additional fields
            all_candles['price_change'] = ((all_candles['close'] - all_candles['open']) / all_candles['open']) * 100
            all_candles['volume_change'] = all_candles['volume'].pct_change() * 100
            all_candles['price_volume'] = all_candles['close'] * all_candles['volume']
            all_candles['day_of_week'] = all_candles['start'].dt.day_name()
            all_candles['month'] = all_candles['start'].dt.month_name()

            #print(all_candles)

            # Filter on price_volume >= 1000000
            filtered_candles = all_candles[all_candles['price_volume'] >= 1000000]

            # Filter on price change >= 20%
            # filtered_candles = all_candles[all_candles['price_change'] >= 20]
            
            # Plot histogram on day of week
            filtered_candles['day_of_week'].hist()
            plt.title('Histogram of Day of Week')
            plt.xlabel('Day of Week')
            plt.ylabel('Frequency')
            # plt.show()

            # Plot histogram on month
            filtered_candles['month'].hist()
            plt.title('Histogram of Month')
            plt.xlabel('Month')
            plt.ylabel('Frequency')
            # plt.show()

            # Plot histogram of volume change
            filtered_candles['volume_change'].hist()
            #plt.xscale('log')
            plt.title('Histogram of Volume Change')
            plt.xlabel('Volume Change')
            plt.ylabel('Frequency')
            # plt.show()
            
            # Save all the candles data to a CSV file
            all_candles.to_csv('coinbase_candles.csv', index=False)
            
            print("program complete.")
            
            isFetch = True
    
            if isFetch:
                # Clear all rows in all_candles
                all_candles = all_candles.iloc[0:0]
            else:
                # Load all_candles from the existing 5-minute CSV file
                if os.path.exists('coinbase_candles_5min.csv'):
                    all_candles = pd.read_csv('coinbase_candles_5min.csv')
                    all_candles['start'] = pd.to_datetime(all_candles['start'])  # Ensure 'start' column is in datetime format
                else:
                    print("coinbase_candles_5min.csv not found.")

            #set product_df to just products in filtered_candles
            product_df = pd.DataFrame(filtered_candles['product_id'].unique(), columns=['product_id'])

            # Fetch and process 5-minute interval data
            if isFetch:
                for product_id in product_df['product_id']:
                    for day in range(180):
                        end = int(time.time()) - (day * 86400)  # Calculate end time for each day in the last 180 days
                        new_symbol_candle_5min = fetch_and_append_candles(product_id, 'FIVE_MINUTE', 300, end)
                        if not new_symbol_candle_5min.empty:
                            new_symbol_candle_5min['price_change'] = ((new_symbol_candle_5min['close'] - new_symbol_candle_5min['open']) / new_symbol_candle_5min['open']) * 100
                            new_symbol_candle_5min['volume_change'] = new_symbol_candle_5min['volume'].pct_change() * 100
                            new_symbol_candle_5min['price_volume'] = new_symbol_candle_5min['close'] * new_symbol_candle_5min['volume']
                            
                            # Convert 'start' to datetime if it's not already
                            if new_symbol_candle_5min['start'].dtype == 'O':  # 'O' stands for object, which is often used for strings
                                new_symbol_candle_5min['start'] = pd.to_datetime(new_symbol_candle_5min['start'])
                            
                            # hour of the day
                            new_symbol_candle_5min['hour'] = new_symbol_candle_5min['start'].dt.hour

                            # Sort the DataFrame by the 'hour' column in ascending order
                            new_symbol_candle_5min = new_symbol_candle_5min.sort_values(by='hour', ascending=True)
            
                            # Append the new data to the all_candles DataFrame
                            all_candles = pd.concat([all_candles, new_symbol_candle_5min]).drop_duplicates(subset=['start', 'product_id']).reset_index(drop=True)
                            
                            print(new_symbol_candle_5min)
                            print(all_candles.count(1))

                        else:
                            print(f"No data fetched for product_id: {product_id} on day: {day}")
            
                # Print the final DataFrame
                print(all_candles)
                                    
            # save all_candles to separate CSV file
            all_candles.to_csv('coinbase_candles_5min.csv', index=False)

                                # filter for price change >= 1%
            all_candles = all_candles[all_candles['price_change'] >= 1]

           # make a table that tallys the number of times a product_id has a price change >= 1% for each hour
            table = pd.pivot_table(all_candles, values='price_change', index=['product_id'], columns=['hour'], aggfunc='sum', fill_value=0)
            
            print(table)

            # save table to CSV
            # Change to save this to our DB!!!
            table.to_csv('coinbase_table_price_action_times.csv')

        else:
            print("No product details found in 'products' column.")

    except Exception as e:
        print(f"An error occurred: {e}")

columns = ['start', 'low', 'high', 'open', 'close', 'volume']
candle_data = pd.DataFrame(columns=columns)

# Function to fetch and return candle data for a specific coin
def fetch_and_append_candles(product_id, granularity, limit=5, end=None):
    # Define a local DataFrame for this product's candle data
    local_candle_data = pd.DataFrame(columns=columns)

    # Define granularity levels in seconds
    granularity_seconds = {
        'ONE_MINUTE': 60,
        'FIVE_MINUTE': 300,
        'FIFTEEN_MINUTES': 900,
        'ONE_HOUR': 3600,
        'SIX_HOURS': 21600,
        'ONE_DAY': 86400
    }

    try:
        # Set end to the current time if it's not specified
        if end is None:
            end = int(time.time())
        
        interval = granularity_seconds.get(granularity, 60)  # Default to 60 seconds if granularity not found
        
        start = end - (limit * interval)  # Calculate start time based on granularity
        
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        # Fetch candle data from the API
        candles = client.get(url, params=params)

        # Convert the candle data into a DataFrame
        new_candles = pd.DataFrame(candles['candles'])
        new_candles['start'] = pd.to_numeric(new_candles['start'])  # Explicitly cast to numeric type
        new_candles['start'] = pd.to_datetime(new_candles['start'], unit='s')  # Convert UNIX timestamp to datetime
        new_candles['product_id'] = product_id  # Add product_id to the DataFrame

        # Ensure numeric columns are correctly typed
        numeric_columns = ['low', 'high', 'open', 'close', 'volume']
        for col in numeric_columns:
            new_candles[col] = pd.to_numeric(new_candles[col], errors='coerce')

        # Check for duplicates and append only new entries
        local_candle_data = pd.concat([local_candle_data, new_candles]).drop_duplicates(subset=['start']).reset_index(drop=True)

        # Sort the DataFrame by 'start' in descending order
        local_candle_data = local_candle_data.sort_values(by='start', ascending=False).reset_index(drop=True)

        return local_candle_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(columns=columns)

# Main loop to continually fetch data
if __name__ == "__main__":
    fetch_products()