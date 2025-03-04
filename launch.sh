#!/usr/bin/env bash

# Exits if error occurs
set -e

curl -s -L https://download.isaacsim.omniverse.nvidia.com/launchable/synthetic-motion-generation/kitcache.tar.gz | tar xzvf - -C /isaac-sim/kit/cache

/isaac-sim/kit/python/bin/python3 -m pip install jupyter

./_isaac_sim/python.sh -m jupyter lab /workspace/isaaclab/notebook/generate_dataset.ipynb --allow-root --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.default_url='/tree/generate_dataset.ipynb'