#!/bin/bash
# Run script for Sales Analytics Dashboard

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    streamlit run app.py
else
    echo "Virtual environment not found. Using system Python..."
    python3 -m streamlit run app.py
fi

