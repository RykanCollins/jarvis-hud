#!/usr/bin/env python3
"""
JARVIS Live Radar — animated sweep overlay, sits on desktop like Conky.
Reads live CPU/MEM/SWAP/DISK/NET and plots them as a radar polygon
with a rotating sweep line on top.
"""
import tkinter as tk
import math, time, subprocess, os, threading

# ── config ────────────────────────────────────────────────────────────────────
SIZE        = 300          # canvas width & height in px
CX = CY     = SIZE // 2    # centre
R           = 110          # outer radius of radar
IFACE       = "wlp0s20f3"
SWEEP_SPEED = 0.4          # full rotations per second
FPS         = 40

# Iron Man palette
C_BG        = "#020c18"
C_GRID      = "#0d2535"
C_RING      = "#1a3a50"
C_SWEEP     = "#00b4ff"
C_SWEEP_END = "#020c18"    # fade-to colour
C_BLOB_OK   = "#00ff88"
C_BLOB_WARN = "#ffd700"
C_BLOB_CRIT = "#ff3c3c"
C_LABEL     = "#7ab8d4"
C_POLY      = "#00b4ff"
C_POLY_FILL = "#003355"
C_TITLE     = "#00b4ff"

LABELS = ["CPU", "MEM", "SWAP", "DISK", "NET"]
N      = len(LABELS)

# ── data collection ───────────────────────────────────────────────────────────
_prev_rx = 0
_prev_ts = 0.0

def get_values():
    global _prev_rx, _prev_ts
    vals = [0.0] * N
    # CPU
    try:
        raw = open("/proc/stat").readline().split()
        u = float(raw[1]) + float(raw[3])
        t = sum(float(x) for x in raw[1:8])
        vals[0] = u / t * 100 if t else 0
    except: pass
    # MEM
    try:
        lines = {l.split()[0]: int(l.split()[1]) for l in open("/proc/meminfo") if l.split()[0] in ("MemTotal:", "MemAvailable:")}
        vals[1] = (1 - lines["MemAvailable:"] / lines["MemTotal:"]) * 100
    except: pass
    # SWAP
    try:
        lines = {l.split()[0]: int(l.split()[1]) for l in open("/proc/meminfo") if l.split()[0] in ("SwapTotal:", "SwapFree:")}
        st = lines.get("SwapTotal:", 0)
        vals[2] = (1 - lines.get("SwapFree:", 0) / st) * 100 if st else 0
    except: pass
    # DISK
    try:
        st = os.statvfs("/")
        vals[3] = (1 - st.f_bavail / st.f_blocks) * 100
    except: pass
    # NET (rx Mbps as % of 100 Mbps ceiling)
    try:
        rx = int(open(f"/sys/class/net/{IFACE}/statistics/rx_bytes").read())
        now = time.monotonic()
        if _prev_ts:
            dt = now - _prev_ts
            mbps = (rx - _prev_rx) * 8 / 1_000_000 / dt if dt > 0 else 0
            vals[4] = min(mbps / 100 * 100, 100)
        _prev_rx, _prev_ts = rx, now
    except: pass
    return [max(0.0, min(100.0, v)) for v in vals]

# ── geometry helpers ──────────────────────────────────────────────────────────
def polar(angle_rad, r, cx=CX, cy=CY):
    return cx + r * math.cos(angle_rad), cy - r * math.sin(angle_rad)

def spoke_angle(i):
    # top = first spoke, clockwise
    return math.pi / 2 - i * 2 * math.pi / N

# ── draw sweep gradient as overlapping wedge slices ───────────────────────────
TRAIL_DEG   = 110          # degrees of visible trail
TRAIL_STEPS = 28

def hex_lerp(c1, c2, t):
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"

