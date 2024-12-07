# data_historical.py
import pandas as pd
import psycopg2

def fetch_data_from_db(product_id):
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }
    query = f"""
    SELECT * FROM trading_data
    WHERE product_id = '{product_id}'
    ORDER BY start ASC;
    """

    try:
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        dataframe.rename(columns={'start': 'time'}, inplace=True)  # Ensure 'time' column exists
        print(f"Data fetched successfully for {product_id}.")
    except Exception as e:
        print(f"Failed to fetch data from database for {product_id}: {e}")
        dataframe = pd.DataFrame()
    finally:
        connection.close()

    return dataframe