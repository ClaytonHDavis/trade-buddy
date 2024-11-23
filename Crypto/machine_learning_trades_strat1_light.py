import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def fetch_data_from_db():
    # PostgreSQL connection parameters
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }
    
    query = "SELECT * FROM public.trading_data;"
    
    try:
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        print("Data fetched successfully.")
    except Exception as e:
        print(f"Failed to fetch data from database: {e}")
    finally:
        connection.close()
        
    return dataframe

# Fetch data
raw_data = fetch_data_from_db()

def preprocess_data(df):
    df['start'] = pd.to_datetime(df['start'])
    df.set_index('start', inplace=True)

    def resample_product_id(group):
        resampled_group = group.resample('5min').ffill().bfill()
        resampled_group['product_id'] = group['product_id'].iloc[0]
        return resampled_group

    df_resampled = df.groupby('product_id').apply(resample_product_id).reset_index(level=0, drop=True).reset_index()
    return df_resampled

# Preprocess the data
processed_data = preprocess_data(raw_data)

def calculate_ema(prices, span):
    return prices.ewm(span=span, adjust=False).mean()

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(df, long_span=26, short_span=12, signal_span=9):
    df['ema_long'] = calculate_ema(df['close'], span=long_span)
    df['ema_short'] = calculate_ema(df['close'], span=short_span)
    df['macd'] = df['ema_short'] - df['ema_long']
    df['signal_line'] = calculate_ema(df['macd'], span=signal_span)
    df['macd_histogram'] = df['macd'] - df['signal_line']
    return df

def add_features(df):
    df['close_1bar'] = df.groupby('product_id')['close'].shift(1)
    df['volume_1bar'] = df.groupby('product_id')['volume'].shift(1)
    
    df['price_change_1bar'] = df['close'] - df['close_1bar']
    df['volume_change_1bar'] = df['volume'] - df['volume_1bar']
    
    df['price_change_3bar'] = df['close'] - df.groupby('product_id')['close'].shift(3)
    df['volume_change_3bar'] = df['volume'] - df.groupby('product_id')['volume'].shift(3)

    # New features
    df['future_price'] = (df.groupby('product_id')['close'].shift(-1) - df['close'])/df['close']   # Future price as a percent change
    df['future_price_5bars'] = (df.groupby('product_id')['close'].shift(-5) - df['close']) / df['close']   # Future price as a percent change
    df['future_price_300bars'] = (df.groupby('product_id')['close'].shift(-300) - df['close']) / df['close']   # Future price as a percent change

    df['SAM_3'] = df.groupby('product_id')['close'].rolling(window=3).mean().reset_index(level=0, drop=True)
    df['SAM_10'] = df.groupby('product_id')['close'].rolling(window=10).mean().reset_index(level=0, drop=True)
    df['SAM_50'] = df.groupby('product_id')['close'].rolling(window=50).mean().reset_index(level=0, drop=True)

    for period in [10, 50, 200]:
        df[f'ema_{period}'] = df.groupby('product_id')['close'].transform(lambda x: calculate_ema(x, span=period))

    df['rsi_14'] = df.groupby('product_id')['close'].transform(calculate_rsi)
    
    df['past_price_percent_1bar'] = df['price_change_1bar'] / df['close_1bar'] 
    df['past_price_percent_5bars'] = (df['close'] - df.groupby('product_id')['close'].shift(5)) / df.groupby('product_id')['close'].shift(5) 
    df['past_price_percent_300bars'] = (df['close'] - df.groupby('product_id')['close'].shift(300)) / df.groupby('product_id')['close'].shift(300)


    df['past_volume_1bar'] = df['volume_1bar']
    df['past_volume_5bars'] = df.groupby('product_id')['volume'].rolling(window=5).mean().reset_index(level=0, drop=True)
    df['past_volume_300bars'] = df.groupby('product_id')['volume'].rolling(window=300).mean().reset_index(level=0, drop=True)

    df = calculate_macd(df)
    
    return df

# Add features to the processed data
enhanced_data = add_features(processed_data)

