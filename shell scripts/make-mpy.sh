#!/bin/bash

# Load environment variables from .env file
if [ -f lx-euclid.env ]; then
    source lx-euclid.env
else
    echo ".env file not found."
    exit 1
fi
# Check if the directory exists
if [ -d "$LX_EUCLID_REPO_DIRECTORY" ]; then
    # Find all .py files in the directory and its subdirectories
    find "$LX_EUCLID_REPO_DIRECTORY" -type f -name "*.py" | while read -r file; do
        # Execute the mpy-cross command for each Python file
        ./micropython/mpy-cross/build/mpy-cross "$file" -march=armv6m
    done
else
    echo "Directory not found: $LX_EUCLID_REPO_DIRECTORY"
fi
