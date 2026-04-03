from csv_resample import CSVResampler
import os
import glob

'''
CSV适用
把CSV的轨迹数据，插值成output_fps的频率，并保存成CSV文件

支持两种模式：
1. 单文件模式：处理单个CSV文件
2. 批量模式：处理整个文件夹下的所有CSV文件（或指定文件名模式）
'''

def resample_single_file(input_file, input_fps, output_fps):
    """
    对单个文件进行重采样
    
    Args:
        input_file: 输入CSV文件路径
        input_fps: 输入帧率
        output_fps: 输出帧率
    """
    print(f"\n{'='*60}")
    print(f"处理文件: {input_file}")
    print(f"输入帧率: {input_fps}, 输出帧率: {output_fps}")
    print(f"{'='*60}")
    
    resampler = CSVResampler(
        csv_file=input_file,
        input_fps=input_fps,
        output_fps=output_fps
    )
    
    print(f"完成！输出文件: {resampler.output_file}")

def resample_folder(input_folder, input_fps, output_fps, pattern='*.csv'):
    """
    对文件夹下的所有匹配文件进行批量重采样
    
    Args:
        input_folder: 输入文件夹路径
        input_fps: 输入帧率
        output_fps: 输出帧率
        pattern: 文件名匹配模式（默认'*.csv'）
    """
    # 获取所有匹配的文件
    search_pattern = os.path.join(input_folder, pattern)
    csv_files = glob.glob(search_pattern)
    
    if len(csv_files) == 0:
        print(f"未找到匹配的文件: {search_pattern}")
        return
    
    print(f"\n{'='*60}")
    print(f"批量重采样模式")
    print(f"文件夹: {input_folder}")
    print(f"匹配模式: {pattern}")
    print(f"找到 {len(csv_files)} 个文件")
    print(f"输入帧率: {input_fps}, 输出帧率: {output_fps}")
    print(f"{'='*60}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        try:
            print(f"\n[{i}/{len(csv_files)}] 处理: {os.path.basename(csv_file)}")
            
            resampler = CSVResampler(
                csv_file=csv_file,
                input_fps=input_fps,
                output_fps=output_fps
            )
            
            print(f"  ✓ 成功！输出: {resampler.output_file}")
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
    input_fps = 100     # 输入帧率
    output_fps = 30   # 输出帧率
    
    # 单文件模式配置
    if MODE == 'single':
        input_file = "input_twist_pkl/data/gvhmr_walk1.csv"
        resample_single_file(input_file, input_fps, output_fps)
    
    # 批量模式配置
    elif MODE == 'batch':
        input_folder = "/home/abo/rl_workspace/motion_target/sim2motion"  # 文件夹路径
        pattern = "*.csv"                      # 文件匹配模式，如 "*.csv" 或 "walk*.csv"
        
        resample_folder(input_folder, input_fps, output_fps, pattern)