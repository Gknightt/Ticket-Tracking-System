#!/bin/sh

# Generate .env file from environment variables
echo "Generating .env file from environment variables..."

# Create or clear the .env file
> .env

# Add all environment variables starting with VITE_ to the .env file
env | grep "^VITE_" > .env

echo ".env file generated:"
cat .env

# Build the app with the generated .env
echo "Building the application..."
npm run build

# Start the server
echo "Starting server..."
exec npx serve -s dist -l 1000