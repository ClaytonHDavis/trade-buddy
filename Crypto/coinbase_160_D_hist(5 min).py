import os
import time
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient
import psycopg2
import psycopg2.extras  # Make sure this is imported for execute_values
import matplotlib.pyplot as plt

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Define PostgreSQL connection parameters
connection_params = {
    'dbname': "postgres",            # replace with your database name
    'user': "postgres",              # replace with your username
    'password': "asheville",         # replace with your password
    'host': "localhost",             # replace with your host
    'port': "5433"                   # replace with your port
}

# Function to store data to PostgreSQL using batch insert
def store_data_to_db_batch(dataframe, batch_size=20000):
    print("Storing data to PostgreSQL using batch insert...")
    try:
        # Establish a database connection
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()

        # SQL command for inserting data
        insert_query = """
            INSERT INTO trading_data (start, low, high, open, close, volume, product_id) 
            VALUES %s ON CONFLICT DO NOTHING;
        """

        # Prepare data for insertion
        records = [
            (
                row['start'], 
                row['low'], 
                row['high'], 
                row['open'], 
                row['close'], 
                row['volume'], 
                row['product_id']
            )
            for _, row in dataframe.iterrows()
        ]

        # Insert records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            psycopg2.extras.execute_values(cursor, insert_query, batch)
            connection.commit()

        print("Data inserted successfully into trading_data table.")
    
    except Exception as e:
        print(f"Failed to insert data into PostgreSQL table: {e}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

# Example usage:
# store_data_to_db_batch(your_dataframe)

# Function to store data to PostgreSQL
def store_data_to_db(dataframe):
    try:
        # Establish a database connection
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        
        # SQL command for inserting data
        insert_query = """
            INSERT INTO trading_data (start, low, high, open, close, volume, product_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """
        
        # Iterate through the DataFrame and insert each row
        for _, row in dataframe.iterrows():
            cursor.execute(insert_query, (
                row['start'], 
                row['low'], 
                row['high'], 
                row['open'], 
                row['close'], 
                row['volume'], 
                row['product_id']
            ))

        # Commit the transaction
        connection.commit()
        print("Data inserted successfully into trading_data table.")
    
    except Exception as e:
        print(f"Failed to insert data into PostgreSQL table: {e}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

columns = ['start', 'low', 'high', 'open', 'close', 'volume', 'product_id']

# Function to fetch and append candle data for a specific coin
def fetch_products():
    all_candles = pd.DataFrame(columns=columns)

    try:
        url = f"/api/v3/brokerage/products"
        products = client.get(url)

        if not products:
            print("No products found.")
            return

        # Convert products JSON response into a DataFrame
        df = pd.DataFrame(products)

        if 'products' in df.columns and df['products'].size > 0:
            product_list = df['products']
            product_df = pd.json_normalize(product_list)

            isFetch = False

            if isFetch:
                for product_id in product_df['product_id']:
                    new_symbol_candle = fetch_and_append_candles(product_id, 'ONE_DAY', 90)
                    all_candles = pd.concat([all_candles, new_symbol_candle]).drop_duplicates(subset=['start', 'product_id']).reset_index(drop=True)
                    print(new_symbol_candle)
                
                store_data_to_db(all_candles)

            else:
                if os.path.exists('coinbase_candles.csv'):
                    all_candles = pd.read_csv('coinbase_candles.csv')
                    all_candles['start'] = pd.to_datetime(all_candles['start'])
                else:
                    print("coinbase_candles.csv not found.")

            # Filter and sort the data
            all_candles = all_candles[~all_candles['product_id'].str.contains('USDC')]
            all_candles = all_candles.groupby('product_id').apply(lambda x: x.sort_values('start', ascending=False)).reset_index(drop=True)

            # Calculate additional fields
            all_candles['price_change'] = ((all_candles['close'] - all_candles['open']) / all_candles['open']) * 100
            all_candles['volume_change'] = all_candles['volume'].pct_change() * 100
            all_candles['price_volume'] = all_candles['close'] * all_candles['volume']
            all_candles['day_of_week'] = all_candles['start'].dt.day_name()
            all_candles['month'] = all_candles['start'].dt.month_name()

            # Plot histograms
            filtered_candles = all_candles[all_candles['price_volume'] >= 1000000]
            filtered_candles['day_of_week'].hist()
            plt.title('Histogram of Day of Week')
            plt.xlabel('Day of Week') 
            plt.ylabel('Frequency')
            # plt.show()

            filtered_candles['month'].hist()
            plt.title('Histogram of Month')
            plt.xlabel('Month')
            plt.ylabel('Frequency')
            # plt.show()

            filtered_candles['volume_change'].hist()
            plt.title('Histogram of Volume Change')
            plt.xlabel('Volume Change')
            plt.ylabel('Frequency')
            # plt.show()
            
            all_candles.to_csv('coinbase_candles.csv', index=False)
            print("program complete.")
            
            isFetch = True

            if isFetch:
                all_candles = all_candles.iloc[0:0]
            else:
                if os.path.exists('coinbase_candles_5min.csv'):
                    all_candles = pd.read_csv('coinbase_candles_5min.csv')
                    all_candles['start'] = pd.to_datetime(all_candles['start'])
                else:
                    print("coinbase_candles_5min.csv not found.")

            product_df = pd.DataFrame(filtered_candles['product_id'].unique(), columns=['product_id'])

            # WE STOPPED THE DATA MINING HERE: 2024-07-22 23:15:00, CSV-USD. NEED TO MODIFY THE CODE TO PICK UP FROM HERE
            #print lentgh of product_df
            # print(len(product_df))

            # #print index of where product CVX-USD is, stopped mining here: 2024-07-22 23:15:00
            # print(product_df[product_df['product_id'] == 'CVX-USD'].index)

            # #remove all products before ATOM-USD
            product_df = product_df.iloc[product_df[product_df['product_id'] == 'ATOM-USD'].index[0]:]

            # #reindex everything after removing products before CVX-USD
            # product_df = product_df.reset_index(drop=True)

            # #print lentgh of product_df
            # print(len(product_df))

            #get tickers from Countbase_Liquid.txt
            with open('Coinbase_Liquid.txt') as f:
                products = f.readlines()
            products = [x.strip() for x in products]

            # Check what % of these products exist in product_df
            print(len(product_df[product_df['product_id'].isin(products)]) / len(products))
            

            
    
            if isFetch:
                for product_id in product_df['product_id']:
                    #empty dataframe for new symbol 
                    new_symbol_set = pd.DataFrame(columns=columns)
                    
                    for day in range(180):
                        end = int(time.time()) - (day * 86400)



                        new_symbol_candle_5min = fetch_and_append_candles(product_id, 'FIVE_MINUTE', 300, end)

                        if not new_symbol_candle_5min.empty:
                            #new_symbol_candle_5min['price_change'] = ((new_symbol_candle_5min['close'] - new_symbol_candle_5min['open']) / new_symbol_candle_5min['open']) * 100
                            #new_symbol_candle_5min['volume_change'] = new_symbol_candle_5min['volume'].pct_change() * 100
                            #new_symbol_candle_5min['price_volume'] = new_symbol_candle_5min['close'] * new_symbol_candle_5min['volume']
                            
                            if new_symbol_candle_5min['start'].dtype == 'O':
                                new_symbol_candle_5min['start'] = pd.to_datetime(new_symbol_candle_5min['start'])
                            
                            #new_symbol_candle_5min['hour'] = new_symbol_candle_5min['start'].dt.hour
                            #new_symbol_candle_5min = new_symbol_candle_5min.sort_values(by='hour', ascending=True)
            
                            new_symbol_set = pd.concat([new_symbol_set, new_symbol_candle_5min]).drop_duplicates(subset=['start', 'product_id']).reset_index(drop=True)
                            
                            # store_data_to_db(new_symbol_candle_5min)
                            print(new_symbol_candle_5min)
                            # print(all_candles.count(1))
                            #print index of product_id
                            print(product_df[product_df['product_id'] == product_id].index[0])
                            
                            #print lentgh of product_df - current product_id index / lentgh of product_df * 100
                            print(product_df[product_df['product_id'] == product_id].index[0] / len(product_df) * 100)
                            

                        else:
                            print(f"No data fetched for product_id: {product_id} on day: {day}")
                            
                    #store batch
                    store_data_to_db_batch(new_symbol_set)

                print(new_symbol_set)

        else:
            print("No product details found in 'products' column.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Function to fetch and return candle data for a specific coin
def fetch_and_append_candles(product_id, granularity, limit=5, end=None):
    local_candle_data = pd.DataFrame(columns=columns)

    granularity_seconds = {
        'ONE_MINUTE': 60,
        'FIVE_MINUTE': 300,
        'FIFTEEN_MINUTES': 900,
        'ONE_HOUR': 3600,
        'SIX_HOURS': 21600,
        'ONE_DAY': 86400
    }

    try:
        if end is None:
            end = int(time.time())
        
        interval = granularity_seconds.get(granularity, 60)
        
        start = end - (limit * interval)
        
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        # Fetch candle data from the API
        candles = client.get(url, params=params)

        # Ensure the candles data exists
        if 'candles' not in candles:
            return pd.DataFrame(columns=columns)
        
        # Convert the candle data into a DataFrame
        new_candles = pd.DataFrame(candles['candles'])
        new_candles['start'] = pd.to_numeric(new_candles['start'])
        new_candles['start'] = pd.to_datetime(new_candles['start'], unit='s')
        new_candles['product_id'] = product_id

        # Ensure numeric columns are correctly typed
        numeric_columns = ['low', 'high', 'open', 'close', 'volume']
        for col in numeric_columns:
            new_candles[col] = pd.to_numeric(new_candles[col], errors='coerce')

        # Append only new entries, checking for duplicates
        local_candle_data = pd.concat([local_candle_data, new_candles]).drop_duplicates(subset=['start']).reset_index(drop=True)

        # Sort DataFrame by 'start' in descending order
        local_candle_data = local_candle_data.sort_values(by='start', ascending=False).reset_index(drop=True)

        return local_candle_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(columns=columns)

# Main loop to continually fetch data
if __name__ == "__main__":
    fetch_products()