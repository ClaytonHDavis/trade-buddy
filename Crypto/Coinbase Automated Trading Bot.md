# Coinbase Automated Trading Bot

**We've been able to successfully:**

1) Pull live-trading data from coinbase
2) Implement an automated **strategy** base on dynamic criteria and live-trading data
3) Connect to the coinbase API to execute BUY and SELL trades
4) Connect to the coinbase API to retreive my Portfolio

Now we need to connect all these concepts into a single file. The first place to start would probably be just parameterizing the BUY/SELL functions that execute via the coinbase API. The next thing we'd want to do is integrate the CB Portfolio stuff. It's going to be a little annoying with my account just holding a bunch of potential coins, a lot of which I want to just ignore. Perhaps I need to implement an "**Ignore Filter/List**". If I create a ignore list I can just add all the noisy stuff in my porfolio in there and it will just pay attention to the few coins I'm dealing with. Conversly, I could probably just include an "**Attention List**" which makes the program only focus on what's in there, and ignore everything else. Once I get my filtered portfolio, I can get my assets dynamically and use those to calculate my portfolio value, sizes for selling orders, etc.

Loop through spot_positions and SELL market orders of 100% portfolios size. This should eliminate a lot of the noise and then we can keep going from there. If this prooves to be too annoying, then I will move to doing the *focus list* approach.

### Ignore List:

- USDC
- SOL
- GALA

## Code to Retreive Portfolio

```python
import os
import json
from coinbase.rest import RESTClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

def list_portfolio():
    try:
        # Endpoint to get portfolio details
        response = client.get('/api/v3/brokerage/portfolios')
        # Print portfolio data
        print(json.dumps(response, indent=4))  # Pretty-print JSON response

        # Return the first portfolio's UUID, assuming only one for simplicity
        portfolio_uuid = response['portfolios'][0]['uuid']
        return portfolio_uuid

    except Exception as e:
        print(f"Error retrieving portfolio: {e}")
        return None

def get_portfolio_breakdown(portfolio_uuid):
    try:
        # Endpoint to get portfolio breakdown details
        endpoint = f'/api/v3/brokerage/portfolios/{portfolio_uuid}'
        response = client.get(endpoint)

        # Print breakdown data
        print(json.dumps(response, indent=4))  # Pretty-print JSON response

    except Exception as e:
        print(f"Error retrieving portfolio breakdown: {e}")

if __name__ == "__main__":
    portfolio_uuid = list_portfolio()
    if portfolio_uuid:
        get_portfolio_breakdown(portfolio_uuid)
```



*Write a cleanup program to sell off all this fractional crap.*

