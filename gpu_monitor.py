import subprocess
import time


def get_gpu_data():
    command = [
        "nvidia-smi",
        "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    values = result.stdout.strip().split(",")

    gpu_usage = values[0].strip()
    vram_used = values[1].strip()
    vram_total = values[2].strip()
    temperature = values[3].strip()
    power = values[4].strip()

    return gpu_usage, vram_used, vram_total, temperature, power


print("GPU PERFORMANCE MONITOR")
print("=======================")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        gpu, vram_used, vram_total, temp, power = get_gpu_data()

        print("\033[H\033[J", end="")

        print("GPU PERFORMANCE MONITOR")
        print("=======================")
        print(f"GPU Usage    : {gpu}%")
        print(f"VRAM Usage   : {vram_used} / {vram_total} MB")
        print(f"Temperature  : {temp} °C")
        print(f"Power Usage  : {power} W")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nMonitoring stopped.")