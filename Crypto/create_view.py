import psycopg2

# Function to create the indicators_view in PostgreSQL
def create_indicators_view():
    try:
        # Establish a database connection
        connection = psycopg2.connect(**connection_params)  # Ensure `connection_params` is defined with your database credentials
        cursor = connection.cursor()
        
        # SQL command to create the indicators_view
        create_view_query = """
        CREATE OR REPLACE VIEW indicators_view AS
        SELECT 
            start,
            low,
            high,
            open,
            close,
            volume,
            product_id,
            
            -- Average Volume over bar lengths
            AVG(volume) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '15 minutes' PRECEDING AND CURRENT ROW) AS avg_volume_15m,
            AVG(volume) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW) AS avg_volume_30m,
            AVG(volume) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND CURRENT ROW) AS avg_volume_60m,
            
            -- Average Price over bar lengths
            AVG((high + low) / 2) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '15 minutes' PRECEDING AND CURRENT ROW) AS avg_price_15m,
            AVG((high + low) / 2) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW) AS avg_price_30m,
            AVG((high + low) / 2) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND CURRENT ROW) AS avg_price_60m,
            
            -- Volume Changes over bar lengths
            volume - LAG(volume, 3) OVER (PARTITION BY product_id ORDER BY start) AS vol_change_15m,
            volume - LAG(volume, 6) OVER (PARTITION BY product_id ORDER BY start) AS vol_change_30m,
            volume - LAG(volume, 12) OVER (PARTITION BY product_id ORDER BY start) AS vol_change_60m,
            
            -- Price Changes over bar lengths
            close - LAG(close, 3) OVER (PARTITION BY product_id ORDER BY start) AS price_change_15m,
            close - LAG(close, 6) OVER (PARTITION BY product_id ORDER BY start) AS price_change_30m,
            close - LAG(close, 12) OVER (PARTITION BY product_id ORDER BY start) AS price_change_60m,
            
            -- Current Price and Volume Comparisons
            CASE WHEN close > (SELECT AVG(close) FROM trading_data WHERE start >= NOW() - INTERVAL '1 day') THEN 1 ELSE 0 END AS current_price_comparison,
            CASE WHEN volume > (SELECT AVG(volume) FROM trading_data WHERE start >= NOW() - INTERVAL '1 day') THEN 1 ELSE 0 END AS current_volume_comparison,
            
            -- Times of Day and Days of Week
            EXTRACT(HOUR FROM start) AS hour_of_day,
            EXTRACT(DOW FROM start) AS day_of_week,
            
            -- Standard Deviation over various intervals
            STDDEV_SAMP(close) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND CURRENT ROW) AS stddev_60m,
            STDDEV_SAMP(close) OVER (PARTITION BY product_id ORDER BY start RANGE BETWEEN INTERVAL '120 minutes' PRECEDING AND CURRENT ROW) AS stddev_120m,
            
            -- Ticker
            product_id AS ticker
            
        FROM trading_data;
        """
        
        # Execute the query to create the view
        cursor.execute(create_view_query)
        connection.commit()
        print("Indicator view created successfully.")
    
    except Exception as e:
        print(f"Failed to create indicators_view in PostgreSQL: {e}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

# Define PostgreSQL connection parameters
connection_params = {
    'dbname': "postgres",            # replace with your database name
    'user': "postgres",              # replace with your username
    'password': "asheville",         # replace with your password
    'host': "localhost",             # replace with your host
    'port': "5433"                   # replace with your port
}

# Call the function to create the view
create_indicators_view()