```json
{
    "portfolios": [
        {
            "name": "Default",
            "uuid": "693507be-ae62-5846-adbc-2426e38ced1e",
            "type": "DEFAULT",
            "deleted": false
        }
    ]
}
{
    "breakdown": {
        "portfolio": {
            "name": "Default",
            "uuid": "693507be-ae62-5846-adbc-2426e38ced1e",
            "type": "DEFAULT",
            "deleted": false
        },
        "portfolio_balances": {
            "total_balance": {
                "value": "428.53",
                "currency": "USD"
            },
            "total_futures_balance": {
                "value": "0",
                "currency": "USD"
            },
            "total_cash_equivalent_balance": {
                "value": "6.13",
                "currency": "USD"
            },
            "total_crypto_balance": {
                "value": "422.4",
                "currency": "USD"
            },
            "futures_unrealized_pnl": {
                "value": "0",
                "currency": "USD"
            },
            "perp_unrealized_pnl": {
                "value": "0",
                "currency": "USD"
            }
        },
        "spot_positions": [
            {
                "asset": "USDC",
                "account_uuid": "077edb61-2a1f-5053-bfb3-48c678e9cb4b",
                "total_balance_fiat": 0.020344,
                "total_balance_crypto": 0.020344,
                "available_to_trade_fiat": 0.020344,
                "allocation": 4.7473055e-05,
                "cost_basis": {
                    "value": "0.020344",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/3c15df5e2ac7d4abbe9499ed9335041f00c620f28e8de2f93474a9f432058742cdf4674bd43f309e69778a26969372310135be97eb183d91c492154176d455b8/asset_icons/9d67b728b6c8f457717154b3a35f9ddc702eae7e76c4684ee39302c4d7fd0bb8.png",
                "is_cash": true,
                "average_entry_price": {
                    "value": "1.00",
                    "currency": "USD"
                },
                "asset_uuid": "2b92315d-eab7-5bef-84fa-089a131333f5",
                "available_to_trade_crypto": 0.020344,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.020344,
                "available_to_transfer_crypto": 0.020344,
                "asset_color": "#2775CA"
            },
            {
                "asset": "SHIB",
                "account_uuid": "3158d6bc-0103-5516-93d9-1d54aedb0f07",
                "total_balance_fiat": 1.4905573e-05,
                "total_balance_crypto": 0.57318103,
                "available_to_trade_fiat": 1.4905573e-05,
                "allocation": 3.47824e-08,
                "cost_basis": {
                    "value": "0.000010452228746953463940435",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/c14c8dc36c003113c898b56dfff649eb0ff71249fd7c8a9de724edb2dedfedde5562ba4a194db8433f2ef31a1e879af0727e6632751539707b17e66d63a9013b/asset_icons/a7309384448163db7e3e9fded23cd6ecf3ea6e1fb3800cab216acb7fc85f9563.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.00",
                    "currency": "USD"
                },
                "asset_uuid": "d6031388-71ab-59c7-8a15-a56ec20d6080",
                "available_to_trade_crypto": 0.57318103,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 1.4905573e-05,
                "available_to_transfer_crypto": 0.57318103,
                "asset_color": "#1C2951"
            },
            {
                "asset": "WAXL",
                "account_uuid": "5e893b9f-de82-5bca-81bc-9f8eac93b04d",
                "total_balance_fiat": 0.008396485,
                "total_balance_crypto": 0.008865,
                "available_to_trade_fiat": 0.008396485,
                "allocation": 1.9593333e-05,
                "cost_basis": {
                    "value": "0.0066851546335457319855",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/393455a2b1993abf3d02f2ac3bd7e14ac91d962cea250ac0790ae5c5419e184786a26afeecff0be7028dd293153b24de7e072ac9a95426f20a2389405365c9ee/asset_icons/752350fddaef1eaadd45fb3c929ce4fb571bebd21ab4b58b8d1c87ffe7b18ae7.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.71",
                    "currency": "USD"
                },
                "asset_uuid": "afb7c221-a5f4-4ddd-ba23-61e627dad8b6",
                "available_to_trade_crypto": 0.008865,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.008396485,
                "available_to_transfer_crypto": 0.008865,
                "asset_color": "#0A0B0D"
            },
            {
                "asset": "USD",
                "account_uuid": "65acdd48-5949-5583-b58b-54d36c82222a",
                "total_balance_fiat": 6.1117268,
                "total_balance_crypto": 6.1117268,
                "available_to_trade_fiat": 6.1117268,
                "allocation": 0.014261814,
                "cost_basis": {
                    "value": "6.1117267764987602",
                    "currency": "USD"
                },
                "asset_img_url": "",
                "is_cash": true,
                "average_entry_price": {
                    "value": "1.00",
                    "currency": "USD"
                },
                "asset_uuid": "",
                "available_to_trade_crypto": 6.1117268,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 6.1117268,
                "available_to_transfer_crypto": 6.1117268,
                "asset_color": ""
            },
            {
                "asset": "SOL",
                "account_uuid": "6639e955-e2c7-5a51-b140-a0181f2f536b",
                "total_balance_fiat": 0.92699736,
                "total_balance_crypto": 0.003818418,
                "available_to_trade_fiat": 0,
                "allocation": 0.0021631634,
                "cost_basis": {
                    "value": "0.5205909326985894491786138",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/b658adaf7913c1513c8d120bcb41934a5a4bf09b6adbcb436085e2fbf6eb128c.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "131.43",
                    "currency": "USD"
                },
                "asset_uuid": "4f039497-3af8-5bb3-951c-6df9afa9be1c",
                "available_to_trade_crypto": 0,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0,
                "available_to_transfer_crypto": 0,
                "asset_color": "#9945FF"
            },
            {
                "asset": "VELO",
                "account_uuid": "6a8907e9-19d2-5d05-90de-5e654df174ce",
                "total_balance_fiat": 0.008225813,
                "total_balance_crypto": 0.06872598,
                "available_to_trade_fiat": 0.008225813,
                "allocation": 1.9195068e-05,
                "cost_basis": {
                    "value": "0.007602017055802961821705",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/f61c887898ac0902737bba0f4d5d460bd1b64247c34e6bf7b506052d39b1adf9.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.11",
                    "currency": "USD"
                },
                "asset_uuid": "5defc2a7-682c-41a5-89d4-049044cc00b8",
                "available_to_trade_crypto": 0.06872598,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.008225813,
                "available_to_transfer_crypto": 0.06872598,
                "asset_color": "#5E93FF"
            },
            {
                "asset": "SOL",
                "account_uuid": "8e0e84a6-d45e-5589-91af-0e819bb99076",
                "total_balance_fiat": 409.38126,
                "total_balance_crypto": 1.6862926,
                "available_to_trade_fiat": 409.38126,
                "allocation": 0.9552978,
                "cost_basis": {
                    "value": "409.8148890449766",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/b658adaf7913c1513c8d120bcb41934a5a4bf09b6adbcb436085e2fbf6eb128c.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "242.18",
                    "currency": "USD"
                },
                "asset_uuid": "4f039497-3af8-5bb3-951c-6df9afa9be1c",
                "available_to_trade_crypto": 1.6862926,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 409.38126,
                "available_to_transfer_crypto": 1.6862926,
                "asset_color": "#9945FF"
            },
            {
                "asset": "ORCA",
                "account_uuid": "9a7bca7f-6521-5e72-ba37-55c507ffa787",
                "total_balance_fiat": 0.01269918,
                "total_balance_crypto": 0.003618,
                "available_to_trade_fiat": 0.01269918,
                "allocation": 2.9633744e-05,
                "cost_basis": {
                    "value": "0.01077488809884377987904",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/dd05661e865e97a78942d6684aa1a90cb28db91e48d33942714f395e75a1a2344ed577d0228d0cae4be2f6e74af774479bbf1c7c1690f13c9f0a1c87dd684efc/asset_icons/49435e1926043887024ed42b2dd3c3a07b096bf08f419d40e22555b9d953ec32.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "2.97",
                    "currency": "USD"
                },
                "asset_uuid": "ba24ad7b-0a8b-533d-816b-e693d9f8a871",
                "available_to_trade_crypto": 0.003618,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.01269918,
                "available_to_transfer_crypto": 0.003618,
                "asset_color": "#000000"
            },
            {
                "asset": "DIA",
                "account_uuid": "aa3b2fe5-1987-5782-ba0d-76769fe2c58e",
                "total_balance_fiat": 1.6961151,
                "total_balance_crypto": 2.0018828,
                "available_to_trade_fiat": 1.6961151,
                "allocation": 0.0039579123,
                "cost_basis": {
                    "value": "1.716633933595277011185",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/d157c473ff0b5272766f761e27e65ac276cbff13404053f55a6564b6347c82c2d6838128005390c5fe8735797e78784e4ae5f27f37a402b1b1ae7ff4b7f0a6e2/asset_icons/8330a8c0463b726ab615976b5d060a49f89b91a71d80adeb9483db5185d540e4.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.85",
                    "currency": "USD"
                },
                "asset_uuid": "d8d9de8a-d13b-57bc-99cb-b1d546f820d6",
                "available_to_trade_crypto": 2.0018828,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 1.6961151,
                "available_to_transfer_crypto": 2.0018828,
                "asset_color": "#6666FF"
            },
            {
                "asset": "KARRAT",
                "account_uuid": "b09d1ef0-2a6f-5a37-a76b-06675f0e8c0b",
                "total_balance_fiat": 0.0001647787,
                "total_balance_crypto": 0.00033461,
                "available_to_trade_fiat": 0.0001647787,
                "allocation": 3.8451375e-07,
                "cost_basis": {
                    "value": "0.00015991600000005398733804948273",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/be94d66c76017a87764038e7491d5fc34fadf6f209c9527fe543685dae224817.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.48",
                    "currency": "USD"
                },
                "asset_uuid": "5671503a-afbe-406b-834d-94b6e9b3afc2",
                "available_to_trade_crypto": 0.00033461,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.0001647787,
                "available_to_transfer_crypto": 0.00033461,
                "asset_color": "#EBBB58"
            },
            {
                "asset": "GALA",
                "account_uuid": "b6e33cd8-5bf0-5c5b-9b43-88401449ec9f",
                "total_balance_fiat": 3.315092,
                "total_balance_crypto": 83.45304,
                "available_to_trade_fiat": 0,
                "allocation": 0.0077358214,
                "cost_basis": {
                    "value": "21.033860424962255861928942",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/a614984dea35ab94f5d195872ba6b3d7c5fa3afb94e0e596370ea3456c22d9e461fa09ce8d2cbf469695ddaee49b794e1c313c24b193aa29aa4e11733cbb12ac/asset_icons/00ecfc90aeeb27b666dda948bfd5dbd884197bc96c181e8e684fd97999243c2e.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.24",
                    "currency": "USD"
                },
                "asset_uuid": "fa0bd074-1230-5a14-bdd3-15f5c9600d8d",
                "available_to_trade_crypto": 0,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 3.315092,
                "available_to_transfer_crypto": 83.45304,
                "asset_color": "#0A0B0D"
            },
            {
                "asset": "CLV",
                "account_uuid": "b9f6296c-bade-5708-8ee4-41d9f3a6b42f",
                "total_balance_fiat": 0.2746297,
                "total_balance_crypto": 3.082264,
                "available_to_trade_fiat": 0.2746297,
                "allocation": 0.0006408529,
                "cost_basis": {
                    "value": "3.005207244",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/2a43e81b3aa4ed326b3403253912cde99823a7bfab1e3df4aa42783a0e418c689663455524e679b892871a0c304a1025ec831c7eec619a7dca4b43a2e7df0b34/asset_icons/556d89987c2bf38e5b8d2a71636215c78cb3398ff7cf99219f67741b36a892cd.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.98",
                    "currency": "USD"
                },
                "asset_uuid": "453639be-192e-5e36-88e3-38496e542524",
                "available_to_trade_crypto": 3.082264,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.2746297,
                "available_to_transfer_crypto": 3.082264,
                "asset_color": "#42C37B"
            },
            {
                "asset": "ATOM",
                "account_uuid": "c60e9751-26d6-590e-9200-6bbb969667fb",
                "total_balance_fiat": 6.630313,
                "total_balance_crypto": 0.78045,
                "available_to_trade_fiat": 0.021807948,
                "allocation": 0.015471944,
                "cost_basis": {
                    "value": "23.162484522848277719811",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/b92276a1f003b87191983dab71970a9a6d522dde514176e5880a75055af1e67ce5f153b96a2ee5ecd22729a73d3a8739b248d853bde74ab6e643bef2d1b4f88d/asset_icons/9c760bf25bca9823f9ef8d651681b779aadc71a2f543f931070034e59ef10120.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "27.77",
                    "currency": "USD"
                },
                "asset_uuid": "64c607d2-4663-5649-86e0-3ab06bba0202",
                "available_to_trade_crypto": 0.002567,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.021807948,
                "available_to_transfer_crypto": 0.002567,
                "asset_color": "#2E3148"
            },
            {
                "asset": "XLM",
                "account_uuid": "cc9f2dd8-643f-54d9-aa00-f5a771066e2e",
                "total_balance_fiat": 0.0051808637,
                "total_balance_crypto": 0.0097245,
                "available_to_trade_fiat": 0.0051808637,
                "allocation": 1.2089629e-05,
                "cost_basis": {
                    "value": "0.00225583759999995048483123176475",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/ddaf9d27a2388105c5568c68ebe4078d057efac1cb9b091af6a57f4d187cf06b2701b95f75bd148d3872df32b69ebb678de71a42da317370aaec7d6448bda379/asset_icons/80782fe2d690f299e7f5bb9b89af87e1db75769e59c14fa0257054c962401805.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.23",
                    "currency": "USD"
                },
                "asset_uuid": "13b83335-5ede-595b-821e-5bcdfa80560f",
                "available_to_trade_crypto": 0.0097245,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.0051808637,
                "available_to_transfer_crypto": 0.0097245,
                "asset_color": "#000000"
            },
            {
                "asset": "GRT",
                "account_uuid": "d2d07f09-bc96-51dc-9739-036d92a16533",
                "total_balance_fiat": 0.0007725453,
                "total_balance_crypto": 0.00284233,
                "available_to_trade_fiat": 0.0007725453,
                "allocation": 1.802747e-06,
                "cost_basis": {
                    "value": "0.001785835939",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/dde480c562f5c7400ba4bfa55423a2a40584e18648a6b1b3470c116fc949e201.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "0.63",
                    "currency": "USD"
                },
                "asset_uuid": "3f9b015d-387d-589b-b65d-bd6d24babc96",
                "available_to_trade_crypto": 0.00284233,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.0007725453,
                "available_to_transfer_crypto": 0.00284233,
                "asset_color": "#5227E8"
            },
            {
                "asset": "MATIC",
                "account_uuid": "d8a407a4-2036-5172-9874-920fa6e392cd",
                "total_balance_fiat": 0.033437222,
                "total_balance_crypto": 0.05845668,
                "available_to_trade_fiat": 0.033437222,
                "allocation": 7.80263e-05,
                "cost_basis": {
                    "value": "0.11543602298373518473044",
                    "currency": "USD"
                },
                "asset_img_url": "https://dynamic-assets.coinbase.com/085ce26e1eba2ccb210ea85df739a0ca2ef782747e47d618c64e92b168b94512df469956de1b667d93b2aa05ce77947e7bf1b4e0c7276371aa88ef9406036166/asset_icons/57f28803aad363f419a950a5f5b99acfd4fba8b683c01b9450baab43c9fa97ea.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "1.90",
                    "currency": "USD"
                },
                "asset_uuid": "026bcc1e-9163-591c-a709-34dd18b2e7a1",
                "available_to_trade_crypto": 0.05845668,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.033437222,
                "available_to_transfer_crypto": 0.05845668,
                "asset_color": "#8247E5"
            },
            {
                "asset": "AERO",
                "account_uuid": "e87528b6-f1d7-5e08-ac9e-975176749ffd",
                "total_balance_fiat": 0.11246087,
                "total_balance_crypto": 0.07934559,
                "available_to_trade_fiat": 0.11246087,
                "allocation": 0.00026242927,
                "cost_basis": {
                    "value": "0.092739505445482494438015",
                    "currency": "USD"
                },
                "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/93b9f25ca937680b4b95a49a3e50aa614c039ff1ad0abed2bf59d24fbcb99b80.png",
                "is_cash": false,
                "average_entry_price": {
                    "value": "1.17",
                    "currency": "USD"
                },
                "asset_uuid": "9476e3be-b731-47fa-82be-347fabc573d9",
                "available_to_trade_crypto": 0.07934559,
                "unrealized_pnl": 0,
                "available_to_transfer_fiat": 0.11246087,
                "available_to_transfer_crypto": 0.07934559,
                "asset_color": "#0433FF"
            }
        ],
        "perp_positions": [],
        "futures_positions": []
    }
}
```

