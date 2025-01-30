from flask import Flask, jsonify
import urllib.request
import json

app = Flask(__name__)

#█▀▀ █▀█ █▀ █▀▀ ▄▀█ █▀▀ █░█ █▀▀   █▀█ █▀▀ █▀ ▀█▀   ▄▀█ █▀█ █
#██▄ █▄█ ▄█ █▄▄ █▀█ █▄▄ █▀█ ██▄   █▀▄ ██▄ ▄█ ░█░   █▀█ █▀▀ █

# Multiple fallback EOS API providers
NETWORK_API_URLS = [
    "https://eos.greymass.com/v1/chain/get_table_rows",  # Primary 
    "https://mainnet.genereos.io/v1/chain/get_table_rows",  # Backup 1
    "https://api.eossupport.io/v1/chain/get_table_rows",  # Backup 2
    "https://api.eossupport.io/v1/chain/get_table_rows"  # Backup 3
]

TOKEN_CONTRACT = "antelopcache"
CACHE_STATS_SCOPE = "76176668312389"
CACHE_TABLE_CURRENCY_STATS = "stat"

def fetch_supply_data():
    """Fetch the total, circulating supply, and supply minus burn with failover."""
    payload = {
        "code": TOKEN_CONTRACT,
        "table": CACHE_TABLE_CURRENCY_STATS,
        "scope": CACHE_STATS_SCOPE,
        "limit": 1,
        "json": True
    }

    data = json.dumps(payload).encode('utf-8')
    
    for api_url in NETWORK_API_URLS:
        try:
            req = urllib.request.Request(api_url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:  # Timeout set to 5 seconds
                result = json.loads(response.read().decode('utf-8'))
                if result and result.get("rows"):
                    row = result["rows"][0]
                    total_supply = float(row["supply"].split(" ")[0])
                    unredeemed_supply = int(row["unredeemed_supply"].split(" ")[0])
                    unredeemed_supply_adjusted = unredeemed_supply // 10_000
                    unredeemed_as_cache = unredeemed_supply_adjusted / 1e18
                    burn_supply = float(row["burn_supply"].split(" ")[0])
                    supply_minus_burn = round(total_supply - burn_supply, 4)
                    circulating_supply = round(supply_minus_burn - unredeemed_as_cache, 4)
                    return total_supply, circulating_supply, supply_minus_burn

        except Exception as e:
            print(f"⚠️ Failed to fetch data from {api_url}: {e}")

    return None, None, None  # All API URLs failed

@app.route('/total_supply', methods=['GET'])
def total_supply():
    """API endpoint to return the total supply as a numerical value."""
    total_supply, _, _ = fetch_supply_data()
    if total_supply is None:
        return jsonify({"error": "All API providers failed"}), 500
    return jsonify(total_supply)

@app.route('/circulating_supply', methods=['GET'])
def circulating_supply():
    """API endpoint to return the circulating supply as a numerical value."""
    _, circulating_supply, _ = fetch_supply_data()
    if circulating_supply is None:
        return jsonify({"error": "All API providers failed"}), 500
    return jsonify(circulating_supply)

@app.route('/supply_minus_burn', methods=['GET'])
def supply_minus_burn():
    """API endpoint to return the supply minus burned tokens as a numerical value."""
    _, _, supply_minus_burn = fetch_supply_data()
    if supply_minus_burn is None:
        return jsonify({"error": "All API providers failed"}), 500
    return jsonify(supply_minus_burn)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
