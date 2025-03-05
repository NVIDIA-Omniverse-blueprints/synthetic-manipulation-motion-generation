# synthetic-motion-generation

Multiply human captured teleop data utilizing Isaac Lab Mimic and GR00T-Gen

# Using NVIDIA Brev

## Deploy NVIDIA Brev Launchable

From build.nvidia.com/nvidia/synthetic-motion-generation, click on the "Deploy Launchable" button to deploy and connect to the Brev Launchable instance.

[NVIDIA Brev](https://developer.nvidia.com/brev) provides streamlined access to NVIDIA GPU instances to run containers in the cloud. No local install needed!

If you do not have an account with Brev, you will be prompted to create one and be provided with a limited number of free credits to use.

## Launch a Jupyter Notebook from NVIDIA Brev

When the Launchable instance is ready, click the `Open Notebook` button to launch the Jupyter Notebook for this demo.

Follow the instructions within the notebook to run the demo.

### (optional) Change scenario parameters and generate new motion trajectories

Follow the instructions in the Jupyter notebook to change values within the Isaac Lab scenario to generate new motion trajectories or update the simulation environment.

## Create a prompt to generate a new world environment

Lastly, inside of the Jupyter notebook, create a prompt to generate a new world environment for your simulation.  This will use NVIDIA Cosmos to generate a new world environment video and display it inside of your notebook for viewing.

# Deploy On Local Workstation

## Prerequisites
Requirements for local deployment:
* Ubuntu 20.04/22.04 Operating System
* NVIDIA GPU (GeForce RTX 3070 or higher)
* [NVIDIA GPU Driver](https://www.nvidia.com/en-us/drivers/unix/) (recommended version 535.129.03)
* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) (minimum version 1.17.0)
* [Isaac Sim WebRTC Streaming Client](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/manual_livestream_clients.html#isaac-sim-short-webrtc-streaming-client)

## Launch a Jupyter Notebook

Steps:

1. Check if your workstation meets the [System Requirements](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/requirements.html#system-requirements) and [Driver Requirements](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/requirements.html#isaac-sim-short-driver-requirements) for running Isaac Sim.

2. Run the command below to confirm your GPU driver version is 535.129.03 or later.

       nvidia-smi

3. Clone this repository to your local machine and navigate to this repository.

       git clone https://github.com/NVIDIA-Omniverse-blueprints/synthetic-motion-generation.git
       cd synthetic-motion-generation

4. Deploy the Jupyter Notebook from the Isaac Lab container.

       docker compose -f docker-compose.yml up
       
5. Access the Jupyter Notebook from a browser at http://localhost:8888/lab/tree/generate_dataset.ipynb.

## Licenses

By running the docker compose command, you accept the terms and conditions of the licenses below

- [NVIDIA Brev](https://www.nvidia.com/en-us/agreements/cloud-services/service-specific-terms-for-brev/),
- [Isaac Sim and WebRTC Client](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/common/legal.html),
- [Isaac Lab](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE), and
- [Isaac Lab mimic](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE-mimic)

