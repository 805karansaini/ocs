import requests
import csv
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


# Function to send combo value to Flask server
class BridgeApp:
    # briding the app to main app
    @staticmethod
    def send_csv(csv_data, combo_id):
        # IP of the reciever
        server_ip = StrategyVariables.ocs_bridge_to_main_app_host
        server_port = StrategyVariables.ocs_bridge_to_main_app_port
        url = f'http://{server_ip}:{server_port}/upload_csv'
        # Data that needs to be send in json
        data = {'combo_id': combo_id, 'dataframe': csv_data.to_json()}  # Convert DataFrame to JSON string
        response = requests.post(url, json=data, timeout=30)
        # Check the status code of the response
        if response.status_code == 200:
            return {'message': 'DataFrame uploaded successfully'}
        else:
            return {'error': f'Failed to upload DataFrame. Status code: {response.status_code}'}
        