"""
watcher.py

Module to monitor Algorand account states.
"""

from flask import Flask, request, jsonify
import threading
import time
import logging
from algosdk.v2client import algod
from urllib.error import URLError
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Algod REST API
algod_address = "https://testnet-api.algonode.cloud"
algod_token = ""

# Initialize the algod client
algod_client = algod.AlgodClient(algod_token, algod_address)

# In-memory storage for watched accounts
watched_accounts = {}
last_states = {}

def get_account_info(address):
    """
    Fetch account information from the Algorand node.

    Args:
        address (str): The Algorand address to fetch information for.

    Returns:
        dict: The account information or an error message.
    """
    try:
        account_info = algod_client.account_info(address)
        logging.info(f"Fetched account info for {address}")
        return account_info
    except URLError as e:
        logging.error(f"Error fetching account info for {address}: {e}")
        return {"address": address, "error": str(e)}
    except Exception as e:
        logging.error(f"Unexpected error fetching account info for {address}: {e}")
        return {"address": address, "error": "Unexpected error"}

def monitor_changes(address, previous_state, current_state):
    """
    Monitor and log changes in the account state.

    Args:
        address (str): The Algorand address being monitored.
        previous_state (dict): The previous state of the account.
        current_state (dict): The current state of the account.
    """
    changes = {key: (previous_state[key], current_state[key]) for key in current_state if previous_state[key] != current_state[key]}
    if changes:
        logging.info(f"State changes detected for {address}: {changes}")

@app.route('/watch', methods=['POST'])
def watch_account():
    """
    API endpoint to start watching an Algorand account.

    Returns:
        Response: JSON response indicating success or failure.
    """
    address = request.json.get('address')
    if not address:
        return jsonify({"error": "Algorand address is required"}), 400
    watched_accounts[address] = True
    logging.info(f"Started watching address {address}")
    return jsonify({"message": f"Watching address {address}"}), 200

@app.route('/accounts', methods=['GET'])
def list_accounts():
    """
    API endpoint to list watched accounts and their current state.

    Returns:
        Response: JSON response with the list of accounts and their information.
    """
    accounts_info = []
    for address in watched_accounts:
        try:
            account_info = algod_client.account_info(address)
            # print(json.dumps(account_info, indent=4))
            accounts_info.append(account_info)
        except URLError as e:
            logging.error(f"Error fetching account info for {address}: {e}")
            accounts_info.append({"address": address, "error": str(e)})
        except Exception as e:
            logging.error(f"Unexpected error fetching account info for {address}: {e}")
            accounts_info.append({"address": address, "error": "Unexpected error"})
    return jsonify(accounts_info), 200

def check_account_states(run_once=False):
    """
    Background task to monitor changes in account states.

    Args:
        run_once (bool): If True, the function runs only one iteration (used for testing).
    """
    while True:
        start_time = time.time()
        for address in watched_accounts:
            account_info = get_account_info(address)
            if 'error' in account_info:
                continue

            # Account state is not only balance, but also rewards, status, etc.
            current_state = {
                'amount': account_info['amount'],
                'pending_rewards': account_info.get('pending-rewards', 0),
                'status': account_info.get('status', ''),
                'total_apps_opted_in': account_info.get('total-apps-opted-in', 0),
                'total_assets_opted_in': account_info.get('total-assets-opted-in', 0),
                'min_balance': account_info.get('min-balance', 0),
                'rewards': account_info.get('rewards', 0)
            }

            if address in last_states:
                previous_state = last_states[address]
                monitor_changes(address, previous_state, current_state)

            last_states[address] = current_state

        elapsed_time = time.time() - start_time
        if run_once:
            break
        time.sleep(max(0, 60 - elapsed_time))

if __name__ == '__main__':
    # Start the background thread to monitor account states
    threading.Thread(target=check_account_states, daemon=True).start()
     # Run the Flask app
    app.run(host='0.0.0.0', port=5000)