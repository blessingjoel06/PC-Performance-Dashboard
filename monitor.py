import psutil
import time
import csv
import os
from datetime import datetime

# Create data folder if it doesn't exist
os.makedirs("data", exist_ok=True)

file_path = "data/performance.csv"

# Create CSV file with headers if it doesn't exist
if not os.path.exists(file_path):
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "CPU (%)", "RAM (%)", "Disk (%)"])

print("PC PERFORMANCE LOGGER")
print("=====================")
print("Recording performance data...")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:\\").percent
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(file_path, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, cpu, ram, disk])

        print(
            f"{timestamp} | "
            f"CPU: {cpu}% | "
            f"RAM: {ram}% | "
            f"Disk: {disk}%"
        )

except KeyboardInterrupt:
    print("\nLogging stopped.")