import tkinter as tk
import math
import random
import time

W, H = 1200, 800
BG = '#0f1b17'
SKY_TOP = '#15352f'
SKY_MID = '#214a40'
SKY_LOW = '#2f5a4b'
INK = '#edf1df'
MUTED = '#bfd0bd'
ACCENT = '#e7c777'
LEAF = '#8eaf5e'
STEM = '#557446'
SOIL_TOP = '#826547'
SOIL_LOW = '#3a3029'
ROOT = '#b79669'
PANEL = '#1a2e28'

PHASE_NAMES = [
    'Biji',
    'Perkecambahan',
    'Tunas',
    'Pertumbuhan',
    'Pembungaan',
    'Penyebaran Biji'
]


def clamp(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


class PlantLifeCycleApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Siklus Kehidupan Tumbuhan')
        self.root.geometry('1200x800')
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)

        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.t = 0.0
        self.duration = 42.0

        rng = random.Random(24)
        self.dust = [(rng.uniform(100, 1080), rng.uniform(80, 520), rng.uniform(0, math.tau), rng.uniform(0.7, 2.0)) for _ in range(90)]
        self.soil_grains = [(rng.uniform(90, 1110), rng.uniform(520, 730), rng.uniform(0.8, 3.2)) for _ in range(450)]
        self.clouds = [(rng.uniform(50, 1000), rng.uniform(90, 210), rng.uniform(60, 120)) for _ in range(6)]

        self.frame()

    def p(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s

    def coords(self, pts):
        out = []
        for x, y in pts:
            px, py = self.p(x, y)
            out.extend((px, py))
        return out

    def rect(self, x, y, w, h, fill, outline='', width=1, radius=0):
        if radius <= 0:
            self.canvas.create_rectangle(*self.p(x, y), *self.p(x + w, y + h), fill=fill, outline=outline, width=width * self.s)
            return
        r = min(radius, w / 2, h / 2)
        pts = [
            (x + r, y), (x + w - r, y), (x + w, y), (x + w, y + r),
            (x + w, y + h - r), (x + w, y + h), (x + w - r, y + h), (x + r, y + h),
            (x, y + h), (x, y + h - r), (x, y + r), (x, y)
        ]
        self.canvas.create_polygon(*self.coords(pts), fill=fill, outline=outline, smooth=True)

    def oval(self, x, y, rx, ry, fill, outline='', width=1):
        self.canvas.create_oval(*self.p(x - rx, y - ry), *self.p(x + rx, y + ry), fill=fill, outline=outline, width=max(1, width * self.s))

    def line(self, pts, fill, width=1, smoothline=False, arrow=None, dash=None):
        self.canvas.create_line(*self.coords(pts), fill=fill, width=max(1, width * self.s), smooth=smoothline,
                                capstyle='round', joinstyle='round', arrow=arrow, dash=dash)

    def poly(self, pts, fill, outline='', smoothline=False):
        self.canvas.create_polygon(*self.coords(pts), fill=fill, outline=outline, smooth=smoothline)

    def txt(self, x, y, text, size=14, color=INK, font='Segoe UI', anchor='nw', bold=False):
        self.canvas.create_text(*self.p(x, y), text=text, fill=color, font=(font, max(8, int(size * self.s)), 'bold' if bold else 'normal'), anchor=anchor)

    def leaf(self, x, y, angle, length, width, color=LEAF):
        if length <= 0:
            return
        def tr(u, v):
            return x + u * math.cos(angle) - v * math.sin(angle), y + u * math.sin(angle) + v * math.cos(angle)

        pts = [tr(length * i / 20, width * math.sin(math.pi * i / 20) ** 0.9) for i in range(21)]
        pts += [tr(length * i / 20, -width * math.sin(math.pi * i / 20) ** 0.9) for i in range(20, -1, -1)]
        self.poly(pts, color, '#adc887')
        self.line([tr(0, 0), tr(length, 0)], '#d6e4a7', 1)
        for j in range(1, 7):
            u = length * j / 8
            v = width * math.sin(math.pi * j / 8) * 0.75
            self.line([tr(u, 0), tr(u + length * 0.12, v)], '#91ad71', 0.7)
            self.line([tr(u, 0), tr(u + length * 0.12, -v)], '#91ad71', 0.7)

    def flower(self, x, y, r, sway=0):
        if r <= 1:
            return
        for j in range(14):
            a = sway + j * math.tau / 14
            ca, sa = math.cos(a), math.sin(a)
            pts = []
            for k in range(34):
                q = k * math.tau / 33
                u = r * (0.54 + 0.6 * math.cos(q))
                v = r * 0.23 * math.sin(q)
                pts.append((x + u * ca - v * sa, y + u * sa + v * ca))
            self.poly(pts, '#f0d996', '#d8ba6a')
        self.oval(x, y, r * 0.34, r * 0.34, '#7b5736', '#caa35b')
        for j in range(70):
            a = j * 2.39996
            d = r * 0.3 * math.sqrt(j / 70)
            self.oval(x + d * math.cos(a), y + d * math.sin(a), max(0.7, r * 0.025), max(0.7, r * 0.025), '#d6aa57')

    def callout(self, bx, by, label, tx, ty, target_anchor='last'):
        box_w = max(100, len(label) * 9 + 28)
        box_h = 38
        cx, cy = bx + box_w / 2, by + box_h / 2
        dx, dy = tx - cx, ty - cy
        if dx or dy:
            # Intersect the ray with the label boundary, then add a small gap.
            factor = 1 / max(abs(dx) / (box_w / 2), abs(dy) / (box_h / 2))
            distance = math.hypot(dx, dy)
            start = (cx + dx * factor + dx / distance * 7,
                     cy + dy * factor + dy / distance * 7)
            if factor + 7 / distance < 1:
                self.line([start, (tx, ty)], ACCENT, 1.7, arrow=target_anchor)
        self.rect(bx, by, box_w, box_h, PANEL, '#3b5a4e', 1, radius=12)
        self.txt(cx, cy, label, 13, INK, anchor='center', bold=True)

    def frame(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last_time)
        self.last_time = now
        self.t = (self.t + dt) % self.duration

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        self.s = min(cw / W, ch / H)
        self.ox = (cw - W * self.s) / 2
        self.oy = (ch - H * self.s) / 2

        if self.s > 0.1:
            self.draw(now)
        self.root.after(33, self.frame)

    def draw_background(self, now):
        for j in range(70):
            y = j * (H / 70)
            if j < 28:
                col = self.mix_color(SKY_TOP, SKY_MID, j / 28)
            else:
                col = self.mix_color(SKY_MID, SKY_LOW, (j - 28) / 42)
            self.rect(0, y, W, H / 70 + 2, col)

        self.oval(970, 120, 42, 42, '#efd697')
        for j in range(9, 0, -1):
            self.oval(970, 120, 48 + j * 7, 48 + j * 7, self.mix_color('#d7c27c', BG, j / 10))

        for idx, (cx, cy, size) in enumerate(self.clouds):
            shift = (now * (8 + idx)) % (W + 260)
            x = (cx + shift) % (W + 260) - 130
            for ox, oy, r in [(-40, 6, 34), (-6, -8, 42), (34, 5, 30), (62, 10, 22)]:
                self.oval(x + ox, cy + oy, r, r * 0.72, '#dbe7df')

        self.poly([(0, 520), (180, 420), (350, 500), (560, 400), (820, 515), (1040, 410), (1200, 500), (1200, 560), (0, 560)], '#244238')
        self.poly([(0, 540), (200, 460), (420, 530), (700, 445), (940, 550), (1200, 470), (1200, 595), (0, 595)], '#1b352c')

        for i in range(45):
            self.rect(0, 500 + i * 6, W, 7, self.mix_color(SOIL_TOP, SOIL_LOW, i / 44))
        self.line([(0, 500), (1200, 500)], '#9b936a', 2)

        for x, y, r in self.soil_grains:
            shade = '#9c805c' if int(x + y) % 5 == 0 else '#604c37'
            self.oval(x, y, r, r * 0.38, shade)

        for x, y, phase, size in self.dust:
            xx = x + math.sin(now * 0.5 + phase) * 12
            yy = y + math.cos(now * 0.35 + phase) * 7
            self.oval(xx, yy, size, size, '#c4d3c1')

    def mix_color(self, c1, c2, t):
        t = clamp(t)
        rgb1 = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
        rgb2 = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
        rgb = [int(a * (1 - t) + b * t) for a, b in zip(rgb1, rgb2)]
        return '#%02x%02x%02x' % tuple(rgb)

    def draw(self, now):
        self.canvas.delete('all')
        self.draw_background(now)

        self.txt(60, 42, 'Siklus Kehidupan Tumbuhan', 30, INK, 'Georgia')
        self.txt(60, 80, 'Animasi pertumbuhan otomatis', 12, MUTED)

        phase_index = int((self.t / self.duration) * 6) % 6
        phase_name = PHASE_NAMES[phase_index]

        pill_w = 205
        self.rect(925, 46, pill_w, 42, '#192d27', '#3e6354', 1, radius=14)
        self.txt(1027.5, 67, phase_name, 14, ACCENT, anchor='center', bold=True)

        progress_w = 260
        self.rect(870, 100, progress_w, 6, '#29473d')
        self.rect(870, 100, progress_w * (self.t / self.duration), 6, ACCENT)

        cx = 600
        ground_y = 500
        wind = math.sin(now * 1.5) * 5

        # phase growth values
        seed_vis = 1 - smooth((self.t - 7) / 4)
        root_g = smooth((self.t - 3) / 10)
        sprout_g = smooth((self.t - 8) / 10)
        leaf_g = smooth((self.t - 14) / 12)
        flower_g = smooth((self.t - 23) / 7)
        fruit_g = smooth((self.t - 31) / 6)
        release_g = smooth((self.t - 36) / 5)
        fade = smooth((self.t - 39) / 3)

        total_height = 260 * sprout_g * (1 - 0.18 * fade)

        # roots
        for k in range(12):
            angle = (k - 5.5) * 0.20
            length = (72 + 16 * math.sin(k * 1.7)) * root_g
            pts = [(cx, ground_y + 4)]
            for j in range(1, 15):
                f = j / 14
                pts.append((cx + math.sin(angle) * length * f + math.sin(f * 4 + k) * 7 * root_g,
                            ground_y + length * f))
            if root_g > 0.02:
                self.line(pts, ROOT, 1.4, True)
                if root_g > 0.4:
                    for q in (5, 9):
                        rx, ry = pts[q]
                        self.line([(rx, ry), (rx + (-1) ** (k + q) * 14 * root_g, ry + 8 * root_g),
                                   (rx + (-1) ** (k + q) * 22 * root_g, ry + 14 * root_g)], ROOT, 0.8, True)

        # seed
        if seed_vis > 0.02:
            self.oval(cx, ground_y + 7, 12 * seed_vis + 4, 7 * seed_vis + 3, '#c39a5a', '#efcea0')

        # stem path
        def stem_point(f):
            return cx + wind * f * f + 14 * math.sin(f * 2.5) * sprout_g, ground_y - total_height * f

        top_x, top_y = cx, ground_y
        if total_height > 1:
            stem_pts = [stem_point(i / 30) for i in range(31)]
            self.line(stem_pts, '#314c2d', 9 * sprout_g, True)
            self.line(stem_pts, STEM, 4.6 * sprout_g, True)
            top_x, top_y = stem_pts[-1]

            # leaves
            for j in range(6):
                f = 0.20 + j * 0.12
                x, y = stem_point(f)
                g = clamp((leaf_g - j * 0.08) * 1.7)
                side = -1 if j % 2 == 0 else 1
                ang = (-2.6 if side == -1 else -0.55) + math.sin(now * 1.4 + j) * 0.05
                length = (100 - j * 8) * g
                width = length * 0.29
                self.leaf(x, y, ang, length, width)

            # sprout small leaf at early phase
            if sprout_g > 0.1 and leaf_g < 0.25:
                x, y = stem_point(0.86)
                self.leaf(x, y, -0.8, 40 * sprout_g, 12 * sprout_g)
                self.leaf(x, y, -2.3, 40 * sprout_g, 12 * sprout_g)

        # flower or fruit
        if flower_g > 0.02 and fruit_g < 0.95:
            bloom_size = 54 * flower_g * (1 - 0.3 * fruit_g)
            self.flower(top_x, top_y, bloom_size, sway=wind * 0.02)

        if fruit_g > 0.08:
            fruit_r = 30 * fruit_g
            self.oval(top_x, top_y, fruit_r, fruit_r, '#6e5838', '#b49d69', 2)
            for j in range(85):
                a = j * 2.39996
                d = fruit_r * 0.9 * math.sqrt(j / 85)
                self.oval(top_x + d * math.cos(a), top_y + d * math.sin(a), fruit_r * 0.045, fruit_r * 0.075, '#d9c184')

        falling_seeds = []
        if release_g > 0.02:
            for j in range(16):
                f = clamp((release_g - j * 0.03) * 1.15)
                if f <= 0:
                    continue
                sx = top_x + (j % 2 * 2 - 1) * (35 + j * 8) * f + math.sin(j + f * 6) * 10
                sy = top_y + 260 * f * f - 30 * math.sin(f * math.pi)
                falling_seeds.append((sx, sy))
                self.oval(sx, sy, 3.5, 2.2, '#dec07e')
                self.line([(sx, sy), (sx + 8, sy - 7)], '#f0e3c4', 0.8)

        # subtle bee during flowering
        if 24 < self.t < 31 and flower_g > 0.5 and fruit_g < 0.5:
            a = now * 1.3
            bx = top_x + 95 * math.cos(a)
            by = top_y + 44 * math.sin(a * 1.4)
            self.oval(bx - 3, by - 4, 5, 3, '#d8e2d2')
            self.oval(bx + 3, by - 4, 5, 3, '#d8e2d2')
            self.oval(bx, by, 6, 3, '#ebb95e')
            self.line([(bx - 2, by), (bx + 2, by)], '#413729', 1.5)

        # callouts per phase
        if phase_index == 0:
            self.callout(230, 310, 'Biji', cx - 4, ground_y + 4)
            self.callout(780, 265, 'Tanah', 760, 520)
        elif phase_index == 1:
            self.callout(210, 240, 'Akar', cx - 38, ground_y + 70)
            self.callout(805, 245, 'Perkecambahan', cx + 10, ground_y - 15)
        elif phase_index == 2:
            self.callout(230, 210, 'Tunas', top_x, max(ground_y - 60, top_y + 30))
            self.callout(815, 285, 'Akar Muda', cx + 25, ground_y + 85)
        elif phase_index == 3:
            self.callout(210, 185, 'Daun', cx - 85, ground_y - 150)
            self.callout(825, 205, 'Batang', cx + 12, ground_y - 160)
        elif phase_index == 4:
            self.callout(215, 160, 'Bunga', top_x - 6, top_y - 8)
            self.callout(840, 235, 'Tanaman Dewasa', cx + 35, ground_y - 210)
        elif phase_index == 5:
            self.callout(220, 155, 'Biji', top_x + 6, top_y)
            target = falling_seeds[min(4, len(falling_seeds) - 1)] if falling_seeds else (top_x + 70, top_y + 40)
            self.callout(835, 250, 'Penyebaran Biji', target[0], target[1])

        # bottom phase strip, minimal
        self.rect(160, 730, 880, 36, '#152720', '#355447', 1, radius=12)
        segment = 880 / 6
        for i, name in enumerate(PHASE_NAMES):
            x = 160 + i * segment
            if i == phase_index:
                self.rect(x + 3, 733, segment - 6, 30, '#27463a', '', 1, radius=10)
            self.txt(x + segment / 2, 748, name, 10, ACCENT if i == phase_index else MUTED, anchor='center', bold=(i == phase_index))
            if i < 5:
                self.line([(x + segment, 736), (x + segment, 760)], '#39584d', 1)


if __name__ == '__main__':
    root = tk.Tk()
    PlantLifeCycleApp(root)
    root.mainloop()
