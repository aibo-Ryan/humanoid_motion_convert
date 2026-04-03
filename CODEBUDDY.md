# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

「以第一性原理！从原始需求和问题本质出发，不从惯例或模板出发。
1. 不要假设我清楚自己想要什么。动机或目标不清晰时，停下来讨论。
2. 目标清晰但路径不是最短的，直接告诉我并建议更好的办法。
3. 遇到问题追根因，不打补丁。每个决策都要能回答"为什么"。
4. 输出说重点，砍掉一切不改变决策的信息。」

## Project Overview

Motion data processing and visualization pipeline for the **PM01 humanoid robot**. Enables recording motion from Mujoco simulations, converting between data formats (PKL/CSV/NPZ), resampling motion sequences, and visualizing in IsaacGym/Mujoco. Supports sim-to-sim motion capture for training robotic locomotion policies.

## Environment Setup

```bash
conda activate zqsa01
python sim2motion/test_dependencies.py  # Verify dependencies
```

No build step required — all scripts run directly as Python.

## Key Commands

```bash
# Record motion from Mujoco simulation (GUI-based)
python sim2motion/sim2sim_pm01.py

# Launch GUI for data conversion and processing
python -m gui.main

# Convert formats
python input_twist_pkl/main_pkl_to_csv.py
python input_twist_pkl/main_csv_to_pkl.py

# Resample to different frame rate
python input_twist_pkl/main_pkl_resample.py
python input_twist_pkl/main_csv_resample.py

# Convert NPZ from IsaacLab / MJLab to CSV
python input_isaaclab_beyondmimic_csv_npz/isaaclab_beyondmimic_npz2csv_no_estimate.py
python input_mjlab_beyondmimic_csv_npz/mjlab_beyondmimic_npz2csv_no_estimate.py

# Visualize motion
python vis_motion/vis_pm01_motion.py
```

## Architecture

Data flows through four stages:

1. **Acquisition** (`sim2motion/sim2sim_pm01.py`): Loads PM01 policy from legged_gym, runs Mujoco simulation, records via Tkinter GUI. Outputs PKL + CSV at 100 Hz.

2. **Import/Conversion** (`input_*/`): Converts NPZ (IsaacLab/MJLab) or twist PKL files to the common PKL/CSV format. Each subdirectory targets a different source.

3. **Resampling** (`input_twist_pkl/pkl_resample.py`, `csv_resample.py`): Interpolates to target FPS using LERP for positions/joints and SLERP for quaternions; computes velocities via finite differences.

4. **Visualization** (`vis_motion/`): IsaacGym-based playback viewers for PM01 and H1 robots.

### Supporting Modules

- `input_twist_pkl/kinematics_model.py` — Parses robot XML, runs PyTorch forward kinematics to compute 29 body link positions from joint angles.
- `input_twist_pkl/torch_utils.py` + `utils_math.py` — Quaternion math (`quat_mul`, `quat_slerp`, `quat_apply`), rotation conversions, transform utilities.

### GUI Application

- **Entry point**: `gui/main.py` — PyQt5-based GUI with tabbed interface
- **Panels**: `gui/panels/` — Each panel provides a specific conversion/processing function
- **Registry pattern**: `gui/registry.py` auto-registers panels as tabs in the main window
- **Logging**: All panels share a common log widget at the bottom of the window

## Data Formats

**PKL** (native format):
```python
{
  "fps": 100,
  "root_pos": (N, 3),          # base position
  "root_rot": (N, 4),          # quaternion [w, x, y, z]
  "dof_pos": (N, 24),          # 24 joint angles
  "local_body_pos": (N, 29, 3),# body link positions (from FK)
  "link_body_list": [str]       # 29 link names
}
```

**CSV** (31 columns, BeyondMimic format):
```
root_x, root_y, root_z, root_qw, root_qx, root_qy, root_qz, j0…j23
```

**NPZ** (IsaacLab/MJLab source):
```python
{"fps", "joint_pos": (N, 23–24), "joint_vel", "body_pos_w": (N, 24–29, 3), "body_quat_w", "body_lin_vel_w", "body_ang_vel_w"}
```

## PM01 Robot — 24 Controllable Joints

- **Legs (12)**: L/R × HIP_PITCH, HIP_ROLL, HIP_YAW, KNEE_PITCH, ANKLE_PITCH, ANKLE_ROLL
- **Arms (12)**: L/R × SHOULDER_PITCH, SHOULDER_ROLL, SHOULDER_YAW, ELBOW_PITCH, ELBOW_YAW, ELBOW_END
- Additional: TORSO_YAW, HEAD_YAW (also recorded)
- Total tracked body links: 29

## External Dependencies

| Dependency | Location | Purpose |
|------------|----------|---------|
| `legged_gym` | `/home/abo/git/zqsa01_legged_gym/` | PM01 config, policy |
| Policy model | `.../logs/pm01_ppo/0_exported/policies/policy_1.pt` | Inference |
| Robot XML | `.../resources/robots/pm01_xml/pm_v2.xml` | Mujoco model |
| `phc` / `smpl_sim` | External | H1 visualization skeleton |

## Important Notes

- **Import order**: `isaacgym`/`legged_gym` must be imported **before** `torch` to avoid initialization errors.
- **Quaternion convention**: `[w, x, y, z]` throughout (verify per script — some converters note the convention explicitly).
- **FPS formula**: `fps = 1.0 / (dt × decimation)` — default dt=0.001s, decimation=10 → 100 Hz.
- **NumPy 2.x**: Compatibility patches for `numpy._core` are present in some scripts (see `main_pkl_to_csv.py`).
- **GUI panels**: To add a new GUI panel, create a class in `gui/panels/` inheriting from `gui.base_panel.BasePanel` and register it in `gui/registry.py`.
