#!/bin/bash

MODULE_NAME=$1
COMMAND=$2

if [ -z "$MODULE_NAME" ]
then
    echo "No module specified. Please provide a module name as an argument."
    exit 1
fi

if [ ! -d "/app/pdr_backend/$MODULE_NAME" ]
then
    echo "Module $MODULE_NAME does not exist."
    exit 1
fi

if [ "${WAIT_FOR_CONTRACTS}" = "true" ]
# Development only
then
  echo "Waiting for contracts to be ready...."
  while [ ! -f "/root/.ocean/ocean-contracts/artifacts/ready" ]; do
    sleep 2
  done
  sleep 10
fi

if [ "${WAIT_FOR_SUBGRAPH}" = "true" ]
# Development only
then
  echo "Waiting for subgraph to be ready...."
  while [ ! -f "/ocean-subgraph/ready" ]; do
    sleep 2
  done
  sleep 10
fi

DELAY=${DELAYED_STARTUP:-0}
echo "Delaying startup for ${DELAY} seconds.."
sleep $DELAY

echo "Running $MODULE_NAME..."
python /app/pdr_backend/$MODULE_NAME/main.py $COMMAND
