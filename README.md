# NVIDIA Omniverse Blueprint: Synthetic Manipulation Motion Generation for Robotics

The NVIDIA Isaac GR00T blueprint for synthetic manipulation motion generation is the ideal place to start. This is a reference workflow for creating exponentially large amounts of synthetic motion trajectories for robot manipulation from a small number of human demonstrations, built on [NVIDIA Omniverse™](https://developer.nvidia.com/isaac/sim) and [NVIDIA Cosmos™](https://www.nvidia.com/en-us/ai/cosmos/).

![image](https://github.com/user-attachments/assets/f3621fcc-91c3-4f4d-a516-c9c9c7f0d339)


# Deploy On Local Workstation

## Prerequisites
**Requirements for local deployment:**
* Ubuntu 22.04 Operating System
* NVIDIA GPU (RTX A 6000 with 48GB VRAM)
* [NVIDIA GPU Driver](https://www.nvidia.com/en-us/drivers/unix/) (recommended version 535.129.03)
* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) (minimum version 1.17.0)

**Requirements for NVIDIA Cosmos:**
* NVIDIA GPU (H100 or higher) with 80GB of VRAM.
  * NVIDIA H100 GPU is available on AWS in a P5 EC2 instance, GCP in a A3 machine type VM and Azure in a ND H100 v5 series VM
* Visit the [Cosmos Hugging Face Model](https://huggingface.co/nvidia/Cosmos-Transfer1-7B) for specific details
>[!NOTE]
NVIDIA Cosmos must be run on a node separate from the Isaac Lab simulation due to differing hardware requirements.

## Launch a Jupyter Notebook

Steps:

1. Clone this repository to your local workstation and navigate to this repository.

       git clone https://github.com/NVIDIA-Omniverse-blueprints/synthetic-manipulation-motion-generation.git
       cd synthetic-manipulation-motion-generation

2. Enable X11 forwarding for a local workstation user.

       xhost +local:

3. Deploy the Jupyter Notebook with the Blueprint container.

       docker compose -f docker-compose.yml up -d
       
4. Access the Jupyter Notebook from a browser at http://localhost:8888/lab/tree/generate_dataset.ipynb.

5. Follow the instructions inside of the Jupyter Notebook.

6. Run the command below to stop the Jupyter Notebook and end the demo.

       docker compose -f docker-compose.yml down

>[!NOTE]
The Blueprint container includes a pre-installed version of Isaac Lab 2.0.2 and Isaac Sim 4.5.0.

# Deploy On RHOAI Cluster

## Prerequisites
**Requirements for Isaac Lab:**
* Red Hat OpenShift AI cluster with GPU-enabled nodes
* NVIDIA GPU (RTX A 6000 with 48GB VRAM)
* [NVIDIA GPU Driver](https://www.nvidia.com/en-us/drivers/unix/) (recommended version 535.129.03)

**Requirements for self-hosted NVIDIA NIM Cosmos:**
* In this RHOAI demo, we used [Cosmos-Transfer2.5-2B](https://build.nvidia.com/nvidia/cosmos-transfer2_5-2b), a more efficient and lightweight model for video-to-video style transfer, with enhanced control capabilities and faster inference times, supported on NIM
* Requirements are as described above for the Cosmos-Transfer1-7B model
* Visit the [Cosmos-Transfer2.5-2B configuration documentation](https://docs.nvidia.com/nim/cosmos/2.0.0/support-matrix.html#configurations-for-cosmos-transfer2-5-2b) for specific requirement details

## Deploy Notebook Image

Steps:

1. Build and register the Isaac Lab notebook image in RHOAI.

       ./deploy/deploy-isaac-lab-image.sh

2. Create a workbench in RHOAI Dashboard:
   * Navigate to RHOAI Dashboard → Data Science Projects
   * Create new project (if needed)
   * Click "Create workbench"
   * Select "Isaac Lab" from notebook image dropdown
   * Configure:
     * Container size: Large
     * GPU: 1x NVIDIA GPU (according to prerequisites)
   * Click Create

3. Access the Jupyter Notebook from the workbench URL provided by RHOAI.

4. Follow the instructions inside of the Jupyter Notebook.

**To rebuild after code changes:**

    oc start-build isaac-lab --from-dir=. --follow -n nvidia-omniverse-blueprint
    oc tag nvidia-omniverse-blueprint/isaac-lab:latest nvidia-omniverse-blueprint/isaac-lab:1.0

# Licenses

By running the docker compose command, you accept the terms and conditions of all the licenses below:

- [Isaac Sim](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/)
- [Isaac Lab](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE)
- [Isaac Lab mimic](https://github.com/isaac-sim/IsaacLab/blob/main/LICENSE-mimic)
- [Cosmos NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)
