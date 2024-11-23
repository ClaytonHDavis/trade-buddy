import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display

# Retrieve the data from the CSV file and display the first few rows
df = pd.read_csv('coinbase_candles_5min.csv')

# Get list of products from "Coinbase_liquid.txt" (each line is a symbol)
with open('Coinbase_liquid.txt') as f:
    products = f.readlines()
products = [x.strip() for x in products]

# Filter the list on these products
df = df[df['product_id'].isin(products)]

# Add a new column to the DataFrame to calculate the moving average
df['MA'] = df['close'].rolling(window=5).mean()

# Add a new column to the DataFrame to calculate the exponential moving average
df['EMA'] = df['close'].ewm(span=5, adjust=False).mean()

# Do EMA for the price_change column
df['price_change_EMA'] = df['price_change'].ewm(span=5, adjust=False).mean()

# Smooth the price_change_EMA column using a rolling mean
df['price_change_EMA_smooth'] = df['price_change_EMA'].rolling(window=5).mean()

# Sort by highest price_change_EMA_smooth
df = df.sort_values(by='price_change_EMA_smooth', ascending=False)

# Function to plot data for a given product_id
def plot_product(product_id):
    product_df = df[df['product_id'] == product_id].sort_values(by='start', ascending=True)
    
    plt.figure(figsize=(14, 7))
    plt.plot(product_df['start'], product_df['price_change_EMA_smooth'], label='price_change_EMA_smooth')
    plt.title(f'Price Change EMA Smooth for {product_id}')
    plt.xlabel('Time')
    plt.ylabel('Price Change EMA Smooth')
    plt.legend()
    plt.show()

# Create a dropdown widget for selecting product_id
product_dropdown = widgets.Dropdown(
    options=products,
    description='Product ID:',
    disabled=False,
)

# Display the interactive plot
widgets.interact(plot_product, product_id=product_dropdown)