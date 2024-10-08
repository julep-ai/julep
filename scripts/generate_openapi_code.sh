#!/usr/bin/env bash

# Turn on command echo and exit on error
set -xe

# Exit on error
set -e
# Define log file for output
LOG_FILE="script.log"
TIME_FORMAT="+%Y-%m-%d %H:%M:%S"

# Function to log actions with timestamps
log_action() {
    echo "$(date "$TIME_FORMAT") - $1" | tee -a "$LOG_FILE"
}

# Function to compile TypeSpec project
compile_typespec() {
    log_action "Starting TypeSpec compilation"
    pushd typespec/ || { log_action "Error: Failed to navigate to typespec/ directory"; exit 1; }
    tsp compile . || { log_action "Error: TypeSpec compilation failed"; exit 1; }
    popd > /dev/null
    log_action "Finished TypeSpec compilation"
}

# Function to run Poetry tasks (codegen and format)
run_poetry_tasks() {
    log_action "Navigating to agents-api directory"
    pushd agents-api || { log_action "Error: Failed to navigate to agents-api/ directory"; exit 1; }

    # Update dependencies if the flag is set
    if [[ "$UPDATE_POETRY" == "true" ]]; then
        log_action "Updating Poetry dependencies"
        poetry update || { log_action "Error: Poetry update failed"; exit 1; }
    fi

    log_action "Running code generation"
    poetry run poe codegen || { log_action "Error: Code generation failed"; exit 1; }

    log_action "Running code formatting"
    poetry run poe format || { log_action "Error: Code formatting failed"; exit 1; }

    popd > /dev/null
    log_action "Finished Poetry tasks in agents-api"
}

# Function to display script usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --update-poetry       Update Poetry dependencies before running tasks"
    echo "  -h, --help            Show this help message"
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --update-poetry)
            UPDATE_POETRY="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown parameter passed: $1"
            usage
            exit 1
            ;;
    esac
done

# Start time logging
START_TIME=$(date +%s)

# Main execution
log_action "Script execution started"
compile_typespec
run_poetry_tasks

# End time logging
END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))

log_action "Script execution completed in $ELAPSED_TIME seconds"

# Success exit
exit 0
