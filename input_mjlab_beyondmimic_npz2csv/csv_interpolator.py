import torch
import numpy as np
import pandas as pd


def quat_mul(q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
    """Multiply two quaternions together."""
    # check input is correct
    if q1.shape != q2.shape:
        msg = f"Expected input quaternion shape mismatch: {q1.shape} != {q2.shape}."
        raise ValueError(msg)
    # reshape to (N, 4) for multiplication
    shape = q1.shape
    q1 = q1.reshape(-1, 4)
    q2 = q2.reshape(-1, 4)
    # extract components from quaternions
    w1, x1, y1, z1 = q1[:, 0], q1[:, 1], q1[:, 2], q1[:, 3]
    w2, x2, y2, z2 = q2[:, 0], q2[:, 1], q2[:, 2], q2[:, 3]
    # perform multiplication
    ww = (z1 + x1) * (x2 + y2)
    yy = (w1 - y1) * (w2 + z2)
    zz = (w1 + y1) * (w2 - z2)
    xx = ww + yy + zz
    qq = 0.5 * (xx + (z1 - x1) * (x2 - y2))
    w = qq - ww + (z1 - y1) * (y2 - z2)
    x = qq - xx + (x1 + w1) * (x2 + w2)
    y = qq - yy + (w1 - x1) * (y2 + z2)
    z = qq - zz + (z1 + y1) * (w2 - x2)

    return torch.stack([w, x, y, z], dim=-1).view(shape)


def quat_conjugate(q: torch.Tensor) -> torch.Tensor:
    """Computes the conjugate of a quaternion."""
    shape = q.shape
    q = q.reshape(-1, 4)
    return torch.cat((q[..., 0:1], -q[..., 1:]), dim=-1).view(shape)


def quat_slerp(q1: torch.Tensor, q2: torch.Tensor, tau: float) -> torch.Tensor:
    """Performs spherical linear interpolation (SLERP) between two quaternions.

    This function does not support batch processing.

    Args:
        q1: First quaternion in (w, x, y, z) format.
        q2: Second quaternion in (w, x, y, z) format.
        tau: Interpolation coefficient between 0 (q1) and 1 (q2).

    Returns:
        Interpolated quaternion in (w, x, y, z) format.
    """
    assert isinstance(q1, torch.Tensor), "Input must be a torch tensor"
    assert isinstance(q2, torch.Tensor), "Input must be a torch tensor"
    if tau == 0.0:
        return q1
    elif tau == 1.0:
        return q2
    d = torch.dot(q1, q2)
    if abs(abs(d) - 1.0) < torch.finfo(q1.dtype).eps * 4.0:
        return q1
    if d < 0.0:
        # Invert rotation
        d = -d
        q2 *= -1.0
    angle = torch.acos(torch.clamp(d, -1, 1))
    if abs(angle) < torch.finfo(q1.dtype).eps * 4.0:
        return q1
    isin = 1.0 / torch.sin(angle)
    q1 = q1 * torch.sin((1.0 - tau) * angle) * isin
    q2 = q2 * torch.sin(tau * angle) * isin
    q1 = q1 + q2
    return q1


def axis_angle_from_quat(quat: torch.Tensor, eps: float = 1.0e-6) -> torch.Tensor:
    """Convert rotations given as quaternions to axis/angle."""
    # Modified to take in quat as [q_w, q_x, q_y, q_z]
    # Quaternion is [q_w, q_x, q_y, q_z] = [cos(theta/2), n_x * sin(theta/2), n_y * sin(theta/2), n_z * sin(theta/2)]
    # Axis-angle is [a_x, a_y, a_z] = [theta * n_x, theta * n_y, theta * n_z]
    # Thus, axis-angle is [q_x, q_y, q_z] / (sin(theta/2) / theta)
    # When theta = 0, (sin(theta/2) / theta) is undefined
    # However, as theta --> 0, we can use the Taylor approximation 1/2 - theta^2 / 48
    quat = quat * (1.0 - 2.0 * (quat[..., 0:1] < 0.0))
    mag = torch.linalg.norm(quat[..., 1:], dim=-1)
    half_angle = torch.atan2(mag, quat[..., 0])
    angle = 2.0 * half_angle
    # check whether to apply Taylor approximation
    sin_half_angles_over_angles = torch.where(
        angle.abs() > eps, torch.sin(half_angle) / angle, 0.5 - angle * angle / 48
    )
    return quat[..., 1:4] / sin_half_angles_over_angles.unsqueeze(-1)


class CSVInterpolator:
    def __init__(
        self,
        csv_file,              # 输入的CSV文件路径
        input_fps,             # 输入视频的帧率
        target_joint_pos,      # 目标关节位置 (24维)
        target_root_pos,       # 目标根节点位置 (3维)
        target_root_rot,       # 目标根节点旋转 (4维四元数)
        device="cpu"           # 计算设备，默认为CPU
    ):
        """
        初始化CSV插值器
        :param csv_file: 输入的CSV文件路径
        :param target_joint_pos: 目标关节位置 (24维)
        :param target_root_pos: 目标根节点位置 (3维)
        :param target_root_rot: 目标根节点旋转 (4维四元数)
        :param device: 计算设备
        """
        # 将输入数据转换为张量并存储
        self.csv_file = csv_file
        self.target_joint_pos = torch.tensor(target_joint_pos, dtype=torch.float, device=device)
        self.target_root_pos = torch.tensor(target_root_pos, dtype=torch.float, device=device)
        self.target_root_rot = torch.tensor(target_root_rot, dtype=torch.float, device=device)
        self.device = device
        
        # 读取CSV数据
        self._load_csv()
        
        # 从CSV获取初始状态（最后一帧）
        self.initial_joint_pos = self.joint_pos[-1]  # 最后一帧的关节位置
        self.initial_root_pos = self.root_pos[-1]    # 最后一帧的根位置
        self.initial_root_rot = self.root_rot[-1]    # 最后一帧的根旋转
        
        # 保存初始帧数和FPS
        self.num_frames = self.joint_pos.shape[0]
        self.fps = input_fps  # 保持原始FPS
        print(f"[CSVInterpolator] FPS: {self.fps}")
        self.dt = 1.0 / self.fps  # 计算时间步长
        
        # 执行插值
        self._interpolate_to_target(interpolation_steps=20)
        
        # 计算速度
        self._compute_velocities()
        
        # 保存结果
        self._save_csv()

    def _load_csv(self):
        """加载CSV文件并解析数据，跳过第一行标题"""
        try:
            # 读取CSV，跳过第一行（标题行）
            data = np.genfromtxt(self.csv_file, delimiter=',')
        

            num_frames = data.shape[0]
            
            # 解析数据 - 只需要位置和旋转数据，速度将从这些数据计算得出
            self.joint_pos = torch.tensor(data[:, 0:24], dtype=torch.float, device=self.device)
            self.root_pos = torch.tensor(data[:, 48:51], dtype=torch.float, device=self.device)
            self.root_rot = torch.tensor(data[:, 51:55], dtype=torch.float, device=self.device)
            
            print(f"[CSVInterpolator] Loading motion from {self.csv_file}")
            print(f"Data shape: {data.shape}")
            print(f"joint_pos shape: {self.joint_pos.shape}")
            print(f"root_pos shape: {self.root_pos.shape}")
            print(f"root_rot shape: {self.root_rot.shape}")
            
        except Exception as e:
            print(f"Error loading CSV file {self.csv_file}: {e}")
            raise e

    def _interpolate_to_target(self, interpolation_steps=120):
        """从CSV最后一帧插值到目标状态"""
        # 创建插值时间步
        timesteps = torch.linspace(0, 1, interpolation_steps, device=self.device, dtype=torch.float32)
        
        # 对关节位置进行插值
        joint_pos_interpolated = self._lerp(self.initial_joint_pos, self.target_joint_pos, timesteps)
        root_pos_interpolated = self._lerp(self.initial_root_pos, self.target_root_pos, timesteps)
        root_rot_interpolated = self._slerp_quat_batch(self.initial_root_rot, self.target_root_rot, timesteps)
        
        # 将原始数据和插值数据拼接 - 仅在原始数据后添加插值部分
        self.joint_pos = torch.cat([self.joint_pos, joint_pos_interpolated], dim=0)
        self.root_pos = torch.cat([self.root_pos, root_pos_interpolated], dim=0)
        self.root_rot = torch.cat([self.root_rot, root_rot_interpolated], dim=0)
        
        print(f"Interpolated to target state with {interpolation_steps} steps")
        print(f"Final data shape: {self.joint_pos.shape[0]} frames")

    def _lerp(self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor) -> torch.Tensor:
        """对张量进行线性插值，支持批量处理"""
        # 扩展维度以支持批量插值
        expanded_blend = blend.unsqueeze(1) if len(blend.shape) == 1 else blend
        return a.unsqueeze(0) * (1 - expanded_blend) + b.unsqueeze(0) * expanded_blend

    def _slerp_quat_batch(self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor) -> torch.Tensor:
        """批量四元数球面插值"""
        # 确保四元数是单位四元数
        a = a / torch.norm(a)
        b = b / torch.norm(b)
        
        # 对每个插值步进行slerp
        result = torch.zeros((len(blend), 4), device=self.device, dtype=torch.float32)
        for i, t in enumerate(blend):
            result[i] = quat_slerp(a, b, float(t))
        return result

    def _compute_velocities(self):
        """计算关节速度和根节点速度"""
        # 计算关节速度
        self.joint_vel = torch.gradient(self.joint_pos, spacing=self.dt, dim=0)[0]
        
        # 计算根节点线速度
        self.root_lin_vel = torch.gradient(self.root_pos, spacing=self.dt, dim=0)[0]
        
        # 计算根节点角速度
        self.root_ang_vel = self._so3_derivative(self.root_rot, self.dt)

    def _so3_derivative(self, rotations: torch.Tensor, dt: float) -> torch.Tensor:
        """计算SO3旋转序列的导数"""
        # 确保四元数是单位四元数
        rotations = rotations / torch.norm(rotations, dim=-1, keepdim=True)
        
        # 对于序列的开始和结束，使用简单的差分
        ang_vels = torch.zeros_like(rotations[:, :3])
        
        if rotations.shape[0] < 3:
            # 如果序列太短，使用简单差分
            if rotations.shape[0] == 2:
                # 使用quat_mul计算相邻四元数的相对旋转
                q_rel = quat_mul(rotations[1], quat_conjugate(rotations[0]))
                axis_angle = axis_angle_from_quat(q_rel)
                ang_vels[0] = axis_angle / dt
                ang_vels[1] = axis_angle / dt
            elif rotations.shape[0] == 1:
                # 只有一个点，速度为0
                pass
            return ang_vels

        # 对于中间点，使用中心差分
        q_prev = rotations[:-2]
        q_next = rotations[2:]
        # 计算相对旋转
        q_rel = quat_mul(q_next, quat_conjugate(q_prev))  # shape (B-2, 4)
        
        # 转换为轴角表示
        axis_angle = axis_angle_from_quat(q_rel) / (2.0 * dt)  # shape (B-2, 3)
        
        # 重复第一个和最后一个样本以扩展到整个序列
        ang_vels[1:-1] = axis_angle
        ang_vels[0] = axis_angle[0]  # 重复第一个样本
        ang_vels[-1] = axis_angle[-1]  # 重复最后一个样本
        
        return ang_vels

    def _save_csv(self):
        """保存插值后的数据到CSV文件"""
        output_file = self.csv_file.replace('.csv', '_interpolated.csv')
        
        # 将所有数据拼接成一列
        all_data = torch.cat([
            self.joint_pos,
            self.joint_vel,
            self.root_pos,
            self.root_rot,
            self.root_lin_vel,
            self.root_ang_vel
        ], dim=1).cpu().numpy()
        
        # 保存为CSV
        np.savetxt(output_file, all_data, delimiter=',', fmt='%.10g')
        
        print(f"Saved interpolated data to {output_file}")
        print(f"Final shape: {all_data.shape}")
        
        # 也保存为pickle格式，与pkl_resample保持一致
        self._save_as_pkl(output_file.replace('.csv', '.pkl'))

    def _save_as_pkl(self, output_file):
        """保存为PKL格式，与pkl_resample保持一致"""
        motion_data = {
            "fps": self.fps,
            "root_pos": self.root_pos.cpu().numpy(),
            "root_rot": self.root_rot.cpu().numpy(),
            "dof_pos": self.joint_pos.cpu().numpy(),
            "dof_vel": self.joint_vel.cpu().numpy(),
            "root_lin_vel": self.root_lin_vel.cpu().numpy(),
            "root_ang_vel": self.root_ang_vel.cpu().numpy(),
        }
        
        print("\n=== Saving motion data shapes ===")
        print(f"FPS: {self.fps}")
        print(f"root_pos shape: {motion_data['root_pos'].shape}")
        print(f"root_rot shape: {motion_data['root_rot'].shape}")
        print(f"dof_pos shape: {motion_data['dof_pos'].shape}")
        print(f"dof_vel shape: {motion_data['dof_vel'].shape}")
        print(f"root_lin_vel shape: {motion_data['root_lin_vel'].shape}")
        print(f"root_ang_vel shape: {motion_data['root_ang_vel'].shape}")
        print("=== End of shapes ===\n")
        
        with open(output_file, "wb") as f:
            import pickle
            pickle.dump(motion_data, f)


if __name__ == "__main__":
    # 示例用法
    # 假设我们有一个CSV文件和目标状态
    csv_file = "/home/abo/rl_workspace/motion_target/input_mjlab_beyondmimic_csv_npz/data/tmp.csv"
    input_fps = 100
    # 目标状态（24个关节位置、速度等）
    target_joint_pos = [-0.345, -0.00314991, 0.11, 0.593, -0.25, -0.0058,-0.345, 0.0041, 0.11, 0.593, -0.25, 0.0058,-0.0,-0.0802, 0.379, -0.763, -0.301, 0,0.106, -0.405, 0.0231, -0.375,0,0]  # 示例数据
    target_root_pos = [-1.725918,0.155812,0.749681]  # 这个值无所谓
    target_root_rot = [0.0, 0.0, 0.0, 1.0]  # 示例数据 (w, x, y, z)
    interpolator = CSVInterpolator(
        csv_file,
        input_fps,
        target_joint_pos,
        target_root_pos,
        target_root_rot,
    )