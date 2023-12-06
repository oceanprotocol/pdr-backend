#!/bin/bash

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
python /app/pdr $@
