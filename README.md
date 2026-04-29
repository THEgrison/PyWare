# Discord System Bot

Bot Discord d administration systeme avec commandes privees (owner) et moderation de base.

## Ce que fait le programme

- Demarre un bot Discord avec le prefixe `!`.
- Detecte l OS (Windows/Linux/macOS) et la distribution Linux.
- Configure un auto demarrage au premier lancement.
- Recupere l IP publique et cree un salon prive par serveur pour la gestion distante.
- Fournit des commandes d administration systeme reservees au proprietaire.
- Fournit des commandes Discord classiques (infos, ping, moderation selon permissions).

## Fonctionnalites par categorie

### Systeme (owner only)
- Execution shell: `!exec`, `!translate_exec`
- Processus: `!processes`, `!kill`
- Infos/monitoring: `!sysinfo`, `!monitor`, `!netinfo`, `!uptime`
- Fichiers: `!ls`, `!pwd`, `!cd`, `!cat`, `!search`, `!download`
- Actions systeme: `!update`, `!shutdown`, `!reboot`, `!service`
- Reseau/pare-feu: `!netstat`, `!who`, `!firewall`
- Surveillance: `!watch`, `!alert`
- Capture/IO: `!screenshot`, `!camera`, `!clipboard`
- Logs/historique: `!logs`, `!history`
- Redemarrage bot: `!restart`

### Discord (permissions Discord)
- `!ping`, `!serverinfo`, `!userinfo`
- Moderation: `!kick`, `!ban`, `!clear`, `!announce`

## Compatibilite

- OS supportes: Windows, Linux, macOS (Darwin)
- Python: 3.9+ recommande
- Discord API: `discord.py`

## Dependances Python

Installees automatiquement au premier lancement (via pip si manquantes):

- `discord.py`
- `psutil`
- `aiohttp`
- `aiofiles`
- `opencv-python` (camera)
- `pyperclip` (clipboard)
- `python-dotenv`

## Outils systeme optionnels

Certaines fonctions demandent des outils externes:

- Linux: `scrot` ou `imagemagick` (commande `import`) pour `!screenshot`
- Linux: `ufw` pour `!firewall`
- Linux: `systemd --user` pour l auto demarrage (sinon autostart desktop)

## Configuration requise

1. Creer une application sur le Developer Portal Discord.
2. Activer les intents necessaires (message content).
3. Creer un bot et recuperer le token.
4. Definir la variable d environnement `DISCORD_TOKEN`.

Exemple (Linux/macOS):

```bash
export DISCORD_TOKEN="votre_token"
```

Exemple (Windows PowerShell):

```powershell
setx DISCORD_TOKEN "votre_token"
```

## Lancement

Depuis le dossier du script:

```bash
python discord_bot.py
```

## Auto demarrage

Le script configure automatiquement un auto demarrage au premier lancement:

- Windows: dossier Startup
- Linux: service user systemd ou fichier autostart
- macOS: LaunchAgents

Un fichier marqueur est cree dans `~/.discord_bot_autostart_done`.

## Securite et bonnes pratiques

- Les commandes sensibles sont limitees au proprietaire du bot (owner).
- Utilisez un serveur prive et limitez les permissions du bot.
- Evitez d exposer le token; utilisez un fichier `.env` ou les variables d environnement.

## Responsabilite

Ce projet est fourni a titre educatif. Vous etes seul responsable de l usage que vous en faites. Le developpeur ne peut en aucun cas etre tenu responsable de toute utilisation abusive, illegale ou dommageable.

## Fichier .env (optionnel)

Creez un fichier `.env` dans le meme dossier:

```
DISCORD_TOKEN=VotreTokenIci
```

## Notes

- `!translate_exec` mappe des phrases vers des commandes shell. A manipuler avec prudence.
- Le bot peut executer des commandes systeme sur la machine hote.

## Licence

Ajoutez une licence si vous souhaitez redistribuer ce projet.
