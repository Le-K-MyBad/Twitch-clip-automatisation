#!/usr/bin/env python3
"""Crée une compilation vidéo à partir des clips téléchargés.

Utilise `ffprobe` pour obtenir la durée et `ffmpeg` pour concaténer.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def probe_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return 0.0
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def write_concat_file(paths, list_path):
    with open(list_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{p}'\n")


def run_ffmpeg_concat(list_path, output_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        output_path,
    ]
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    out = cfg.get("output_dir", "output")
    target_min = float(cfg.get("target_duration_minutes", 12))
    clips_dir = os.path.join(out, "clips")
    if not os.path.isdir(clips_dir):
        print(f"Dossier clips introuvable: {clips_dir}")
        sys.exit(1)

    files = [os.path.join(clips_dir, f) for f in os.listdir(clips_dir) if f.lower().endswith(".mp4")]
    files.sort()

    selected = []
    total = 0.0
    target_seconds = target_min * 60.0
    for f in files:
        dur = probe_duration(f)
        if dur <= 0:
            continue
        if total >= target_seconds:
            break
        selected.append(f)
        total += dur

    if not selected:
        print("Aucun clip sélectionné pour la compilation.")
        return

    os.makedirs(out, exist_ok=True)
    list_path = os.path.join(out, "concat_list.txt")
    write_concat_file(selected, list_path)
    output_path = os.path.join(out, "compilation.mp4")

    print(f"Création compilation {output_path} (durée visée: {target_min} min, sélection: {len(selected)} clips, durée réelle approximative: {total/60:.2f} min)")
    if args.dry_run:
        print("Dry run — commande ffmpeg non exécutée. Liste des fichiers:")
        for s in selected:
            print(s)
        return

    run_ffmpeg_concat(list_path, output_path)
    print("Compilation terminée.")


if __name__ == "__main__":
    main()
