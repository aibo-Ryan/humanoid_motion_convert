# 处理：

source ~/venv/pm01/bin/activate

pkl的数据结构： 用在gmr和twist、mimicKit上
motion_data = {
    "fps": fps,
    "root_pos": root_pos,
    "root_rot": root_rot,
    "dof_pos": dof_pos,
    "local_body_pos": np.zeros((len(data), 29, 3)),  # 29个身体部位，每个3D位置
    "link_body_list": ['LINK_BASE', 'LINK_HIP_PITCH_L', 'LINK_HIP_ROLL_L', 'LINK_HIP_YAW_L', 'LINK_KNEE_PITCH_L', 'LINK_ANKLE_PITCH_L', 'LINK_ANKLE_ROLL_L', 'LINK_FOOT_L', 'LINK_HIP_PITCH_R', 'LINK_HIP_ROLL_R', 'LINK_HIP_YAW_R', 'LINK_KNEE_PITCH_R', 'LINK_ANKLE_PITCH_R', 'LINK_ANKLE_ROLL_R', 'LINK_FOOT_R', 'LINK_TORSO_YAW', 'LINK_SHOULDER_PITCH_L', 'LINK_SHOULDER_ROLL_L', 'LINK_SHOULDER_YAW_L', 'LINK_ELBOW_PITCH_L', 'LINK_ELBOW_YAW_L', 'LINK_ELBOW_END_L', 'LINK_SHOULDER_PITCH_R', 'LINK_SHOULDER_ROLL_R', 'LINK_SHOULDER_YAW_R', 'LINK_ELBOW_PITCH_R', 'LINK_ELBOW_YAW_R', 'LINK_ELBOW_END_R', 'LINK_HEAD_YAW']
}

csv用在beyondmimic上
csv的数据结构： 31列
root_pos, 3
root_rot, 4
dof_pos, 24