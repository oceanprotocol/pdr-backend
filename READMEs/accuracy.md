# PDR Backend Accuracy Module

## Overview
The Accuracy module is responsible for calculating and tracking prediction accuracy statistics for Ocean Protocol's Predictoor network. It provides a Flask-based web service that periodically collects prediction data and serves statistical information about prediction accuracy and staking amounts.

## Key Features
- Periodic data collection (every 5 minutes)
- Support for different timeframes (5min and 1hr predictions)
- REST API endpoint for accessing statistics
- Persistent storage of statistics in JSON format

## Related Subgraph Methods

### Predictions (subgraph_predictions.py)

#### `fetch_filtered_predictions()`
Retrieves predictions from the subgraph within a specified time range. Supports:
- Filtering by contract addresses
- Time-based querying with start and end timestamps
- Pagination with customizable chunk sizes
- Returns detailed prediction data including stakes, payouts, and true values

#### `get_all_contract_ids_by_owner()`
Fetches contract IDs associated with a specific owner address:
- Retrieves all tokens owned by a given address
- Supports both mainnet and testnet queries
- Returns a list of contract IDs

#### `fetch_contract_id_and_spe()`
Queries contract details including:
- Contract IDs
- Seconds per epoch (SPE)
- Token names
- Essential for accuracy calculations and contract identification

### Subscriptions (subgraph_subscriptions.py)

#### `fetch_filtered_subscriptions()`
Retrieves subscription data with features including:
- Time range filtering
- Contract-based filtering
- Pagination support
- Network selection
- Returns detailed subscription information including:
  - Pair information
  - Timeframe details
  - Source data
  - Transaction IDs
  - User information

## Technical Details

### Main Components

#### 1. Flask Web Service (`app.py`)
- Provides `/statistics` endpoint for retrieving accuracy data
- Runs a background thread for periodic data collection
- Implements CORS support for cross-origin requests

#### 2. Statistics Calculation
- Calculates prediction accuracy for each asset
- Tracks staking amounts for different time periods
- Supports multiple timeframes:
  - 5-minute predictions (1 week of historical data)
  - 1-hour predictions (4 weeks of historical data)

#### 3. Data Storage
- Statistics are stored in `accuracy_data.json`
- Location: `pdr_backend/accuracy/output/accuracy_data.json`

### API Endpoint

#### GET /statistics
Returns statistical data for all tracked prediction contracts.

## Configuration
- Network selection: Currently configured for mainnet
- Whitelist feeds: Uses `WHITELIST_FEEDS_MAINNET` constant
- Update interval: 5 minutes (300 seconds)

## Dependencies
- Flask
- enforce_typing
- threading
- datetime
- json
- logging

## Usage

### Running the Service

To run the service, use the following command:

```bash
python pdr_backend/accuracy/app.py
```

## Error Handling
- API endpoint returns 500 status code with error details if file access fails

## Notes
- The service maintains separate statistics for 5-minute and 1-hour prediction contracts
- Accuracy calculations exclude canceled slots
- Staking amounts are tracked for both current and previous day