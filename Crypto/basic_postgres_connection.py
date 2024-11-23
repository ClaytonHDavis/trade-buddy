import psycopg2
from psycopg2 import sql

def connect():
    try:
        # Define your connection parameters
        connection = psycopg2.connect(
            dbname="postgres",            # Database name
            user="postgres",          # Default PostgreSQL admin user
            password="asheville",     # Replace with your password
            host="localhost",         # Usually localhost if local
            port="5433"               # Default port is 5432
        )

        # Create a cursor object using the connection
        cursor = connection.cursor()

        # SQL command to create a new table
        create_table_query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS trading_data (
            start TIMESTAMP,
            low DECIMAL,
            high DECIMAL,
            open DECIMAL,
            close DECIMAL,
            volume DECIMAL,
            product_id VARCHAR(50)
        );
        """)

        # Execute the SQL command
        cursor.execute(create_table_query)
        # Commit the changes to the database
        connection.commit()
        print("Table created successfully.")

        # Optional: check connection by executing a simple query
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    
    finally:
        # Closing the database connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

# Call the connect function
connect()