---

### Scratch Pad

```json
/usr/local/bin/python3 /Users/claytondavis/Desktop/trade-buddy/trade-buddy/Crypto/coinbase_portfolio.py
claytondavis@Claytons-MacBook-Air trade-buddy % /usr/local/bin/python3 /Users/claytondavis/Desktop/trade-buddy/trade-buddy/Crypto/coinbase_portf
olio.py
Filtered Portfolio:
[
    {
        "asset": "USDC",
        "account_uuid": "077edb61-2a1f-5053-bfb3-48c678e9cb4b",
        "total_balance_fiat": 0.020344,
        "total_balance_crypto": 0.020344,
        "available_to_trade_fiat": 0.020344,
        "allocation": 4.7902115e-05,
        "cost_basis": {
            "value": "0.020344",
            "currency": "USD"
        },
        "asset_img_url": "https://dynamic-assets.coinbase.com/3c15df5e2ac7d4abbe9499ed9335041f00c620f28e8de2f93474a9f432058742cdf4674bd43f309e69778a26969372310135be97eb183d91c492154176d455b8/asset_icons/9d67b728b6c8f457717154b3a35f9ddc702eae7e76c4684ee39302c4d7fd0bb8.png",
        "is_cash": true,
        "average_entry_price": {
            "value": "1.00",
            "currency": "USD"
        },
        "asset_uuid": "2b92315d-eab7-5bef-84fa-089a131333f5",
        "available_to_trade_crypto": 0.020344,
        "unrealized_pnl": 0,
        "available_to_transfer_fiat": 0.020344,
        "available_to_transfer_crypto": 0.020344,
        "asset_color": "#2775CA"
    },
    {
        "asset": "USD",
        "account_uuid": "65acdd48-5949-5583-b58b-54d36c82222a",
        "total_balance_fiat": 6.9711328,
        "total_balance_crypto": 6.9711328,
        "available_to_trade_fiat": 6.9711328,
        "allocation": 0.016414275,
        "cost_basis": {
            "value": "6.9711325264987602",
            "currency": "USD"
        },
        "asset_img_url": "",
        "is_cash": true,
        "average_entry_price": {
            "value": "1.00",
            "currency": "USD"
        },
        "asset_uuid": "",
        "available_to_trade_crypto": 6.9711328,
        "unrealized_pnl": 0,
        "available_to_transfer_fiat": 6.9711328,
        "available_to_transfer_crypto": 6.9711328,
        "asset_color": ""
    },
    {
        "asset": "SOL",
        "account_uuid": "8e0e84a6-d45e-5589-91af-0e819bb99076",
        "total_balance_fiat": 405.00534,
        "total_balance_crypto": 1.6862926,
        "available_to_trade_fiat": 405.00534,
        "allocation": 0.95362824,
        "cost_basis": {
            "value": "409.8148890449766",
            "currency": "USD"
        },
        "asset_img_url": "https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/b658adaf7913c1513c8d120bcb41934a5a4bf09b6adbcb436085e2fbf6eb128c.png",
        "is_cash": false,
        "average_entry_price": {
            "value": "242.18",
            "currency": "USD"
        },
        "asset_uuid": "4f039497-3af8-5bb3-951c-6df9afa9be1c",
        "available_to_trade_crypto": 1.6862926,
        "unrealized_pnl": 0,
        "available_to_transfer_fiat": 405.00534,
        "available_to_transfer_crypto": 1.6862926,
        "asset_color": "#9945FF"
    },
    {
        "asset": "GALA",
        "account_uuid": "b6e33cd8-5bf0-5c5b-9b43-88401449ec9f",
        "total_balance_fiat": 3.6157157,
        "total_balance_crypto": 83.45304,
        "available_to_trade_fiat": 0,
        "allocation": 0.008513588,
        "cost_basis": {
            "value": "21.033860424962255861928942",
            "currency": "USD"
        },
        "asset_img_url": "https://dynamic-assets.coinbase.com/a614984dea35ab94f5d195872ba6b3d7c5fa3afb94e0e596370ea3456c22d9e461fa09ce8d2cbf469695ddaee49b794e1c313c24b193aa29aa4e11733cbb12ac/asset_icons/00ecfc90aeeb27b666dda948bfd5dbd884197bc96c181e8e684fd97999243c2e.png",
        "is_cash": false,
        "average_entry_price": {
            "value": "0.24",
            "currency": "USD"
        },
        "asset_uuid": "fa0bd074-1230-5a14-bdd3-15f5c9600d8d",
        "available_to_trade_crypto": 0,
        "unrealized_pnl": 0,
        "available_to_transfer_fiat": 3.6157157,
        "available_to_transfer_crypto": 83.45304,
        "asset_color": "#0A0B0D"
    }
]

Total Cash Equivalent Balance:
6.99
claytondavis@Claytons-MacBook-Air trade-buddy % 
```



