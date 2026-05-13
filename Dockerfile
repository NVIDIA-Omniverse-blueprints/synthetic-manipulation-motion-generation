# This image is used to run the Isaac Lab notebook in Red Hat OpenShift AI.

FROM nvcr.io/nvidia/gr00t-smmg-bp:1.0

# Install Xvfb for headless rendering
RUN apt-get update && \
    apt-get install -y xvfb x11-utils && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for OpenShift mode
# OPENSHIFT_MODE=true triggers Xvfb in launch.sh
# ACCEPT_EULA=Y accepts NVIDIA licenses (Isaac Sim, Isaac Lab, Cosmos)
# DISPLAY=:99 is the virtual display Xvfb creates
ENV OPENSHIFT_MODE=true \
    DISPLAY=:99 \
    ACCEPT_EULA=Y \
    HOME=/opt/app-root/src

# Copy modified launch script
COPY launch.sh /workspace/isaaclab/launch.sh
RUN chmod +x /workspace/isaaclab/launch.sh

# Install Jupyter Lab at build time
RUN /isaac-sim/kit/python/bin/python3 -m pip install jupyter

# Copy all notebook files (replaces docker-compose volume mounts)
COPY notebook/app.py /workspace/isaaclab/app.py
COPY notebook/cosmos_request.py /workspace/isaaclab/cosmos_request.py
COPY notebook/generate_dataset.ipynb /workspace/isaaclab/generate_dataset.ipynb
COPY notebook/notebook_utils.py /workspace/isaaclab/notebook_utils.py
COPY notebook/notebook_widgets.py /workspace/isaaclab/notebook_widgets.py
COPY notebook/stacking_prompt.toml /workspace/isaaclab/stacking_prompt.toml

# Copy input dataset (human demonstrations for Isaac Lab Mimic)
COPY samples/annotated_dataset.hdf5 /workspace/isaaclab/annotated_dataset.hdf5

# Set permissions for OpenShift compatibility
# OpenShift runs as random UID but always group 0
# Note: Actual directories and symlinks are creating at runtime in launch.sh
# because PVC mount at /opt/app-root/src replaces any build-time content
RUN chgrp -R 0 /opt/app-root/src && \
    chmod -R g=u /opt/app-root/src && \
    chmod -R 775 /workspace/isaaclab

# Make Isaac Sim directories writable for OpenShift (runs as random UID, group 0)
# cache and logs exist but are read-only for group, data directory is missing
RUN mkdir -p /isaac-sim/kit/data && \
    chmod -R g+w /isaac-sim/kit/cache \
                 /isaac-sim/kit/data \
                 /isaac-sim/kit/logs

# Set working directory
WORKDIR /workspace/isaaclab

# Entrypoint
ENTRYPOINT ["/workspace/isaaclab/launch.sh"]
