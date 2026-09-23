#!/bin/bash

# Check if arguments were provided
if [ $# -eq 0 ]; then
    echo "Error: No arguments provided."
    echo "Usage: $0 <graphrag_command_and_args>"
    echo "Example: $0 query --method drift --query \"Your query here\""
    echo "Example with query file: $0 query --method drift --query-file /path/to/query.txt"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Create log filename with timestamp
LOG_FILENAME="logs/cc_test_run_$(date +"%Y%m%d_%H%M%S").log" 

# Check if query-file parameter is used
QUERY_FILE_PARAM="--query-file"
QUERY_PARAM="--query"
NEW_ARGS=()

# Process args to handle query files
i=0
while [ $i -lt $# ]; do
    i=$((i+1))
    ARG="${!i}"
    
    if [ "$ARG" = "$QUERY_FILE_PARAM" ]; then
        # Next arg should be the file path
        i=$((i+1))
        if [ $i -le $# ]; then
            FILE_PATH="${!i}"
            if [ -f "$FILE_PATH" ]; then
                # Read file content and replace with regular query param
                FILE_CONTENT=$(cat "$FILE_PATH")
                NEW_ARGS+=("$QUERY_PARAM" "$FILE_CONTENT")
                echo "Reading query from file: $FILE_PATH" | tee -a "$LOG_FILENAME"
            else
                echo "Error: Query file not found: $FILE_PATH" | tee -a "$LOG_FILENAME"
                exit 1
            fi
        else
            echo "Error: Missing file path after $QUERY_FILE_PARAM" | tee -a "$LOG_FILENAME"
            exit 1
        fi
    else
        NEW_ARGS+=("$ARG")
    fi
done

echo "Running graphrag command..." | tee "$LOG_FILENAME"
echo "Command: python -m graphrag ${NEW_ARGS[@]}" | tee -a "$LOG_FILENAME"

# Build command with proper quoting below are samples for different methods with the same query
# responses are logged in the logs/cc_test_run_<timestamp>.log file
# ./graph_rag_runner.sh query --root ./ --method drift --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method global  --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method basic  --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method local  --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method drift --query-file /path/to/query.txt
CMD="python -m graphrag"
for arg in "${NEW_ARGS[@]}"; do
    CMD+=" \"${arg}\""
done

# Run the command
eval $CMD 2>&1 | tee -a "$LOG_FILENAME"

# Write a confirmation that the script completed
echo "Command completed and logged to $LOG_FILENAME" | tee -a "$LOG_FILENAME" 