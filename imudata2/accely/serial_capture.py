import serial
from datetime import datetime, timedelta
import csv
import sys

def capture_serial_data(port, baudrate=115200, duration=60):
    """
    从串口捕获指定时长的IMU数据（适配浮点数格式）
    :param port: 串口设备路径 (如 '/dev/ttyUSB0')
    :param baudrate: 波特率 (默认115200)
    :param duration: 采集时长（秒）
    :return: (有效数据列表, 无效行数)
    """
    raw_data = []
    invalid_count = 0
    buffer = bytearray()
    
    try:
        # 初始化串口
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1  # 读取超时1秒
        )
        print(f"Connected to {ser.name}, starting data acquisition...")

        # 计算结束时间
        end_time = datetime.now() + timedelta(seconds=duration)
        
        while datetime.now() < end_time:
            # 读取串口数据
            data = ser.read_all()
            if data:
                buffer.extend(data)
                
                # 按行分割处理
                while b'\n' in buffer:
                    line_end = buffer.index(b'\n')
                    try:
                        # 解码处理
                        line = buffer[:line_end].decode("utf-8").strip()
                    except UnicodeDecodeError:
                        # 备用解码方案
                        line = buffer[:line_end].decode("ISO-8859-1").strip()
                    finally:
                        del buffer[:line_end+1]  # 删除已处理数据
                    
                    # 验证数据格式
                    if line.count(',') == 6:
                        try:
                            # 分割数据字段
                            parts = line.split(',')
                            
                            # 转换数据格式（前6个是浮点数，最后是整数）
                            accel = [float(parts[0]), float(parts[1]), float(parts[2])]
                            gyro = [float(parts[3]), float(parts[4]), float(parts[5])]
                            temp = int(parts[6])
                            
                            # 打包数据并保存
                            raw_data.append(accel + gyro + [temp])
                        except (ValueError, IndexError) as e:
                            invalid_count += 1
                    else:
                        invalid_count += 1

        print("\nData acquisition completed")
        return raw_data, invalid_count

    except serial.SerialException as e:
        print(f"Serial port error: {str(e)}")
        sys.exit(1)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

def save_to_csv(data, filename):
    """保存校准后的IMU数据到CSV文件"""
    headers = [
        "Accel_X(g)", "Accel_Y(g)", "Accel_Z(g)",
        "Gyro_X(dps)", "Gyro_Y(dps)", "Gyro_Z(dps)",
        "Temperature"
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in data:
            # 格式化数据保留两位小数
            formatted = [
                f"{row[0]:.2f}", f"{row[1]:.2f}", f"{row[2]:.2f}",
                f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}",
                row[6]
            ]
            writer.writerow(formatted)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    # 配置参数
    SERIAL_PORT = "/dev/ttyUSB0"  # 根据实际设备修改
    BAUD_RATE = 115200            # 保持与设备一致
    DURATION = 60                 # 采集时长（秒）
    OUTPUT_FILE = "imu_calibrated.csv"

    # 执行数据采集
    imu_data, invalid_lines = capture_serial_data(SERIAL_PORT, BAUD_RATE, DURATION)
    
    # 保存结果
    save_to_csv(imu_data, OUTPUT_FILE)
    
    # 显示统计信息
    print("\n[Acquisition Report]")
    print(f"Valid data rows: {len(imu_data)}")
    print(f"Invalid lines: {invalid_lines}")
    print(f"Sampling rate: {len(imu_data)/DURATION:.1f} Hz")
    
    # 后续处理建议
    print("\nRun analysis with:")
    print(f"python process_imu.py {OUTPUT_FILE}")
