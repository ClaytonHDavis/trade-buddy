import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import psycopg2
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV

def fetch_data_from_db():
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }
    query = "SELECT * FROM public.simplified_trading_data WHERE product_id = 'BTC-USD' ORDER BY start ASC;"
    
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

def preprocess_data(data):
    # Remove missing values
    data.dropna(inplace=True)
    
    # Add lagged features and moving averages
    data = add_features(data)

    # Ensure inclusion of relevant features even after transformation
    selected_features = ['close', 'past_volume_5bars', 'macd_histogram', 'lag_1', 'lag_5', 'lag_10', 'ma_5', 'ma_10']
    X = data[selected_features]

    # Ensure that the future price is available for target creation
    y = data['future_price_5bars']

    # Split into training and testing data manually
    train_size = int(len(data) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    return X_train, X_test, y_train, y_test, data

def add_features(data):
    # Add lagged features
    data['lag_1'] = data['close'].shift(1)
    data['lag_5'] = data['close'].shift(5)
    data['lag_10'] = data['close'].shift(10)

    # Add moving averages
    data['ma_5'] = data['close'].rolling(window=5).mean()
    data['ma_10'] = data['close'].rolling(window=10).mean()

    # Drop NA values created by lagging
    data.dropna(inplace=True)
    return data

def categorize_target(data):
    # Create labels for target variable
    conditions = [
        (data['future_price_5bars'] > 0.05),
        (data['future_price_5bars'] > 0),
        (data['future_price_5bars'] < -0.05),
        (data['future_price_5bars'] <= 0) & (data['future_price_5bars'] >= -0.05)
    ]
    choices = ['Up > 5%', 'Up 0-5%', 'Down > 5%', 'Down 0-5%']
    
    data['price_movement_category'] = np.select(conditions, choices, default='Stable')

    # Optional debugging step: Print counts of each category
    print(data['price_movement_category'].value_counts())
    
    # Save as csv
    data.to_csv('data_with_categories.csv', index=False)

    return data

def train_xgboost(X_train, X_test, y_train, y_test):
    xgb_model = XGBClassifier(n_estimators=100, learning_rate=0.05)
    xgb_model.fit(X_train, y_train)
    
    y_pred = xgb_model.predict(X_test)
    
    # Evaluate performance
    accuracy = accuracy_score(y_test, y_pred)
    print(f"XGBoost - Accuracy: {accuracy}")
    print(classification_report(y_test, y_pred))
    return y_test, y_pred

def train_xgboost_with_grid_search(X_train, X_test, y_train, y_test):
    # Define the parameter grid
    param_grid = {
        'n_estimators': [50, 100, 150],
        'max_depth': [3, 4, 5],
        'learning_rate': [0.01, 0.05, 0.1]
    }

    xgb_model = XGBClassifier(random_state=42)
    grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, cv=3, scoring='accuracy')

    # Fit grid search
    grid_search.fit(X_train, y_train)

    # Use the best estimator to predict
    best_xgb_model = grid_search.best_estimator_
    y_pred = best_xgb_model.predict(X_test)

    # Evaluate performance
    accuracy = accuracy_score(y_test, y_pred)
    print(f"XGBoost GridSearch - Best Parameters: {grid_search.best_params_}")
    print(f"XGBoost with tuned hyperparameters - Accuracy: {accuracy}")
    print(classification_report(y_test, y_pred))

    return y_test, y_pred

def train_and_evaluate_rf(X_train, X_test, y_train, y_test):
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Random Forest - Accuracy: {accuracy}")
    print(confusion_matrix(y_test, y_pred))
    return y_test, y_pred

def normalize_data(X_train, X_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled

def main():
    # Fetch data
    data = fetch_data_from_db()

    # Categorize target variable before dropping 'future_price_5bars'
    data = categorize_target(data)

    # Feature engineering including derived features
    data = add_features(data)

    # Convert categorical labels to numerical labels
    label_encoder = LabelEncoder()
    data['price_movement_category_encoded'] = label_encoder.fit_transform(data['price_movement_category'])

    # Define features and labels after ensuring all features are calculated
    X = data[['lag_1', 'lag_5', 'lag_10']]
    y = data['price_movement_category_encoded']

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # Normalize data
    X_train_scaled, X_test_scaled = normalize_data(X_train, X_test)

    # print the data columns that our model is going to be trained on
    print(X_train.columns)

    # Train models
    y_test_xgb, y_pred_xgb = train_xgboost_with_grid_search(X_train_scaled, X_test_scaled, y_train, y_test)

    # Saving results
    y_test_labels = label_encoder.inverse_transform(y_test_xgb)
    y_pred_labels = label_encoder.inverse_transform(y_pred_xgb)

    results_df = pd.DataFrame({
        'Actual': y_test_labels,
        'Predicted': y_pred_labels
    })
    
    results_df.to_csv('xgboost_predictions.csv', index=False)

    print("Results saved to xgboost_predictions.csv")

# Run the main function
if __name__ == "__main__":
    main()
