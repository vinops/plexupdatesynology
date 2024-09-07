#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install Python3 to continue."
    exit 1
fi

# Create a virtual environment
echo "Create a virtual environment."
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies from requirements.txt
if [ -f requirements.txt ]; then
    echo "Install dependencies from requirements.txt."
    pip install -r requirements.txt
else
    echo "The requirements.txt file was not found."
    deactivate
    exit 1
fi

# Deactivate the virtual environment
deactivate

echo "Dependency installation is complete."