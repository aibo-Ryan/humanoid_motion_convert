"""
PM01 Robot Motion Visualizer using IsaacGym

Features:
1. Dynamic joint visualization configuration
2. Spherical markers for joint positions (using draw_lines)
3. Loop playback of motion data
4. Support for PKL motion files
"""

import os
import sys
import pickle
import argparse
import tempfile
import shutil

# IMPORTANT: Import isaacgym BEFORE torch
from isaacgym import gymapi, gymutil, gymtorch

import numpy as np
import torch

from types import ModuleType
import numpy as np
import sys
# Patch sys.modules to fake missing modules from numpy 2.x
class FakeModule(ModuleType):
    def __init__(self, name, real=None):
        super().__init__(name)
        if real:
            self.__dict__.update(real.__dict__)

# Patch potentially missing modules
sys.modules['numpy._core'] = FakeModule('numpy._core', np.core if hasattr(np, 'core') else np)
sys.modules['numpy._core.multiarray'] = FakeModule('numpy._core.multiarray', getattr(np.core, 'multiarray', None))


# Store original argv for later
_original_argv = sys.argv.copy()


# Configuration for joint visualization
class JointVisualizationConfig:
    """Configuration for which joints to visualize"""
    
    # All available PM01 joints (link names)
    ALL_JOINTS = [
        'LINK_BASE',
        'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L',
        'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L',
        'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R',
        'LINK_KNEE_PITCH_R', 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R',
        'LINK_TORSO_YAW',
        'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L',
        'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L',
        'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R',
        'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R',
        'LINK_HEAD_YAW'
    ]
    
    # Preset configurations
    PRESETS = {
        'all': ALL_JOINTS,
        'lower_body': [
            'LINK_BASE',
            'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L',
            'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L',
            'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R',
            'LINK_KNEE_PITCH_R', 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R',
        ],
        'upper_body': [
            'LINK_BASE', 'LINK_TORSO_YAW',
            'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L',
            'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L',
            'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R',
            'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R',
            'LINK_HEAD_YAW'
        ],
        'legs_only': [
            'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L',
            'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L',
            'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R',
            'LINK_KNEE_PITCH_R', 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R',
        ],
        'arms_only': [
            'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L',
            'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L',
            'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R',
            'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R',
        ],
        'key_points': [
            'LINK_BASE', 'LINK_FOOT_L', 'LINK_FOOT_R',
            'LINK_ELBOW_END_L', 'LINK_ELBOW_END_R', 'LINK_HEAD_YAW'
        ]
    }


class PM01MotionLoader:
    """Loader for PM01 robot motion PKL files"""
    
    def __init__(self, motion_file, device='cuda:0'):
        self.motion_file = motion_file
        self.device = device
        self._load_motion()
        
    def _load_motion(self):
        """Load motion data from PKL file"""
        if not os.path.exists(self.motion_file):
            raise FileNotFoundError(f"Motion file not found: {self.motion_file}")

        import sys as _sys
        _twist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'input_twist_pkl')
        if _twist_dir not in _sys.path:
            _sys.path.insert(0, _twist_dir)
        from pkl_loader import load_pkl
        motion_data = load_pkl(self.motion_file)
        
        self.fps = motion_data.get('fps', 30.0)
        self.dt = 1.0 / self.fps
        
        # Convert numpy arrays to torch tensors
        self.root_pos = torch.tensor(motion_data['root_pos'], dtype=torch.float32, device=self.device)
        self.root_rot = torch.tensor(motion_data['root_rot'], dtype=torch.float32, device=self.device)
        self.dof_pos = torch.tensor(motion_data['dof_pos'], dtype=torch.float32, device=self.device)
        
        # Local body positions if available
        if 'local_body_pos' in motion_data:
            self.local_body_pos = torch.tensor(motion_data['local_body_pos'], dtype=torch.float32, device=self.device)
        else:
            self.local_body_pos = None
            
        self.link_body_list = motion_data.get('link_body_list', JointVisualizationConfig.ALL_JOINTS)
        self.num_frames = self.root_pos.shape[0]
        self.duration = self.num_frames * self.dt
        
        print(f"[MotionLoader] Loaded motion: {self.num_frames} frames, "
              f"FPS: {self.fps:.1f}, Duration: {self.duration:.2f}s")
        print(f"[MotionLoader] Links: {len(self.link_body_list)}")
        
    def get_frame_at_time(self, time):
        """Get motion frame at specific time (with looping)"""
        # Loop the motion smoothly
        loop_time = time % self.duration if self.duration > 0 else 0
        frame_idx = min(int(loop_time / self.dt), self.num_frames - 1)
        
        return {
            'root_pos': self.root_pos[frame_idx:frame_idx+1],
            'root_rot': self.root_rot[frame_idx:frame_idx+1],
            'dof_pos': self.dof_pos[frame_idx:frame_idx+1],
            'local_body_pos': self.local_body_pos[frame_idx:frame_idx+1] if self.local_body_pos is not None else None,
            'frame_idx': frame_idx
        }


