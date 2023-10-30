from flask import Flask, jsonify, request, abort
from utils.extract_statistics import extract_statistics
from utils.get_all_predictions import get_all_predictions 
from utils.date_to_unix import date_to_unix

app = Flask(__name__)

@app.route('/predictions', methods=['POST'])
def get_predictions():
    data = request.get_json()

    try:
        contract_addresses = data['contract_addresses']
        start_dt = data['start_dt']
        end_dt = data['end_dt']
        network_param = data['network']

        start_ts_param = date_to_unix(start_dt)
        end_ts_param = date_to_unix(end_dt)

        # check if contract_addresses is a list
        if not isinstance(contract_addresses, list):
            contract_addresses = [contract_addresses]

        predictions = get_all_predictions(
            start_ts_param, end_ts_param, contract_addresses, network_param
        )

        # print("Predictions: ", predictions)
        # Since get_statistics is printing results instead of returning them, we'll need to capture the print outputs.
        # Here's a modified version of get_statistics that returns the results instead:
        statistics = extract_statistics(predictions)

        return jsonify({
            # 'predictions': [vars(p) for p in predictions],
            'statistics': statistics
        })

    except KeyError:
        abort(400, description="Required fields not provided")


if __name__ == '__main__':
    app.run(debug=True)
