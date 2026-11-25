#!/usr/bin/env python3
"""
JARVIS Live Wallpaper — fullscreen Iron Man HUD background.
Sits in the desktop layer behind all windows and the radar overlay.
"""
import tkinter as tk
import math, time, random, subprocess

W, H   = 1600, 900
FPS    = 30
CX, CY = W // 2, H // 2

# ── palette ───────────────────────────────────────────────────────────────────
C_BG        = "#020c18"
C_GRID      = "#0a1f30"
C_GRID_BR   = "#0d2d44"
C_ARC_1     = "#00b4ff"
C_ARC_2     = "#004466"
C_SCAN      = "#00b4ff"
C_PARTICLE  = "#00b4ff"
C_GOLD      = "#ffd700"
C_DIM       = "#051525"
C_TEXT      = "#0d3550"

# ── hex grid ──────────────────────────────────────────────────────────────────
HEX_SIZE    = 36
HEX_COLS    = int(W / (HEX_SIZE * 1.73)) + 3
HEX_ROWS    = int(H / (HEX_SIZE * 1.5))  + 3

def hex_corners(cx, cy, s):
    return [(cx + s * math.cos(math.radians(60*i - 30)),
             cy + s * math.sin(math.radians(60*i - 30))) for i in range(6)]

def flat_list(pts):
    return [v for p in pts for v in p]

# precompute grid offsets
HEX_GRID = []
for row in range(-1, HEX_ROWS + 1):
    for col in range(-1, HEX_COLS + 1):
        x = col * HEX_SIZE * math.sqrt(3)
        if row % 2 == 1:
            x += HEX_SIZE * math.sqrt(3) / 2
        y = row * HEX_SIZE * 1.5
        HEX_GRID.append((x, y))

