#!/bin/bash

# Check if arguments were provided
if [ $# -eq 0 ]; then
    echo "Error: No arguments provided."
    echo "Usage: $0 <graphrag_command_and_args>"
    echo "Example: $0 query --method drift --query \"Your query here\""
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Create log filename with timestamp
LOG_FILENAME="logs/cc_test_run_$(date +"%Y%m%d_%H%M%S").log" 

echo "Running graphrag command..." | tee "$LOG_FILENAME"
echo "Command: python -m graphrag $@" | tee -a "$LOG_FILENAME"

# Build command with proper quoting below are samples for different methods with the same query
# responses are logged in the logs/cc_test_run_<timestamp>.log file
# ./graph_rag_runner.sh query --root ./ --method drift --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method global  --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method basic  --query "Who is scrooge?"
# ./graph_rag_runner.sh query --root ./ --method local  --query "Who is scrooge?"
CMD="python -m graphrag"
for arg in "$@"; do
    CMD+=" \"${arg}\""
done

# Run the command
eval $CMD 2>&1 | tee -a "$LOG_FILENAME"

# Write a confirmation that the script completed
echo "Command completed and logged to $LOG_FILENAME" | tee -a "$LOG_FILENAME" 