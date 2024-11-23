import pandas as pd
import psycopg2

def fetch_data_from_db():
    # Define PostgreSQL connection parameters
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }
    
    # Modify query to fetch all product IDs instead of a single product
    query = "SELECT * FROM public.trading_data where product_id = 'BTC-USD';"
    
    try:
        # Connect to the database, and execute the query
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        print("Data fetched successfully.")
        
    except Exception as e:
        print(f"Failed to fetch data from database: {e}")
    
    finally:
        # Close the connection
        connection.close()
        
    return dataframe

# Fetch data
raw_data = fetch_data_from_db()

def preprocess_data(df):
    df['start'] = pd.to_datetime(df['start'])
    df.set_index('start', inplace=True)
    df = df.resample('5T').ffill().bfill()
    return df

def calculate_ema(prices, span):
    return prices.ewm(span=span, adjust=False).mean()

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_features(df):
    df['avg_volume_15m'] = df['volume'].rolling(window=3).mean()
    df['avg_volume_30m'] = df['volume'].rolling(window=6).mean()
    df['avg_volume_60m'] = df['volume'].rolling(window=12).mean()

    price_avg = (df['high'] + df['low']) / 2
    df['avg_price_15m'] = price_avg.rolling(window=3).mean()
    df['avg_price_30m'] = price_avg.rolling(window=6).mean()
    df['avg_price_60m'] = price_avg.rolling(window=12).mean()

    ema_periods = [5, 8, 13, 20, 200]
    for period in ema_periods:
        df[f'ema_{period}'] = calculate_ema(df['close'], span=period)

    df['rsi_14'] = calculate_rsi(df['close'])
    
    df['vol_change_15m'] = df['volume'].diff(periods=3)
    df['vol_change_30m'] = df['volume'].diff(periods=6)
    df['vol_change_60m'] = df['volume'].diff(periods=12)
    
    df['price_change_15m'] = df['close'].diff(periods=3)
    df['price_change_30m'] = df['close'].diff(periods=6)
    df['price_change_60m'] = df['close'].diff(periods=12)
    
    df['current_price_comparison'] = (df['close'] > df['close'].rolling(window=12*24).mean()).astype(int)
    df['current_volume_comparison'] = (df['volume'] > df['volume'].rolling(window=12*24).mean()).astype(int)
    
    df['hour_of_day'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    
    df['stddev_60m'] = df['close'].rolling(window=12).std()
    df['stddev_120m'] = df['close'].rolling(window=24).std()

    return df

def add_advanced_features(df):
    forward_periods = [3, 6, 12]
    for period in forward_periods:
        df[f'forward_price_change_{15*period}m'] = (df['close'].shift(-period) - df['close']) / df['close'] * 100

    def categorize_change(change_pct):
        if change_pct > 100:
            return "100%+"
        elif change_pct > 40:
            return "40%+"
        elif change_pct > 20:
            return "20%+"
        elif change_pct > 10:
            return "10%+"
        elif change_pct > 5:
            return "5%+"
        elif change_pct > 2:
            return "2%+"
        elif change_pct > 1:
            return "1%+"
        else:
            return "No significant change"

    for period in forward_periods:
        df[f'increase_level_{15*period}m'] = df[f'forward_price_change_{15*period}m'].apply(categorize_change)
    
    for period in forward_periods:
        df[f'absolute_price_movement_{15*period}m'] = df['close'].diff(periods=period).abs()

    df['market_trend'] = 'SIDEWAYS'
    df['market_strength'] = 'Weak'

    df['market_range_60m'] = df['close'].rolling(window=12).apply(lambda x: x.max() - x.min())

    return df

# Apply transformations while maintaining each product_id's scope
def transform_group(df):
    df_transformed = preprocess_data(df)
    df_transformed = add_features(df_transformed)
    df_transformed = add_advanced_features(df_transformed)
    df_transformed['product_id'] = df['product_id'].iloc[0]  # Add back the product_id
    return df_transformed

grouped_data = raw_data.groupby('product_id', group_keys=False, as_index=False).apply(transform_group)

def save_to_database(dataframe, table_name, connection_params):
    try:
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            start TIMESTAMPTZ PRIMARY KEY,
            close FLOAT,
            volume FLOAT,
            high FLOAT,
            low FLOAT,
            open FLOAT,
            product_id TEXT,
            avg_volume_15m FLOAT,
            avg_volume_30m FLOAT,
            avg_volume_60m FLOAT,
            avg_price_15m FLOAT,
            avg_price_30m FLOAT,
            avg_price_60m FLOAT,
            ema_5 FLOAT,
            ema_8 FLOAT,
            ema_13 FLOAT,
            ema_20 FLOAT,
            ema_200 FLOAT,
            rsi_14 FLOAT,
            vol_change_15m FLOAT,
            vol_change_30m FLOAT,
            vol_change_60m FLOAT,
            price_change_15m FLOAT,
            price_change_30m FLOAT,
            price_change_60m FLOAT,
            current_price_comparison INT,
            current_volume_comparison INT,
            hour_of_day INT,
            day_of_week INT,
            stddev_60m FLOAT,
            stddev_120m FLOAT,
            forward_price_change_45m FLOAT,
            increase_level_45m TEXT,
            absolute_price_movement_45m FLOAT,
            forward_price_change_90m FLOAT,
            increase_level_90m TEXT,
            absolute_price_movement_90m FLOAT,
            forward_price_change_180m FLOAT,
            increase_level_180m TEXT,
            absolute_price_movement_180m FLOAT,
            market_trend TEXT,
            market_strength TEXT,
            market_range_60m FLOAT
        );
        '''
        cursor.execute(create_table_query)
        
        for i, row in dataframe.iterrows():
            insert_query = f'''
            INSERT INTO {table_name} (start, close, volume, high, low, open, product_id, avg_volume_15m, avg_volume_30m, avg_volume_60m, avg_price_15m, avg_price_30m, avg_price_60m, ema_5, ema_8, ema_13, ema_20, ema_200, rsi_14, vol_change_15m, vol_change_30m, vol_change_60m, price_change_15m, price_change_30m, price_change_60m, current_price_comparison, current_volume_comparison, hour_of_day, day_of_week, stddev_60m, stddev_120m, forward_price_change_45m, increase_level_45m, absolute_price_movement_45m, forward_price_change_90m, increase_level_90m, absolute_price_movement_90m, forward_price_change_180m, increase_level_180m, absolute_price_movement_180m, market_trend, market_strength, market_range_60m)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            '''
            cursor.execute(insert_query, (
                row.name, row['close'], row['volume'], row['high'], row['low'], row['open'], row['product_id'],
                row['avg_volume_15m'], row['avg_volume_30m'], row['avg_volume_60m'], 
                row['avg_price_15m'], row['avg_price_30m'], row['avg_price_60m'], 
                row['ema_5'], row['ema_8'], row['ema_13'], row['ema_20'], row['ema_200'], 
                row['rsi_14'], row['vol_change_15m'], row['vol_change_30m'], row['vol_change_60m'], 
                row['price_change_15m'], row['price_change_30m'], row['price_change_60m'], 
                row['current_price_comparison'], row['current_volume_comparison'], 
                row['hour_of_day'], row['day_of_week'], 
                row['stddev_60m'], row['stddev_120m'],
                row['forward_price_change_45m'], row['increase_level_45m'], row['absolute_price_movement_45m'], 
                row['forward_price_change_90m'], row['increase_level_90m'], row['absolute_price_movement_90m'], 
                row['forward_price_change_180m'], row['increase_level_180m'], row['absolute_price_movement_180m'], 
                row['market_trend'], row['market_strength'], row['market_range_60m']
            ))
        
        connection.commit()
        print("Data saved to database successfully.")
        
    except Exception as e:
        print(f"Failed to save data to database: {e}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# Ensure your database connection parameters are reused here
connection_params = {
    'dbname': "postgres",
    'user': "postgres",
    'password': "asheville",
    'host': "localhost",
    'port': "5433"
}

# Save the transformed data for each product_id to the database
save_to_database(grouped_data, 'enhanced_trading_data', connection_params)