# ── particles ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x  = random.uniform(0, W)
        self.y  = random.uniform(0, H)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.6, -0.1)
        self.r  = random.uniform(1, 2.5)
        self.alpha = random.uniform(0.3, 1.0)
        self.life  = random.uniform(0.4, 1.0)
        self.decay = random.uniform(0.002, 0.006)

    def step(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        if self.life <= 0 or self.y < -5:
            self.reset()
            self.y = H + 5

PARTICLES = [Particle() for _ in range(80)]

# ── arc reactor rings ─────────────────────────────────────────────────────────
class ArcRing:
    def __init__(self, delay=0):
        self.t     = delay
        self.speed = 0.4

    def step(self, dt):
        self.t += dt * self.speed
        if self.t > 1.0:
            self.t -= 1.0

    @property
    def radius(self):
        return 60 + self.t * 420

    @property
    def opacity(self):
        # fade in then out
        return max(0.0, 1.0 - self.t) * 0.6

ARC_RINGS = [ArcRing(delay=i / 4) for i in range(4)]

# ── scan line ─────────────────────────────────────────────────────────────────
class ScanLine:
    def __init__(self, start_y, speed):
        self.y     = start_y
        self.speed = speed

    def step(self, dt):
        self.y += self.speed * dt * H
        if self.y > H + 10:
            self.y = -10

SCAN_LINES = [ScanLine(H * i / 3, 0.08) for i in range(3)]

# ── corner brackets ───────────────────────────────────────────────────────────
CORNERS = [
    (40, 40, 1, 1), (W-40, 40, -1, 1),
    (40, H-40, 1, -1), (W-40, H-40, -1, -1)
]

# ── alpha → hex colour ────────────────────────────────────────────────────────
def alpha_col(base_hex, alpha):
    r = int(base_hex[1:3], 16)
    g = int(base_hex[3:5], 16)
    b = int(base_hex[5:7], 16)
    br = int(int("02", 16) + (r - int("02", 16)) * alpha)
    bg = int(int("0c", 16) + (g - int("0c", 16)) * alpha)
    bb = int(int("18", 16) + (b - int("18", 16)) * alpha)
    return f"#{max(0,min(255,br)):02x}{max(0,min(255,bg)):02x}{max(0,min(255,bb)):02x}"

# ── grid scroll offset ────────────────────────────────────────────────────────
grid_offset_x = 0.0
grid_offset_y = 0.0
GRID_SPEED_X  = 4.0
GRID_SPEED_Y  = 2.0

# ── main ──────────────────────────────────────────────────────────────────────
class Wallpaper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS WALLPAPER")
        self.root.geometry(f"{W}x{H}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", False)
        self.root.attributes("-alpha", 1.0)
        self.root.config(bg=C_BG)

        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg=C_BG, highlightthickness=0)
        self.canvas.pack()

        self.root.after(300, self._pin_to_desktop)
        self._last_t = time.monotonic()
        self._frame()

    def _pin_to_desktop(self):
        wid = hex(self.root.winfo_id())
        subprocess.Popen([
            "xprop", "-id", wid,
            "-f", "_NET_WM_WINDOW_TYPE", "32a",
            "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DESKTOP"
        ], stderr=subprocess.DEVNULL)
        subprocess.Popen(
            ["wmctrl", "-i", "-r", wid, "-b", "add,below"],
            stderr=subprocess.DEVNULL
        )

    def _frame(self):
        global grid_offset_x, grid_offset_y
        now = time.monotonic()
        dt  = now - self._last_t
        self._last_t = now

        grid_offset_x = (grid_offset_x + GRID_SPEED_X * dt) % (HEX_SIZE * math.sqrt(3))
        grid_offset_y = (grid_offset_y + GRID_SPEED_Y * dt) % (HEX_SIZE * 1.5)

        for ring in ARC_RINGS:
            ring.step(dt)
        for sl in SCAN_LINES:
            sl.step(dt)
        for p in PARTICLES:
            p.step()

        self._draw()
        self.root.after(int(1000 / FPS), self._frame)

    def _draw(self):
        c = self.canvas
        c.delete("all")

        # ── background ────────────────────────────────────────────────────
        c.create_rectangle(0, 0, W, H, fill=C_BG, outline="")

        # ── scrolling hex grid ────────────────────────────────────────────
        ox = -grid_offset_x
        oy = -grid_offset_y
        for (gx, gy) in HEX_GRID:
            pts = hex_corners(gx + ox, gy + oy, HEX_SIZE - 2)
            # highlight random hexes faintly
            dist = math.hypot(gx + ox - CX, gy + oy - CY)
            col  = C_GRID_BR if dist < 200 else C_GRID
            c.create_polygon(flat_list(pts), fill=C_DIM, outline=col, width=1)

        # ── arc reactor pulse rings ───────────────────────────────────────
        for ring in ARC_RINGS:
            if ring.opacity <= 0:
                continue
            col = alpha_col(C_ARC_1, ring.opacity)
            r   = ring.radius
            c.create_oval(CX-r, CY-r, CX+r, CY+r,
                          outline=col, width=1, fill="")

        # ── arc reactor centre ────────────────────────────────────────────
        pulse = 0.5 + 0.5 * math.sin(time.monotonic() * 3)
        inner = 18 + pulse * 6
        c.create_oval(CX-30, CY-30, CX+30, CY+30,
                      outline=C_ARC_2, width=1, fill=C_DIM)
        c.create_oval(CX-int(inner), CY-int(inner),
                      CX+int(inner), CY+int(inner),
                      outline=C_ARC_1, width=2, fill=C_DIM)
        # triangle inside
        tri = [(CX + 12*math.cos(math.radians(90 + 120*i)),
                CY - 12*math.sin(math.radians(90 + 120*i))) for i in range(3)]
        c.create_polygon(flat_list(tri), fill="", outline=C_ARC_1, width=1)

        # ── scan lines ────────────────────────────────────────────────────
        for sl in SCAN_LINES:
            alpha = 0.12
            col   = alpha_col(C_SCAN, alpha)
            c.create_line(0, sl.y, W, sl.y, fill=col, width=1)
            # glow band
            for off in (1, 2, 3):
                a2  = alpha * (1 - off / 4)
                col2 = alpha_col(C_SCAN, a2)
                c.create_line(0, sl.y + off, W, sl.y + off, fill=col2, width=1)
                c.create_line(0, sl.y - off, W, sl.y - off, fill=col2, width=1)

        # ── particles ─────────────────────────────────────────────────────
        for p in PARTICLES:
            col = alpha_col(C_PARTICLE, p.life * p.alpha)
            x, y, r = p.x, p.y, p.r
            c.create_oval(x-r, y-r, x+r, y+r, fill=col, outline="")

        # ── corner brackets ───────────────────────────────────────────────
        L = 40
        for (bx, by, sx, sy) in CORNERS:
            c.create_line(bx, by, bx + sx*L, by,       fill=C_ARC_1, width=2)
            c.create_line(bx, by, bx,         by + sy*L, fill=C_ARC_1, width=2)

        # ── status text ───────────────────────────────────────────────────
        c.create_text(CX, H - 18,
                      text="STARK INDUSTRIES  ·  MARK L  ·  ARC REACTOR ONLINE",
                      fill=C_TEXT, font=("Share Tech Mono", 8))
        c.create_text(20, H - 18, anchor="w",
                      text=time.strftime("%H:%M:%S"),
                      fill=C_TEXT, font=("Share Tech Mono", 8))
        c.create_text(W - 20, H - 18, anchor="e",
                      text="SYSTEM NOMINAL",
                      fill=C_TEXT, font=("Share Tech Mono", 8))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    Wallpaper().run()
