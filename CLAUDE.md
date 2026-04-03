# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- **NumPy 2.x**: Compatibility patches for `numpy._core` are present in some scripts.
