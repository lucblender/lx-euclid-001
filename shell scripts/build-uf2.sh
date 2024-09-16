#!/bin/bash

# Load environment variables from .env file
if [ -f lx-euclid.env ]; then
    source lx-euclid.env
else
    echo ".env file not found."
    exit 1
fi

# Copy all sources files into micropython folder
# Check if the source directory exists
if [ -d "$LX_EUCLID_REPO_DIRECTORY" ]; then
    # Create the destination directory if it doesn't exist
    mkdir -p "$MICROPYTHON_RP2_MODULE_DIRECTORY"

    # Copy all .py files from the source directory and its subdirectories to the destination directory
    find "$LX_EUCLID_REPO_DIRECTORY" -type f -name "*.py"  -not -path "*/.git/*" -not -path "*/tmp/*" | while read -r file; do
        # Get the relative path of the file from the source directory
        relative_path="${file#$LX_EUCLID_REPO_DIRECTORY/}"
		
        # Create the directory structure in the destination directory (if it doesn't exist)
        mkdir -p "$MICROPYTHON_RP2_MODULE_DIRECTORY/$(dirname "$relative_path")"

        # Copy the file to the destination directory with the same relative path
        cp "$file" "$MICROPYTHON_RP2_MODULE_DIRECTORY/$relative_path"
    done

    echo "Python files copied successfully."
else
    echo "Source directory not found: $LX_EUCLID_REPO_DIRECTORY"
fi

# Compile a micropython image
# Go to micropython folder
cd $MICROPYTHON_RP2_DIRECTORY

# Clean then build UF2 file
make clean
make -j4

# Copy uf2 file to specific output path
cp ./build-RPI_PICO/firmware.uf2 $DIR_2_UF2_NO_FILESYSTEM_FILE

# Add filesystem to micropython UF2
# Create binary folder if needed and copy bin files
cd $DIR_2_UF2_FOLDER
mkdir -p $BINARY_FOLDER
cp -a $LX_EUCLID_BIN_DIRECTORY ./

python3 dir2uf2 ./$BINARY_FOLDER --append-to $DIR_2_UF2_NO_FILESYSTEM_FILE --fs-compact  

# Copy the concatenanted UF2 (micropython + filesystem) to output path
cp $DIR_2_UF2_W_FILESYSTEM_FILE $UF2_OUTPUT_FILE
echo $UF2_OUTPUT_FILE successfully created
