# Use Node.js Alpine
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy project files
COPY . .

# Make the startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 1000

# Use our start script instead of directly building
CMD ["./start.sh"]