## Portfolio Class Implementation

*This is working.*

```python
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
    print(filtered_positions)
```

*Output*

```json
[{'asset': 'ORCA', 'account_uuid': '9a7bca7f-6521-5e72-ba37-55c507ffa787', 'total_balance_fiat': 0.012838473, 'total_balance_crypto': 0.003618, 'available_to_trade_fiat': 0.012838473, 'allocation': 3.0266692e-05, 'cost_basis': {'value': '0.01077488809884377987904', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/dd05661e865e97a78942d6684aa1a90cb28db91e48d33942714f395e75a1a2344ed577d0228d0cae4be2f6e74af774479bbf1c7c1690f13c9f0a1c87dd684efc/asset_icons/49435e1926043887024ed42b2dd3c3a07b096bf08f419d40e22555b9d953ec32.png', 'is_cash': False, 'average_entry_price': {'value': '2.97', 'currency': 'USD'}, 'asset_uuid': 'ba24ad7b-0a8b-533d-816b-e693d9f8a871', 'available_to_trade_crypto': 0.003618, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.012838473, 'available_to_transfer_crypto': 0.003618, 'asset_color': '#000000'}, {'asset': 'CLV', 'account_uuid': 'b9f6296c-bade-5708-8ee4-41d9f3a6b42f', 'total_balance_fiat': 0.27355093, 'total_balance_crypto': 3.082264, 'available_to_trade_fiat': 0.27355093, 'allocation': 0.0006448961, 'cost_basis': {'value': '3.005207244', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/2a43e81b3aa4ed326b3403253912cde99823a7bfab1e3df4aa42783a0e418c689663455524e679b892871a0c304a1025ec831c7eec619a7dca4b43a2e7df0b34/asset_icons/556d89987c2bf38e5b8d2a71636215c78cb3398ff7cf99219f67741b36a892cd.png', 'is_cash': False, 'average_entry_price': {'value': '0.98', 'currency': 'USD'}, 'asset_uuid': '453639be-192e-5e36-88e3-38496e542524', 'available_to_trade_crypto': 3.082264, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.27355093, 'available_to_transfer_crypto': 3.082264, 'asset_color': '#42C37B'}, {'asset': 'ATOM', 'account_uuid': 'c60e9751-26d6-590e-9200-6bbb969667fb', 'total_balance_fiat': 6.8570337, 'total_balance_crypto': 0.78045, 'available_to_trade_fiat': 0.022553662, 'allocation': 0.016165452, 'cost_basis': {'value': '23.162484522848277719811', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/b92276a1f003b87191983dab71970a9a6d522dde514176e5880a75055af1e67ce5f153b96a2ee5ecd22729a73d3a8739b248d853bde74ab6e643bef2d1b4f88d/asset_icons/9c760bf25bca9823f9ef8d651681b779aadc71a2f543f931070034e59ef10120.png', 'is_cash': False, 'average_entry_price': {'value': '27.77', 'currency': 'USD'}, 'asset_uuid': '64c607d2-4663-5649-86e0-3ab06bba0202', 'available_to_trade_crypto': 0.002567, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.022553662, 'available_to_transfer_crypto': 0.002567, 'asset_color': '#2E3148'}, {'asset': 'MATIC', 'account_uuid': 'd8a407a4-2036-5172-9874-920fa6e392cd', 'total_balance_fiat': 0.035018474, 'total_balance_crypto': 0.05845668, 'available_to_trade_fiat': 0.035018474, 'allocation': 8.255603e-05, 'cost_basis': {'value': '0.11543602298373518473044', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/085ce26e1eba2ccb210ea85df739a0ca2ef782747e47d618c64e92b168b94512df469956de1b667d93b2aa05ce77947e7bf1b4e0c7276371aa88ef9406036166/asset_icons/57f28803aad363f419a950a5f5b99acfd4fba8b683c01b9450baab43c9fa97ea.png', 'is_cash': False, 'average_entry_price': {'value': '1.90', 'currency': 'USD'}, 'asset_uuid': '026bcc1e-9163-591c-a709-34dd18b2e7a1', 'available_to_trade_crypto': 0.05845668, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.035018474, 'available_to_transfer_crypto': 0.05845668, 'asset_color': '#8247E5'}, {'asset': 'AERO', 'account_uuid': 'e87528b6-f1d7-5e08-ac9e-975176749ffd', 'total_balance_fiat': 0.1158882, 'total_balance_crypto': 0.07934559, 'available_to_trade_fiat': 0.1158882, 'allocation': 0.00027320636, 'cost_basis': {'value': '0.092739505445482494438015', 'currency': 'USD'}, 'asset_img_url': 'https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/93b9f25ca937680b4b95a49a3e50aa614c039ff1ad0abed2bf59d24fbcb99b80.png', 'is_cash': False, 'average_entry_price': {'value': '1.17', 'currency': 'USD'}, 'asset_uuid': '9476e3be-b731-47fa-82be-347fabc573d9', 'available_to_trade_crypto': 0.07934559, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.1158882, 'available_to_transfer_crypto': 0.07934559, 'asset_color': '#0433FF'}]
```

