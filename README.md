# NVIDIA Omniverse Blueprint: Isaac GR00T for Synthetic Manipulation Motion Generation

The NVIDIA Isaac GR00T blueprint for synthetic manipulation motion generation is the ideal place to start. This is a reference workflow for creating exponentially large amounts of synthetic motion trajectories for robot manipulation from a small number of human demonstrations, built on [NVIDIA Omniverse™](https://developer.nvidia.com/isaac/sim) and [NVIDIA Cosmos™](https://www.nvidia.com/en-us/ai/cosmos/).

![image](https://github.com/user-attachments/assets/f93e9285-ac47-4db9-8c28-25a92367b3cd)

# Deploy On Local Workstation

## Prerequisites
Requirements for local deployment:
* Ubuntu 22.04 Operating System
* NVIDIA GPU (GeForce RTX 4090 or higher)
* [NVIDIA GPU Driver](https://www.nvidia.com/en-us/drivers/unix/) (recommended version 535.129.03)
* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) (minimum version 1.17.0)

Requirements for NVIDIA Cosmos:
* NVIDIA GPU (H100 or higher)
* NVIDIA H100 GPU is available on Azure in a ND H100 v5 series VM, AWS in a P5 EC2 instance and GCP in a A3 machine type VM.
* Visit the [Cosmos Hugging Face collection](https://huggingface.co/collections/nvidia/cosmos-6751e884dc10e013a0a0d8e6) for details about specific Cosmos hardware requirements.
  

## Launch a Jupyter Notebook

Steps:

1. Clone this repository to your local workstation and navigate to this repository.

       git clone https://github.com/NVIDIA-Omniverse-blueprints/synthetic-manipulation-motion-generation.git
       cd synthetic-manipulation-motion-generation

2. Enable X11 forwarding for a local workstation user.

       xhost +local:

3. Deploy the Jupyter Notebook with the Isaac Lab container.

       docker compose -f docker-compose.yml up -d
       
4. Access the Jupyter Notebook from a browser at http://localhost:8888/lab/tree/generate_dataset.ipynb.

5. Run the command below to stop the Jupyter Notebook and end the demo.

       docker compose -f docker-compose.yml down

6. Follow the instructions inside of the Jupyter Notebook

# Licenses

By running the docker compose command, you accept the terms and conditions of all the licenses below:

- [Isaac Sim](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/)
- [Isaac Lab](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE)
- [Isaac Lab mimic](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE-mimic)
- [Cosmos NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)