def parse_arguments():
    """Parse command line arguments"""
    # Create parser for our custom args (add_help=False to avoid conflict)
    parser = argparse.ArgumentParser(description='PM01 Robot Motion Visualizer', add_help=False)
    
    parser.add_argument('--motion_file', type=str, required=True,
                        help='Path to PKL motion file')
    parser.add_argument('--asset_file', type=str,
                        default='pm01_description/urdf/serial_pm_v2.urdf',
                        help='Path to robot URDF file')
    parser.add_argument('--joint_preset', type=str, default='all',
                        choices=list(JointVisualizationConfig.PRESETS.keys()),
                        help='Joint visualization preset')
    parser.add_argument('--visible_joints', type=str, nargs='+', default=None,
                        help='Specific joint names to visualize (overrides preset)')
    parser.add_argument('--sphere_radius', type=float, default=0.06,
                        help='Radius of joint visualization spheres')
    parser.add_argument('--sphere_color', type=float, nargs=3, default=[1.0, 0.0, 0.0],
                        help='RGB color of spheres (0-1 range)')
    parser.add_argument('--speed_scale', type=float, default=1.0,
                        help='Playback speed multiplier')
    parser.add_argument('--device', type=str, default='cuda:0',
                        help='Device for computation')
    
    # Parse only our args, ignore unknown args (for IsaacGym)
    args, remaining = parser.parse_known_args()
    
    # Store remaining args for IsaacGym
    args._remaining = remaining
    
    return args


def create_fixed_urdf(original_path):
    """Create a temporary URDF with absolute mesh paths"""
    with open(original_path, 'r') as f:
        urdf_content = f.read()
    
    # Replace relative mesh paths with absolute paths
    asset_root = os.path.dirname(original_path)
    meshes_dir = os.path.abspath(os.path.join(asset_root, '../meshes'))
    urdf_content = urdf_content.replace('filename="../meshes/', f'filename="{meshes_dir}/')
    
    # Write temporary URDF
    temp_dir = tempfile.mkdtemp()
    temp_urdf_path = os.path.join(temp_dir, 'fixed_pm01.urdf')
    with open(temp_urdf_path, 'w') as f:
        f.write(urdf_content)
    
    return temp_dir, temp_urdf_path


