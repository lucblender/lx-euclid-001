#!/bin/bash

# Specify the source directory
source_directory="/mnt/c/Users/lucas/Documents/randomGit/lx-euclid-001"

# Specify the destination directory
destination_directory="/home/lucas/micropython/ports/rp2/modules"

# Check if the source directory exists
if [ -d "$source_directory" ]; then
    # Create the destination directory if it doesn't exist
    mkdir -p "$destination_directory"

    # Copy all .py files from the source directory and its subdirectories to the destination directory
    find "$source_directory" -type f -name "*.py" | while read -r file; do
        # Get the relative path of the file from the source directory
        relative_path="${file#$source_directory/}"

        # Create the directory structure in the destination directory (if it doesn't exist)
        mkdir -p "$destination_directory/$(dirname "$relative_path")"

        # Copy the file to the destination directory with the same relative path
        cp "$file" "$destination_directory/$relative_path"
    done

    echo "Python files copied successfully."
else
    echo "Source directory not found: $source_directory"
fi