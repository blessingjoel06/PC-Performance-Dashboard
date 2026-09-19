import re
import platform
import subprocess
import winreg
import psutil
import requests
import matplotlib
matplotlib.rcParams['toolbar'] = 'None'  # removes the light-gray navigation toolbar

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
from collections import deque

MAX_POINTS = 60

cpu_data = deque(maxlen=MAX_POINTS)
ram_data = deque(maxlen=MAX_POINTS)
gpu_data = deque(maxlen=MAX_POINTS)
disk_data = deque(maxlen=MAX_POINTS)
cpu_temp_data = deque(maxlen=MAX_POINTS)

LHM_URL = "http://localhost:8085/data.json"
DISK_PATH = "C:\\"  # change if you want to monitor a different drive

# --- Dark theme styling ---
BG_COLOR = "#0d1117"
PANEL_COLOR = "#161b22"
GRID_COLOR = "#30363d"
TEXT_COLOR = "#e6edf3"
SUBTEXT_COLOR = "#8b949e"
ACCENT_CPU = "#58a6ff"
ACCENT_RAM = "#f85149"   # red
ACCENT_GPU = "#3fb950"   # green
ACCENT_DISK = "#d29922"

# Near-black instead of magenta: any anti-aliased edge blends into
# near-black instead of a visibly different fringe color
TRANSPARENT_KEY = "#010101"

PREFERRED_FONTS = ["Segoe UI", "Consolas", "DejaVu Sans"]
available_fonts = {f.name for f in fm.fontManager.ttflist}
chosen_font = next((f for f in PREFERRED_FONTS if f in available_fonts), "DejaVu Sans")

plt.rcParams.update({
    "font.family": chosen_font,
    "font.size": 10,
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": PANEL_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "axes.titlecolor": TEXT_COLOR,
    "axes.titleweight": "bold",
    "axes.titlesize": 11,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "grid.color": GRID_COLOR,
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})


# ---------- Static hardware info (fetched once at startup) ----------

def get_cpu_name():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        if name:
            return name.strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            capture_output=True, text=True, timeout=2
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if len(lines) >= 2:
            return lines[1]
    except Exception:
        pass

    try:
        name = platform.processor()
        if name:
            return name.strip()
    except Exception:
        pass

    return "Unknown CPU"


def get_gpu_name():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=2
        )
        name = result.stdout.strip()
        return name if name else "Unknown GPU"
    except Exception:
        return "Unknown GPU"


def get_total_ram_gb():
    try:
        return psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        return 0.0


CPU_NAME = get_cpu_name()
GPU_NAME = get_gpu_name()
TOTAL_RAM_GB = get_total_ram_gb()


# ---------- Live metric functions ----------

def get_gpu_data():
    command = [
        "nvidia-smi",
        "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
        "--format=csv,noheader,nounits"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=2
        )

        values = result.stdout.strip().split(",")

        gpu = float(values[0].strip())
        vram_used = float(values[1].strip())
        vram_total = float(values[2].strip())
        temperature = float(values[3].strip())

        return gpu, vram_used, vram_total, temperature
    except Exception:
        return 0.0, 0.0, 0.0, 0.0


def find_cpu_temperature(data):
    if isinstance(data, dict):
        text = str(data.get("Text", "")).lower()

        if "core (tctl/tdie)" in text or "core (tjmax)" in text or "cpu package" in text:
            value_str = str(data.get("Value", ""))
            match = re.search(r"[-+]?\d*\.?\d+", value_str)
            if match:
                return float(match.group())
            return None

        for value in data.values():
            result = find_cpu_temperature(value)

            if result is not None:
                return result

    elif isinstance(data, list):
        for item in data:
            result = find_cpu_temperature(item)

            if result is not None:
                return result

    return None


def get_cpu_temperature():
    try:
        response = requests.get(LHM_URL, timeout=2)
        data = response.json()

        temperature = find_cpu_temperature(data)

        if temperature is None:
            return 0.0

        return temperature
    except Exception:
        return 0.0


def get_disk_usage():
    try:
        return psutil.disk_usage(DISK_PATH).percent
    except Exception:
        return 0.0


# --- Figure setup: 2x2 grid of subplots ---
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.patch.set_facecolor(BG_COLOR)
fig.canvas.manager.set_window_title("PC Performance Dashboard")
fig.subplots_adjust(left=0.06, right=0.97, top=0.85, bottom=0.08, hspace=0.6, wspace=0.25)

ax_cpu, ax_ram = axes[0]
ax_gpu, ax_disk = axes[1]

cpu_line, = ax_cpu.plot([], [], color=ACCENT_CPU, linewidth=2)
ram_line, = ax_ram.plot([], [], color=ACCENT_RAM, linewidth=2)
gpu_line, = ax_gpu.plot([], [], color=ACCENT_GPU, linewidth=2)
disk_line, = ax_disk.plot([], [], color=ACCENT_DISK, linewidth=2)

