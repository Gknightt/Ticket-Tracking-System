#!/bin/bash

set -e # Exit on any error

# Function to convert line endings to Unix-style
convert_to_unix() {
    if [ -f "$1/start.sh" ]; then
        dos2unix "$1/start.sh"
        echo "Converted $1/start.sh to Unix-style line endings."
    else
        echo "No start.sh found in $1, skipping."
    fi
}

# Convert start.sh in all service directories
echo "Converting start.sh files to Unix-style line endings..."
convert_to_unix "frontend"
convert_to_unix "user_service"
convert_to_unix "ticket_service"
convert_to_unix "workflow_api"

echo "Conversion complete."