*Buy/Sell Modularization*

```python
from coinbase_make_transactions import place_market_order

if __name__ == "__main__":
    place_market_order('DIA-USD', 1, 'BUY')
```

*Results*

```json
Order placed successfully. Response: {'success': True, 'success_response': {'order_id': 'e5f9d109-c750-4535-9cc0-a02ffa2f3137', 'product_id': 'DIA-USD', 'side': 'BUY', 'client_order_id': '7ef133d0-1d9a-41e7-ae6c-0af02c46af39', 'attached_order_id': ''}, 'order_configuration': {'market_market_ioc': {'base_size': '1', 'rfq_enabled': False, 'rfq_disabled': False}}}
```



---

## Integration

- **Need to merge trader.portfolio and portfolio_manager.filter_portfolio**
  - Most important things are to extract asset IDs. Then make sure they have "-USD" (-currency) added to the end so that it can be easily traded with the API.
  - the size of the positions should be grabbed from the total_balance_crypto field
  - Total porfolio value should be available_to_trade_fiat for each coin


*trader.portfolio*

```python
Current portfolio: {'SOL-USD': np.float64(2.4640213040258004e-06), 'LTC-USD': np.float64(5.267299042395793e-08), 'BTC-USD': np.float64(6.563458385564957e-05), 'SHIB-USD': np.float64(13920.709584756922), 'ETH-USD': np.float64(9.785615643887327e-06)}
```

*portfolio_manager.filter_portfolio*

```json
[{'asset': 'ORCA', 'account_uuid': '9a7bca7f-6521-5e72-ba37-55c507ffa787', 'total_balance_fiat': 0.012838473, 'total_balance_crypto': 0.003618, 'available_to_trade_fiat': 0.012838473, 'allocation': 3.0266692e-05, 'cost_basis': {'value': '0.01077488809884377987904', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/dd05661e865e97a78942d6684aa1a90cb28db91e48d33942714f395e75a1a2344ed577d0228d0cae4be2f6e74af774479bbf1c7c1690f13c9f0a1c87dd684efc/asset_icons/49435e1926043887024ed42b2dd3c3a07b096bf08f419d40e22555b9d953ec32.png', 'is_cash': False, 'average_entry_price': {'value': '2.97', 'currency': 'USD'}, 'asset_uuid': 'ba24ad7b-0a8b-533d-816b-e693d9f8a871', 'available_to_trade_crypto': 0.003618, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.012838473, 'available_to_transfer_crypto': 0.003618, 'asset_color': '#000000'}, {'asset': 'CLV', 'account_uuid': 'b9f6296c-bade-5708-8ee4-41d9f3a6b42f', 'total_balance_fiat': 0.27355093, 'total_balance_crypto': 3.082264, 'available_to_trade_fiat': 0.27355093, 'allocation': 0.0006448961, 'cost_basis': {'value': '3.005207244', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/2a43e81b3aa4ed326b3403253912cde99823a7bfab1e3df4aa42783a0e418c689663455524e679b892871a0c304a1025ec831c7eec619a7dca4b43a2e7df0b34/asset_icons/556d89987c2bf38e5b8d2a71636215c78cb3398ff7cf99219f67741b36a892cd.png', 'is_cash': False, 'average_entry_price': {'value': '0.98', 'currency': 'USD'}, 'asset_uuid': '453639be-192e-5e36-88e3-38496e542524', 'available_to_trade_crypto': 3.082264, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.27355093, 'available_to_transfer_crypto': 3.082264, 'asset_color': '#42C37B'}, {'asset': 'ATOM', 'account_uuid': 'c60e9751-26d6-590e-9200-6bbb969667fb', 'total_balance_fiat': 6.8570337, 'total_balance_crypto': 0.78045, 'available_to_trade_fiat': 0.022553662, 'allocation': 0.016165452, 'cost_basis': {'value': '23.162484522848277719811', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/b92276a1f003b87191983dab71970a9a6d522dde514176e5880a75055af1e67ce5f153b96a2ee5ecd22729a73d3a8739b248d853bde74ab6e643bef2d1b4f88d/asset_icons/9c760bf25bca9823f9ef8d651681b779aadc71a2f543f931070034e59ef10120.png', 'is_cash': False, 'average_entry_price': {'value': '27.77', 'currency': 'USD'}, 'asset_uuid': '64c607d2-4663-5649-86e0-3ab06bba0202', 'available_to_trade_crypto': 0.002567, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.022553662, 'available_to_transfer_crypto': 0.002567, 'asset_color': '#2E3148'}, {'asset': 'MATIC', 'account_uuid': 'd8a407a4-2036-5172-9874-920fa6e392cd', 'total_balance_fiat': 0.035018474, 'total_balance_crypto': 0.05845668, 'available_to_trade_fiat': 0.035018474, 'allocation': 8.255603e-05, 'cost_basis': {'value': '0.11543602298373518473044', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/085ce26e1eba2ccb210ea85df739a0ca2ef782747e47d618c64e92b168b94512df469956de1b667d93b2aa05ce77947e7bf1b4e0c7276371aa88ef9406036166/asset_icons/57f28803aad363f419a950a5f5b99acfd4fba8b683c01b9450baab43c9fa97ea.png', 'is_cash': False, 'average_entry_price': {'value': '1.90', 'currency': 'USD'}, 'asset_uuid': '026bcc1e-9163-591c-a709-34dd18b2e7a1', 'available_to_trade_crypto': 0.05845668, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.035018474, 'available_to_transfer_crypto': 0.05845668, 'asset_color': '#8247E5'}, {'asset': 'AERO', 'account_uuid': 'e87528b6-f1d7-5e08-ac9e-975176749ffd', 'total_balance_fiat': 0.1158882, 'total_balance_crypto': 0.07934559, 'available_to_trade_fiat': 0.1158882, 'allocation': 0.00027320636, 'cost_basis': {'value': '0.092739505445482494438015', 'currency': 'USD'}, 'asset_img_url': 'https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/93b9f25ca937680b4b95a49a3e50aa614c039ff1ad0abed2bf59d24fbcb99b80.png', 'is_cash': False, 'average_entry_price': {'value': '1.17', 'currency': 'USD'}, 'asset_uuid': '9476e3be-b731-47fa-82be-347fabc573d9', 'available_to_trade_crypto': 0.07934559, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.1158882, 'available_to_transfer_crypto': 0.07934559, 'asset_color': '#0433FF'}]
```

