import os
import uuid
from coinbase.rest import RESTClient
from dotenv import load_dotenv
from coinbase_portfolio import PortfolioManager

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

if __name__ == "__main__":
    #SHOW PORTFOLIO HERE
    portfolio_manager = PortfolioManager()
    portfolio_uuid = portfolio_manager.list_portfolio()
    portfolio_data = portfolio_manager.get_portfolio_breakdown(portfolio_uuid)
    #filter porfolio on asset names SOL, GALA, DIA
    asset_names = ['SOL', 'GALA', 'DIA','USD','USDC']
    uuid_list = ['6639e955-e2c7-5a51-b140-a0181f2f536b']
    filtered_positions = portfolio_manager.filter_portfolio(portfolio_data, asset_names, uuid_list, name_filter_mode='exclude', uuid_filter_mode='exclude')
    #get the total cash balance
    total_cash = portfolio_manager.extract_total_cash_balance(portfolio_data)
    print(total_cash)

    #print(filtered_positions)