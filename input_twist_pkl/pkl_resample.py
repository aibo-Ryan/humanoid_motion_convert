import torch
import numpy as np
import pickle
from utils_math import quat_mul, quat_conjugate, quat_slerp, axis_angle_from_quat

class MotionLoader:
    def __init__(
        self,
        motion_file,
        output_fps,
        device
    ):
        self.motion_file = motion_file
        self.output_file = motion_file.replace(".pkl", f"_resampled_{output_fps}fps.pkl")
        self.output_fps = output_fps
        self.output_dt = 1.0 / self.output_fps
        self.current_idx = 0
        self.device = device
        self._load_motion()
        self._interpolate_motion()
        self._compute_velocities()
        self._save_motion()

    def _load_motion(self):
        """Loads the motion from pkl file (supports joblib/pickle/torch/numpy)."""
        curr_file = self.motion_file
        try:
            from pkl_loader import load_pkl
            motion_data = load_pkl(curr_file)

            self.input_fps = motion_data["fps"]
            self.input_dt = 1.0 / self.input_fps

            print(f"[MotionLib] Loading motion {curr_file} with fps={self.input_fps:.2f}")
            self.motion_base_poss_input = torch.tensor(motion_data["root_pos"], dtype=torch.float, device=self.device)
            self.motion_base_rots_input = torch.tensor(motion_data["root_rot"], dtype=torch.float, device=self.device)
            self.motion_dof_poss_input  = torch.tensor(motion_data["dof_pos"], dtype=torch.float, device=self.device)
            if "local_body_pos" in motion_data:
                self.motion_local_body_poss_input = torch.tensor(motion_data["local_body_pos"], dtype=torch.float, device=self.device)
                self._has_local_body_pos = True
            else:
                self._has_local_body_pos = False
                print("[MotionLib] local_body_pos 不存在，跳过")
            self._link_body_list = motion_data.get("link_body_list", [])
            print(f'motion_data link_body_list: {self._link_body_list}')

            self.input_frames = self.motion_base_poss_input.shape[0]
            self.duration = (self.input_frames - 1) * self.input_dt

        except Exception as e:
            print(f"Error loading motion file {curr_file}: {e}")

    def _interpolate_motion(self):
        """Interpolates the motion to the output fps."""
        times = torch.arange(
            0, self.duration, self.output_dt, device=self.device, dtype=torch.float32
            )
        self.output_frames = times.shape[0]
        index_0, index_1, blend = self._compute_frame_blend(times)
        print(f'index_0 {index_0.shape}, index_1 {index_1.shape}, blend {blend.shape}')
        print(f'self.motion_base_poss_input {self.motion_base_poss_input.shape}')
        print(f'self.motion_base_rots_input {self.motion_base_rots_input.shape}')
        print(f'self.motion_dof_poss_input {self.motion_dof_poss_input.shape}')
        if self._has_local_body_pos:
            print(f'self.motion_local_body_poss_input {self.motion_local_body_poss_input.shape}')

        self.motion_base_poss = self._lerp(
            self.motion_base_poss_input[index_0],
            self.motion_base_poss_input[index_1],
            blend.unsqueeze(1),
            )
        self.motion_base_rots = self._slerp(
            self.motion_base_rots_input[index_0],
            self.motion_base_rots_input[index_1],
            blend,
            )
        self.motion_dof_poss = self._lerp(
            self.motion_dof_poss_input[index_0],
            self.motion_dof_poss_input[index_1],
            blend.unsqueeze(1),
            )

        if self._has_local_body_pos:
            self.motion_local_body_poss = self._lerp_3d(
                self.motion_local_body_poss_input[index_0],
                self.motion_local_body_poss_input[index_1],
                blend,
                )

        print(
            f"Motion interpolated, input frames: {self.input_frames}, "
            f"input fps: {self.input_fps}, "
            f"output frames: {self.output_frames}, "
            f"output fps: {self.output_fps}"
            )

    def _lerp(
        self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor
    ) -> torch.Tensor:
        """Linear interpolation between two tensors."""
        return a * (1 - blend) + b * blend

    def _lerp_3d(
        self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor
    ) -> torch.Tensor:
        """Linear interpolation between two 3D tensors."""
        # Reshape blend to match the dimensions for broadcasting
        blend = blend.view(-1, 1, 1)
        return a * (1 - blend) + b * blend


    def _slerp(
            self, a: torch.Tensor, b: torch.Tensor, blend: torch.Tensor
        ) -> torch.Tensor:
        """Spherical linear interpolation between two quaternions."""
        slerped_quats = torch.zeros_like(a)
        for i in range(a.shape[0]):
            slerped_quats[i] = quat_slerp(a[i], b[i], float(blend[i]))
        return slerped_quats

    def _compute_frame_blend(
        self, times: torch.Tensor
        ):
        """Computes the frame blend for the motion."""
        phase = times / self.duration
        index_0 = (phase * (self.input_frames - 1)).floor().long()
        index_1 = torch.minimum(index_0 + 1, torch.tensor(self.input_frames - 1))
        blend = phase * (self.input_frames - 1) - index_0
        return index_0, index_1, blend

    def _compute_velocities(self):
        """Computes the velocities of the motion."""
        self.motion_base_lin_vels = torch.gradient(
            self.motion_base_poss, spacing=self.output_dt, dim=0
            )[0]
        self.motion_dof_vels = torch.gradient(
            self.motion_dof_poss, spacing=self.output_dt, dim=0
            )[0]
        self.motion_base_ang_vels = self._so3_derivative(
            self.motion_base_rots, self.output_dt
            )

    def _so3_derivative(self, rotations: torch.Tensor, dt: float) -> torch.Tensor:
        """Computes the derivative of a sequence of SO3 rotations.

        Args:
        rotations: shape (B, 4).
        dt: time step.
        Returns:
        shape (B, 3).
        """
        q_prev, q_next = rotations[:-2], rotations[2:]
        q_rel = quat_mul(q_next, quat_conjugate(q_prev))  # shape (B−2, 4)

        omega = axis_angle_from_quat(q_rel) / (2.0 * dt)  # shape (B−2, 3)
        omega = torch.cat(
            [omega[:1], omega, omega[-1:]], dim=0
            )  # repeat first and last sample
        return omega

    def get_next_state(
        self,
    ):
        """Gets the next state of the motion."""
        state = (
        self.motion_base_poss[self.current_idx : self.current_idx + 1],
        self.motion_base_rots[self.current_idx : self.current_idx + 1],
        self.motion_base_lin_vels[self.current_idx : self.current_idx + 1],
        self.motion_base_ang_vels[self.current_idx : self.current_idx + 1],
        self.motion_dof_poss[self.current_idx : self.current_idx + 1],
        self.motion_dof_vels[self.current_idx : self.current_idx + 1],
        )
        self.current_idx += 1
        reset_flag = False
        if self.current_idx >= self.output_frames:
            self.current_idx = 0
        reset_flag = True
        return state, reset_flag

    def _save_motion(self):
        """Saves the motion to a file."""
        motion_data = {
            "fps": self.output_fps,
            "root_pos": self.motion_base_poss.cpu().numpy(),
            "root_rot": self.motion_base_rots.cpu().numpy(),
            "dof_pos": self.motion_dof_poss.cpu().numpy(),
        }
        if self._has_local_body_pos:
            motion_data["local_body_pos"] = self.motion_local_body_poss.cpu().numpy()
        if self._link_body_list:
            motion_data["link_body_list"] = self._link_body_list

        # Print shapes of all data
        print("\n=== Saving motion data shapes ===")
        print(f"FPS: {self.output_fps}")
        for k, v in motion_data.items():
            if hasattr(v, 'shape'):
                print(f"{k} shape: {v.shape}")
        print("=== End of shapes ===\n")

        with open(self.output_file, "wb") as f:
            pickle.dump(motion_data, f)

