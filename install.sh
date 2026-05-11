#!/bin/bash

echo "Setting up grants pipeline..."

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make runner executable
chmod +x run.sh

# Create folders if missing
mkdir -p input
mkdir -p output

# Absolute path to project
PROJECT_PATH=$(pwd)

# Detect shell config
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    SHELL_CONFIG="$HOME/.bashrc"
fi

# Add alias if missing
if ! grep -q "grants-pipeline" "$SHELL_CONFIG"; then

    echo "" >> "$SHELL_CONFIG"

    echo "alias grants-pipeline=\"$PROJECT_PATH/run.sh\"" >> "$SHELL_CONFIG"

    echo "Alias added to $SHELL_CONFIG"
fi

echo ""
echo "Installation complete."
echo ""
echo "Run:"
echo "source $SHELL_CONFIG"
echo ""
echo "Then use:"
echo "grants-pipeline"
