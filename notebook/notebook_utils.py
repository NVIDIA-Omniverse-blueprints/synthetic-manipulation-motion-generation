import os
import warp as wp
import numpy as np
from PIL import Image


# Set directories to use for inputs/outputs
ISAACLAB_OUTPUT_DIR = "_isaaclab_out"
COSMOS_OUTPUT_DIR = "_cosmos_out"

# Video and rendering settings
DEFAULT_FRAMERATE = 24.0
DEFAULT_LIGHT_DIRECTION = (0.0, 0.0, 1.0)  # Points straight down at surface


@wp.kernel
def _shade_segmentation(
    segmentation: wp.array3d(dtype=wp.uint8),
    normals: wp.array3d(dtype=wp.float32),
    shading_out: wp.array3d(dtype=wp.uint8),
    light_source: wp.array(dtype=wp.vec3f),
):
    """Apply shading to semantic segmentation using surface normals.

    Args:
        segmentation: Input semantic segmentation image (H,W,C)
        normals: Surface normal vectors (H,W,3)
        shading_out: Output shaded segmentation image (H,W,C)
        light_source: Position of light source
    """
    i, j = wp.tid()
    normal = normals[i, j]
    light_source_vec = wp.normalize(light_source[0])
    shade = 0.5 + wp.dot(wp.vec3f(normal[0], normal[1], normal[2]), light_source_vec) * 0.5

    shading_out[i, j, 0] = wp.uint8(wp.float32(segmentation[i, j, 0]) * shade)
    shading_out[i, j, 1] = wp.uint8(wp.float32(segmentation[i, j, 1]) * shade)
    shading_out[i, j, 2] = wp.uint8(wp.float32(segmentation[i, j, 2]) * shade)
    shading_out[i, j, 3] = wp.uint8(255)

def get_trial_frames(root_dir: str, camera_name: str, min_frames: int = 30) -> dict:
    """Get the last frame number for each trial in the dataset.
    
    Args:
        root_dir: Directory containing the frames
        camera_name: Name of the camera used
        min_frames: Minimum number of frames required for a valid trial
        
    Returns:
        dict: Dictionary mapping trial numbers to (start_frame, end_frame) tuples
    """
    import re
    
    # Pattern to match trial and frame numbers
    pattern = f"{camera_name}_semantic_segmentation_trial_(\d+)_env_0_step_(\d+).png"
    
    trial_frames = {}
    for filename in os.listdir(root_dir):
        match = re.match(pattern, filename)
        if match:
            trial_num = int(match.group(1))
            frame_num = int(match.group(2))
            
            if trial_num not in trial_frames:
                trial_frames[trial_num] = []
            trial_frames[trial_num].append(frame_num)
            

    valid_trials = {}
    for trial_num, frames in sorted(trial_frames.items()):
        # Skip if not enough frames
        if len(frames) < min_frames:
            continue
            
        # Sort frames and get range
        frames.sort()
        start_frame = frames[0]
        end_frame = frames[-1]
        
        # Verify frame sequence is continuous
        expected_frames = set(range(start_frame, end_frame + 1))
        actual_frames = set(frames)
        if len(expected_frames - actual_frames) > 0:
            continue
            
        valid_trials[trial_num] = (start_frame, end_frame)
    
    return valid_trials

def encode_video(root_dir: str, start_frame: int, num_frames: int, camera_name: str, output_path: str, trial_num: int) -> None:
    """Encode a sequence of shaded segmentation frames into a video.

    Args:
        root_dir: Directory containing the input frames
        start_frame: Starting frame index
        num_frames: Number of frames to encode
        camera_name: Name of the camera (used in filename pattern)
        output_path: Output path for the encoded video
        trial_num: Trial number for the sequence

    Raises:
        ValueError: If start_frame is negative or if any required frame is missing
    """
    from video_encoding import get_video_encoding_interface

    if start_frame < 0:
        raise ValueError("start_frame must be non-negative")
    if num_frames <= 0:
        raise ValueError("num_frames must be positive")

    # Validate all frames exist before starting
    for frame_idx in range(start_frame, start_frame + num_frames):
        file_path_normals = os.path.join(root_dir, f"{camera_name}_normals_trial_{trial_num}_env_0_step_{frame_idx}.png")
        file_path_segmentation = os.path.join(root_dir, f"{camera_name}_semantic_segmentation_trial_{trial_num}_env_0_step_{frame_idx}.png")
        if not os.path.exists(file_path_normals) or not os.path.exists(file_path_segmentation):
            raise ValueError(f"Missing frame at frame index {frame_idx} for trial {trial_num}")

    # Initialize video encoding
    video_encoding = get_video_encoding_interface()
    
    # Get dimensions from first frame
    first_frame = np.array(Image.open(os.path.join(
        root_dir, f"{camera_name}_semantic_segmentation_trial_{trial_num}_env_0_step_{start_frame}.png")))
    height, width = first_frame.shape[:2]
    
    # Pre-allocate buffers
    normals_wp = wp.empty((height, width, 3), dtype=wp.float32, device="cuda")
    segmentation_wp = wp.empty((height, width, 4), dtype=wp.uint8, device="cuda")
    shaded_segmentation_wp = wp.empty_like(segmentation_wp)
    light_source = wp.array(DEFAULT_LIGHT_DIRECTION, dtype=wp.vec3f, device="cuda")

    video_encoding.start_encoding(
        video_filename=output_path,
        framerate=DEFAULT_FRAMERATE,
        nframes=num_frames,
        overwrite_video=True,
    )

    for frame_idx in range(start_frame, start_frame + num_frames):
        file_path_normals = os.path.join(root_dir, f"{camera_name}_normals_trial_{trial_num}_env_0_step_{frame_idx}.png")
        file_path_segmentation = os.path.join(root_dir, f"{camera_name}_semantic_segmentation_trial_{trial_num}_env_0_step_{frame_idx}.png")
        
        # Load and copy data to existing buffers
        normals_np = np.array(Image.open(file_path_normals)).astype(np.float32) / 255.0
        wp.copy(normals_wp, wp.from_numpy(normals_np))
        
        segmentation_np = np.array(Image.open(file_path_segmentation))
        wp.copy(segmentation_wp, wp.from_numpy(segmentation_np))
    
        # Launch kernel
        wp.launch(_shade_segmentation, dim=(height, width), inputs=[segmentation_wp, normals_wp, shaded_segmentation_wp, light_source])
        
        # Encode frame
        video_encoding.encode_next_frame_from_buffer(shaded_segmentation_wp.numpy().tobytes(), width=width, height=height)