def main():
    args = parse_arguments()
    
    # Determine which joints to visualize
    if args.visible_joints:
        visible_joints = args.visible_joints
    else:
        visible_joints = JointVisualizationConfig.PRESETS[args.joint_preset]
    
    print(f"[Config] Visualizing {len(visible_joints)} joints: {visible_joints}")
    
    # Initialize IsaacGym
    gym = gymapi.acquire_gym()
    
    # Parse arguments for IsaacGym (pass remaining args)
    sys.argv = [sys.argv[0]] + args._remaining
    sim_args = gymutil.parse_arguments(description="PM01 Motion Visualizer")
    
    # Use CPU device for CPU pipeline
    device = 'cpu'
    
    # Load motion data (on CPU)
    motion_loader = PM01MotionLoader(args.motion_file, device=device)
    
    # Configure simulation (use CPU pipeline for compatibility)
    sim_params = gymapi.SimParams()
    sim_params.dt = 1.0 / 60.0
    sim_params.up_axis = gymapi.UP_AXIS_Z
    sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.81)
    sim_params.physx.solver_type = 1
    sim_params.physx.num_position_iterations = 6
    sim_params.physx.num_velocity_iterations = 0
    sim_params.physx.num_threads = sim_args.num_threads
    sim_params.physx.use_gpu = False  # Use CPU for physics
    sim_params.use_gpu_pipeline = False  # Use CPU pipeline
    
    sim = gym.create_sim(sim_args.compute_device_id, sim_args.graphics_device_id, 
                         gymapi.SIM_PHYSX, sim_params)
    if sim is None:
        raise RuntimeError("Failed to create simulation")
    
    # Add ground plane
    plane_params = gymapi.PlaneParams()
    plane_params.normal = gymapi.Vec3(0.0, 0.0, 1.0)
    gym.add_ground(sim, plane_params)
    
    # Create viewer
    viewer = gym.create_viewer(sim, gymapi.CameraProperties())
    if viewer is None:
        raise RuntimeError("Failed to create viewer")
    
    # Set camera position
    gym.viewer_camera_look_at(viewer, None, 
                              gymapi.Vec3(2.0, -2.0, 1.5),
                              gymapi.Vec3(0.0, 0.0, 0.5))
    
    # Load robot asset with fixed URDF
    asset_path = os.path.abspath(args.asset_file)
    temp_dir, temp_urdf_path = create_fixed_urdf(asset_path)
    
    try:
        asset_root = os.path.dirname(temp_urdf_path)
        asset_file = os.path.basename(temp_urdf_path)
        
        asset_options = gymapi.AssetOptions()
        asset_options.fix_base_link = False
        asset_options.use_mesh_materials = True
        
        print(f"[Asset] Loading from: {asset_root}/{asset_file}")
        asset = gym.load_asset(sim, asset_root, asset_file, asset_options)
        
        num_dofs = gym.get_asset_dof_count(asset)
        print(f"[Asset] Loaded robot with {num_dofs} DOFs")
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir)
    
    # Create environment
    num_envs = 1
    num_per_row = 1
    spacing = 5.0
    env_lower = gymapi.Vec3(-spacing, -spacing, 0.0)
    env_upper = gymapi.Vec3(spacing, spacing, spacing)
    
    env = gym.create_env(sim, env_lower, env_upper, num_per_row)
    
    # Add actor
    pose = gymapi.Transform()
    pose.p = gymapi.Vec3(0.0, 0.0, 0.0)
    pose.r = gymapi.Quat(0.0, 0.0, 0.0, 1.0)
    
    actor_handle = gym.create_actor(env, asset, pose, "pm01", 0, 1)
    
    # Set initial DOF states
    dof_states = np.zeros(num_dofs, dtype=gymapi.DofState.dtype)
    gym.set_actor_dof_states(env, actor_handle, dof_states, gymapi.STATE_ALL)
    
    # Prepare simulation
    gym.prepare_sim(sim)
    
    # Acquire tensors
    actor_root_state = gym.acquire_actor_root_state_tensor(sim)
    actor_root_state = gymtorch.wrap_tensor(actor_root_state)
    
    rigid_body_state = gym.acquire_rigid_body_state_tensor(sim)
    rigid_body_state = gymtorch.wrap_tensor(rigid_body_state)
    
    dof_state_tensor = gym.acquire_dof_state_tensor(sim)
    dof_state_tensor = gymtorch.wrap_tensor(dof_state_tensor)
    
    # Environment IDs for indexed updates (on CPU)
    env_ids = torch.arange(num_envs, dtype=torch.int32, device='cpu')
    
    print(f"[Visualization] Ready to visualize {len(visible_joints)} joints")
    
    # Simulation loop
    time_step = 0.0
    frame_count = 0
    dt = sim_params.dt
    
    print("[Running] Press ESC or close window to exit")
    
    # Sphere geometry for joint visualization
    sphere_radius = args.sphere_radius
    sphere_color = tuple(args.sphere_color)
    
    while not gym.query_viewer_has_closed(viewer):
        # Get current motion frame
        motion_frame = motion_loader.get_frame_at_time(time_step)
        
        # Update root state
        root_pos = motion_frame['root_pos']
        root_rot = motion_frame['root_rot']
        root_vel = torch.zeros_like(root_pos)
        root_ang_vel = torch.zeros_like(root_pos)
        
        root_states = torch.cat([root_pos, root_rot, root_vel, root_ang_vel], dim=-1)
        root_states = root_states.repeat(num_envs, 1)
        
        # Use indexed update
        gym.set_actor_root_state_tensor_indexed(
            sim, 
            gymtorch.unwrap_tensor(root_states),
            gymtorch.unwrap_tensor(env_ids),
            len(env_ids)
        )
        
        gym.refresh_actor_root_state_tensor(sim)
        
        # Update DOF positions
        dof_pos = motion_frame['dof_pos']
        dof_vel = torch.zeros_like(dof_pos)
        dof_state = torch.stack([dof_pos, dof_vel], dim=-1).squeeze().repeat(num_envs, 1)
        
        gym.set_dof_state_tensor_indexed(
            sim,
            gymtorch.unwrap_tensor(dof_state),
            gymtorch.unwrap_tensor(env_ids),
            len(env_ids)
        )
        
        # Step simulation
        gym.simulate(sim)
        gym.fetch_results(sim, True)
        
        # Refresh rigid body states for visualization
        gym.refresh_rigid_body_state_tensor(sim)
        
        # Clear previous frame lines
        gym.clear_lines(viewer)
        
        # Draw joint spheres
        if motion_frame['local_body_pos'] is not None:
            body_positions = motion_frame['local_body_pos'][0]  # [num_links, 3] local positions
            root_pos = motion_frame['root_pos'][0]  # [3] root position
            root_rot = motion_frame['root_rot'][0]  # [4] root rotation (quaternion: w, x, y, z)
            
            # Convert quaternion to rotation matrix
            # PKL format: (x, y, z, w)
            x, y, z, w = root_rot[0], root_rot[1], root_rot[2], root_rot[3]
            
            # Build rotation matrix
            R = torch.zeros((3, 3), dtype=torch.float32)
            R[0, 0] = 1 - 2*(y*y + z*z)
            R[0, 1] = 2*(x*y - w*z)
            R[0, 2] = 2*(x*z + w*y)
            R[1, 0] = 2*(x*y + w*z)
            R[1, 1] = 1 - 2*(x*x + z*z)
            R[1, 2] = 2*(y*z - w*x)
            R[2, 0] = 2*(x*z - w*y)
            R[2, 1] = 2*(y*z + w*x)
            R[2, 2] = 1 - 2*(x*x + y*y)
            
            for joint_name in visible_joints:
                if joint_name in motion_loader.link_body_list:
                    joint_idx = motion_loader.link_body_list.index(joint_name)
                    # Convert local position to world position
                    local_pos = body_positions[joint_idx]
                    # Rotate local position by root rotation, then add root position
                    rotated_pos = R @ local_pos
                    world_pos = rotated_pos + root_pos
                    
                    # Create sphere geometry and draw
                    sphere_geom = gymutil.WireframeSphereGeometry(
                        sphere_radius, 8, 8, None, color=sphere_color
                    )
                    sphere_pose = gymapi.Transform(
                        gymapi.Vec3(world_pos[0].item(), world_pos[1].item(), world_pos[2].item())
                    )
                    gymutil.draw_lines(sphere_geom, gym, viewer, env, sphere_pose)
        
        # Update viewer
        gym.step_graphics(sim)
        gym.draw_viewer(viewer, sim, True)
        
        # Sync frame time
        gym.sync_frame_time(sim)
        
        # Update time
        time_step += dt * args.speed_scale
        frame_count += 1
        
        # Print progress
        if frame_count % 60 == 0:
            loop_count = int(time_step / motion_loader.duration)
            print(f"\r[Playback] Loop: {loop_count}, Time: {time_step % motion_loader.duration:.2f}s", 
                  end='', flush=True)
    
    print("\n[Done] Visualization ended")
    
    # Cleanup
    gym.destroy_viewer(viewer)
    gym.destroy_sim(sim)


if __name__ == '__main__':
    main()
