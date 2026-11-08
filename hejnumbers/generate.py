"""Schritt 1: Thema wählen, recherchieren, prüfen, rendern. Ergebnis in media/<datum>/."""
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from . import design, research

ROOT = design.ROOT
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    cfg = load(os.path.join(ROOT, "config.json"), {})
    hist_path = os.path.join(ROOT, "data", "history.json")
    history = load(hist_path, [])
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    day = now.strftime("%Y-%m-%d")
    fmt = os.environ.get("FORMAT") or cfg["weekly_formats"][DAYS[now.weekday()]]
    category = cfg["categories"][now.timetuple().tm_yday % len(cfg["categories"])]

    if os.environ.get("SAMPLE") == "1":
        post = load(os.path.join(ROOT, "data", "sample_post.json"), None)
        print("Beispieldaten ohne Recherche")
    else:
        post, avoid = None, [h["topic"] for h in history]
        for attempt in range(1, cfg.get("max_attempts", 3) + 1):
            print(f"Versuch {attempt}: Kategorie {category}")
            try:
                cand = research.research(cfg["model"], category, avoid)
            except Exception as e:  # noqa: BLE001
                print("Recherche fehlgeschlagen:", e)
                continue
            if not research.valid_shape(cand):
                print("Verworfen: unvollständig oder weniger als 2 Quellen")
                avoid.append(cand.get("topic", "?"))
                continue
            check = research.verify(cfg["model"], cand)
            if check.get("verdict") == "ok":
                post = cand
                break
            print("Verworfen beim Faktencheck:", check.get("problems"))
            avoid.append(cand.get("topic", "?"))
        if not post:
            print("Kein Thema hat den Faktencheck bestanden. Heute kein Post.")
            sys.exit(1)

    post["bg"] = design.BG_ORDER[len(history) % 3]
    post["format"] = fmt
    folder = os.path.join(ROOT, "media", day)
    os.makedirs(folder, exist_ok=True)
    files = {}
    files["reel"], files["reel_thumb"] = [os.path.basename(p) for p in design.render_reel(post, os.path.join(folder, "reel.mp4"))]
    files["image"] = os.path.basename(design.render_image(post, os.path.join(folder, "image.jpg"))[0])
    if fmt == "carousel":
        files["carousel"] = [os.path.basename(p) for p in design.render_carousel(post, folder, "slide")]
    post["files"] = files
    post["date"] = day
    with open(os.path.join(folder, "post.json"), "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=1)

    history.append({"date": day, "topic": post.get("topic", post["title"]), "title": post["title"]})
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)
    print(f"Fertig: {post['title']} ({fmt}) in media/{day}")


if __name__ == "__main__":
    main()