### Current code:

```python
import os
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient  # Import RESTClient from coinbase.rest
from coinbase_portfolio import PortfolioManager

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Does not change
def fetch_historical_data(product_id, granularity='ONE_MINUTE', limit=300):
    try:
        # Calculate start and end times
        now = int(time.time())
        granularity_seconds_map = {
            'ONE_MINUTE': 60,
            'FIVE_MINUTE': 300,
            'FIFTEEN_MINUTE': 900,
            'THIRTY_MINUTE': 1800,
            'ONE_HOUR': 3600,
            'TWO_HOUR': 7200,
            'SIX_HOUR': 21600,
            'ONE_DAY': 86400,
        }
        if granularity not in granularity_seconds_map:
            raise ValueError(f"Unsupported granularity: {granularity}")
        interval_seconds = granularity_seconds_map[granularity]
        total_seconds = interval_seconds * limit
        start = now - total_seconds
        end = now

        # Create the request URL and parameters
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        # Fetch candle data using RESTClient
        response = client.get(url, params=params)

        # Extract candles
        candles = response.get('candles', [])
        if not candles:
            print(f"No candle data returned for {product_id}")
            return pd.DataFrame()

        # Prepare DataFrame
        df_candles = pd.DataFrame(candles)

        # Convert 'start' to datetime
        df_candles['start'] = pd.to_datetime(df_candles['start'], unit='s')

        # Rename 'start' to 'time' to match previous code
        df_candles.rename(columns={'start': 'time'}, inplace=True)

        # Ensure correct data types
        float_columns = ['low', 'high', 'open', 'close', 'volume']
        df_candles[float_columns] = df_candles[float_columns].astype(float)

        # Reorder columns if necessary
        df_candles = df_candles[['time', 'low', 'high', 'open', 'close', 'volume']]

        # Sort the DataFrame by time
        df_candles = df_candles.sort_values(by='time').reset_index(drop=True)

        return df_candles
    except Exception as e:
        print(f"Error fetching data for {product_id}: {e}")
        return pd.DataFrame()

# Does not change
def get_bar_data(symbol, granularity='ONE_MINUTE', limit=300):
    return fetch_historical_data(symbol, granularity, limit)

#Does not change
def save_market_data_to_csv(df_candles, coin, file_name_prefix="market_data"):
    try:
        file_name = f"{file_name_prefix}_{coin.replace('-', '_')}.csv"
        df_candles.to_csv(file_name, index=False)
        print(f"Market data for {coin} saved to {file_name}")
    except Exception as e:
        print(f"Error saving market data for {coin} to CSV: {e}")


class PaperTrader:
    def __init__(self, initial_cash, commission_rate, params):
        self.cash = initial_cash
        self.portfolio = {}
        self.commission_rate = commission_rate
        self.trade_log = []
        self.last_purchase_info = {}  # Use this to store purchase details

        # Set strategy parameters
        self.params = params

    # this can be retrieved from the portfolio class
    def calculate_total_portfolio_value(self, market_data):
        total_value = self.cash  # Start with current cash balance
        for coin, quantity in self.portfolio.items():
            if quantity > 0:
                # Get the current market price for this coin
                if coin in market_data and not market_data[coin].empty:
                    price = market_data[coin]['close'].iloc[0]
                    total_value += quantity * price
        print(f"Total portfolio value: {total_value:.2f}")
        return total_value

    def save_trade_log_to_csv(self, file_name="trade_log.csv"):
        try:
            df_trade_log = pd.DataFrame(self.trade_log)
            df_trade_log.to_csv(file_name, index=False)
            print(f"Trade log saved to {file_name}")
        except Exception as e:
            print(f"Error saving trade log to CSV: {e}")

    def buy(self, coin, price, quantity):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
        trade_datetime = datetime.now()  # Capture current datetime
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.portfolio[coin] = self.portfolio.get(coin, 0) + quantity
            # this can be replaced. Will come from Portfolio class.
            self.last_purchase_info[coin] = {
                'price': price,
                'quantity': quantity,
                'commission': commission_fee,
                'datetime': trade_datetime
            }
            # Log the trade with datetime
            self.log_trade('Buy', coin, price, quantity, trade_datetime)
            print(f"Bought {quantity:.4f} {coin} at {price}, including commission of {commission_fee:.2f}")
        else:
            print("Not enough cash to complete the purchase.")

    def sell(self, coin, price):
        quantity = self.portfolio.get(coin, 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            self.portfolio[coin] -= quantity
            trade_datetime = datetime.now()  # Capture current datetime
            # Get purchase info
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            purchase_commission = purchase_info.get('commission', 0)
            # Calculate profit: (Sell Price - Purchase Price) * Quantity - Total Commissions
            profit = (price - purchase_price) * quantity - (purchase_commission + commission_fee)
            # Log the trade with profit and datetime
            self.log_trade('Sell', coin, price, quantity, trade_datetime, profit)
            print(f"Sold {quantity:.4f} {coin} at {price}, with commission of {commission_fee:.2f}")
            # Remove last purchase info after selling
            self.last_purchase_info.pop(coin, None)
        else:
            print(f"No holdings to sell for {coin}.")

    def commission(self, amount):
        return amount * self.commission_rate

    def log_trade(self, action, coin, price, quantity, trade_datetime, profit=0):
        commission_fee = self.commission(price * quantity)
        self.trade_log.append({
            'Datetime': trade_datetime,
            'Action': action,
            'Coin': coin,
            'Price': price,
            'Quantity': quantity,
            'Cash': self.cash,
            'Portfolio': self.portfolio.copy(),
            'Profit': profit,
            'Commission': commission_fee
        })

    def evaluate_trades(self, df_candles, coin):
        # Ensure we have enough data to compute indicators
        if len(df_candles) < 2:
            return

        # Get the latest data
        latest = df_candles.iloc[0]
        previous = df_candles.iloc[-1]
        print(f"Latest: {latest['time']}, Close: {latest['close']}, Previous: {previous['time']}, Close: {previous['close']}")

        # Access parameters directly from self.params
        price_move = self.params['price_move']
        profit_target = self.params['profit_target']

        # Buy condition: significant price drop and not currently holding the coin
        if self.portfolio.get(coin, 0) == 0:
            # Calculate probability
            p = self.calculate_probability(df_candles)
            q = 1 - p
            b = profit_target / price_move
            f_star = (b * p - q) / b
            f_star = max(0, f_star)
            available_cash = self.cash
            max_quantity = (available_cash * f_star) / latest['close']
            if max_quantity > 0:
                self.buy(coin, latest['close'], max_quantity)
                print(f"BUY: {coin}, Price: {latest['close']}, Quantity: {max_quantity}")
        # Sell condition: price increase since purchase
        elif self.portfolio.get(coin, 0) > 0:
            if coin in self.last_purchase_info:
                purchase_info = self.last_purchase_info[coin]
                last_purchase_price = purchase_info.get('price', latest['close'])
            else:
                last_purchase_price = latest['close']
            price_increase = (latest['close'] - last_purchase_price) / last_purchase_price
            # **Restored print statements for price increase**
            print(f"Price increase: {price_increase:.5f}")
            print(f"Latest close: {latest['close']}, Last purchase price: {last_purchase_price}")
            if price_increase >= price_move:
                self.sell(coin, latest['close'])

    def calculate_probability(self, df_candles):
        prices = df_candles['close'].values

        # Access parameters directly from self.params
        drop_threshold = self.params['drop_threshold']
        increase_threshold = self.params['price_move']
        look_back = self.params['look_back']

        drop_count = 0
        increase_count = 0
        for i in range(1, len(prices)):
            price_drop = (prices[i] - prices[i - 1]) / prices[i - 1]
            if price_drop <= drop_threshold:
                drop_count += 1
                for j in range(i + 1, min(i + 1 + look_back, len(prices))):
                    price_increase = (prices[j] - prices[i]) / prices[i]
                    if price_increase >= increase_threshold:
                        increase_count += 1
                        break
        if drop_count == 0:
            return 0.0
        probability = increase_count / drop_count
        return probability

def main_trading_logic(coins):
    #get portfolio data
    portfolio_manager = PortfolioManager()
    portfolio_uuid = portfolio_manager.list_portfolio()
    portfolio_data = portfolio_manager.get_portfolio_breakdown(portfolio_uuid)
    asset_names = coins
    uuid_list = ['6639e955-e2c7-5a51-b140-a0181f2f536b']
    filtered_positions = portfolio_manager.filter_portfolio(portfolio_data, asset_names, uuid_list, name_filter_mode='exclude', uuid_filter_mode='exclude')
    #get the total cash balance
    initial_cash =  portfolio_manager.extract_total_cash_balance(portfolio_data)
 # this will be retrieved from the portfolio class
    commission_rate = 0.006
    params = {
        'profit_target': 0.027, # how much to "motivate" the trader to bet
        'price_move': 0.00005, # when to sell
        'look_back': 100, # how far back to look when calculating probability
        'drop_threshold': -0.00005, # when to buy
    }

    trader = PaperTrader(
        initial_cash=initial_cash,
        commission_rate=commission_rate,
        params=params
    )
    cumulative_data = {}

    # Initialize cumulative_data for each coin
    for coin in coins:
        df = get_bar_data(coin, 'ONE_MINUTE', 300)
        if not df.empty:
            df = df.sort_values(by='time').reset_index(drop=True)
            cumulative_data[coin] = df.copy()
            # Save initial market data to CSV
            save_market_data_to_csv(df, coin)
        else:
            print(f"No initial data for {coin}")
            cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    while True:
        try:
            market_data = {}
            for coin in coins:
                df_new = get_bar_data(coin, 'ONE_MINUTE', limit=1)
                if not df_new.empty:
                    df_new = df_new.sort_values(by='time').reset_index(drop=True)
                    last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                    new_time = df_new['time'].iloc[0]
                    if last_time is None or new_time > last_time:
                        # Append the new data
                        cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                        cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                        cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                        # Save market data to CSV
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Appended new data for {coin}")
                    elif new_time == last_time:
                        # Replace the last candle
                        cumulative_data[coin].iloc[0] = df_new.iloc[0]
                        # Save market data to CSV
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Replaced last candle for {coin}")
                    else:
                        print(f"No new data for {coin}. Latest time: {last_time}")
                    # Update market_data with the latest cumulative data
                    market_data[coin] = cumulative_data[coin].copy()

                    #print portfolio
                    print(f"Current portfolio: {trader.portfolio}")

                    # Proceed to evaluate trades
                    trader.evaluate_trades(cumulative_data[coin], coin)
                else:
                    print(f"No data fetched for {coin}")
                    # Do not modify cumulative_data[coin]; use last known data
                    if coin in cumulative_data and not cumulative_data[coin].empty:
                        market_data[coin] = cumulative_data[coin].copy()
                        # Proceed to evaluate trades with existing data
                        print(f"Current portfolio: {trader.portfolio}")
                        trader.evaluate_trades(cumulative_data[coin], coin)
                    else:
                        print(f"No historical data available for {coin}. Skipping.")
                        continue
            # Save trade logs
            trader.calculate_total_portfolio_value(market_data)

            #print cash
            print(f"Current cash: {trader.cash:.2f}")

            trader.save_trade_log_to_csv()
            time.sleep(10)
        except Exception as e:
            print("Exception in main trading logic:")
            print(e)
            time.sleep(10)


if __name__ == '__main__':
    # Define the coins to trade
    coins = ['SOL-USD', 'LTC-USD', 'BTC-USD', 'SHIB-USD', 'ETH-USD']
    main_trading_logic(coins)

```

