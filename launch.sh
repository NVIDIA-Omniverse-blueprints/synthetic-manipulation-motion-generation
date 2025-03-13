#!/usr/bin/env bash

# Exits if error occurs
set -e

/isaac-sim/kit/python/bin/python3 -m pip install jupyter

./_isaac_sim/python.sh -m jupyter lab /workspace/isaaclab/generate_dataset.ipynb --allow-root --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.default_url='/tree/generate_dataset.ipynb'
