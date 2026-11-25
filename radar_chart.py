#!/usr/bin/env python3
import subprocess, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def read_val(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        return float(out)
    except:
        return 0.0

def cpu():
    return read_val("grep -m1 'cpu ' /proc/stat | awk '{u=$2+$4; t=$2+$3+$4+$5; print int(u/t*100)}'")

def mem():
    return read_val("free | awk '/Mem/{printf \"%.0f\", $3/$2*100}'")

def swap():
    v = read_val("free | awk '/Swap/{if($2>0) printf \"%.0f\", $3/$2*100; else print 0}'")
    return v

def disk():
    return read_val("df / | awk 'NR==2{printf \"%.0f\", $3/$2*100}'")

def net_load():
    # rx bytes delta over 1s as % of a 100 Mbps ceiling
    try:
        iface = "wlp0s20f3"
        p = f"/sys/class/net/{iface}/statistics/rx_bytes"
        with open(p) as f: b1 = int(f.read())
        import time; time.sleep(0.5)
        with open(p) as f: b2 = int(f.read())
        mbps = (b2 - b1) * 2 * 8 / 1_000_000
        return min(mbps / 100 * 100, 100)
    except:
        return 0.0

values = [cpu(), mem(), swap(), disk(), net_load()]
labels = ['CPU', 'MEM', 'SWAP', 'DISK', 'NET']
N = len(values)
angles = [n / float(N) * 2 * math.pi for n in range(N)]
angles += angles[:1]
vals = [v / 100.0 for v in values]
vals += vals[:1]

fig = plt.figure(figsize=(2.8, 2.8), facecolor='none')
ax = fig.add_subplot(111, polar=True, facecolor='none')

# grid rings
for r in [0.25, 0.5, 0.75, 1.0]:
    ring_angles = np.linspace(0, 2 * np.pi, 200)
    ax.plot(ring_angles, [r]*200, color='#1a3a50', linewidth=0.6, zorder=1)

# spokes
for a in angles[:-1]:
    ax.plot([a, a], [0, 1], color='#1a3a50', linewidth=0.6, zorder=1)

# filled area
ax.fill(angles, vals, alpha=0.25, color='#00b4ff', zorder=2)
ax.plot(angles, vals, color='#00b4ff', linewidth=1.5, zorder=3)

# dots at vertices
for a, v in zip(angles[:-1], vals[:-1]):
    color = '#ff3c3c' if v > 0.8 else '#ffd700' if v > 0.5 else '#00ff88'
    ax.plot(a, v, 'o', color=color, markersize=4, zorder=4)

# labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, color='#7ab8d4', fontsize=7, fontfamily='monospace')
ax.set_ylim(0, 1)
ax.set_yticks([])
ax.spines['polar'].set_visible(False)
ax.tick_params(pad=4)

plt.tight_layout(pad=0.2)
out = os.path.expanduser('~/.config/conky/radar.png')
fig.savefig(out, dpi=100, transparent=True, bbox_inches='tight', pad_inches=0.05)
plt.close(fig)
