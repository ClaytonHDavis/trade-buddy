import pandas as pd
import numpy as np
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy
import seaborn as sns
import matplotlib.pyplot as plt

def fetch_data_from_db():

    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }

    query = "SELECT * FROM public.simplified_trading_data WHERE product_id = 'DIA-USD' ORDER BY start ASC;"

    try:
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        print("Data fetched successfully.")
    except Exception as e:
        print(f"Failed to fetch data from the database: {e}")
        dataframe = pd.DataFrame()
    finally:
        connection.close()

    return dataframe

def transform_data(dataframe):
    dataframe['start'] = pd.to_datetime(dataframe['start'])

    # Calculate EMAs
    dataframe['ema5'] = dataframe['close'].ewm(span=5, adjust=False).mean()
    dataframe['ema8'] = dataframe['close'].ewm(span=8, adjust=False).mean()
    dataframe['ema13'] = dataframe['close'].ewm(span=13, adjust=False).mean()
    dataframe['ema50'] = dataframe['close'].ewm(span=50, adjust=False).mean()
    dataframe['ema100'] = dataframe['close'].ewm(span=100, adjust=False).mean()
    dataframe['ema200'] = dataframe['close'].ewm(span=200, adjust=False).mean()

    # Calculate Standard Deviations
    dataframe['std_dev5'] = dataframe['close'].rolling(window=5).std()
    dataframe['std_dev10'] = dataframe['close'].rolling(window=10).std()
    dataframe['std_dev100'] = dataframe['close'].rolling(window=100).std()

    # Calculate Slope Level Detection and Std Percent
    dataframe['slope_level_detection'] = dataframe['ema100'].diff() / dataframe['ema100']
    dataframe['std_percent_100'] = dataframe['std_dev100'] / dataframe['ema100']
    dataframe['std_percent_to_slope'] = dataframe['slope_level_detection'] / dataframe['std_percent_100']

    # Initialize buffers for rolling standard deviations calculation
    dataframe['sts_std5'] = dataframe['std_percent_to_slope'].rolling(window=5).std()
    dataframe['sts_std10'] = dataframe['std_percent_to_slope'].rolling(window=10).std()
    dataframe['sts_std100'] = dataframe['std_percent_to_slope'].rolling(window=100).std()

    # Drop NA values created by lagging or rolling calculations
    dataframe.dropna(inplace=True)

    return dataframe

# def preprocess_data(data):
#     data = transform_data(data)

#     # Define feature columns
#     features = ['ema5', 'ema8', 'ema13', 'ema50', 'ema100', 'ema200',
#                 'slope_level_detection', 
#                 'std_percent_100', 'std_percent_to_slope', 'sts_std5', 
#                 'sts_std10', 'sts_std100']
    
#     # Define the target for predicting gain or loss
#     data['next_close'] = data['close'].shift(-10)
#     data['gain_loss'] = (data['next_close'] > data['close']).astype(int)  # Binary classification target

#     # Drop the last row (which will have a NaN target due to shift)
#     data.dropna(inplace=True)

#     X = data[features]
#     y = data['gain_loss']

#     # Split data
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

#     return X_train, X_test, y_train, y_test, data

# def normalize_data(X_train, X_test):
#     scaler = StandardScaler()
#     X_train_scaled = scaler.fit_transform(X_train)
#     X_test_scaled = scaler.transform(X_test)
#     return X_train_scaled, X_test_scaled

# def train_and_evaluate_lstm(X_train, X_test, y_train, y_test, all_features_test):
#     num_features = X_train.shape[1]
    
#     # Reshape data for LSTM model
#     X_train_lstm = X_train.reshape((X_train.shape[0], 1, num_features))
#     X_test_lstm = X_test.reshape((X_test.shape[0], 1, num_features))
    
#     model = Sequential()
#     model.add(LSTM(50, activation='relu', input_shape=(1, num_features)))
#     model.add(Dropout(0.2))
#     model.add(Dense(1, activation='sigmoid'))  # Sigmoid activation for binary classification

