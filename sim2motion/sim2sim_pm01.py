#!/usr/bin/env python3
"""
Sim2Sim with Data Recording for PM01 Robot
Features:
1. Run Mujoco simulation with policy control
2. Record robot state data (pose, joint angles, etc.)
3. Save data as both PKL and CSV formats
4. GUI interface with Start/Stop recording buttons
"""

import tkinter as tk
from tkinter import ttk
import threading
import numpy as np
from datetime import datetime
import os
from collections import deque
import math
from scipy.spatial.transform import Rotation as R

# Import isaacgym related modules first
from legged_gym.envs import PM01Cfg
from legged_gym import LEGGED_GYM_ROOT_DIR

# Import other modules
import mujoco, mujoco_viewer
import pickle
import pandas as pd
import torch

# Global variables for data recording
recording = False
data_buffer = []
record_start_time = None


class RecordingGUI:
    """Simple GUI for controlling data recording"""
    
    def __init__(self, root, start_callback, stop_callback):
        self.root = root
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        
        self.root.title("Sim2Sim Data Recorder")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="PM01 Robot Data Recorder", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Status
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Helvetica", 10))
        status_label.pack(pady=(0, 10))
        
        # Frame counter
        self.frame_counter_var = tk.StringVar(value="Frames: 0")
        frame_counter_label = ttk.Label(main_frame, textvariable=self.frame_counter_var, font=("Helvetica", 10))
        frame_counter_label.pack(pady=(0, 20))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Start button
        self.start_button = ttk.Button(
            button_frame,
            text="Start Recording",
            command=self.start_recording,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Recording",
            command=self.stop_recording,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # Info
        info_label = ttk.Label(
            main_frame,
            text="Data will be saved in current directory",
            font=("Helvetica", 8),
            foreground="gray"
        )
        info_label.pack(pady=(20, 0))


    
    def start_recording(self):
        global recording, data_buffer, record_start_time
        if not recording:
            recording = True
            data_buffer = []
            record_start_time = datetime.now()
            self.status_var.set("Status: Recording...")
            self.frame_counter_var.set("Frames: 0")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            if self.start_callback:
                self.start_callback()
    
    def stop_recording(self):
        global recording
        if recording:
            recording = False
            self.status_var.set("Status: Saving data...")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if self.stop_callback:
                self.stop_callback()
    
    def update_frame_count(self, count):
        self.frame_counter_var.set(f"Frames: {count}")
    
    def set_status(self, status):
        self.status_var.set(f"Status: {status}")


def quaternion_to_euler_array(quat):
    """Convert quaternion to euler angles (roll, pitch, yaw)"""
    x, y, z, w = quat
    
    # Roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = np.arctan2(t0, t1)
    
    # Pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch_y = np.arcsin(t2)
    
    # Yaw (z-axis rotation)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = np.arctan2(t3, t4)
    
    return np.array([roll_x, pitch_y, yaw_z])


def get_obs(data, model):
    """Extract observation from mujoco data structure"""
    q = data.qpos.astype(np.double)
    dq = data.qvel.astype(np.double)
    
    # Get base orientation from sensor or qpos
    quat = data.sensor('base_link_quaternion').data[[1, 2, 3, 0]].astype(np.double)
    
    base_pos = q[:3]
    base_rot = q[3:7]  # quaternion
    # print(f'base pos {base_pos}, base rot {base_rot}')
    # print(f'quat {quat}')
    # Extract joint positions and velocities
    q_joint = q[7:]  # Skip first 7 elements (3 pos + 4 quat)
    dq_joint = dq[6:]  # Skip first 6 elements (3 lin vel + 3 ang vel)
    
    return q_joint, dq_joint, base_pos, base_rot


def pd_control(target_q, q, kp, target_dq, dq, kd, cfg):
    """Calculate torques from position commands"""
    torque_out = (target_q + cfg.robot_config.default_dof_pos - q) * kp + (target_dq - dq) * kd
    return torque_out


def get_body_positions_from_mujoco(data, model, body_names):
    """Get body positions directly from mujoco simulation"""
    body_positions = []
    for body_name in body_names:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if body_id >= 0:
            body_positions.append(data.xpos[body_id].copy())
        else:
            # Fill with zeros if body not found
            body_positions.append(np.zeros(3))
    return np.array(body_positions)


def save_data_pkl(data, filename, fps, body_names):
    """Save data to PKL format"""
    motion_data = {
        "fps": fps,
        "root_pos": data["root_pos"],
        "root_rot": data["root_rot"],
        "dof_pos": data["dof_pos"],
        "local_body_pos": np.zeros((len(data["root_pos"]), len(body_names), 3)),
        "link_body_list": body_names,
    }
    
    with open(filename, "wb") as f:
        pickle.dump(motion_data, f)
    print(f"PKL file saved to: {filename}")


def save_data_csv(data, filename):
    """Save data to CSV format (31 columns: 3 root_pos + 4 root_rot + 24 dof_pos)"""
    motion_data_combined = np.concatenate([
        data["root_pos"],
        data["root_rot"],
        data["dof_pos"]
    ], axis=1)
    
    df = pd.DataFrame(motion_data_combined)
    df.to_csv(filename, index=False, header=False)
    print(f"CSV file saved to: {filename}")


class Sim2simCfg(PM01Cfg):
    """Configuration for sim2sim simulation"""
    class sim_config:
        mujoco_model_path = f'{LEGGED_GYM_ROOT_DIR}/resources/robots/pm01_xml/pm_v2.xml'
        sim_duration = 1000.0  # Long duration for recording
        dt = 0.001
        decimation = 10
    
    class robot_config:
        kps = np.array([70, 50, 50, 70, 20, 20, 70, 50, 50, 70, 20, 20, 
                       50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50], dtype=np.double)
        kds = np.array([7.0, 5.0, 5.0, 7.0, 0.2, 0.2, 7.0, 5.0, 5.0, 7.0, 0.2, 0.2, 
                       1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.double)
        tau_limit = 200. * np.ones(24, dtype=np.double)
        default_dof_pos = np.array([-0.12, 0.0, -0.0, 0.24, -0.12, 0.0, -0.12, 0.0, -0.0, 0.24, -0.12, 0.0,
                                   0.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, -0.3, 0.0, 0.0, 0.0, 0.0])
        active_joint_idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


def run_simulation_with_gui():
    """Main simulation loop with GUI integration"""
    global recording, data_buffer, record_start_time
    
    # GUI callbacks
    def on_start_recording():
        print("Recording started...")
    
    def on_stop_recording():
        save_recorded_data()
        gui.set_status("Ready")
    
    # Create and start GUI in main thread
    root = tk.Tk()
    gui = RecordingGUI(root, on_start_recording, on_stop_recording)
    
    # Load policy
    parser_args = type('Args', (), {
        'load_model': '/home/abo/git/zqsa01_legged_gym/logs/pm01_ppo/0_exported/policies/policy_1.pt',
        'terrain': False
    })()

    policy = torch.jit.load(parser_args.load_model)
    cfg = Sim2simCfg()

    # Define body names for motion data
    body_names = ['LINK_BASE', 'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L',
                 'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L',
                 'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R', 'LINK_KNEE_PITCH_R',
                 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R', 'LINK_TORSO_YAW',
                 'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L',
                 'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L',
                 'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R',
                 'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R', 'LINK_HEAD_YAW']
    
    # Initialize Mujoco model
    model = mujoco.MjModel.from_xml_path(cfg.sim_config.mujoco_model_path)
    model.opt.timestep = cfg.sim_config.dt
    
    data = mujoco.MjData(model)
    data.qpos[-len(cfg.robot_config.default_dof_pos):] = cfg.robot_config.default_dof_pos
    mujoco.mj_step(model, data)
    
    # Initialize viewer
    viewer = mujoco_viewer.MujocoViewer(model, data)
    viewer.cam.distance = 3.0
    viewer.cam.azimuth = 90
    viewer.cam.elevation = -45
    viewer.cam.lookat[:] = np.array([0.0, -0.25, 0.824])
    
    # Control variables
    vx, vy, dyaw = 0.0, 0.0, 0.0
    target_q = cfg.robot_config.default_dof_pos.copy()
    target_q[:cfg.env.num_actions] = 0.0
    # target_q = np.zeros((len(cfg.robot_config.default_dof_pos)), dtype=np.double)
    action = np.zeros((cfg.env.num_actions), dtype=np.double)
    
    # Initialize observation history
    hist_obs = deque()
    for _ in range(cfg.env.frame_stack):
        hist_obs.append(np.zeros([1, cfg.env.num_single_obs], dtype=np.double))
    
    count_lowlevel = 1
    
    # Keyboard control for movement
    def on_press(key):
        nonlocal vx, vy, dyaw
        try:
            if key.char == '2':  # Forward
                vx += 0.1
            elif key.char == '3':  # Backward
                vx -= 0.1
            elif key.char == '4':  # Left
                vy += 0.1
            elif key.char == '5':  # Right
                vy -= 0.1
            elif key.char == '6':  # Rotate CCW
                dyaw += 0.1
            elif key.char == '7':  # Rotate CW
                dyaw -= 0.1
            elif key.char == '0':  # Reset
                vx = 0.0
                vy = 0.0
                dyaw = 0.0
            vx = np.clip(vx, -1.0, 5.0)
            vy = np.clip(vy, -1.0, 0.6)
            dyaw = np.clip(dyaw, -1.0, 1.0)
        except AttributeError:
            pass
    
    from pynput import keyboard as kb
    listener = kb.Listener(on_press=on_press)
    listener.start()
    
    def save_recorded_data():
        """Save recorded data to files"""
        global recording, data_buffer, record_start_time

        if len(data_buffer) == 0:
            print("No data to save")
            gui.set_status("No data recorded")
            return

        # Generate filename with timestamp
        timestamp = record_start_time.strftime("%Y%m%d_%H%M%S")
        base_filename = f"pm01_motion_{timestamp}"

        # Prepare data dictionaries
        root_pos_list = []
        root_rot_list = []
        dof_pos_list = []

        for frame_data in data_buffer:
            root_pos_list.append(frame_data['root_pos'])
            root_rot_list.append(frame_data['root_rot'])
            dof_pos_list.append(frame_data['dof_pos'])

        data_dict = {
            "root_pos": np.array(root_pos_list),
            "root_rot": np.array(root_rot_list),
            "dof_pos": np.array(dof_pos_list)
        }

        # Calculate FPS (based on decimation and dt)
        fps = int(1.0 / (cfg.sim_config.dt * cfg.sim_config.decimation))

        # Save PKL file
        pkl_filename = f"{base_filename}.pkl"
        save_data_pkl(data_dict, pkl_filename, fps, body_names)

        # Save CSV file
        csv_filename = f"{base_filename}.csv"
        save_data_csv(data_dict, csv_filename)

        print(f"Saved {len(data_buffer)} frames to {pkl_filename} and {csv_filename}")

        # Clear buffer
        data_buffer = []

        # Update GUI
        gui.update_frame_count(0)
        gui.set_status(f"Saved {len(data_buffer)} frames")
    
    def simulation_step():
        """Single simulation step - called repeatedly"""
        nonlocal count_lowlevel, vx, vy, dyaw, target_q, action
        
        try:
            # Get observation
            q, dq, base_pos, base_rot = get_obs(data, model)
            # Policy update at lower frequency
            if count_lowlevel % cfg.sim_config.decimation == 0:
                if hasattr(cfg.commands,"sw_switch"):
                    vel_norm = np.sqrt(vx**2 + vy**2 + dyaw**2)
                    if cfg.commands.sw_switch and vel_norm <= cfg.commands.stand_com_threshold:
                        count_lowlevel = 0
                
                obs = np.zeros([1, cfg.env.num_single_obs], dtype=np.float32)
                
                obs[0, 0] = math.sin(2 * math.pi * count_lowlevel * cfg.sim_config.dt / cfg.rewards.cycle_time)
                obs[0, 1] = math.cos(2 * math.pi * count_lowlevel * cfg.sim_config.dt / cfg.rewards.cycle_time)
                obs[0, 2] = vx * cfg.normalization.obs_scales.lin_vel
                obs[0, 3] = vy * cfg.normalization.obs_scales.lin_vel
                obs[0, 4] = dyaw * cfg.normalization.obs_scales.ang_vel
                
                obs_q = q - cfg.robot_config.default_dof_pos
                obs_q = obs_q[cfg.robot_config.active_joint_idx]
                obs_dq = dq[cfg.robot_config.active_joint_idx]
                
                obs[0, 5:17] = obs_q * cfg.normalization.obs_scales.dof_pos
                obs[0, 17:29] = obs_dq * cfg.normalization.obs_scales.dof_vel
                obs[0, 29:41] = action
                
                # Get angular velocity from qvel
                omega = data.qvel[3:6].copy()
                obs[0, 41:44] = omega
                
                # Gravity vector
                r = R.from_quat(base_rot[[1, 2, 3, 0]])
                gvec = r.apply(np.array([0., 0., -1.]), inverse=True)
                obs[0, 44:47] = gvec
                
                obs = np.clip(obs, -cfg.normalization.clip_observations, cfg.normalization.clip_observations)
                
                hist_obs.append(obs)
                hist_obs.popleft()
                
                policy_input = np.zeros([1, cfg.env.num_observations], dtype=np.float32)
                for i in range(cfg.env.frame_stack):
                    policy_input[0, i * cfg.env.num_single_obs : (i + 1) * cfg.env.num_single_obs] = hist_obs[i][0, :]
                
                action[:] = policy(torch.tensor(policy_input))[0].detach().numpy()
                action = np.clip(action, -cfg.normalization.clip_actions, cfg.normalization.clip_actions)
                
                target_q[:cfg.env.num_actions] = action * cfg.control.action_scale
                target_q[cfg.env.num_actions:] = cfg.robot_config.default_dof_pos[cfg.env.num_actions:]  # 保持上半身在默认位置
            

            # PD control
            target_dq = np.zeros(len(cfg.robot_config.default_dof_pos), dtype=np.double)
            tau = pd_control(target_q, q, cfg.robot_config.kps,
                          target_dq, dq, cfg.robot_config.kds, cfg)
            tau = np.clip(tau, -cfg.robot_config.tau_limit, cfg.robot_config.tau_limit)
            # print(f"tau: {tau}",flush=True)
            # data.ctrl[:len(tau)] = tau
            data.ctrl = tau
            
            # Step simulation
            mujoco.mj_step(model, data)
            
            # Record data if recording
            if recording and count_lowlevel % cfg.sim_config.decimation == 0:
                frame_data = {
                    'root_pos': base_pos.copy(),
                    'root_rot': base_rot[[1, 2, 3, 0]].copy(),
                    'dof_pos': q.copy()
                }
                data_buffer.append(frame_data)
                
                # Update GUI frame count in main thread
                root.after(0, lambda: gui.update_frame_count(len(data_buffer)))
            
            # Render
            viewer.render()
            count_lowlevel += 1
            
            # Schedule next step
            root.after(1, simulation_step)
            
        except Exception as e:
            print(f"Simulation error: {e}")
            import traceback
            traceback.print_exc()
            viewer.close()
            root.destroy()
    
    # Start simulation
    root.after(100, simulation_step)
    
    # Run GUI main loop
    root.mainloop()
    
    # Cleanup
    listener.stop()
    viewer.close()


if __name__ == '__main__':
    print("Starting Sim2Sim PM01 Data Recorder...")
    print("Keyboard controls:")
    print("  2: Forward")
    print("  3: Backward")
    print("  4: Left")
    print("  5: Right")
    print("  6: Rotate CCW")
    print("  7: Rotate CW")
    print("  0: Reset")
    print("\nUse GUI buttons to start/stop recording")
    
    run_simulation_with_gui()
