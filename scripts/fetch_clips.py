#!/usr/bin/env python3
"""Télécharge les clips Twitch pour une catégorie donnée (ex: Just Chatting).

Utilise l'API Helix de Twitch. Configurez `twitch_client_id` et
`twitch_oauth_token` (Bearer) dans un fichier JSON (ex: `config.json`).
"""
import argparse
import datetime
import json
import os
import re
import sys
from typing import List

import requests


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def helix_get(url: str, headers: dict, params: dict = None):
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_game_id(name: str, headers: dict):
    url = "https://api.twitch.tv/helix/games"
    data = helix_get(url, headers, params={"name": name})
    if data.get("data"):
        return data["data"][0]["id"]
    return None


def get_clips(game_id: str, headers: dict, started_at: str, ended_at: str) -> List[dict]:
    url = "https://api.twitch.tv/helix/clips"
    clips = []
    params = {"game_id": game_id, "first": 100, "started_at": started_at, "ended_at": ended_at}
    data = helix_get(url, headers, params=params)
    clips.extend(data.get("data", []))
    return clips


def thumb_to_mp4(url: str) -> str:
    # Twitch preview URL -> guess MP4 URL (heuristic used commonly)
    return re.sub(r"-preview-.*\\.jpg$", ".mp4", url)


def download_file(url: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    client_id = cfg.get("twitch_client_id")
    token = cfg.get("twitch_oauth_token")
    category = cfg.get("category", "Just Chatting")
    days = int(cfg.get("days", 7))
    num_clips = int(cfg.get("num_clips", 10))
    out = cfg.get("output_dir", "output")

    if not client_id or not token:
        print("Erreur: remplissez twitch_client_id et twitch_oauth_token dans le config.json")
        sys.exit(1)

    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}
    game_id = get_game_id(category, headers)
    if not game_id:
        print(f"Catégorie '{category}' introuvable via l'API Twitch Helix.")
        sys.exit(1)

    ended_at = datetime.datetime.utcnow()
    started_at = ended_at - datetime.timedelta(days=days)
    ended_at_s = ended_at.isoformat() + "Z"
    started_at_s = started_at.isoformat() + "Z"

    clips = get_clips(game_id, headers, started_at_s, ended_at_s)
    if not clips:
        print("Aucun clip trouvé pour la période demandée.")
        return

    # Trier par view_count décroissant
    clips.sort(key=lambda c: c.get("view_count", 0), reverse=True)
    selected = clips[:num_clips]

    downloads = []
    for c in selected:
        clip_id = c.get("id")
        thumb = c.get("thumbnail_url")
        if not thumb:
            continue
        mp4 = thumb_to_mp4(thumb)
        dest = os.path.join(out, "clips", f"{clip_id}.mp4")
        downloads.append((mp4, dest, c.get("title")))

    for url, dest, title in downloads:
        print(f"Téléchargement: {title} -> {dest}")
        if args.dry_run:
            continue
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"Erreur téléchargement {url}: {e}")


if __name__ == "__main__":
    main()
