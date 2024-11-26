import psycopg2

def drop_table(connection_params, table_name):
    return
    """
    Drops a table from the PostgreSQL database.
    
    Parameters:
    - connection_params: A dictionary containing the connection parameters (dbname, user, password, host, port).
    - table_name: The name of the table to drop.
    """
    connection = None
    cursor = None
    
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**connection_params)
        # Create a cursor to perform database operations
        cursor = connection.cursor()
        
        # Create the SQL query to drop the table
        query = f'DROP TABLE IF EXISTS {table_name};'
        
        # Execute the query
        cursor.execute(query)
        
        # Commit the changes to the database
        connection.commit()
        
        # Confirm action
        print(f'The table {table_name} has been dropped successfully.')
    
    except psycopg2.Error as e:
        print(f'An error occurred: {e}')
    
    finally:
        # Ensure the cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def count_rows(connection_params, table_name):
    """
    Counts the number of rows in a table.
    
    Parameters:
    - connection_params: A dictionary containing the connection parameters (dbname, user, password, host, port).
    - table_name: The name of the table for which to count rows.
    
    Returns:
    - The number of rows in the table.
    """
    connection = None
    cursor = None
    
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(**connection_params)
        # Create a cursor to perform database operations
        cursor = connection.cursor()
        
        # Create the SQL query to count rows
        query = f'SELECT COUNT(*) FROM {table_name};'
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch the result of the query
        count = cursor.fetchone()[0]
        
        # Return the count of rows
        return count
    
    except psycopg2.Error as e:
        print(f'An error occurred: {e}')
        return None
    
    finally:
        # Ensure the cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    # Define your database connection parameters
    connection_params = {
        'dbname': "postgres",      # replace with your database name
        'user': "postgres",        # replace with your username
        'password': "asheville",   # replace with your password
        'host': "localhost",       # replace with your host
        'port': "5433"             # replace with your port
    }
    
    # The name of the table you want to query
    table_name = 'trading_data'   # replace with your table name
    
    # Example usage of count_rows
    row_count = count_rows(connection_params, table_name)
    if row_count is not None:
        print(f'The table {table_name} contains {row_count} rows.')
    
    # Example usage of drop_table
    #drop_table(connection_params, table_name)  # Uncomment to drop the table