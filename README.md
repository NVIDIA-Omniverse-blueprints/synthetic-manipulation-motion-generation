# synthetic-motion-generation

Multiply human captured teleop data utilizing Isaac Lab Mimic and GR00T-Gen

# Using Brev

## Deploy Brev Launchable

From build.nvidia.com/nvidia/synthetic-motion-generation, click on the "Deploy Launchable" button to deploy and connect to the Brev Launchable instance.

[NVIDIA Brev](https://developer.nvidia.com/brev) NVIDIA Brev provides streamlined access to NVIDIA GPU instances to run containers in the cloud. No local install needed!

If you do not have an account with Brev, you will be prompted to create one and be provided with a limited number of free credits to use.

## Launch a Jupyter Notebook from Brev

When the Brev instance is ready, click the `Open Notebook` button to launch the Jupyter Notebook for this demo.

Follow the instructions within the notebook to run the demo.

### (optional) Change scenario parameters and generate new motion trajectories

Follow the instructions in the Jupyter notebook to change values within the Isaac Lab scenario to generate new motion trajectories or update the simulation environment.

## Create a prompt to generate a new world environment

Lastly, inside of the Jupyter notebook, create a prompt to generate a new world environment for your simulation.  This will use NVIDIA Cosmos to generate a new world environment video and display it inside of your notebook for viewing.

# Using Local Isaac Lab

* If you have not already, [install Isaac Sim and Isaac Lab](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html).

* Install Docker on your local machine

* Clone this repository to your local machine

* Launch a terminal and navigate to this repository

* Run `docker compose`
