#!/bin/bash

# Specify the directory containing your Python files
start_directory="/mnt/c/Users/lucas/Documents/randomGit/lx-euclid-001"

# Check if the directory exists
if [ -d "$start_directory" ]; then
    # Find all .py files in the directory and its subdirectories
    find "$start_directory" -type f -name "*.py" | while read -r file; do
        # Execute the mpy-cross command for each Python file
        ./micropython/mpy-cross/build/mpy-cross "$file"
    done
else
    echo "Directory not found: $start_directory"
fi