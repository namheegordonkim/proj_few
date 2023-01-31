#!/bin/bash

# Usage: bash run.sh [python train.py args]

# Navigate to appropriate place to run experiment launch code. Ensure to point to correct result visualization outside of src directory
# Necessary because a lot of research packages don't have scripts running from correct directory.

RUNNABLE_DIR="<CHANGE THIS TO DIRECTORY WHERE MAIN PYTHON FILE LIVES>"

current_dir=$(pwd)

# strip all .git stuff
rm -rf ./**/.git
rm -rf ./**/.github

cd "$RUNNABLE_DIR"
PYTHONPATH="$current_dir":$PYTHONPATH "$@"
