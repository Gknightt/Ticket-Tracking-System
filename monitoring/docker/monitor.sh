#!/bin/bash

# Docker Container Resource Monitoring Script
# Monitors CPU, Memory, Network, and Disk I/O for all TTS containers

OUTPUT_DIR="$(dirname "$0")/../logs"
REPORT_FILE="$OUTPUT_DIR/docker-stats-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Docker Container Resource Monitor"
echo "=========================================="
echo "Monitoring TTS containers..."
echo "Output: $REPORT_FILE"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to get container stats
get_container_stats() {
    docker stats --no-stream --format "table {{.Container}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker ps >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running or not accessible${NC}"
        exit 1
    fi
}

# Single snapshot mode
if [ "$1" = "--snapshot" ] || [ "$1" = "-s" ]; then
    check_docker
    echo "Taking single snapshot..."
    get_container_stats | tee "$REPORT_FILE"
    echo ""
    echo "Snapshot saved to: $REPORT_FILE"
    exit 0
fi

# Continuous monitoring mode
check_docker

# Write header
{
    echo "Docker Container Monitoring Report"
    echo "Started: $(date)"
    echo "=========================================="
    echo ""
} > "$REPORT_FILE"

# Monitor loop
INTERVAL=${1:-5}  # Default 5 seconds
COUNTER=0

while true; do
    COUNTER=$((COUNTER + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Clear screen for continuous display
    clear
    
    echo -e "${GREEN}=========================================="
    echo "Docker Container Resource Monitor"
    echo "==========================================${NC}"
    echo "Timestamp: $TIMESTAMP"
    echo "Update #$COUNTER | Interval: ${INTERVAL}s"
    echo ""
    
    # Get and display stats
    STATS=$(get_container_stats)
    echo "$STATS"
    
    # Append to log file
    {
        echo "[$TIMESTAMP] Update #$COUNTER"
        echo "$STATS"
        echo ""
    } >> "$REPORT_FILE"
    
    # Check for high resource usage
    HIGH_CPU=$(echo "$STATS" | awk '{if ($3 ~ /%/) {gsub(/%/, "", $3); if ($3 > 80) print $2}}')
    HIGH_MEM=$(echo "$STATS" | awk '{if ($5 ~ /%/) {gsub(/%/, "", $5); if ($5 > 80) print $2}}')
    
    if [ -n "$HIGH_CPU" ]; then
        echo -e "\n${RED}⚠️  High CPU usage detected:${NC} $HIGH_CPU"
    fi
    
    if [ -n "$HIGH_MEM" ]; then
        echo -e "${RED}⚠️  High Memory usage detected:${NC} $HIGH_MEM"
    fi
    
    echo ""
    echo -e "${YELLOW}Log file: $REPORT_FILE${NC}"
    echo "Press Ctrl+C to stop"
    
    sleep "$INTERVAL"
done
