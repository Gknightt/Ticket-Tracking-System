#!/bin/bash

set -e # Exit on any error

# Function to convert line endings to Unix-style
convert_to_unix() {
    if [ -f "$1/start.sh" ]; then
        dos2unix "$1/start.sh" > /dev/null 2>&1
        echo "Converted $1/start.sh"
    fi
}

# Convert start.sh in all service directories
echo "Converting start.sh files to Unix-style line endings..."
convert_to_unix "frontend"
convert_to_unix "user_service"
convert_to_unix "ticket_service"
convert_to_unix "workflow_api"
convert_to_unix "Docker/db-init"

# Convert init-multiple-dbs.sh in Docker/db-init directory
if [ -f "Docker/db-init/init-multiple-dbs.sh" ]; then
    dos2unix "Docker/db-init/init-multiple-dbs.sh" > /dev/null 2>&1
    echo "Converted Docker/db-init/init-multiple-dbs.sh"
fi

echo "Conversion complete."