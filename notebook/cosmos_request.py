import requests
import os
import socket
from urllib.parse import urlparse
import time


def test_connection(url):
    """Test basic connectivity to the server."""
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    try:
        # Try to establish a TCP connection
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return True, None
    except socket.timeout:
        return False, f"Connection timed out when trying to reach {host}:{port}"
    except socket.gaierror:
        return False, f"DNS resolution failed for {host}"
    except ConnectionRefusedError:
        return False, f"Connection refused by {host}:{port}"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"


def process_video(
    url: str,
    video_path: str,
    output_path: str,
    prompt: str,
    sigma_max: float = 70,
    control_weight: float = 0.5,
    canny_strength: str = "medium",
    seed: int = 42,
    poll_interval: int = 10,
    max_poll_time: int = 3600,
) -> requests.Response:
    """
    Process a video using the NVCF API.

    Args:
        url (str): The base URL of the NVCF API.
        video_path (str): The path to the video file to process.
        output_path (str): The path to save the processed video.
        prompt (str): The prompt to use to condition the Cosmos model.
        sigma_max (float): The maximum sigma value.
        control_weight (float): Controls how strongly the control input should affect the output.
        canny_strength (str): The strength of the canny edge detection.
        seed (int): The seed for the random number generator.
        poll_interval (int): How often to poll for job completion (seconds).
        max_poll_time (int): Maximum time to wait for job completion (seconds).
    """

    if not os.path.exists(video_path):
        raise ValueError(f"Video file not found at {video_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Test connection first
    print(f"Testing connection to {url}...")
    success, message = test_connection(url)
    if not success:
        print(f"Connection test failed: {message}")
        print("Please check:")
        print("1. If the server is running")
        print("2. If the IP address and port are correct")
        print("3. If there are any firewalls blocking the connection")
        print("4. If the server is accessible from your network")
        return None

    # Parameters for the request
    params = {
        "prompt": f"\"{prompt}\"",
        "sigma_max": sigma_max,
        "control_weight": control_weight,
        "canny_strength": canny_strength.lower().replace(" ", "_"),
        "seed": seed,
    }
    
    submit_url = f"{url}/canny/submit"
    status_url = f"{url}/canny/status"
    result_url = f"{url}/canny/result"
    
    try:
        # Submit the job
        print("Submitting video processing job...")
        files = {
            'video': ('video.mp4', open(video_path, 'rb'), 'video/mp4')
        }
        
        try:
            # Submit the job with a shorter timeout
            response = requests.post(
                submit_url,
                data=params,
                files=files,
                timeout=90,
                verify=False
            )
            
            if response.status_code != 200:
                print(f"Error submitting job: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except ValueError:
                    print(f"Error details: {response.text}")
                return None
            
            # Get job ID from response
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"Job submitted successfully. Job ID: {job_id}")
            
            # Poll for completion
            start_time = time.time()
            while True:
                if time.time() - start_time > max_poll_time:
                    print(f"Maximum polling time ({max_poll_time}s) exceeded")
                    return None
                
                try:
                    status_response = requests.get(
                        f"{status_url}/{job_id}",
                        timeout=30,
                        verify=False
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data['status']
                        
                        if status == 'completed':
                            print("Processing completed successfully!")
                            break
                        elif status == 'failed':
                            print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                            return None
                        else:
                            print(f"Status: {status}")
                    else:
                        print(f"Error checking status: HTTP {status_response.status_code}")
                        return None
                        
                except requests.RequestException as e:
                    print(f"Error checking status: {e}")
                    # Continue polling despite temporary errors
                
                time.sleep(poll_interval)
            
            # Download the result
            print("Downloading processed video...")
            result_response = requests.get(
                f"{result_url}/{job_id}",
                timeout=90,
                verify=False,
                stream=True
            )
            
            if result_response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in result_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"Video successfully downloaded and saved to {output_path}")
                return result_response
            else:
                print(f"Error downloading result: HTTP {result_response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("Request timed out")
        except requests.exceptions.SSLError:
            print("SSL/TLS error occurred. If using self-signed certificates, verify=False is already set.")
        except requests.exceptions.ConnectionError as e:
            print(f"Failed to connect to the server: {e}")
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            
    finally:
        # Ensure the file is closed
        if 'files' in locals():
            files['video'][1].close()
    
    return None