#     model.compile(optimizer=Adam(), loss=BinaryCrossentropy(), metrics=['accuracy'])
#     model.fit(X_train_lstm, y_train, epochs=100, batch_size=10, validation_data=(X_test_lstm, y_test))

#     y_pred_prob = model.predict(X_test_lstm).flatten()
#     y_pred = (y_pred_prob > 0.5).astype(int)  # Convert probabilities to binary predictions
    
#     # Calculate accuracy
#     accuracy = np.mean(y_pred == y_test)
#     print('LSTM Model Accuracy: ', accuracy)

#     # Save results to CSV
#     results_df = all_features_test.iloc[y_train.size:].copy()
#     results_df['Predicted_Prob'] = y_pred_prob
#     results_df['Predicted'] = y_pred
#     results_df['Actual'] = y_test
    
#     # Select relevant columns for output
#     output_cols = ['Actual', 'Predicted', 'Predicted_Prob'] + list(results_df.columns)
#     results_df.to_csv('lstm_predictions_gain_or_loss.csv', columns=output_cols, index=False)
#     print("Predictions vs Actual saved to lstm_predictions_gain_or_loss.csv")

def calculate_price_change_metrics(dataframe, window=5):
    # Calculate price changes
    dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

    # Calculate the max price change in the previous 5 bars
    max_change_prev = dataframe['price_change'].rolling(window=window).max()
    
    # Calculate the max price change in the next 5 bars
    max_change_future = dataframe['price_change'].rolling(window=window).max().shift(-window)
    
    dataframe['max_change_prev'] = max_change_prev
    dataframe['max_change_future'] = max_change_future

    #save to csv
    dataframe.to_csv('price_change_metrics.csv', index=False)

    return dataframe

def categorize_changes(dataframe):
    # Define bins and labels
    bins = [-np.inf, -0.05, -0.04, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, 0.04, 0.05, np.inf]
    labels = ['<-5%', '-4% to -5%', '-3% to -4%', '-2% to -3%', '-1% to -2%', '-1% to 0%',
              '0% to 1%', '1% to 2%', '2% to 3%', '3% to 4%', '4% to 5%', '>5%']
    
    dataframe['category_prev'] = pd.cut(dataframe['max_change_prev'], bins=bins, labels=labels)
    dataframe['category_future'] = pd.cut(dataframe['max_change_future'], bins=bins, labels=labels)

    dataframe.dropna(subset=['category_prev', 'category_future'], inplace=True)

    return dataframe

def create_probability_matrix(dataframe):
    dataframe = categorize_changes(dataframe)
    
    probability_matrix = pd.DataFrame(index=dataframe['category_prev'].cat.categories, 
                                      columns=dataframe['category_future'].cat.categories, data=0.0)

    for _, row in dataframe.iterrows():
        probability_matrix.loc[row['category_prev'], row['category_future']] += 1

    # Normalize each row to sum to 1
    probability_matrix = probability_matrix.div(probability_matrix.sum(axis=1), axis=0).fillna(0)

    return probability_matrix

def save_probability_matrix_to_csv(probability_matrix, filename="probability_matrix.csv"):
    probability_matrix.to_csv(filename)
    print(f"Probability matrix saved to {filename}")
    
def plot_heatmap(matrix):
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(matrix, annot=True, fmt=".2f", cmap="YlGnBu", cbar=True)
    ax.set_xlabel('Current Event')
    ax.set_ylabel('Previous Event')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title("Probability Matrix Heatmap (Max Change over 5 Bars)")
    plt.show()

def main():
    data = fetch_data_from_db()
    transformed_data = transform_data(data)
    calculated_data = calculate_price_change_metrics(transformed_data, window=5)
    probability_matrix = create_probability_matrix(calculated_data)
    save_probability_matrix_to_csv(probability_matrix)

    plot_heatmap(probability_matrix)

if __name__ == "__main__":
    main()