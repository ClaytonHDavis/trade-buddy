import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

def load_data_from_csv(csv_file):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file, parse_dates=['start'])
    df.set_index('start', inplace=True)
    return df

def plot_average_gain_by_hour(df):
    # Calculate average forward_price_change_180m by hour of day
    avg_gain_by_hour = df.groupby('hour_of_day')['forward_price_change_180m'].mean()

    # Plotting
    plt.figure(figsize=(10, 6))
    avg_gain_by_hour.plot(kind='bar', color='orange')
    plt.title('Average Gain % by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Gain (%)')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_gainers_by_hour(df):
    # Filter for +40% gainers in 180-minute interval as an example
    gainers_40_plus = df[df['increase_level_180m'] == '40%+']

    # Count gainers by hour
    counts_by_hour = gainers_40_plus['hour_of_day'].value_counts().sort_index()

    if counts_by_hour.empty:
        print("No +40% gainers found in the data for the given intervals.")
        return

    # Plotting
    plt.figure(figsize=(10, 6))
    counts_by_hour.plot(kind='bar', color='skyblue')
    plt.title('Count of +40% Gainers by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Count of +40% Gainers')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_candlestick(df):
    # Ensure the index is datetime for mplfinance
    if not df.index.dtype == 'datetime64[ns]':
        df.index = pd.to_datetime(df.index)

    # Selecting a sample period for better visualization if the dataset is large
    sample_df = df[['open', 'high', 'low', 'close']].iloc[-100:]

    # Plotting
    mpf.plot(
        sample_df,
        type='candle',
        style='charles',
        title='Candlestick Chart',
        ylabel='Price',
        volume=False
    )

def plot_boxplot_by_hour(df):
    # Preparing the data for the boxplot
    data_to_plot = [group['forward_price_change_180m'].dropna().values
                    for name, group in df.groupby('hour_of_day')]

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.boxplot(data_to_plot, labels=range(24))
    plt.title('Distribution of Forward Price Change (%) by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Forward Price Change (%)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()

def plot_histogram(df):
    plt.figure(figsize=(10, 6))
    # Plot histogram of forward_price_change_180m
    df['forward_price_change_180m'].dropna().plot(kind='hist', bins=50, color='lightblue', edgecolor='black')
    plt.title('Histogram of Forward Price Change (%)')
    plt.xlabel('Forward Price Change (%)')
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# Main function to execute reading and plotting
def main():
    # Load data from CSV
    csv_file = 'enhanced_data.csv'  # Specify your path
    data = load_data_from_csv(csv_file)
    
    # Visualize the data
    #plot_gainers_by_hour(data)
    #plot_boxplot_by_hour(data)
    #plot_average_gain_by_hour(data)
    #plot_histogram(data)
    #plot_candlestick(data)

if __name__ == "__main__":
    main()