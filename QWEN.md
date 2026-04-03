# QWEN.md — Motion Target

## Project Overview

**Motion Target** is a motion data processing and visualization pipeline for the **PM01 humanoid robot**. It provides tools to:

- **Record** motion from Mujoco simulations (via a Tkinter-based GUI)
- **Convert** between data formats (PKL ↔ CSV ↔ NPZ)
- **Resample** motion sequences to different frame rates (using LERP/SLERP interpolation)
- **Visualize** motion playback in IsaacGym or Mujoco

The project supports sim-to-sim motion capture for training robotic locomotion policies, targeting downstream applications like TWIST, ASAP, and BeyondMimic.

### Key Technologies

| Stack | Details |
|-------|---------|
| **Language** | Python 3.8/3.10 |
| **GUI** | PyQt5 (main app), Tkinter (sim2sim recorder) |
| **Simulation** | Mujoco, IsaacGym, IsaacLab |
| **ML/Math** | PyTorch, NumPy, SciPy |
| **Data** | Pickle (PKL), CSV, NPZ |

### Conda Environment

```bash
conda activate zqsa01
```

---

## Directory Structure

```
motion_target/
├── sim2motion/                          # Motion acquisition (Mujoco sim + recording)
│   ├── sim2sim_pm01.py                  # Main recording script (GUI-based)
│   ├── test_dependencies.py             # Dependency checker
│   └── load_data.py                     # Data loading utilities
├── input_twist_pkl/                     # TWIST PKL conversion & resampling
│   ├── main_pkl_to_csv.py               # PKL → CSV converter
│   ├── main_csv_to_pkl.py               # CSV → PKL converter
│   ├── main_pkl_resample.py             # PKL resampling (CLI)
│   ├── main_csv_resample.py             # CSV resampling (CLI)
│   ├── pkl_resample.py                  # Core resampling logic (torch-based)
│   ├── csv_resample.py                  # CSV resampling logic
│   ├── pkl_loader.py                    # PKL file loader
│   ├── kinematics_model.py              # Forward kinematics from robot XML
│   ├── torch_utils.py                   # Quaternion math utilities
│   └── utils_math.py                    # Rotation/transform utilities
├── input_isaaclab_beyondmimic_csv_npz/  # IsaacLab NPZ → CSV conversion
│   └── isaaclab_beyondmimic_npz2csv_no_estimate.py
├── input_mjlab_beyondmimic_csv_npz/     # MJLab NPZ → CSV conversion
│   ├── mjlab_beyondmimic_npz2csv.py
│   ├── mjlab_beyondmimic_npz2csv_no_estimate.py
│   └── csv_interpolator.py
├── vis_motion/                          # Motion visualization
│   ├── vis_pm01_motion.py               # PM01 IsaacGym viewer
│   └── vis_isaacgym_motion.py           # Generic IsaacGym viewer
├── gui/                                 # PyQt5 GUI application
│   ├── main.py                          # Entry point: python -m gui.main
│   ├── app.py                           # MainWindow (tabbed interface)
│   ├── base_panel.py                    # Base panel class
│   ├── registry.py                      # Panel registry (extension point)
│   └── panels/                          # Individual functional panels
│       ├── pkl_to_csv_panel.py
│       ├── csv_to_pkl_panel.py
│       ├── pkl_resample_panel.py
│       ├── csv_resample_panel.py
│       ├── isaaclab_npz_panel.py
│       ├── mjlab_npz_base_panel.py
│       ├── mjlab_npz_full_panel.py
│       └── load_data_panel.py
└── run_conda.sh                         # Conda activation script
```

---

## Data Pipeline

Data flows through four stages:

### 1. Acquisition (`sim2motion/`)

Records motion from a Mujoco simulation running a trained PM01 PPO policy. Outputs PKL + CSV at 100 Hz.

```bash
python sim2motion/sim2sim_pm01.py
```

**FPS formula**: `fps = 1.0 / (dt × decimation)` — default dt=0.001s, decimation=10 → **100 Hz**.

### 2. Import/Conversion (`input_*/`)

Converts external formats to the common PKL/CSV format:

| Source | Script | Notes |
|--------|--------|-------|
| TWIST PKL | `input_twist_pkl/main_pkl_to_csv.py` | PKL → CSV (31 columns) |
| TWIST CSV | `input_twist_pkl/main_csv_to_pkl.py` | CSV → PKL |
| IsaacLab NPZ | `input_isaaclab_beyondmimic_csv_npz/isaaclab_beyondmimic_npz2csv_no_estimate.py` | 23 joints |
| MJLab NPZ | `input_mjlab_beyondmimic_csv_npz/mjlab_beyondmimic_npz2csv.py` | 24 joints |

### 3. Resampling (`input_twist_pkl/`)

Interpolates motion to a target frame rate:
- **Positions/Joints**: Linear interpolation (LERP)
- **Quaternions**: Spherical interpolation (SLERP)
- **Velocities**: Computed via finite differences

```bash
python input_twist_pkl/main_pkl_resample.py
python input_twist_pkl/main_csv_resample.py
```

