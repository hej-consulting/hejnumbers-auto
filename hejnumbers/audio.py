"""Eigene, lizenzfreie Tonspur für die Reels (wird im Skript erzeugt, kein Fremdmaterial).

House-Stil: Four-on-the-floor-Kick, Clap auf 2 und 4, offene Hi-Hats, Offbeat-Bass,
Akkord-Stabs mit Sidechain-Pumpen. Dazu dezentes Rauschen beim Erscheinen der Balken.
"""
import wave
import numpy as np

SR = 44100
BPM = 112
BEAT = 60 / BPM


def env(n, attack=0.005, release=0.2):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.exp(-t / release)
    return a * r


def tone(freq, dur, kind="sine", release=0.3, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "sine":
        w = np.sin(2 * np.pi * freq * t)
    elif kind == "soft_saw":
        w = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 6))
        w /= 2.0
    else:
        w = np.sin(2 * np.pi * freq * t)
    return w * env(n, release=release) * vol


def kick(vol=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 110 * np.exp(-t * 28) + 45
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * vol


def hat(vol=1.0, rng=np.random.default_rng(1)):
    n = int(0.06 * SR)
    noise = rng.standard_normal(n)
    noise = np.diff(np.concatenate([[0], noise]))  # Hochpass-Charakter
    return noise * env(n, attack=0.001, release=0.02) * vol


def whoosh(dur=0.5, vol=1.0, rng=np.random.default_rng(2)):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    # weicher Tiefpass über gleitenden Mittelwert, Hüllkurve an/ab
    k = 60
    noise = np.convolve(noise, np.ones(k) / k, mode="same")
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    return noise * shape * vol * 3


def noise_swell(dur=1.0, vol=1.0, rng=np.random.default_rng(6)):
    """Weiches, dunkles Rauschen, das langsam anschwillt (ohne Ton-Sweep)."""
    n = int(dur * SR)
    noise = np.convolve(rng.standard_normal(n), np.ones(48) / 48, mode="same")
    shape = np.linspace(0, 1, n) ** 2.5
    return noise * shape * vol * 4


def riser(dur=0.8, vol=1.0, rng=np.random.default_rng(3)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 200 + 1400 * (t / dur) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    noise = np.convolve(rng.standard_normal(n), np.ones(8) / 8, mode="same")
    shape = (t / dur) ** 2
    return (np.sin(ph) * 0.4 + noise * 0.6) * shape * vol


def add(buf, sig, at):
    i = int(round(at * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    if i < len(buf) and j > i:
        buf[i:j] += sig[: j - i]


def clap(vol=1.0, rng=np.random.default_rng(4)):
    n = int(0.22 * SR)
    noise = rng.standard_normal(n)
    noise = noise - np.convolve(noise, np.ones(6) / 6, mode="same")  # Hochpass
    t = np.arange(n) / SR
    e = np.zeros(n)
    for k, d in enumerate((0.0, 0.011, 0.022)):  # mehrfacher Anschlag wie echte Claps
        e += np.where(t >= d, np.exp(-(t - d) * (60 if k < 2 else 18)), 0)
    return noise * e * vol * 0.5


def open_hat(vol=1.0, rng=np.random.default_rng(5)):
    n = int(0.18 * SR)
    noise = rng.standard_normal(n)
    noise = np.diff(np.concatenate([[0], noise]))
    return noise * env(n, attack=0.002, release=0.07) * vol


def piano(freq, dur, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = sum(np.sin(2 * np.pi * freq * k * t) * (0.6 ** (k - 1)) * np.exp(-t * (3 + 2 * k)) for k in range(1, 6))
    return w * np.clip(t / 0.003, 0, 1) * vol


def organ(freq, dur, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = sum(np.sin(2 * np.pi * freq * k * t) * a for k, a in ((1, 1), (2, 0.6), (3, 0.35), (4, 0.25), (6, 0.12)))
    return w * env(n, attack=0.004, release=dur * 0.5) * vol * 0.6


def marimba(freq, dur, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = np.sin(2 * np.pi * freq * t) * np.exp(-t * 7) + 0.3 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 30)
    return w * np.clip(t / 0.002, 0, 1) * vol


def bass_note(freq, dur, vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    return w * env(n, attack=0.004, release=dur * 0.6) * vol


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


QUAL = {"maj": (0, 4, 7), "min": (0, 3, 7), "maj7": (0, 4, 7, 11), "min7": (0, 3, 7, 10)}

# Sechs House-Stile. Jeden Tag ein anderer, zusätzlich in wechselnder Tonart.
# chords: Klang der Akkorde; hits: Achtel-Positionen im Takt (0..7), auf denen Akkorde anschlagen
STYLES = {
    "deep house":    {"bpm": 122, "prog": [(57, "min7"), (53, "maj7"), (55, "maj"), (52, "min7")], "chords": "organ",   "hits": [1, 4, 7],       "bass": "offbeat", "clap": True, "openhat": True},
    "piano house":   {"bpm": 124, "prog": [(48, "maj"), (55, "maj"), (57, "min"), (53, "maj")],    "chords": "piano",   "hits": [0, 3, 6],       "bass": "offbeat", "clap": True, "openhat": True},
    "tropical":      {"bpm": 108, "prog": [(55, "maj"), (52, "min"), (48, "maj"), (50, "maj")],    "chords": "marimba", "hits": [0, 2, 3, 5, 7], "bass": "long",    "clap": True, "openhat": False},
    "tech house":    {"bpm": 126, "prog": [(50, "min7"), (50, "min7"), (46, "maj"), (48, "maj")],  "chords": "organ",   "hits": [3, 7],          "bass": "rolling", "clap": True, "openhat": True},
    "melodic house": {"bpm": 120, "prog": [(52, "min"), (48, "maj"), (55, "maj"), (50, "maj")],    "chords": "pad",     "hits": [],              "bass": "offbeat", "clap": True, "openhat": True},
    "disco house":   {"bpm": 124, "prog": [(53, "maj7"), (52, "min7"), (50, "min7"), (55, "maj")], "chords": "piano",   "hits": [1, 2, 5, 6],    "bass": "octave",  "clap": True, "openhat": True},
}
STYLE_ORDER = list(STYLES)
TRANSPOSE = [0, 2, -3, 5, -2]


def pick_style(day_number):
    """Gibt Stil und Tonart für einen Tag zurück; wiederholt sich erst nach 30 Tagen."""
    name = STYLE_ORDER[day_number % len(STYLE_ORDER)]
    shift = TRANSPOSE[(day_number // len(STYLE_ORDER)) % len(TRANSPOSE)]
    return name, shift


def make_track(path, seconds=9.0, bar_starts=(1.0, 2.4, 3.8, 5.2), fact_at=6.8, style="deep house", transpose=0):
    st = STYLES[style]
    beat = 60 / st["bpm"]
    e8 = beat / 2
    bar_len = beat * 4
    n = int(seconds * SR)
    harm = np.zeros(n)   # Akkorde (werden "gepumpt")
    drums = np.zeros(n)
    bass = np.zeros(n)
    sfx = np.zeros(n)
    drop = bar_starts[0]           # Beat setzt mit dem ersten Balken ein
    origin = drop - bar_len        # Raster so legen, dass ein Takt auf den Drop fällt

    # Akkorde und Bass, taktweise
    t, ci = origin, 0
    while t < seconds:
        root, q = st["prog"][ci % len(st["prog"])]
        root += transpose
        notes = [midi(root + iv) for iv in QUAL[q]]
        b = midi(root - 12)
        if st["chords"] == "pad":
            for f in notes:
                add(harm, tone(f, bar_len, "soft_saw", release=bar_len, vol=0.06), t)
                add(harm, tone(f * 2, e8, "sine", release=0.08, vol=0.05), t + e8 * ((ci * 3) % 8))
        else:
            maker = {"piano": piano, "organ": organ, "marimba": marimba}[st["chords"]]
            length = e8 * (1.6 if st["chords"] != "organ" else 0.9)
            for h in st["hits"]:
                for f in notes:
                    add(harm, maker(f, length, vol=0.09), t + h * e8)
        if t >= drop - 0.01:
            if st["bass"] == "offbeat":
                for k in range(4):
                    add(bass, bass_note(b, e8 * 0.9, 0.32), t + k * beat + e8)
            elif st["bass"] == "rolling":
                for k in range(16):
                    if k % 4 != 0:
                        add(bass, bass_note(b, e8 * 0.45, 0.26), t + k * e8 / 2)
            elif st["bass"] == "octave":
                for k in range(8):
                    add(bass, bass_note(b * (2 if k % 2 else 1), e8 * 0.8, 0.28), t + k * e8)
            else:
                add(bass, bass_note(b, bar_len, 0.3), t)
        t += bar_len
        ci += 1

    # Drums: Four-on-the-floor ab dem Drop, Clap auf 2 und 4, offene Hi-Hat auf dem Offbeat, 16tel-Shaker
    k = 0
    tb = drop
    while tb < seconds - 0.05:
        add(drums, kick(0.75), tb)
        if st["clap"] and k % 2 == 1:
            add(drums, clap(0.55), tb)
        if st["openhat"]:
            add(drums, open_hat(0.16), tb + e8)
        for s16 in (1, 3):
            add(drums, hat(0.05), tb + s16 * e8 / 2)
        tb += beat
        k += 1

    # Sidechain-Pumpen: Akkorde ducken bei jedem Kick (typisch für House)
    duck = np.ones(n)
    tb = drop
    while tb < seconds:
        i = int(tb * SR)
        m = min(n - i, int(beat * SR))
        if m > 0:
            curve = 1 - 0.75 * np.exp(-np.arange(m) / SR / (beat * 0.22))
            duck[i:i + m] = np.minimum(duck[i:i + m], curve)
        tb += beat
    harm *= duck
    bass *= 0.4 + 0.6 * duck

    # Dezente Effekte: leises, weiches Rauschen beim Erscheinen der Balken, kein Klingeln
    for s0 in bar_starts:
        add(sfx, whoosh(0.5, 0.10), s0 - 0.15)
    add(sfx, noise_swell(1.0, 0.10), drop - 1.0)

    mix = harm + drums + bass + sfx
    fade_in, fade_out = int(0.2 * SR), int(0.8 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)
    mix = np.tanh(mix * 1.3)
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.88
    pcm = (mix * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
    return path
