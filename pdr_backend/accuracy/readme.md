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
    
The script will output the accuracy of the model based on the provided values to a file named `pdr_backend/accuracy/output/accuracy.json`.

## Flask API

The `app.py` script provides a Flask endpoint with `/statistics` route to get the accuracy of the model.

```bash
curl http://localhost:5000/statistics
```

The endpoint will return the accuracy of the model in JSON format.


## Warning about Multithreading

The `app.py` script uses multithreading to handle multiple tasks simultaneously. Please ensure that the script is run in a thread-safe environment to avoid any issues.

The main thread will be used to handle the Flask API requests, while the worker threads will be used to calculate the accuracy of the model.