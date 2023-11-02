#!/bin/bash

# Get the current directory path
CURRENT_DIR=$(pwd)

# Define the string to be replaced and the new string
search="C:/PolyHaven"
replace="${CURRENT_DIR//\//\/}"

files=("main.py" "get_path.py" "shelf.py")

# Find and replace the string
for file in "${files[@]}"; do
    sed -i '' "s|$search|$replace|g" "$file"
done

# Define the string to be replaced and the new string
search="C:/PolyHaven/inventory"
replace="${CURRENT_DIR//\//\/}/inventory"

file="settings.json"

# Find and replace the string
sed -i '' "s|$search|$replace|g" "$file"
