import os
import json
from coinbase.rest import RESTClient
from dotenv import load_dotenv

class PortfolioManager:
    def __init__(self):
        # Load environment variables from the .env file
        load_dotenv()
        # Retrieve API keys from environment variables
        api_key = os.getenv("COINBASE_API_KEY").strip()
        api_secret = os.getenv("COINBASE_API_SECRET").strip()
        # Create the REST client
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)

    def list_portfolio(self):
        try:
            # Endpoint to get portfolio details
            response = self.client.get('/api/v3/brokerage/portfolios')
            # Return the first portfolio's UUID, assuming only one for simplicity
            portfolio_uuid = response['portfolios'][0]['uuid']
            return portfolio_uuid
        except Exception as e:
            print(f"Error retrieving portfolio: {e}")
            return None

    def get_portfolio_breakdown(self, portfolio_uuid):
        try:
            # Endpoint to get portfolio breakdown details
            endpoint = f'/api/v3/brokerage/portfolios/{portfolio_uuid}'
            response = self.client.get(endpoint)
            return response
        except Exception as e:
            print(f"Error retrieving portfolio breakdown: {e}")
            return None

    def filter_portfolio(self, data, asset_names, uuid_list, name_filter_mode='exclude', uuid_filter_mode='exclude'):
        try:
            all_positions = data['breakdown']['spot_positions']
            
            # Initial filtering based on asset names
            if name_filter_mode == 'exclude':
                name_filtered_positions = [position for position in all_positions if position['asset'] not in asset_names]
            elif name_filter_mode == 'include':
                name_filtered_positions = [position for position in all_positions if position['asset'] in asset_names]
            else:
                print(f"Unknown name_filter_mode {name_filter_mode}. Defaulting to exclude.")
                name_filtered_positions = [position for position in all_positions if position['asset'] not in asset_names]
            
            # Further filtering based on asset UUIDs
            if uuid_filter_mode == 'exclude':
                uuid_filtered_positions = [position for position in name_filtered_positions if position['account_uuid'] not in uuid_list]
            elif uuid_filter_mode == 'include':
                uuid_filtered_positions = [position for position in name_filtered_positions if position['account_uuid'] in uuid_list]
            else:
                print(f"Unknown uuid_filter_mode {uuid_filter_mode}. Defaulting to exclude.")
                uuid_filtered_positions = [position for position in name_filtered_positions if position['account_uuid'] not in uuid_list]
            
            # Final filtering based on total fiat balance < .01, Filters out DUST
            final_filtered_positions = [position for position in uuid_filtered_positions if float(position.get('total_balance_fiat', 0)) >= 0.01]

            return final_filtered_positions
        except Exception as e:
            print(f"Error filtering and deduplicating portfolio: {e}")
            return []

    def extract_total_cash_balance(self, data):
        try:
            # Extract total cash equivalent balance from portfolio_balances
            total_cash_balance = data['breakdown']['portfolio_balances']['total_cash_equivalent_balance']['value']
            return float(total_cash_balance)
        except Exception as e:
            print(f"Error extracting the total cash balance: {e}")
            return 0.0