cpu_fill = ax_cpu.fill_between([], [], color=ACCENT_CPU, alpha=0.15)
ram_fill = ax_ram.fill_between([], [], color=ACCENT_RAM, alpha=0.15)
gpu_fill = ax_gpu.fill_between([], [], color=ACCENT_GPU, alpha=0.15)
disk_fill = ax_disk.fill_between([], [], color=ACCENT_DISK, alpha=0.15)

fills = {"cpu": cpu_fill, "ram": ram_fill, "gpu": gpu_fill, "disk": disk_fill}

for ax in (ax_cpu, ax_ram, ax_gpu, ax_disk):
    ax.set_xlim(0, MAX_POINTS)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Time (s)", fontsize=9)
    ax.set_ylabel("Usage (%)", fontsize=9)
    ax.grid(True, alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

suptitle_obj = fig.suptitle("PC PERFORMANCE DASHBOARD", fontsize=16, fontweight="bold", color=TEXT_COLOR, y=0.98)

cpu_name_text = ax_cpu.text(
    0.5, 1.14, CPU_NAME, transform=ax_cpu.transAxes,
    ha="center", va="bottom", fontsize=8.5, color=SUBTEXT_COLOR
)
gpu_name_text = ax_gpu.text(
    0.5, 1.14, GPU_NAME, transform=ax_gpu.transAxes,
    ha="center", va="bottom", fontsize=8.5, color=SUBTEXT_COLOR
)
ram_name_text = ax_ram.text(
    0.5, 1.14, f"{TOTAL_RAM_GB:.1f} GB Total", transform=ax_ram.transAxes,
    ha="center", va="bottom", fontsize=8.5, color=SUBTEXT_COLOR
)
disk_name_text = ax_disk.text(
    0.5, 1.14, f"Drive {DISK_PATH}", transform=ax_disk.transAxes,
    ha="center", va="bottom", fontsize=8.5, color=SUBTEXT_COLOR
)

# ---------- Compact / floating overlay mode ----------

compact_ax = fig.add_axes([0.02, 0.05, 0.96, 0.88])
compact_ax.set_xticks([])
compact_ax.set_yticks([])
compact_ax.set_visible(False)

# White outline instead of transparent-key-matched outline
STROKE = [pe.withStroke(linewidth=2.5, foreground="white")]

compact_cpu_text = compact_ax.text(
    0.06, 0.80, "", transform=compact_ax.transAxes,
    ha="left", va="center", fontsize=11.2, color=ACCENT_CPU,   # 11 → 11.2 (~2% bigger)
    fontweight="bold", path_effects=STROKE
)
compact_ram_text = compact_ax.text(
    0.06, 0.55, "", transform=compact_ax.transAxes,
    ha="left", va="center", fontsize=11.2, color=ACCENT_RAM,
    fontweight="bold", path_effects=STROKE
)
compact_gpu_text = compact_ax.text(
    0.06, 0.30, "", transform=compact_ax.transAxes,
    ha="left", va="center", fontsize=11.2, color=ACCENT_GPU,
    fontweight="bold", path_effects=STROKE
)
compact_disk_text = compact_ax.text(
    0.06, 0.05, "", transform=compact_ax.transAxes,
    ha="left", va="center", fontsize=11.2, color=ACCENT_DISK,
    fontweight="bold", path_effects=STROKE
)
button_ax = fig.add_axes([0.88, 0.935, 0.10, 0.05])
compact_button = Button(button_ax, "Overlay", color=PANEL_COLOR, hovercolor=GRID_COLOR)
compact_button.label.set_color(TEXT_COLOR)
compact_button.label.set_fontsize(8)

compact_state = {"active": False, "saved_geometry": None}
drag_state = {"dragging": False, "start_x": 0, "start_y": 0}


def toggle_compact(event):
    window = fig.canvas.manager.window
    compact_state["active"] = not compact_state["active"]

    if compact_state["active"]:
        compact_state["saved_geometry"] = window.geometry()

        window.overrideredirect(True)
        window.geometry("300x150+30+30")
        window.attributes("-topmost", True)
        window.attributes("-transparentcolor", TRANSPARENT_KEY)

        fig.patch.set_facecolor(TRANSPARENT_KEY)
        compact_ax.set_facecolor(TRANSPARENT_KEY)
        for spine in compact_ax.spines.values():
            spine.set_visible(False)

        for ax in (ax_cpu, ax_ram, ax_gpu, ax_disk):
            ax.set_visible(False)
        cpu_name_text.set_visible(False)
        gpu_name_text.set_visible(False)
        ram_name_text.set_visible(False)
        disk_name_text.set_visible(False)
        suptitle_obj.set_visible(False)

        compact_ax.set_visible(True)
        compact_button.label.set_text("X")

    else:
        window.attributes("-transparentcolor", "")
        window.attributes("-topmost", False)
        window.overrideredirect(False)

        fig.patch.set_facecolor(BG_COLOR)
        compact_ax.set_facecolor(PANEL_COLOR)
        for spine in compact_ax.spines.values():
            spine.set_visible(True)
            spine.set_color(GRID_COLOR)

        if compact_state["saved_geometry"]:
            window.geometry(compact_state["saved_geometry"])

        for ax in (ax_cpu, ax_ram, ax_gpu, ax_disk):
            ax.set_visible(True)
        cpu_name_text.set_visible(True)
        gpu_name_text.set_visible(True)
        ram_name_text.set_visible(True)
        disk_name_text.set_visible(True)
        suptitle_obj.set_visible(True)

        compact_ax.set_visible(False)
        compact_button.label.set_text("Overlay")

    fig.canvas.draw_idle()


compact_button.on_clicked(toggle_compact)


def on_press(event):
    if not compact_state["active"]:
        return
    if event.inaxes == button_ax:
        return
    if event.guiEvent is None:
        return
    drag_state["dragging"] = True
    drag_state["start_x"] = event.guiEvent.x_root
    drag_state["start_y"] = event.guiEvent.y_root


def on_release(event):
    drag_state["dragging"] = False


def on_motion(event):
    if not drag_state["dragging"] or not compact_state["active"]:
        return
    if event.guiEvent is None:
        return
    window = fig.canvas.manager.window
    x_root = event.guiEvent.x_root
    y_root = event.guiEvent.y_root
    dx = x_root - drag_state["start_x"]
    dy = y_root - drag_state["start_y"]
    new_x = window.winfo_x() + dx
    new_y = window.winfo_y() + dy
    window.geometry(f"+{new_x}+{new_y}")
    drag_state["start_x"] = x_root
    drag_state["start_y"] = y_root


fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("motion_notify_event", on_motion)


def update(frame):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    ram_used_gb = psutil.virtual_memory().used / (1024 ** 3)
    disk = get_disk_usage()

    gpu, vram_used, vram_total, gpu_temp = get_gpu_data()
    cpu_temp = get_cpu_temperature()

    cpu_data.append(cpu)
    ram_data.append(ram)
    gpu_data.append(gpu)
    disk_data.append(disk)
    cpu_temp_data.append(cpu_temp)

    x = list(range(len(cpu_data)))

    cpu_line.set_data(x, cpu_data)
    ram_line.set_data(x, ram_data)
    gpu_line.set_data(x, gpu_data)
    disk_line.set_data(x, disk_data)

    fills["cpu"].remove()
    fills["ram"].remove()
    fills["gpu"].remove()
    fills["disk"].remove()

    fills["cpu"] = ax_cpu.fill_between(x, cpu_data, color=ACCENT_CPU, alpha=0.15)
    fills["ram"] = ax_ram.fill_between(x, ram_data, color=ACCENT_RAM, alpha=0.15)
    fills["gpu"] = ax_gpu.fill_between(x, gpu_data, color=ACCENT_GPU, alpha=0.15)
    fills["disk"] = ax_disk.fill_between(x, disk_data, color=ACCENT_DISK, alpha=0.15)

    ax_cpu.set_title(f"CPU  {cpu:.0f}%   ·   {cpu_temp:.0f}°C")
    ax_ram.set_title(f"RAM  {ram:.0f}%   ·   {ram_used_gb:.1f}/{TOTAL_RAM_GB:.1f} GB")
    ax_gpu.set_title(f"GPU  {gpu:.0f}%   ·   {gpu_temp:.0f}°C   ·   {vram_used:.0f}/{vram_total:.0f} MB")
    ax_disk.set_title(f"DISK  {disk:.0f}%")

    compact_cpu_text.set_text(f"CPU   {cpu:>3.0f}%   {cpu_temp:.0f}°C")
    compact_ram_text.set_text(f"RAM   {ram:>3.0f}%   {ram_used_gb:.1f}/{TOTAL_RAM_GB:.1f} GB")
    compact_gpu_text.set_text(f"GPU   {gpu:>3.0f}%   {gpu_temp:.0f}°C")
    compact_disk_text.set_text(f"DISK  {disk:>3.0f}%")

    return (
        cpu_line, ram_line, gpu_line, disk_line,
        fills["cpu"], fills["ram"], fills["gpu"], fills["disk"],
        compact_cpu_text, compact_ram_text, compact_gpu_text, compact_disk_text
    )


ani = FuncAnimation(
    fig,
    update,
    interval=1000,
    cache_frame_data=False
)

plt.show()