#!/bin/bash

if [ ! -d "./env" ]; then
    echo "Environment not found. Installing Miniconda..."
    (cd ./install && bash install.sh)
    if [ $? -ne 0 ]; then
        echo "Installation failed. Please check the error messages above."
        exit 1
    fi
fi

echo "Running main.py with the installed Python..."
./env/bin/python main.py