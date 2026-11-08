"""hejnumbers-Design: Einzelbild (1080x1350), Karussell (4 Slides), Reel (1080x1920, 9 s)."""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")

BLUE = (116, 102, 196)
BLACK = (24, 24, 27)
WHITE = (255, 255, 255)
GREY_TEXT = (150, 150, 155)
# Hintergrund, Balkenfarbe
BACKGROUNDS = {
    "sand": ((243, 227, 188), (110, 106, 99)),
    "grau": ((233, 234, 236), (122, 122, 122)),
    "blaugrau": ((152, 166, 191), (79, 85, 99)),
}
BG_ORDER = ["sand", "grau", "blaugrau"]

W = 1080
L, R = 80, 1000


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Poppins-{weight}.ttf"), size)


def wrap(d, text, fo, max_w):
    lines, cur = [], ""
    for word in text.split():
        nxt = (cur + " " + word).strip()
        if d.textlength(nxt, font=fo) <= max_w:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def bar_widths(d, post, full):
    """Balkenbreiten: proportional, Beschriftung passt immer, Reihenfolge bleibt logisch."""
    lf, vf = font("Regular", 40), font("Medium", 40)
    nums = [float(i["number"]) for i in post["items"]]
    lo = min(nums)
    if lo < 0:  # z. B. Temperaturen: verschieben, damit alles positiv ist
        span = max(nums) - lo or 1
        nums = [n - lo + span * 0.25 for n in nums]
    mx = max(nums) or 1
    widths, mins, maxs = [], [], []
    for item, n in zip(post["items"], nums):
        min_w = d.textlength(item["label"], font=lf) + 70
        max_w = full - d.textlength(item["value"], font=vf) - 100  # Abstand Balken -> Wert
        mins.append(min_w); maxs.append(max_w)
        widths.append(max(min_w, min(max_w, full * n / mx)))
    desc = nums[0] >= nums[-1]
    if desc:
        for i in range(len(widths) - 2, -1, -1):
            widths[i] = max(widths[i], widths[i + 1])
    else:
        for i in range(1, len(widths)):
            widths[i] = max(widths[i], widths[i - 1])
    # Jeder Wert behält immer seinen Abstand zum Balken
    return [max(mn, min(mx_, w)) for w, mn, mx_ in zip(widths, mins, maxs)]


def draw_logo(d, x, y, bg):
    edge = tuple(max(0, c - 40) for c in bg)
    dot = tuple(max(0, c - 70) for c in bg)
    d.rectangle([x, y, x + 76, y + 76], outline=edge, width=3)
    for r in range(3):
        for c in range(3):
            cx, cy = x + 20 + c * 18, y + 20 + r * 18
            d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=dot)


def draw_label(d, x, y):
    d.rectangle([x, y, x + 132, y + 50], fill=BLACK)
    d.text((x + 66, y + 25), "TOP 4", font=font("SemiBold", 22), fill=WHITE, anchor="mm")


def draw_footer(d, H, bg, source):
    fy = H - 130
    draw_logo(d, L, fy, bg)
    d.text((R, fy + 22), "@hejnumbers", font=font("SemiBold", 30), fill=BLACK, anchor="rm")
    d.text((R, fy + 60), "Source: " + source, font=font("Regular", 24), fill=(70, 70, 75), anchor="rm")


def draw_card(post, H=1350, y0=90, title_a=1.0, bars=(1, 1, 1, 1), fact_a=1.0, hook_a=0.0):
    """Zeichnet die Top-4-Karte. bars = Fortschritt je Balken (Platz 1..4), 0..1."""
    bg, dark = BACKGROUNDS[post["bg"]]
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    if hook_a > 0 and post.get("hook"):
        # Hook-Frage oben im Reel, sichtbar ab dem ersten Bild
        hf = font("SemiBold", 62)
        hy = y0 - 230
        for ln in wrap(d, post["hook"], hf, R - L)[:2]:
            d.text((L, hy), ln, font=hf, fill=mix(bg, BLUE, hook_a))
            hy += 76
    y = y0
    draw_label(d, L, y)
    y += 80
    tf = font("Medium", 74)
    for ln in wrap(d, post["title"], tf, R - L):
        d.text((L, y), ln, font=tf, fill=mix(bg, BLACK, title_a))
        y += 86
    if post.get("subtitle"):
        d.text((L, y + 8), post["subtitle"], font=font("Regular", 36), fill=mix(bg, (70, 70, 75), title_a))
        y += 60
    y += 30
    # Platz bis zum Footer berechnen, Balken bei Bedarf enger setzen
    ff = font("Regular", 34)
    fact_lines = wrap(d, post["fact"], ff, R - L - 80)
    fact_h = 70 + len(fact_lines) * 46 + 30
    avail = (H - 160) - y - 20 - fact_h
    step = max(128, min(150, avail / 4))
    bh = step - 26
    bx0, bx1 = 150, R
    widths = bar_widths(d, post, bx1 - bx0)
    lf, vf = font("Regular", 40), font("Medium", 40)
    num_col = (40, 44, 54) if post["bg"] == "blaugrau" else BLACK
    for i, item in enumerate(post["items"]):
        top = y + i * step
        p = max(0.0, min(1.0, bars[i]))
        if p <= 0:
            continue
        ease = 1 - (1 - p) ** 3
        d.text((L, top + bh / 2), str(i + 1), font=font("Medium", 52), fill=mix(bg, num_col, min(1, p * 2)), anchor="lm")
        d.rectangle([bx0, top, bx1, top + bh], fill=mix(bg, WHITE, min(1, p * 2)))
        bw = widths[i] * ease
        d.rectangle([bx0, top, bx0 + bw, top + bh], fill=BLUE if i == 0 else dark)
        if p > 0.5:
            d.text((bx0 + 34, top + bh / 2), item["label"], font=lf, fill=WHITE, anchor="lm")
            d.text((bx1 - 34, top + bh / 2), item["value"], font=vf, fill=mix(WHITE, BLACK, min(1, (p - 0.5) * 2)), anchor="rm")
    y += 4 * step + 20
    if fact_a > 0:
        lines = fact_lines
        box_h = fact_h
        d.rectangle([L, y, R, y + box_h], fill=mix(bg, BLACK, fact_a))
        d.text((L + 40, y + 36), "DID YOU KNOW?", font=font("SemiBold", 22), fill=mix(BLACK, GREY_TEXT, fact_a))
        for j, ln in enumerate(lines):
            d.text((L + 40, y + 76 + j * 46), ln, font=ff, fill=mix(BLACK, WHITE, fact_a))
    draw_footer(d, H, bg, post["source"])
    return im


