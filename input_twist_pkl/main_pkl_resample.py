from pkl_resample import MotionLoader
import os
import glob

'''
twist适用
把pkl的轨迹数据，插值成output_fps的频率，并保存成pkl文件

支持两种模式：
1. 单文件模式：处理单个pkl文件
2. 批量模式：处理整个文件夹下的所有pkl文件（或指定文件名模式）
'''

def resample_single_file(input_file, output_fps, device='cuda:0'):
    """
    对单个文件进行重采样
    
    Args:
        input_file: 输入pkl文件路径
        output_fps: 输出帧率
        device: 设备
    """
    print(f"\n{'='*60}")
    print(f"处理文件: {input_file}")
    print(f"{'='*60}")
    
    motion = MotionLoader(
        motion_file=input_file,
        output_fps=output_fps,
        device=device
    )
    
    print(f"完成！输出文件: {motion.output_file}")

def resample_folder(input_folder, output_fps, device='cuda:0', pattern='*.pkl', output_suffix='_resampled'):
    """
    对文件夹下的所有匹配文件进行批量重采样
    
    Args:
        input_folder: 输入文件夹路径
        output_fps: 输出帧率
        device: 设备
        pattern: 文件名匹配模式（默认'*.pkl'）
        output_suffix: 输出文件后缀（默认'_resampled'）
    """
    # 获取所有匹配的文件
    search_pattern = os.path.join(input_folder, pattern)
    pkl_files = glob.glob(search_pattern)
    
    if len(pkl_files) == 0:
        print(f"未找到匹配的文件: {search_pattern}")
        return
    
    print(f"\n{'='*60}")
    print(f"批量重采样模式")
    print(f"文件夹: {input_folder}")
    print(f"匹配模式: {pattern}")
    print(f"找到 {len(pkl_files)} 个文件")
    print(f"输出帧率: {output_fps}")
    print(f"{'='*60}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, pkl_file in enumerate(pkl_files, 1):
        try:
            print(f"\n[{i}/{len(pkl_files)}] 处理: {os.path.basename(pkl_file)}")
            
            motion = MotionLoader(
                motion_file=pkl_file,
                output_fps=output_fps,
                device=device
            )
            
            print(f"  ✓ 成功！输出: {motion.output_file}")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"批量处理完成！")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"{'='*60}")

if __name__ == "__main__":
    
    # ==================== 配置区域 ====================
    
    # 模式选择: 'single' 或 'batch'
    MODE = 'batch'
    
    # 通用配置
    output_fps = 500
    device = 'cuda:0'
    
    # 单文件模式配置
    if MODE == 'single':
        # input_file = "input_pkl/gvhmr_walk1_resampled.pkl"
        input_file = "input_twist_pkl/data/hmr4d_results.pkl"
        resample_single_file(input_file, output_fps, device)
    
    # 批量模式配置
    elif MODE == 'batch':
        input_folder = "/home/abo/rl_workspace/_dataset/mujoco_motions_pm01"  # 文件夹路径
        pattern = "*.pkl"                     # 文件匹配模式，如 "*.pkl" 或 "walk*.pkl"
        # output_suffix = "_resampled"           # 可选：修改输出文件后缀（在pkl_resample.py中修改）
        
        resample_folder(input_folder, output_fps, device, pattern)