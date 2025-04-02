#!/bin/bash

# RabbitMQ Workflow Manager
# Starts all services in order and cleans up on exit
# Shows Producer output in console

# Configuration
RABBITMQ_HOST="localhost"
LOG_FILE="/dev/null"  # No data stored in files
PYTHON_CMD="python3"

# Process IDs storage (in memory only)
declare -A PIDS

# Function to start a service
start_service() {
    local name=$1
    local script=$2
    local args=$3 
    local redirect="$LOG_FILE"
    
    # Special handling for Producer to show output
    if [ "$name" = "Producer" ]; then
        redirect="/dev/stdout"
    fi
    
    echo "Starting $name..."
    if [ -n "$args" ]; then
        $PYTHON_CMD "$script" $args > "$redirect" 2>&1 &
    else
        $PYTHON_CMD "$script" > "$redirect" 2>&1 &
    fi
    PIDS[$name]=$!
}

# Function to clean up processes
cleanup() {
    echo -e "\nShutting down services..."
    for name in "${!PIDS[@]}"; do
        if kill -0 "${PIDS[$name]}" 2>/dev/null; then
            kill -TERM "${PIDS[$name]}" 2>/dev/null && echo "Stopped $name"
        fi
    done
    # Wait for processes to terminate
    sleep 2
    # Force kill any remaining processes
    for name in "${!PIDS[@]}"; do
        if kill -0 "${PIDS[$name]}" 2>/dev/null; then
            kill -KILL "${PIDS[$name]}" 2>/dev/null && echo "Force stopped $name"
        fi
    done
}

# Trap CTRL+C and other termination signals
trap cleanup INT TERM EXIT

run_tests(){
    echo "Producer finished Producing"

    # Log Verification Script
    # Checks that original numbers match their squared and cubed counterparts

    LOG_FILE="rabbitmq_messages.log"
    TEMP_FILE="/tmp/verify_temp.log"
    NAME_FILTER="test1"  # Change this to filter by different names

    # Check if log file exists
    if [ ! -f "$LOG_FILE" ]; then
        echo "Error: Log file $LOG_FILE not found!"
        exit 1
    fi

    # Extract and sort relevant log entries
    grep "$NAME_FILTER" "$LOG_FILE" | sort -t '[' -k 2 > "$TEMP_FILE"

    # Initialize verification
    original_numbers=()
    squared_numbers=()
    cubed_numbers=()
    current_number=""
    errors=0
    echo "Starting verification for name: $NAME_FILTER"
    echo "-------------------------------------------"

    # Process log file
    while IFS= read -r line; do
        # Extract components from log line
        timestamp=$(echo "$line" | cut -d '[' -f 2 | cut -d ']' -f 1)
        name=$(echo "$line" | awk -F ':' '{print $3}' | xargs)
        type=$(echo "$line" | awk -F ':' '{print $4}' | xargs)
        number=$(echo "$line" | awk -F ':' '{print $5}' | xargs)
        echo $name $type $number
        # Store numbers in appropriate arrays
        case $type in
            "original")
                original_numbers+=($number)
                ;;
            "squared")
                current_number=${original_numbers[${#squared_numbers[@]}]}
                # echo ${#squared_numbers[@]}
                expected=$((current_number * current_number))
                if [ "$number" -ne "$expected" ]; then
                    echo "ERROR: $current_number ² should be $expected but got $number (at $timestamp)"
                    ((errors++))
                fi
                squared_numbers+=($number)
                ;;
            "cubed")
                current_number=${original_numbers[${#cubed_numbers[@]}]}
                expected=$((current_number * current_number * current_number))
                if [ "$number" -ne "$expected" ]; then
                    echo "ERROR: $current_number ³ should be $expected but got $number (at $timestamp)"
                    ((errors++))
                fi
                cubed_numbers+=($number)
                ;;
        esac
    done < "$TEMP_FILE"

    # Clean up temp file
    rm -f "$TEMP_FILE"

    # Print summary
    echo "-------------------------------------------"
    echo "Verification complete:"
    echo "Total numbers processed: ${#original_numbers[@]}"
    echo "Errors found: $errors"

    if [ "$errors" -eq 0 ]; then
        echo "SUCCESS: All records match correctly!"
        exit 0
    else
        echo "FAILURE: Found $errors mismatches in records"
        exit 1
    fi
}

# Start services in proper order
start_service "Logger" "Logger.py"
start_service "Squarer" "Squarer.py"
start_service "Cuber" "Cuber.py"
sleep 1  # Give it a moment to initialize
start_service "Producer" "Producer.py" "test1 5 0.0"

echo "All services running. Press CTRL+C to stop."
echo "------------------------------------------"

# Keep script running while services work
while true; do
    sleep 1
    # Check if any critical process died
    for name in "${!PIDS[@]}"; do
        if ! kill -0 "${PIDS[$name]}" 2>/dev/null; then
            if [ "$name" = "Producer" ]; then
                run_tests
            else
                echo "ERROR: $name died!"
                cleanup
                exit 1
            fi
        fi
    done
done
