#!/bin/bash

# Check if arguments were provided
if [ $# -eq 0 ]; then
    echo "Error: No arguments provided."
    echo "Usage: $0 <graphrag_command_and_args>"
    echo "Example: $0 query --method drift --query \"Your query here\""
    echo "Example with query file: $0 query --method drift --query-file /path/to/query.txt"
    echo "Example with GPU selection: $0 --gpus 0,1 query --method drift --query \"Your query here\""
    exit 1
fi

# Default GPU configuration - use all available GPUs
GPUS_TO_USE=""

# Create logs directory if it doesn't exist
mkdir -p logs

# Create log filename with timestamp
LOG_FILENAME="logs/cc_test_run_$(date +"%Y%m%d_%H%M%S").log" 

# Check for ROCm vs CUDA (AMD vs NVIDIA)
if command -v rocm-smi &> /dev/null; then
    GPU_PLATFORM="ROCm"
else
    GPU_PLATFORM="CUDA" 
fi
echo "Detected GPU platform: $GPU_PLATFORM" | tee -a "$LOG_FILENAME"

# Check if query-file parameter is used
QUERY_FILE_PARAM="--query-file"
QUERY_PARAM="--query"
GPUS_PARAM="--gpus"
NEW_ARGS=()

# Process args to handle query files and GPU selection
i=0
while [ $i -lt $# ]; do
    i=$((i+1))
    ARG="${!i}"
    
    if [ "$ARG" = "$GPUS_PARAM" ]; then
        # Next arg should be the GPU indices
        i=$((i+1))
        if [ $i -le $# ]; then
            GPUS_TO_USE="${!i}"
            if [ "$GPU_PLATFORM" = "ROCm" ]; then
                echo "Setting HIP_VISIBLE_DEVICES=$GPUS_TO_USE" | tee -a "$LOG_FILENAME"
            else
                echo "Setting CUDA_VISIBLE_DEVICES=$GPUS_TO_USE" | tee -a "$LOG_FILENAME"
            fi
        else
            echo "Error: Missing GPU indices after $GPUS_PARAM" | tee -a "$LOG_FILENAME"
            exit 1
        fi
    elif [ "$ARG" = "$QUERY_FILE_PARAM" ]; then
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
# ./graph_rag_runner.sh --gpus 0,1 query --root ./ --method drift --query "Who is scrooge?"
CMD="python -m graphrag"
for arg in "${NEW_ARGS[@]}"; do
    CMD+=" \"${arg}\""
done

# Set appropriate GPU environment variables if specified
if [ -n "$GPUS_TO_USE" ]; then
    echo "Using GPUs: $GPUS_TO_USE" | tee -a "$LOG_FILENAME"
    if [ "$GPU_PLATFORM" = "ROCm" ]; then
        export HIP_VISIBLE_DEVICES="$GPUS_TO_USE"
        # Also set ROCR for compatibility
        export ROCR_VISIBLE_DEVICES="$GPUS_TO_USE"
    else
        export CUDA_VISIBLE_DEVICES="$GPUS_TO_USE"
    fi
fi

# Run the command
eval $CMD 2>&1 | tee -a "$LOG_FILENAME"

# Write a confirmation that the script completed
echo "Command completed and logged to $LOG_FILENAME" | tee -a "$LOG_FILENAME" 