# ── main app ──────────────────────────────────────────────────────────────────
class RadarApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS RADAR")
        self.root.geometry(f"{SIZE}x{SIZE}+20+40")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", False)
        self.root.attributes("-alpha", 0.88)
        self.root.config(bg=C_BG)

        self.canvas = tk.Canvas(self.root, width=SIZE, height=SIZE,
                                bg=C_BG, highlightthickness=0)
        self.canvas.pack()

        # Pin to desktop layer after window is mapped
        self.root.after(300, self._pin_to_desktop)

        # drag to reposition
        self._drag_x = self._drag_y = 0
        self.canvas.bind("<ButtonPress-1>",   self._drag_start)
        self.canvas.bind("<B1-Motion>",       self._drag_move)

        self.angle   = 0.0        # current sweep angle in radians
        self.values  = [0.5] * N
        self._last_t = time.monotonic()

        self._update_data()
        self._frame()

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x_root, e.y_root

    def _drag_move(self, e):
        dx, dy = e.x_root - self._drag_x, e.y_root - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self._drag_x, self._drag_y = e.x_root, e.y_root

    def _pin_to_desktop(self):
        wid = hex(self.root.winfo_id())
        # Set window type to desktop so the WM keeps it in the desktop layer
        subprocess.Popen([
            "xprop", "-id", wid,
            "-f", "_NET_WM_WINDOW_TYPE", "32a",
            "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DESKTOP"
        ], stderr=subprocess.DEVNULL)
        # Also send below all other windows
        subprocess.Popen(
            ["wmctrl", "-i", "-r", wid, "-b", "add,below"],
            stderr=subprocess.DEVNULL
        )

    def _update_data(self):
        self.values = get_values()
        self.root.after(1500, self._update_data)

    def _frame(self):
        now  = time.monotonic()
        dt   = now - self._last_t
        self._last_t = now
        self.angle = (self.angle + SWEEP_SPEED * 2 * math.pi * dt) % (2 * math.pi)
        self._draw()
        self.root.after(int(1000 / FPS), self._frame)

    def _draw(self):
        c = self.canvas
        c.delete("all")

        # ── background circle ──────────────────────────────────────────────
        c.create_oval(CX-R, CY-R, CX+R, CY+R, fill=C_BG, outline=C_RING, width=1)

        # ── concentric rings ───────────────────────────────────────────────
        for frac in (0.25, 0.5, 0.75):
            r = R * frac
            c.create_oval(CX-r, CY-r, CX+r, CY+r,
                          fill="", outline=C_RING, width=1)

        # ── spokes ─────────────────────────────────────────────────────────
        for i in range(N):
            a = spoke_angle(i)
            x, y = polar(a, R)
            c.create_line(CX, CY, x, y, fill=C_GRID, width=1)

        # ── sweep trail (gradient wedge) ───────────────────────────────────
        trail_rad = math.radians(TRAIL_DEG)
        step_rad  = trail_rad / TRAIL_STEPS
        for s in range(TRAIL_STEPS):
            t     = s / TRAIL_STEPS           # 0 = tail, 1 = head
            a_end = self.angle - s * step_rad
            a_sta = a_end - step_rad
            col   = hex_lerp(C_SWEEP, C_SWEEP_END, 1 - t ** 0.6)
            # build wedge polygon (centre + arc approximation)
            pts = [CX, CY]
            steps = 4
            for k in range(steps + 1):
                aa = a_sta + (a_end - a_sta) * k / steps
                # convert from standard math angle to tkinter (y flipped)
                px = CX + R * math.cos(aa)
                py = CY - R * math.sin(aa)
                pts += [px, py]
            if len(pts) >= 6:
                c.create_polygon(pts, fill=col, outline="", stipple="")

        # ── sweep leading line ─────────────────────────────────────────────
        lx, ly = polar(self.angle, R)
        c.create_line(CX, CY, lx, ly, fill=C_SWEEP, width=1)

        # ── data polygon ───────────────────────────────────────────────────
        poly_pts = []
        for i, v in enumerate(self.values):
            a = spoke_angle(i)
            r = R * v / 100
            poly_pts += list(polar(a, r))
        if len(poly_pts) >= 6:
            c.create_polygon(poly_pts, fill=C_POLY_FILL,
                             outline=C_POLY, width=1, stipple="gray50")

        # ── vertex dots ────────────────────────────────────────────────────
        for i, v in enumerate(self.values):
            a = spoke_angle(i)
            r = R * v / 100
            x, y = polar(a, r)
            col = C_BLOB_CRIT if v > 80 else C_BLOB_WARN if v > 50 else C_BLOB_OK
            c.create_oval(x-3, y-3, x+3, y+3, fill=col, outline="")

        # ── labels ─────────────────────────────────────────────────────────
        for i, (lbl, v) in enumerate(zip(LABELS, self.values)):
            a    = spoke_angle(i)
            x, y = polar(a, R + 14)
            c.create_text(x, y, text=f"{lbl}\n{v:.0f}%",
                          fill=C_LABEL, font=("Share Tech Mono", 7),
                          justify="center")

        # ── centre dot ─────────────────────────────────────────────────────
        c.create_oval(CX-3, CY-3, CX+3, CY+3, fill=C_SWEEP, outline="")

        # ── title ──────────────────────────────────────────────────────────
        c.create_text(CX, SIZE - 10, text="ARC REACTOR  ·  RADAR",
                      fill=C_TITLE, font=("Share Tech Mono", 7))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    RadarApp().run()
