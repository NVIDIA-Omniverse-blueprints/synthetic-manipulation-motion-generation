from flask import Flask, request, jsonify, send_file
import subprocess
import os
import json
from werkzeug.utils import secure_filename
import uuid
import shutil
import threading
from typing import Dict, Optional
import time

app = Flask(__name__)

# Configure folders
UPLOAD_FOLDER = "temp_uploads"
OUTPUT_FOLDER = "temp_outputs"
ALLOWED_EXTENSIONS = {"mp4"}
CONTROL2WORLD_PATH = "cosmos_transfer1/diffusion/inference/control2world.py"

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Store job information
class JobStatus:
    def __init__(self):
        self.status: str = "processing"  # processing, completed, failed
        self.error: Optional[str] = None
        self.output_path: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None
        self.upload_dir: str = ""
        self.output_dir: str = ""

# Global job storage
jobs: Dict[str, JobStatus] = {}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def process_video_job(job_id: str, output_video_path: str, cmd: list, env: dict):
    """Background processing function."""
    job = jobs[job_id]
    
    try:
        # Execute the command
        print("Executing command: ", cmd)
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        job.process = process
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            job.status = "failed"
            job.error = f"Command failed: {stderr}"
            return
        
        # Check if output file exists
        if not os.path.exists(output_video_path):
            job.status = "failed"
            job.error = "Output video file was not generated"
            return
        
        job.status = "completed"
        job.output_path = output_video_path
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)

@app.route("/")
def home():
    return jsonify({
        "message": "Cosmos Canny API",
        "endpoints": {
            "/canny/submit": "POST - Submit a video processing job",
            "/canny/status/<job_id>": "GET - Check job status",
            "/canny/result/<job_id>": "GET - Download completed video"
        }
    })

@app.route("/canny/submit", methods=["POST"])
def submit_job():
    # Check if video file is present in request
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No selected video file"}), 400
    
    if not allowed_file(video_file.filename):
        return jsonify({"error": "Invalid file type. Only MP4 files are allowed"}), 400

    # Generate unique ID for this request
    job_id = str(uuid.uuid4())
    
    # Create unique directories for this request
    request_upload_dir = os.path.join(UPLOAD_FOLDER, job_id)
    request_output_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(request_upload_dir, exist_ok=True)
    os.makedirs(request_output_dir, exist_ok=True)

    # Save the uploaded video
    input_video_path = os.path.join(request_upload_dir, secure_filename(video_file.filename))
    video_file.save(input_video_path)
    
    # Get parameters from the request
    data = request.form.to_dict()
    if not data:
        return jsonify({"error": "No parameters provided"}), 400
    
    required_params = [
        "prompt",
        "sigma_max",
        "control_weight",
        "canny_strength",
        "seed",
    ]
    
    # Check for required parameters
    missing_params = [param for param in required_params if param not in data]
    if missing_params:
        return jsonify({"error": f"Missing required parameters: {', '.join(missing_params)}"}), 400

    # Set output video path
    output_video_name = "output"
    output_video_path = os.path.join(request_output_dir, f"{output_video_name}.mp4")

    # Create controlnet specs
    controlnet_specs = {
        "canny": {
            "control_weight": float(data["control_weight"]),
        },
    }
    specs_path = os.path.join(request_output_dir, "controlnet_specs.json")
    with open(specs_path, "w") as f:
        json.dump(controlnet_specs, f)

    # Construct the command
    cmd = [
        "python",
        CONTROL2WORLD_PATH,
        "--prompt", data["prompt"],
        "--blur_or_canny_str", str(data["canny_strength"]),
        "--input_video_path", input_video_path,
        "--video_save_name", output_video_name,
        "--video_save_folder", request_output_dir,
        "--sigma_max", str(data["sigma_max"]),
        "--controlnet_specs", specs_path,
        "--seed", str(data["seed"]),
    ]
    
    try:
        # Set PYTHONPATH environment variable
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        # Create job status object
        job_status = JobStatus()
        job_status.upload_dir = request_upload_dir
        job_status.output_dir = request_output_dir
        jobs[job_id] = job_status
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_video_job,
            args=(job_id, output_video_path, cmd, env)
        )
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "processing",
            "message": "Job submitted successfully"
        })
        
    except Exception as e:
        # Clean up on error
        shutil.rmtree(request_upload_dir, ignore_errors=True)
        shutil.rmtree(request_output_dir, ignore_errors=True)
        if job_id in jobs:
            del jobs[job_id]
        return jsonify({"error": f"Error starting job: {str(e)}"}), 500

@app.route("/canny/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    response = {
        "status": job.status
    }
    
    if job.error:
        response["error"] = job.error
    
    return jsonify(response)

@app.route("/canny/result/<job_id>", methods=["GET"])
def get_job_result(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job.status != "completed":
        return jsonify({"error": "Job not completed"}), 400
    
    if not job.output_path or not os.path.exists(job.output_path):
        return jsonify({"error": "Output file not found"}), 500
    
    try:
        return_data = send_file(
            job.output_path,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="output"
        )
        
        # Clean up after sending
        def cleanup():
            time.sleep(1)  # Wait a bit to ensure file is sent
            shutil.rmtree(job.upload_dir, ignore_errors=True)
            shutil.rmtree(job.output_dir, ignore_errors=True)
            del jobs[job_id]
        
        thread = threading.Thread(target=cleanup)
        thread.start()
        
        return return_data
        
    except Exception as e:
        return jsonify({"error": f"Error sending output file: {str(e)}"}), 500

if __name__ == "__main__":
    if not os.path.exists(CONTROL2WORLD_PATH):
        raise ValueError(f"Control2World at `{CONTROL2WORLD_PATH}` not found - please place `app.py` in the root directory of cosmos_transfer1 or alter the path to the new location of `control2world.py`.")
    app.run(debug=True, host="0.0.0.0", port=5000)
