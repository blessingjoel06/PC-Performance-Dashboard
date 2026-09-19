import pandas as pd
import matplotlib.pyplot as plt

# Read logged data
data = pd.read_csv("data/performance.csv")

# Convert timestamp to datetime
data["Timestamp"] = pd.to_datetime(data["Timestamp"])

# Create CPU graph
plt.figure(figsize=(10, 5))
plt.plot(data["Timestamp"], data["CPU (%)"])
plt.title("CPU Usage")
plt.xlabel("Time")
plt.ylabel("Usage (%)")
plt.ylim(0, 100)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()