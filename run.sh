#!/bin/bash

set -e

cd "$(dirname "$0")"
source venv/bin/activate

python3 -m src.setup
python3 -m src.cli