### 4. Visualization (`vis_motion/`)

IsaacGym-based playback viewers for PM01 and H1 robots.

```bash
python vis_motion/vis_pm01_motion.py
```

---

## Data Formats

### PKL (native format — used by TWIST, ASAP, mimicKit)

```python
{
    "fps": 100,                          # frames per second
    "root_pos": (N, 3),                  # base position (x, y, z)
    "root_rot": (N, 4),                  # quaternion [w, x, y, z]
    "dof_pos": (N, 24),                  # 24 joint angles
    "local_body_pos": (N, 29, 3),        # body link positions from FK
    "link_body_list": [str]              # 29 link names
}
```

### CSV (31 columns — used by BeyondMimic)

```
root_x, root_y, root_z, root_qw, root_qx, root_qy, root_qz, j0, j1, ..., j23
```

- 3 (root position) + 4 (root rotation) + 24 (joint angles) = **31 columns**

### NPZ (IsaacLab / MJLab source)

```python
{
    "fps": float,
    "joint_pos": (N, 23-24),
    "joint_vel": (N, 23-24),
    "body_pos_w": (N, 24-29, 3),
    "body_quat_w": (N, 24-29, 4),
    "body_lin_vel_w": (N, 24-29, 3),
    "body_ang_vel_w": (N, 24-29, 3),
}
```

> **Note**: IsaacLab NPZ has 23 joints; MJLab NPZ has 24 joints. Their CSV output column counts differ accordingly (59 vs 61).

---

## PM01 Robot — 24 Controllable Joints

| Group | Joints | Count |
|-------|--------|-------|
| **Legs** | L/R × HIP_PITCH, HIP_ROLL, HIP_YAW, KNEE_PITCH, ANKLE_PITCH, ANKLE_ROLL | 12 |
| **Arms** | L/R × SHOULDER_PITCH, SHOULDER_ROLL, SHOULDER_YAW, ELBOW_PITCH, ELBOW_YAW, ELBOW_END | 12 |
| **Tracked (not controlled)** | TORSO_YAW, HEAD_YAW | 2 |

Total tracked body links: **29**

---

## GUI Application

Launch the PyQt5-based GUI:

```bash
python -m gui.main
```

### Registered Panels

| Tab Label | Function |
|-----------|----------|
| PKL → CSV | Convert PKL files to CSV format |
| CSV → PKL | Convert CSV files to PKL format |
| PKL 重采样 | Resample PKL to target FPS |
| CSV 重采样 | Resample CSV to target FPS |
| IsaacLab NPZ→CSV | Convert IsaacLab NPZ to CSV |
| MJLab NPZ→CSV | Convert MJLab NPZ to CSV (base) |
| MJLab NPZ→CSV Full | Convert MJLab NPZ to CSV (full, 61 columns) |
| PKL 数据检查 | Inspect PKL file contents |

### Adding a New Panel

1. Create a new class in `gui/panels/` inheriting from `BasePanel` or `SubprocessPanel`
2. Register it in `gui/registry.py` by adding a `PanelEntry(...)`

The `SubprocessRunner` widget (`gui/widgets/subprocess_runner.py`) handles running CLI scripts asynchronously with progress feedback.

---

## External Dependencies

| Dependency | Location | Purpose |
|------------|----------|---------|
| `legged_gym` | `/home/abo/git/zqsa01_legged_gym/` | PM01 config, PPO policy |
| Policy model | `.../logs/pm01_ppo/0_exported/policies/policy_1.pt` | Inference during recording |
| Robot XML | `.../resources/robots/pm01_xml/pm_v2.xml` | Mujoco model definition |
| `phc` / `smpl_sim` | External | H1 visualization skeleton |

Verify dependencies:

```bash
python sim2motion/test_dependencies.py
```

---

## Important Notes

1. **Import order**: `isaacgym` / `legged_gym` **must** be imported before `torch` to avoid initialization errors.

2. **Quaternion convention**: `[w, x, y, z]` throughout the codebase (verify per script — some converters document the convention explicitly).

3. **CSV format differences**:
   - PKL-derived CSV: 31 columns (root_pos 3 + root_rot 4 + dof_pos 24)
   - MJLab/BeyondMimic CSV: 61 columns (joint_pos 24 + joint_vel 24 + body_pos 3 + body_quat 4 + body_lin_vel 3 + body_ang_vel 3)
   - IsaacLab CSV: 59 columns (23 joints instead of 24)

4. **NumPy 2.x**: Compatibility patches for `numpy._core` are present in some scripts.

5. **PKL is for TWIST/ASAP/mimicKit**; CSV is for BeyondMimic visualization tools.

---

## Key Commands Quick Reference

```bash
# Activate environment
conda activate zqsa01

# Check dependencies
python sim2motion/test_dependencies.py

# Launch GUI
python -m gui.main

# Record motion (Mujoco simulation)
python sim2motion/sim2sim_pm01.py

# Visualize motion
python vis_motion/vis_pm01_motion.py
```
