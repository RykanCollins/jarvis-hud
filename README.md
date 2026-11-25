# JARVIS HUD

An Iron Man–themed desktop overlay for Linux, built with Conky and Python.

![Iron Man HUD](https://img.shields.io/badge/theme-Iron%20Man-cc0000?style=flat-square) ![Platform](https://img.shields.io/badge/platform-Linux-blue?style=flat-square) ![Python](https://img.shields.io/badge/python-3.8%2B-yellow?style=flat-square)

---

## Features

- **System Vitals** — CPU, memory, swap, load average, uptime, process count
- **Thermal** — live temperature readout from thermal zones
- **Storage** — disk usage and I/O rates
- **Network** — interface, SSID, IP, TX/RX speeds
- **Top Processes** — top 5 by CPU and memory
- **LAN Scanner** — nmap sweep of your local subnet, cached every 60 seconds
- **Live Animated Radar** — rotating sweep line with real-time CPU/MEM/SWAP/DISK/NET polygon, draggable window
- **Clock** — large Orbitron font date and time

---

## Requirements

```bash
sudo apt install conky-all nmap python3-matplotlib python3-numpy
```

Fonts (copy to `~/.local/share/fonts/` and run `fc-cache -fv`):
- [Orbitron](https://fonts.google.com/specimen/Orbitron)
- [Share Tech Mono](https://fonts.google.com/specimen/Share+Tech+Mono)

---

## File Overview

| File | Purpose |
|------|---------|
| `jarvis.conf` | Main Conky panel — right side of screen |
| `jarvis-radar.conf` | Static radar Conky panel (optional, superseded by live radar) |
| `radar_live.py` | Animated radar overlay — standalone Python/Tkinter window |
| `radar_chart.py` | Generates static radar PNG for Conky (used by jarvis-radar.conf) |
| `net_scan.sh` | LAN scanner script called by Conky every 60s |

---

## Installation

```bash
# Clone
git clone https://github.com/RykanCollins/jarvis-hud.git ~/.config/conky

# Make scripts executable
chmod +x ~/.config/conky/net_scan.sh ~/.config/conky/radar_live.py ~/.config/conky/radar_chart.py

# Allow passwordless nmap for MAC/vendor lookup (optional)
echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/nmap" | sudo tee /etc/sudoers.d/jarvis-nmap
sudo chmod 440 /etc/sudoers.d/jarvis-nmap

# Launch
conky -c ~/.config/conky/jarvis.conf --daemonize
nohup python3 ~/.config/conky/radar_live.py > /tmp/radar.log 2>&1 & disown
```

### Autostart

Copy `jarvis-conky.desktop` to `~/.config/autostart/` or create it:

```ini
[Desktop Entry]
Type=Application
Name=JARVIS Conky HUD
Exec=bash -c "sleep 8 && conky -c ~/.config/conky/jarvis.conf & sleep 1 && nohup python3 ~/.config/conky/radar_live.py > /tmp/radar.log 2>&1 & disown"
X-GNOME-Autostart-enabled=true
```

---

## Customisation

| Setting | File | Variable |
|---------|------|----------|
| Sweep speed | `radar_live.py` | `SWEEP_SPEED` (rotations/sec) |
| Radar size | `radar_live.py` | `SIZE`, `R` |
| Network interface | `radar_live.py` / `net_scan.sh` | `IFACE` / subnet |
| Screen position | `jarvis.conf` | `alignment`, `gap_x`, `gap_y` |

---

## Preview

```
J . A . R . V . I . S
────────────────────────────────
▸ SYSTEM VITALS
  CPU  12%  ████████░░░░░░░░░░░░
  MEM  47%  █████████████░░░░░░░
  ...
▸ LAN SCANNER
  192.168.1.1      TP-Link
  192.168.1.42     Apple
  ...
MARK L  ·  ARC REACTOR  ·  NOMINAL
```

---

## License

MIT