## Example of portfolio

```python
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
```

Using that class - can we alter this other file to produce the same outputs but using this live porfolio?

```python
    # this can be retrieved from the portfolio class
    def calculate_total_portfolio_value(self, market_data):
        total_value = self.cash  # Start with current cash balance
        for coin, quantity in self.portfolio.items():
            if quantity > 0:
                # Get the current market price for this coin
                if coin in market_data and not market_data[coin].empty:
                    price = market_data[coin]['close'].iloc[0]
                    total_value += quantity * price
        print(f"Total portfolio value: {total_value:.2f}")
        return total_value
```

Keep in mind that the data outouts already look pretty different. I think we need to standardize. The ultimate end product should contain these fields:

- Datetime
- Ticker/product ID
- purchased/average entry price
- current total value
- current total position size
- ...

Here's what the data structure looks like in this current portfolio calc method. It's super small and doesn't have everything we need:

```json
Current portfolio: {'SOL-USD': np.float64(2.4640213040258004e-06), 'LTC-USD': np.float64(5.267299042395793e-08), 'BTC-USD': np.float64(6.563458385564957e-05), 'SHIB-USD': np.float64(13920.709584756922), 'ETH-USD': np.float64(9.785615643887327e-06)}
```



Here's what the data strcuture looks like in the portfolio class:

