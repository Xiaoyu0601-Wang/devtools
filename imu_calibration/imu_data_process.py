import sys
import csv
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from tabulate import tabulate

# 设置纯英文字体
plt.rcParams.update({
    'font.sans-serif': ['Arial'],
    'axes.unicode_minus': False
})

def load_calibration(calib_file):
    """加载校准参数文件"""
    try:
        with open(calib_file) as f:
            return json.load(f)
    except:
        print(f"Warning: No calibration file found at {calib_file}")
        return {
            'accel_bias': [0.0, 0.0, 0.0],
            'accel_scale': [1.0, 1.0, 1.0],
            'gyro_bias': [0.0, 0.0, 0.0]
        }

def process_imu_data(filename, calib_file='calibration.json'):
    # 加载校准参数
    calib = load_calibration(calib_file)
    
    # 初始化数据存储
    time_stamps = []
    accel = [[] for _ in range(3)]
    gyro = [[] for _ in range(3)]
    temperature = []
    temp_windows = defaultdict(list)
    
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                # 读取浮点数据（单位已转换为g和dps）
                parts = list(map(float, line.strip().split(',')))
                if len(parts) != 7:
                    raise ValueError
                
                # 应用加速度校准（零偏+比例因子）
                for i in range(3):
                    calibrated = (parts[i] - calib['accel_bias'][i]) * calib['accel_scale'][i]
                    accel[i].append(calibrated)
                
                # 应用陀螺仪校准（仅零偏）
                for i in range(3):
                    calibrated = parts[i+3] - calib['gyro_bias'][i]
                    gyro[i].append(calibrated)
                
                # 时间戳计算
                t = line_num * 0.005  # 200Hz采样率
                time_stamps.append(t)
                
                # 温度窗口处理
                window_idx = int(t * 10)
                temp_windows[window_idx].append(parts[6])
                temperature.append(parts[6])
            
            except (ValueError, IndexError):
                print(f"Skipped invalid line: {line_num+1}")
                continue

    # 计算统计量
    def calc_stats(data, unit):
        means = [sum(ch)/len(ch) for ch in data]
        stds = [
            (sum((x - mean)**2 for x in ch)/len(ch))**0.5 
            for ch, mean in zip(data, means)
        ]
        return {
            'bias': means,  # 校准后应接近零
            'std': stds,
            'unit': unit
        }
    
    # 处理温度窗口
    temp_avg = []
    window_centers = []
    for idx in sorted(temp_windows.keys()):
        values = temp_windows[idx]
        if values:
            window_center = idx*0.1 + 0.05
            temp_avg.append(sum(values)/len(values))
            window_centers.append(window_center)

    return {
        'accel': calc_stats(accel, 'g'),
        'gyro': calc_stats(gyro, 'dps'),
        'temp_raw': (time_stamps, temperature),
        'accel_raw': (time_stamps, accel),
        'gyro_raw': (time_stamps, gyro),
        'temp_avg': (window_centers, temp_avg)
    }

def plot_sensor_data(data, filename, sensor_name):
    """绘制传感器数据（校准后）"""
    plt.figure(figsize=(12, 8))
    
    time_stamps = data[0]
    sensor_data = data[1]
    stats = data[2]
    axes = ['X', 'Y', 'Z']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i in range(3):
        plt.subplot(3, 1, i+1)
        plt.plot(time_stamps, sensor_data[i], 
                 color=colors[i], linewidth=0.5, label='Calibrated Data')
        
        # 绘制理论零线
        plt.axhline(y=0, 
                    color='red', 
                    linestyle='--', 
                    linewidth=1,
                    label=f"Bias: {stats['bias'][i]:.3f} ± {stats['std'][i]:.3f} {stats['unit']}")
        
        plt.ylabel(f'{axes[i]} Axis ({stats["unit"]})')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper right', fontsize=8)
        
        if i == 0:
            plt.title(f'{sensor_name} Calibrated Data\n(Sampling Rate: 200Hz)')
    
    plt.xlabel('Time (seconds)')
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

# ... (plot_temperature和main函数保持结构不变，单位标注修改为实际单位)

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_imu.py <data_file>")
        return

    input_file = sys.argv[1]
    base_name = input_file.rsplit('.', 1)[0]
    results = process_imu_data(input_file)

    # 生成图表（修改文件名后缀）
    plot_files = {
        'temperature': f"{base_name}_temperature.png",
        'acceleration': f"{base_name}_accel_calibrated.png",
        'gyroscope': f"{base_name}_gyro_calibrated.png"
    }
    
    # ... (保持原有调用逻辑)

    # 修改CSV输出表头
    def save_bias_csv(filename, stats):
        headers = ["Axis", f"Bias ({stats['unit']})", f"Std Dev ({stats['unit']})"]
        # ... (保持其余逻辑不变)

if __name__ == "__main__":
    main()