def save_to_database(dataframe, table_name, connection_params):
    try:
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()

        create_table_query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
        start TIMESTAMPTZ NOT NULL,
        product_id TEXT NOT NULL,
        PRIMARY KEY (start, product_id),
        close FLOAT,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        volume FLOAT,
        future_price FLOAT,
        future_price_5bars FLOAT,
        future_price_300bars FLOAT,
        SAM_3 FLOAT,
        SAM_10 FLOAT,
        SAM_50 FLOAT,
        close_1bar FLOAT,
        volume_1bar FLOAT,
        price_change_1bar FLOAT,
        volume_change_1bar FLOAT,
        price_change_3bar FLOAT,
        volume_change_3bar FLOAT,
        ema_10 FLOAT,
        ema_50 FLOAT,
        ema_200 FLOAT,
        rsi_14 FLOAT,
        past_price_percent_1bar FLOAT,
        past_price_percent_5bars FLOAT,
        past_price_percent_300bars FLOAT,
        past_volume_1bar FLOAT,
        past_volume_5bars FLOAT,
        past_volume_300bars FLOAT,
        macd FLOAT,
        signal_line FLOAT,
        macd_histogram FLOAT
        );
        '''
        cursor.execute(create_table_query)
        connection.commit()
        
        # Sort the dataframe by `start` and `product_id`
        dataframe.sort_values(by=['start', 'product_id'], ascending=[True, True], inplace=True)

        required_columns = {
            'start', 'product_id', 'close', 'open', 'high', 'low', 'volume', 
            'future_price', 'future_price_5bars', 'future_price_300bars', 
            'SAM_3', 'SAM_10', 'SAM_50', 'close_1bar', 'volume_1bar', 
            'price_change_1bar', 'volume_change_1bar', 
            'price_change_3bar', 'volume_change_3bar', 
            'ema_10', 'ema_50', 'ema_200', 'rsi_14', 
            'past_price_percent_1bar', 'past_price_percent_5bars', 'past_price_percent_300bars', 
            'past_volume_1bar', 'past_volume_5bars', 'past_volume_300bars', 
            'macd', 'signal_line', 'macd_histogram'
        }

        if not required_columns.issubset(dataframe.columns):
            raise KeyError("Required columns are missing from dataframe.")
        
        insert_query = f'''
        INSERT INTO {table_name} (
            start, product_id, close, open, high, low, volume, future_price, future_price_5bars, 
            future_price_300bars, SAM_3, SAM_10, SAM_50, close_1bar, volume_1bar, price_change_1bar, 
            volume_change_1bar, price_change_3bar, volume_change_3bar, ema_10, ema_50, ema_200, rsi_14, 
            past_price_percent_1bar, past_price_percent_5bars, past_price_percent_300bars, 
            past_volume_1bar, past_volume_5bars, past_volume_300bars, macd, signal_line, macd_histogram
        )
        VALUES %s ON CONFLICT (start, product_id) DO NOTHING;
        '''

        # Prepare data for insertion
        values = [
        (
            row['start'], row['product_id'], row['close'], row['open'], row['high'],
            row['low'], row['volume'], row['future_price'], row['future_price_5bars'], 
            row['future_price_300bars'], row['SAM_3'], row['SAM_10'], row['SAM_50'],
            row['close_1bar'], row['volume_1bar'], row['price_change_1bar'], 
            row['volume_change_1bar'], row['price_change_3bar'], row['volume_change_3bar'], 
            row['ema_10'], row['ema_50'], row['ema_200'], row['rsi_14'], 
            row['past_price_percent_1bar'], row['past_price_percent_5bars'], 
            row['past_price_percent_300bars'], row['past_volume_1bar'], 
            row['past_volume_5bars'], row['past_volume_300bars'], 
            row['macd'], row['signal_line'], row['macd_histogram']
        )
        for _, row in dataframe.iterrows()
        ]
        
        execute_values(cursor, insert_query, values)
        connection.commit()
        print(f"Data successfully saved to '{table_name}' table.")

    except Exception as e:
        print(f"Failed to save data to database: {e}")
    finally:
        connection.close()

# Define the table name and save the enhanced data to the database
table_name = "simplified_trading_data"
save_to_database(enhanced_data, table_name, {
    'dbname': "postgres",
    'user': "postgres",
    'password': "asheville",
    'host': "localhost",
    'port': "5433"
})