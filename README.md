# PC Performance Dashboard 🖥️

A little desktop dashboard that shows your CPU, RAM, GPU, and Disk usage live, right on your screen. It's got a dark theme, live graphs, hardware names, and even a floating "overlay" mode you can drag around and keep on top of games running in borderless windowed mode.

Built this mostly for fun / to keep an eye on my PC while gaming without alt-tabbing to Task Manager every 5 minutes.

## What's in here

- **`dashboard.py`** — the main event. This is the one you actually want to run. Full dashboard with graphs, dark mode, hardware names, and the overlay button.
- **`scripts/`** — some earlier/simpler versions I built along the way while figuring things out:
  - `monitor.py` — logs CPU/RAM/Disk usage to a CSV file
  - `graph.py` — plots that CSV data after the fact
  - `live_graph.py` — an early live-updating graph (just CPU + RAM, no styling)
  - `gpu_monitor.py` — a terminal-only GPU stats readout
  
  These aren't required to run the dashboard, just kept around as the "rough drafts."

## Before you run it

You'll need a few things:

1. **Windows** — sorry, this one's Windows-only. It leans on `winreg`, `nvidia-smi`, and some Windows-specific window tricks for the overlay.
2. **An NVIDIA GPU** — GPU stats come from `nvidia-smi`, which ships with NVIDIA drivers. No NVIDIA card, no GPU graph (it'll just show 0).
3. **[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)** running in the background, with its web server turned on:
   - Open LibreHardwareMonitor
   - Go to **Options > Remote Web Server > Run**
   - Make sure it's serving on `localhost:8085` (that's the default, and what the script expects)
   
   Without this running, CPU temp will just sit at 0°C — everything else still works fine though.

## Setup

Clone the repo, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Running it

```bash
python dashboard.py
```

A window pops up with four live graphs: CPU, RAM, GPU, and Disk. Hit the **Overlay** button in the top-right corner to shrink it down into a small floating, transparent panel you can drag anywhere on screen — handy for keeping an eye on stats while gaming. Click the button again (now labeled **X**) to go back to the full dashboard view.

## Notes / known quirks

- The overlay's transparency trick only works because of how Windows handles a specific "magic" background color — it won't play nice with true exclusive-fullscreen games, only borderless windowed ones.
- If your CPU is Intel rather than AMD, you might need to tweak the sensor name matching in `find_cpu_temperature()` — it currently looks for AMD's "Tctl/Tdie" label plus a couple of generic fallbacks.
- Disk usage defaults to the `C:\` drive — change `DISK_PATH` at the top of `dashboard.py` if you want to track something else.

## License

MIT — do whatever you want with it.
