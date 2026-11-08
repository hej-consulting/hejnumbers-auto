"""Schritt 2: Den heutigen Post an Buffer übergeben (Instagram, TikTok, LinkedIn)."""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from . import buffer_api
from .buffer_api import Enum
from .design import ROOT


def wait_public(url, tries=20):
    for _ in range(tries):
        if requests.head(url, timeout=20, allow_redirects=True).status_code == 200:
            return
        time.sleep(10)
    raise RuntimeError("Datei nicht öffentlich erreichbar: " + url)


def main():
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    berlin = ZoneInfo("Europe/Berlin")
    day = datetime.now(berlin).strftime("%Y-%m-%d")
    path = os.path.join(ROOT, "media", day, "post.json")
    if not os.path.exists(path):
        print("Heute kein Post vorhanden.")
        sys.exit(1)
    post = json.load(open(path, encoding="utf-8"))
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/media/{day}/"
    f = post["files"]
    url = lambda name: base + name  # noqa: E731
    for name in [f["reel"], f["reel_thumb"], f["image"]] + f.get("carousel", []):
        wait_public(url(name))

    draft = os.environ.get("DRAFT") == "1"
    hh, mm = map(int, cfg["post_time_berlin"].split(":"))
    due = datetime.now(berlin).replace(hour=hh, minute=mm, second=0, microsecond=0)
    if due < datetime.now(berlin) + timedelta(minutes=10):
        due = datetime.now(berlin) + timedelta(minutes=15)
    due_utc = due.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    video = [{"video": {"url": url(f["reel"]), "thumbnailUrl": url(f["reel_thumb"])}}]
    single = [{"image": {"url": url(f["image"])}}]
    slides = [{"image": {"url": url(n)}} for n in f.get("carousel", [])]
    fmt = post["format"]

    jobs = []
    ch = cfg["channels"]
    if ch.get("instagram"):
        assets = video if fmt == "reel" else slides if fmt == "carousel" else single
        ig_type = Enum("reel") if fmt == "reel" else Enum("post")
        jobs.append(("Instagram", ch["instagram"], post["captions"]["instagram"], assets,
                     {"instagram": {"type": ig_type, "shouldShareToFeed": True}}))
    if ch.get("tiktok"):
        jobs.append(("TikTok", ch["tiktok"], post["captions"]["tiktok"], video, None))
    if ch.get("linkedin"):
        jobs.append(("LinkedIn", ch["linkedin"], post["captions"]["linkedin"],
                     slides if fmt == "carousel" else single, None))
    if not jobs:
        print("Keine Kanal-IDs in config.json eingetragen.")
        sys.exit(1)

    failed = False
    for name, cid, text, assets, meta in jobs:
        inp = {"text": text, "channelId": cid, "schedulingType": Enum("automatic"), "assets": assets}
        if meta:
            inp["metadata"] = meta
        if draft:
            inp.update({"mode": Enum("addToQueue"), "saveToDraft": True})
        else:
            inp.update({"mode": Enum("customScheduled"), "dueAt": due_utc})
        try:
            p = buffer_api.create_post(inp)
            print(f"{name}: {'Entwurf angelegt' if draft else 'geplant für ' + str(p.get('dueAt'))}")
        except Exception as e:  # noqa: BLE001
            failed = True
            print(f"{name}: FEHLER {e}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
