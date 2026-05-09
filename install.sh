#!/bin/bash

echo "Setting up grants pipeline..."

if ! command -v fzf &> /dev/null
then
    echo ""
    echo "fzf is required but not installed."
    echo ""
    echo "Install instructions:"
    echo ""

    echo "macOS (Homebrew):"
    echo "  brew install fzf"
    echo ""

    echo "Debian / Ubuntu:"
    echo "  sudo apt update && sudo apt install fzf"
    echo ""

    echo "Windows (Chocolatey):"
    echo "  choco install fzf"
    echo ""

    echo "Windows (Scoop):"
    echo "  scoop install fzf"
    echo ""

    exit 1
fi

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