#!/bin/bash

# Docker Container Logs Collector
# Collects logs from all TTS containers for analysis

OUTPUT_DIR="$(dirname "$0")/../logs/container-logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Docker Container Logs Collector"
echo "=========================================="
echo "Collecting logs from TTS containers..."
echo ""

# Get all running containers with 'tts' or common service names
CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "(tts|auth|ticket|workflow|notification|messaging)")

if [ -z "$CONTAINERS" ]; then
    echo "No TTS containers found running."
    echo "Looking for any running containers..."
    CONTAINERS=$(docker ps --format "{{.Names}}")
fi

if [ -z "$CONTAINERS" ]; then
    echo "No running containers found."
    exit 1
fi

for CONTAINER in $CONTAINERS; do
    echo "📋 Collecting logs from: $CONTAINER"
    
    LOG_FILE="$OUTPUT_DIR/${CONTAINER}-${TIMESTAMP}.log"
    
    # Get last 1000 lines of logs
    docker logs --tail 1000 "$CONTAINER" > "$LOG_FILE" 2>&1
    
    # Get container info
    INFO_FILE="$OUTPUT_DIR/${CONTAINER}-${TIMESTAMP}-info.json"
    docker inspect "$CONTAINER" > "$INFO_FILE"
    
    echo "   ✓ Saved to: $LOG_FILE"
done

echo ""
echo "=========================================="
echo "✓ Log collection complete!"
echo "=========================================="
echo "Location: $OUTPUT_DIR"
echo ""

# Create summary
SUMMARY_FILE="$OUTPUT_DIR/summary-${TIMESTAMP}.txt"
{
    echo "Container Logs Collection Summary"
    echo "=================================="
    echo "Timestamp: $(date)"
    echo "Containers: $(echo "$CONTAINERS" | wc -l)"
    echo ""
    echo "Containers logged:"
    echo "$CONTAINERS"
} > "$SUMMARY_FILE"

echo "Summary: $SUMMARY_FILE"
