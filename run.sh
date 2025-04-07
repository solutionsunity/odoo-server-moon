#!/bin/bash

# Start the Odoo Dev Server Monitoring Tool

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Install dependencies if not already installed
echo "Checking dependencies..."
pip3 install -r requirements.txt

# Start the application
echo "Starting Odoo Dev Server Monitoring Tool..."
python3 -m app.main