# ---------- Formate ----------

def render_image(post, path):
    draw_card(post).save(path, "JPEG", quality=94)
    return [path]


def render_carousel(post, folder, prefix):
    bg, _ = BACKGROUNDS[post["bg"]]
    paths = []

    # 1 Hook
    im = Image.new("RGB", (W, 1350), bg)
    d = ImageDraw.Draw(im)
    draw_label(d, L, 90)
    y = 420
    for ln in wrap(d, post["title"], font("SemiBold", 96), R - L):
        d.text((L, y), ln, font=font("SemiBold", 96), fill=BLACK)
        y += 112
    d.text((L, y + 50), post.get("hook", "Can you guess #1?"), font=font("Regular", 48), fill=BLUE)
    d.text((R, 1350 - 190), "Swipe for #1", font=font("Medium", 36), fill=BLACK, anchor="rm")
    draw_footer(d, 1350, bg, post["source"])
    paths.append(os.path.join(folder, f"{prefix}_1.jpg")); im.save(paths[-1], "JPEG", quality=94)

    # 2 Top 4
    paths.append(os.path.join(folder, f"{prefix}_2.jpg")); draw_card(post).save(paths[-1], "JPEG", quality=94)

    # 3 Fun Fact
    im = Image.new("RGB", (W, 1350), BLACK)
    d = ImageDraw.Draw(im)
    d.text((L, 380), "DID YOU KNOW?", font=font("SemiBold", 34), fill=GREY_TEXT)
    y = 460
    for ln in wrap(d, post["fact"], font("Medium", 64), R - L):
        d.text((L, y), ln, font=font("Medium", 64), fill=WHITE)
        y += 84
    d.text((R, 1350 - 108), "@hejnumbers", font=font("SemiBold", 30), fill=WHITE, anchor="rm")
    paths.append(os.path.join(folder, f"{prefix}_3.jpg")); im.save(paths[-1], "JPEG", quality=94)

    # 4 Follow
    im = Image.new("RGB", (W, 1350), BLUE)
    d = ImageDraw.Draw(im)
    y = 470
    for ln in ["A new Top 4", "every day."]:
        d.text((L, y), ln, font=font("SemiBold", 96), fill=WHITE)
        y += 112
    d.text((L, y + 50), "Follow @hejnumbers", font=font("Regular", 52), fill=WHITE)
    d.text((L, y + 130), "Save this post · Share it with a friend", font=font("Regular", 34), fill=(205, 210, 255))
    paths.append(os.path.join(folder, f"{prefix}_4.jpg")); im.save(paths[-1], "JPEG", quality=94)
    return paths


def render_reel(post, path, fps=30, seconds=9):
    """9-s-Reel: Titel, dann Balken von Platz 4 zu Platz 1, dann Fun Fact."""
    H, y0 = 1920, 380
    frames = fps * seconds
    # Zeitplan in Sekunden: Platz 4 ab 1.0, Platz 3 ab 2.4, Platz 2 ab 3.8, Platz 1 ab 5.2
    starts = {3: 1.0, 2: 2.4, 1: 3.8, 0: 5.2}
    from . import audio
    wav = path.replace(".mp4", "_audio.wav")
    from datetime import date
    style, shift = audio.pick_style(int(post.get("music_day", date.today().toordinal())))
    print(f"Musik: {style} (Tonart {shift:+d})")
    audio.make_track(wav, seconds=seconds, bar_starts=(starts[3], starts[2], starts[1], starts[0]), fact_at=6.8,
                     style=style, transpose=shift)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", wav,
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-shortest",
           "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    dur = 1.1
    for f in range(frames):
        t = f / fps
        title_a = 1.0  # Titel und Hook sofort sichtbar, kein leeres erstes Bild
        hook_a = 1.0 if t < 5.0 else max(0.0, 1 - (t - 5.0) / 0.4)  # verschwindet, wenn Platz 1 kommt
        bars = [min(1.0, max(0.0, (t - starts[i]) / dur)) for i in range(4)]
        fact_a = min(1.0, max(0.0, (t - 6.8) / 0.5))
        im = draw_card(post, H=H, y0=y0, title_a=title_a, bars=bars, fact_a=fact_a, hook_a=hook_a)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg fehlgeschlagen")
    os.remove(wav)
    # Vorschaubild = letzter Frame
    thumb = path.replace(".mp4", "_thumb.jpg")
    draw_card(post, H=H, y0=y0).save(thumb, "JPEG", quality=92)
    return [path, thumb]
