#!/bin/bash

set -e

cd "$(dirname "$0")"
source venv/bin/activate

python3 -m src.app.setup
python3 -m src.app.cli
