#!/bin/bash

MODULE_NAME=$1

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

echo "Running $MODULE_NAME..."
python /app/pdr_backend/$MODULE_NAME/main.py
