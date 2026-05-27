#!/usr/bin/env bash

# Exits if error occurs
set -e

# OpenShift Mode - handle and exit
if [ "$OPENSHIFT_MODE" = "true" ]; then
    echo "Running in OpenShift mode (headless with Xvfb)"

    # Copy notebook files to PVC on first startup
    if [ ! -f /opt/app-root/src/generate_dataset.ipynb ]; then
        echo "First startup - copying notebook files to PVC..."
        cp /workspace/isaaclab/generate_dataset.ipynb /opt/app-root/src/
        cp /workspace/isaaclab/notebook_utils.py /opt/app-root/src/
        cp /workspace/isaaclab/notebook_widgets.py /opt/app-root/src/
        cp /workspace/isaaclab/stacking_prompt.toml /opt/app-root/src/
        cp /workspace/isaaclab/cosmos_request.py /opt/app-root/src/
        echo "Notebook files ready"
    fi

    # Create user data directories on PVC (must be at runtime, not build time)
    # Note: Isaac Sim system directories (cache/data/logs) are now writable in /isaac-sim/kit/
    echo "Creating user data directories on PVC..."
    mkdir -p /opt/app-root/src/datasets \
             /opt/app-root/src/Documents/Kit/shared

    # Copy input dataset to PVC on first startup
    if [ ! -f /opt/app-root/src/datasets/annotated_dataset.hdf5 ]; then
        echo "Copying input dataset to PVC..."
        cp /workspace/isaaclab/annotated_dataset.hdf5 /opt/app-root/src/datasets/
        echo "Input dataset ready"
    fi

    # Start Xvfb for headless rendering
    echo "Starting Xvfb virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!

    # Wait for Xvfb to start
    sleep 2

    # Verify Xvfb is running
    if ! ps -p $XVFB_PID > /dev/null; then
        echo "ERROR: Xvfb failed to start"
        exit 1
    fi

    echo "Xvfb started successfully on DISPLAY=:99 (PID: $XVFB_PID)"

    # Export DISPLAY for Isaac Sim
    export DISPLAY=:99

    # Cleanup function for Xvfb
    cleanup() {
        echo "Stopping Xvfb..."
        kill $XVFB_PID 2>/dev/null || true
    }
    trap cleanup EXIT

    # Start Jupyter Lab (non-root mode for OpenShift)
    # RHOAI injects NOTEBOOK_ARGS with correct base_url, token, password, port
    /isaac-sim/python.sh -m jupyter lab \
        --ip=0.0.0.0 \
        --no-browser \
        $NOTEBOOK_ARGS

    exit 0
fi

# Running in docker-compose mode
/isaac-sim/kit/python/bin/python3 -m pip install jupyter

./_isaac_sim/python.sh -m jupyter lab /workspace/isaaclab/generate_dataset.ipynb --allow-root --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.default_url='/tree/generate_dataset.ipynb'