```json
[{'asset': 'ORCA', 'account_uuid': '9a7bca7f-6521-5e72-ba37-55c507ffa787', 'total_balance_fiat': 0.012838473, 'total_balance_crypto': 0.003618, 'available_to_trade_fiat': 0.012838473, 'allocation': 3.0266692e-05, 'cost_basis': {'value': '0.01077488809884377987904', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/dd05661e865e97a78942d6684aa1a90cb28db91e48d33942714f395e75a1a2344ed577d0228d0cae4be2f6e74af774479bbf1c7c1690f13c9f0a1c87dd684efc/asset_icons/49435e1926043887024ed42b2dd3c3a07b096bf08f419d40e22555b9d953ec32.png', 'is_cash': False, 'average_entry_price': {'value': '2.97', 'currency': 'USD'}, 'asset_uuid': 'ba24ad7b-0a8b-533d-816b-e693d9f8a871', 'available_to_trade_crypto': 0.003618, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.012838473, 'available_to_transfer_crypto': 0.003618, 'asset_color': '#000000'}, {'asset': 'CLV', 'account_uuid': 'b9f6296c-bade-5708-8ee4-41d9f3a6b42f', 'total_balance_fiat': 0.27355093, 'total_balance_crypto': 3.082264, 'available_to_trade_fiat': 0.27355093, 'allocation': 0.0006448961, 'cost_basis': {'value': '3.005207244', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/2a43e81b3aa4ed326b3403253912cde99823a7bfab1e3df4aa42783a0e418c689663455524e679b892871a0c304a1025ec831c7eec619a7dca4b43a2e7df0b34/asset_icons/556d89987c2bf38e5b8d2a71636215c78cb3398ff7cf99219f67741b36a892cd.png', 'is_cash': False, 'average_entry_price': {'value': '0.98', 'currency': 'USD'}, 'asset_uuid': '453639be-192e-5e36-88e3-38496e542524', 'available_to_trade_crypto': 3.082264, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.27355093, 'available_to_transfer_crypto': 3.082264, 'asset_color': '#42C37B'}, {'asset': 'ATOM', 'account_uuid': 'c60e9751-26d6-590e-9200-6bbb969667fb', 'total_balance_fiat': 6.8570337, 'total_balance_crypto': 0.78045, 'available_to_trade_fiat': 0.022553662, 'allocation': 0.016165452, 'cost_basis': {'value': '23.162484522848277719811', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/b92276a1f003b87191983dab71970a9a6d522dde514176e5880a75055af1e67ce5f153b96a2ee5ecd22729a73d3a8739b248d853bde74ab6e643bef2d1b4f88d/asset_icons/9c760bf25bca9823f9ef8d651681b779aadc71a2f543f931070034e59ef10120.png', 'is_cash': False, 'average_entry_price': {'value': '27.77', 'currency': 'USD'}, 'asset_uuid': '64c607d2-4663-5649-86e0-3ab06bba0202', 'available_to_trade_crypto': 0.002567, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.022553662, 'available_to_transfer_crypto': 0.002567, 'asset_color': '#2E3148'}, {'asset': 'MATIC', 'account_uuid': 'd8a407a4-2036-5172-9874-920fa6e392cd', 'total_balance_fiat': 0.035018474, 'total_balance_crypto': 0.05845668, 'available_to_trade_fiat': 0.035018474, 'allocation': 8.255603e-05, 'cost_basis': {'value': '0.11543602298373518473044', 'currency': 'USD'}, 'asset_img_url': 'https://dynamic-assets.coinbase.com/085ce26e1eba2ccb210ea85df739a0ca2ef782747e47d618c64e92b168b94512df469956de1b667d93b2aa05ce77947e7bf1b4e0c7276371aa88ef9406036166/asset_icons/57f28803aad363f419a950a5f5b99acfd4fba8b683c01b9450baab43c9fa97ea.png', 'is_cash': False, 'average_entry_price': {'value': '1.90', 'currency': 'USD'}, 'asset_uuid': '026bcc1e-9163-591c-a709-34dd18b2e7a1', 'available_to_trade_crypto': 0.05845668, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.035018474, 'available_to_transfer_crypto': 0.05845668, 'asset_color': '#8247E5'}, {'asset': 'AERO', 'account_uuid': 'e87528b6-f1d7-5e08-ac9e-975176749ffd', 'total_balance_fiat': 0.1158882, 'total_balance_crypto': 0.07934559, 'available_to_trade_fiat': 0.1158882, 'allocation': 0.00027320636, 'cost_basis': {'value': '0.092739505445482494438015', 'currency': 'USD'}, 'asset_img_url': 'https://asset-metadata-service-production.s3.amazonaws.com/asset_icons/93b9f25ca937680b4b95a49a3e50aa614c039ff1ad0abed2bf59d24fbcb99b80.png', 'is_cash': False, 'average_entry_price': {'value': '1.17', 'currency': 'USD'}, 'asset_uuid': '9476e3be-b731-47fa-82be-347fabc573d9', 'available_to_trade_crypto': 0.07934559, 'unrealized_pnl': 0, 'available_to_transfer_fiat': 0.1158882, 'available_to_transfer_crypto': 0.07934559, 'asset_color': '#0433FF'}]
```

Can you help me achieve the new one?
