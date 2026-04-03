# 读取 PKL（支持 joblib / pickle / torch / numpy 格式）
import os
import sys

_twist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'input_twist_pkl')
if _twist_dir not in sys.path:
    sys.path.insert(0, _twist_dir)

from pkl_loader import load_pkl

# filename = "/home/abo/rl_workspace/_dataset/mujoco_motions_pm01/pm01_motion_walk_forward_resampled_30fps"
# filename = "/home/abo/rl_workspace/_dataset/KIT/3/walking_forward_4steps_right_02_stageii"
filename = "/home/abo/rl_workspace/_dataset/mujoco_motions_pm01/motion_saved_20260130_175847_edit"

motion = load_pkl(filename + '.pkl')
fps = motion['fps']
root_pos = motion['root_pos']
dof_pos = motion['dof_pos']
local_body_pos = motion.get('local_body_pos')
link_body_list = motion.get('link_body_list', [])
print(f"FPS: {fps}, frames: {root_pos.shape[0]}")
print(f'link_body_list: {link_body_list}')