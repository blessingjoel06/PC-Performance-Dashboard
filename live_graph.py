import psutil
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

MAX_POINTS = 60

cpu_data = deque(maxlen=MAX_POINTS)
ram_data = deque(maxlen=MAX_POINTS)

fig, ax = plt.subplots(figsize=(10, 5))

cpu_line, = ax.plot([], [], label="CPU Usage")
ram_line, = ax.plot([], [], label="RAM Usage")

ax.set_xlim(0, MAX_POINTS)
ax.set_ylim(0, 100)

ax.set_xlabel("Seconds")
ax.set_ylabel("Usage (%)")
ax.set_title("Live PC Performance")

ax.legend()


def update(frame):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    cpu_data.append(cpu)
    ram_data.append(ram)

    x = range(len(cpu_data))

    cpu_line.set_data(x, cpu_data)
    ram_line.set_data(x, ram_data)

    return cpu_line, ram_line


ani = FuncAnimation(
    fig,
    update,
    interval=1000,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()