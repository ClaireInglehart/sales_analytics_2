#!/bin/bash
# Setup script for Sales Analytics Dashboard

echo "Setting up Sales Analytics Dashboard..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run: streamlit run app.py"
echo ""
echo "Or use the run script: ./run.sh"

