from __future__ import annotations

import torch
import numpy as np
import pandas as pd

class CSVResampler:
    def __init__(
        self,
        csv_file,
        input_fps,
        output_fps,
    ):
        """
        CSV数据重采样器
        
        Args:
            csv_file: 输入CSV文件路径
            input_fps: 输入帧率
            output_fps: 输出帧率
        """
        self.csv_file = csv_file
        self.output_file = csv_file.replace(".csv", f"_resampled_{output_fps}fps.csv")
        self.input_fps = input_fps
        self.output_fps = output_fps
        self.input_dt = 1.0 / self.input_fps
        self.output_dt = 1.0 / self.output_fps
        self.current_idx = 0
        
        self._load_csv()
        self._interpolate_motion()
        self._save_csv()
    
    def _load_csv(self):
        """加载CSV文件"""
        try:
            df = pd.read_csv(self.csv_file, header=None)
            data = df.values
            
            print(f"[CSVResampler] Loading CSV {self.csv_file} with {len(data)} frames")
            print(f"Input FPS: {self.input_fps}, Output FPS: {self.output_fps}")
            
            # 提取数据
            self.motion_base_poss_input = torch.tensor(data[:, :3], dtype=torch.float32)      # 3列: 位置
            self.motion_base_rots_input = torch.tensor(data[:, 3:7], dtype=torch.float32)    # 4列: 姿态
            self.motion_dof_poss_input = torch.tensor(data[:, 7:], dtype=torch.float32)       # 24列: 关节角度
            
            self.input_frames = self.motion_base_poss_input.shape[0]
            self.duration = (self.input_frames - 1) * self.input_dt
            
            print(f"root_pos shape: {self.motion_base_poss_input.shape}")
            print(f"root_rot shape: {self.motion_base_rots_input.shape}")
            print(f"dof_pos shape: {self.motion_dof_poss_input.shape}")
            
        except Exception as e:
            print(f"Error loading CSV file {self.csv_file}: {e}")
            raise
    
    def _interpolate_motion(self):
        """对运动数据进行插值"""
        times = torch.arange(
            0, self.duration, self.output_dt, dtype=torch.float32
        )
        self.output_frames = times.shape[0]
        index_0, index_1, blend = self._compute_frame_blend(times)
        
        # 线性插值位置和关节角度
        self.motion_base_poss = self._lerp(
            self.motion_base_poss_input[index_0],
            self.motion_base_poss_input[index_1],
            blend.unsqueeze(1),
        )
        self.motion_dof_poss = self._lerp(
            self.motion_dof_poss_input[index_0],
            self.motion_dof_poss_input[index_1],
            blend.unsqueeze(1),
        )
        
        # 球形线性插值姿态
        self.motion_base_rots = self._slerp(
            self.motion_base_rots_input[index_0],
            self.motion_base_rots_input[index_1],
            blend,
        )
        
        print(
            f"Motion interpolated, input frames: {self.input_frames}, "
            f"input fps: {self.input_fps}, "
            f"output frames: {self.output_frames}, "
            f"output fps: {self.output_fps}"
        )
    
    def _lerp(self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor) -> torch.Tensor:
        """线性插值"""
        return a * (1 - blend) + b * blend
    
    def _slerp(self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor) -> torch.Tensor:
        """球形线性插值四元数"""
        slerped_quats = torch.zeros_like(a)
        for i in range(a.shape[0]):
            slerped_quats[i] = self._quat_slerp(a[i], b[i], float(blend[i]))
        return slerped_quats
    
    def _quat_slerp(self, q1, q2, t):
        """
        四元数球形线性插值
        
        Args:
            q1, q2: 输入四元数 (4,)
            t: 插值系数 [0, 1]
        Returns:
            插值后的四元数
        """
        # 确保四元数单位化
        q1 = q1 / torch.norm(q1)
        q2 = q2 / torch.norm(q2)
        
        # 计算点积
        dot = torch.dot(q1, q2)
        
        # 如果点积为负，反转q2以取最短路径
        if dot < 0:
            q2 = -q2
            dot = -dot
        
        # 如果四元数非常接近，使用线性插值
        if dot > 0.9995:
            result = q1 + t * (q2 - q1)
            return result / torch.norm(result)
        
        # 计算插值角度
        theta = torch.acos(dot)
        sin_theta = torch.sin(theta)
        
        # 球形线性插值
        w1 = torch.sin((1 - t) * theta) / sin_theta
        w2 = torch.sin(t * theta) / sin_theta
        
        return w1 * q1 + w2 * q2
    
    def _compute_frame_blend(self, times: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """计算帧混合参数"""
        phase = times / self.duration
        index_0 = (phase * (self.input_frames - 1)).floor().long()
        index_1 = torch.minimum(index_0 + 1, torch.tensor(self.input_frames - 1))
        blend = phase * (self.input_frames - 1) - index_0
        return index_0, index_1, blend
    
    def _save_csv(self):
        """保存为CSV文件"""
        # 合并数据
        motion_data_combined = np.concatenate([
            self.motion_base_poss.numpy(),
            self.motion_base_rots.numpy(),
            self.motion_dof_poss.numpy()
        ], axis=1)
        
        # 转换为DataFrame并保存
        df = pd.DataFrame(motion_data_combined)
        df.to_csv(self.output_file, index=False, header=False)
        
        print(f"\n=== Saving CSV ===")
        print(f"Output file: {self.output_file}")
        print(f"Total frames: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        print("=== End ===\n")
