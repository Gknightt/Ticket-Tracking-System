#!/bin/bash

# Docker Container Performance Analysis
# Analyzes resource usage patterns from monitoring logs

LOGS_DIR="$(dirname "$0")/../logs"

echo "=========================================="
echo "Docker Performance Analysis"
echo "=========================================="
echo ""

# Find latest docker stats log
LATEST_LOG=$(ls -t "$LOGS_DIR"/docker-stats-*.log 2>/dev/null | head -n1)

if [ -z "$LATEST_LOG" ]; then
    echo "No monitoring logs found."
    echo "Run ./monitor.sh first to collect data."
    exit 1
fi

echo "Analyzing: $LATEST_LOG"
echo ""

# Extract container names
CONTAINERS=$(grep -E "^\w+" "$LATEST_LOG" | awk '{print $2}' | sort -u)

echo "Containers monitored:"
echo "$CONTAINERS"
echo ""
echo "=========================================="
echo "Resource Usage Summary"
echo "=========================================="
echo ""

for CONTAINER in $CONTAINERS; do
    echo "Container: $CONTAINER"
    echo "----------------------------------------"
    
    # Extract CPU percentages
    CPU_VALUES=$(grep "$CONTAINER" "$LATEST_LOG" | awk '{print $3}' | sed 's/%//' | grep -E '^[0-9.]+$')
    
    if [ -n "$CPU_VALUES" ]; then
        AVG_CPU=$(echo "$CPU_VALUES" | awk '{sum+=$1; count++} END {if (count>0) print sum/count}')
        MAX_CPU=$(echo "$CPU_VALUES" | sort -n | tail -1)
        echo "  CPU Usage:"
        echo "    Average: ${AVG_CPU}%"
        echo "    Peak:    ${MAX_CPU}%"
    fi
    
    # Extract Memory percentages
    MEM_VALUES=$(grep "$CONTAINER" "$LATEST_LOG" | awk '{print $5}' | sed 's/%//' | grep -E '^[0-9.]+$')
    
    if [ -n "$MEM_VALUES" ]; then
        AVG_MEM=$(echo "$MEM_VALUES" | awk '{sum+=$1; count++} END {if (count>0) print sum/count}')
        MAX_MEM=$(echo "$MEM_VALUES" | sort -n | tail -1)
        echo "  Memory Usage:"
        echo "    Average: ${AVG_MEM}%"
        echo "    Peak:    ${MAX_MEM}%"
    fi
    
    echo ""
done

# Count updates
UPDATES=$(grep -c "Update #" "$LATEST_LOG")
echo "=========================================="
echo "Total monitoring updates: $UPDATES"
echo "=========================================="
