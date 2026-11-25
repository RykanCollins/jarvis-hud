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

## Layout

The HUD uses three Conky panels across two sides of the screen:

**Right panel** (`jarvis.conf`)
- Date / Time (top)
- System Vitals — CPU, memory, swap, load, uptime, processes
- Thermal — live thermal zone temperatures
- Storage — disk usage and I/O
- Network — interface, SSID, IP, TX/RX

**Left panel — top** (`jarvis-radar.conf` + `radar_live.py`)
- Animated radar sweep with CPU/MEM/SWAP/DISK/NET polygon

**Left panel — bottom** (`jarvis-left.conf`, positioned below radar)
- Top Processes — top 5 by CPU and memory
- LAN Scanner — nmap sweep of local subnet, cached every 60s

---

## File Overview

| File | Purpose |
|------|---------|
| `jarvis.conf` | Right panel — vitals, thermal, storage, network |
| `jarvis-left.conf` | Left panel — top processes and LAN scanner (below radar) |
| `jarvis-radar.conf` | Left panel — animated radar overlay via Conky |
| `jarvis-conky.desktop` | Autostart entry for all three panels + radar script |
| `radar_live.py` | Animated radar — standalone Python/Tkinter window |
| `radar_chart.py` | Generates static radar PNG for Conky |
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

# Launch all panels
conky -c ~/.config/conky/jarvis.conf -d
conky -c ~/.config/conky/jarvis-radar.conf -d
conky -c ~/.config/conky/jarvis-left.conf -d
nohup python3 ~/.config/conky/radar_live.py > /tmp/radar.log 2>&1 & disown
```

### Autostart

Copy `jarvis-conky.desktop` to `~/.config/autostart/`:

```bash
cp jarvis-conky.desktop ~/.config/autostart/
```

It launches all three panels and the radar script with an 8-second delay to let the desktop settle.

---

## Customisation

| Setting | File | Variable |
|---------|------|----------|
| Sweep speed | `radar_live.py` | `SWEEP_SPEED` (rotations/sec) |
| Radar size | `radar_live.py` | `SIZE`, `R` |
| Network interface | `radar_live.py` / `net_scan.sh` | `IFACE` / subnet |
| Screen position (right) | `jarvis.conf` | `alignment`, `gap_x`, `gap_y` |
| Screen position (left bottom) | `jarvis-left.conf` | `gap_y` (default 512 — adjust to clear radar) |

---

## Preview

```
LEFT SIDE                          RIGHT SIDE
─────────────────────────          ─────────────────────────
A R C  ·  R A D A R                J . A . R . V . I . S
▸ SYSTEM LOAD                      ────────────────────────
  [animated radar polygon]         ▸ DATE / TIME
  CPU 12%  MEM 47%  ...              22:14:07
────────────────────────             Wednesday, 25 Nov 2026
                                   ▸ SYSTEM VITALS
▸ TOP PROCESSES                      CPU  12%  ████████░░░
  firefox    4.2%   1.8%             MEM  47%  █████████░░
  conky      0.9%   0.3%             ...
  ...                              ▸ THERMAL
▸ LAN SCANNER                      ▸ STORAGE
  192.168.1.1    TP-Link            ▸ NETWORK
  192.168.1.42   Apple            ────────────────────────
────────────────────────
```

---

## License

MIT
