# pdr_backend/accuracy

This document provides instructions on how to deploy and run the `app.py` script in the `pdr_backend/accuracy` directory.

## Requirements

- Python 3.x
- Required Python packages (listed in `requirements.txt`)

## Deployment

```bash
git clone <repository_url>
cd pdr_backend

pip install -r requirements.txt
```

## Usage

The `app.py` script is used to calculate the accuracy of a model based on the predicted and true values.

```bash
python pdr_backend/accuracy/app.py
```


The script uses the `GQLDataFactory` to fetch the predictions. Be sure to provide the correct values for `st_timestr` in the `ppss.yaml` file to get the correct predictions. It needs to be at least `28 days ago` from the current date. 
    
The script will output the accuracy of the predictoor based on the provided values to a file named `pdr_backend/accuracy/output/accuracy.json`.

The data includes the pair name, the average accuracy of the model, the total staked amount yesterday, and the total staked amount today.

Example Output:
```json

[
    {
        "alias": "5m",
        "statistics": {
            "0xb1c55346023dee4d8b0d7b10049f0c8854823766": {
                "token_name": "LTC/USDT",
                "average_accuracy": 53.67847411444142,
                "total_staked_yesterday": 217456.43999999997,
                "total_staked_today": 203650.03999999992
            },
            ........
        }
    },
    {
        "alias": "1h",
        "statistics": {
            "0xb1c55346023dee4d8b0d7b10049f0c8854823766": {
                "token_name": "LTC/USDT",
                "average_accuracy": 53.67847411444142,
                "total_staked_yesterday": 217456.43999999997,
                "total_staked_today": 203650.03999999992
            },
            ........
        
    }
]
```

## Flask API

The `app.py` script provides a Flask endpoint with `/statistics` route to get the accuracy of the model.

```bash
curl http://localhost:5000/statistics
```

The endpoint will return the accuracy of the model in JSON format.


## Warning about multithreading

The `app.py` script uses multithreading to handle multiple tasks simultaneously. Please ensure that the script is run in a thread-safe environment to avoid any issues.

The main thread will be used to handle the Flask API requests, while the worker threads will be used to calculate the accuracy of the model.