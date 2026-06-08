# Twitch-clip-automatisation

Petit outil pour récupérer automatiquement les clips Twitch populaires (ex: `Just Chatting`) et créer un mini-montage pour YouTube.

Usage rapide

1. Dupliquer `config.example.json` en `config.json` et remplir `twitch_client_id` et `twitch_oauth_token` (Bearer token).
2. Installer les dépendances:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Télécharger les clips (dry-run pour tester):

```bash
python scripts/fetch_clips.py --config config.json --dry-run
```

4. Lancer la compilation (dry-run possible):

```bash
python scripts/make_compilation.py --config config.json --dry-run
```

Notes
- Le script cible `category` (par défaut `Just Chatting`) et récupère les clips de la période `days` dans la config.
- Aucune musique ajoutée (comme demandé).
- L'upload automatique YouTube n'est pas activé par défaut; peut être ajouté plus tard si nécessaire.

Automatisation clip in Twitch for YouTube
