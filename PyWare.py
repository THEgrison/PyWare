import os
try:
    from dotenv import load_dotenv
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], check=False)
    from dotenv import load_dotenv

load_dotenv()
import sys
import subprocess
import platform
import shutil
import socket
import time
import importlib
import asyncio
from datetime import datetime


def ensure_dependencies():
    """Installe automatiquement les dépendances manquantes (hors modules nécessitant des paquets système)."""
    required = [
        ("discord.py", "discord"),
        ("psutil", "psutil"),
        ("aiohttp", "aiohttp"),
        ("aiofiles", "aiofiles"),
        ("opencv-python", "cv2"),
        ("pyperclip", "pyperclip"),
    ]

    for package, module_name in required:
        try:
            importlib.import_module(module_name)
        except Exception:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except Exception as e:
                print(f"❌ Installation échouée pour {package}: {e}")

ensure_dependencies()

import discord
from discord.ext import commands
import psutil
import aiohttp

# Configuration du bot avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True  # IMPORTANT: Activer les Privileged Intents dans le Developer Portal
intents.members = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)
START_TIME = time.time()

# Variable globale pour l'OS
SYSTEM = platform.system()  # "Windows", "Linux", "Darwin"
DISTRO = ""
if SYSTEM == "Linux":
    try:
        with open("/etc/os-release") as f:
            content = f.read()
            if "debian" in content.lower() or "ubuntu" in content.lower():
                DISTRO = "debian"
            elif "arch" in content.lower() or "manjaro" in content.lower():
                DISTRO = "arch"
            elif "fedora" in content.lower():
                DISTRO = "fedora"
            else:
                DISTRO = "linux"
    except:
        DISTRO = "linux"

# Commande: Traduire et exécuter une commande Discord sur le serveur
@bot.command(name='translate_exec')
@commands.is_owner()
async def translate_exec(ctx, *, commande: str):
    """
    Traduit une commande système en français/anglais en commande shell, puis l'exécute sur le serveur.
    Ex: !translate_exec lister les fichiers du dossier courant
    """
    # Dictionnaire simple de correspondance (à enrichir selon besoin)
    mapping = {
        "lister les fichiers": "ls",
        "dossier courant": "pwd",
        "afficher les processus": "ps aux",
        "utilisation cpu": "top -b -n1 | head -20",
        "utilisation ram": "free -h",
        "espace disque": "df -h",
        "redémarrer": "sudo reboot",
        "éteindre": "sudo shutdown now",
        "mise à jour": "sudo apt update && sudo apt upgrade -y",
        "afficher l'ip": "hostname -I",
        "afficher les ports": "netstat -tunap",
        "afficher les utilisateurs": "who",
        "afficher l'historique": "history",
        "afficher le contenu de": "cat",
        "supprimer le fichier": "rm",
        "créer un dossier": "mkdir",
        "changer de dossier": "cd",
        "tuer le processus": "kill -9",
        # Ajoute d'autres correspondances ici
    }
    # Recherche d'une correspondance
    commande_shell = None
    for cle, val in mapping.items():
        if commande.lower().startswith(cle):
            reste = commande[len(cle):].strip()
            commande_shell = f"{val} {reste}".strip()
            break
    if not commande_shell:
        commande_shell = commande  # Si pas de correspondance, exécute tel quel
    try:
        result = subprocess.run(commande_shell, shell=True, capture_output=True, text=True, timeout=20)
        output = result.stdout or result.stderr or "(Aucune sortie)"
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        await ctx.send(f"Commande shell exécutée : `{commande_shell}`\n```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

def get_list_command():
    """Retourne la commande pour lister les processus selon l'OS"""
    if SYSTEM == "Windows":
        return "tasklist"
    elif SYSTEM == "Linux":
        if DISTRO == "arch":
            return "ps aux"  # Arch/Manjaro
        else:
            return "ps aux"  # Debian/Ubuntu
    else:
        return "ps aux"

def get_kill_command(pid):
    """Retourne la commande pour tuer un processus"""
    if SYSTEM == "Windows":
        return f"taskkill /PID {pid} /F"
    else:
        return f"kill -9 {pid}"

def get_system_info():
    """Retourne les infos système adaptées à l'OS"""
    if SYSTEM == "Windows":
        return "systeminfo"
    elif SYSTEM == "Linux":
        return "uname -a"
    else:
        return "system_profiler SPSoftwareDataType"

def get_df_command():
    """Retourne la commande pour voir l'espace disque"""
    if SYSTEM == "Windows":
        return "disk usage"  # Utiliser psutil plutôt
    elif SYSTEM == "Linux":
        return "df -h /"
    else:
        return "df -h /"

def setup_autostart():
    """Configure l'auto-démarrage au premier lancement"""
    try:
        home_dir = os.path.expanduser("~")
        marker_path = os.path.join(home_dir, ".discord_bot_autostart_done")
        if os.path.exists(marker_path):
            return

        script_path = os.path.abspath(__file__)
        python_path = sys.executable

        if SYSTEM == "Windows":
            startup_dir = os.path.join(
                os.environ.get("APPDATA", ""),
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
            )
            os.makedirs(startup_dir, exist_ok=True)
            bat_path = os.path.join(startup_dir, "discord_bot_autostart.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f"\"{python_path}\" \"{script_path}\"\n")

        elif SYSTEM == "Linux":
            systemctl = shutil.which("systemctl")
            if systemctl:
                user_service_dir = os.path.join(home_dir, ".config", "systemd", "user")
                os.makedirs(user_service_dir, exist_ok=True)
                service_path = os.path.join(user_service_dir, "discord-bot.service")
                service_content = f"""[Unit]
Description=Discord Bot

[Service]
ExecStart={python_path} {script_path}
Restart=always
RestartSec=5
WorkingDirectory={os.path.dirname(script_path)}

[Install]
WantedBy=default.target
"""
                with open(service_path, "w", encoding="utf-8") as f:
                    f.write(service_content)

                subprocess.run([systemctl, "--user", "daemon-reload"], check=False)
                subprocess.run([systemctl, "--user", "enable", "--now", "discord-bot.service"], check=False)
            else:
                # Fallback: autostart desktop entry (sessions graphiques)
                autostart_dir = os.path.join(home_dir, ".config", "autostart")
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_path = os.path.join(autostart_dir, "discord-bot.desktop")
                desktop_content = f"""[Desktop Entry]
Type=Application
Name=Discord Bot
Exec={python_path} {script_path}
X-GNOME-Autostart-enabled=true
"""
                with open(desktop_path, "w", encoding="utf-8") as f:
                    f.write(desktop_content)

        elif SYSTEM == "Darwin":
            launch_agents_dir = os.path.join(home_dir, "Library", "LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            plist_path = os.path.join(launch_agents_dir, "com.discord.bot.plist")
            plist_content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>Label</key>
  <string>com.discord.bot</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>{script_path}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>{os.path.dirname(script_path)}</string>
</dict>
</plist>
"""
            with open(plist_path, "w", encoding="utf-8") as f:
                f.write(plist_content)

        with open(marker_path, "w", encoding="utf-8") as f:
            f.write("autostart configured")

        print("✅ Auto‑démarrage configuré.")
    except Exception as e:
        print(f"❌ Auto‑démarrage non configuré: {e}")

# Répertoires de travail par channel
WORKDIRS = {}

def get_cwd(ctx):
    """Retourne le répertoire courant pour ce channel"""
    return WORKDIRS.get(ctx.channel.id, os.getcwd())

def set_cwd(ctx, path):
    """Définit le répertoire courant pour ce channel"""
    WORKDIRS[ctx.channel.id] = path

def resolve_path(ctx, path: str = None):
    """Résout un chemin relatif au répertoire courant"""
    if not path:
        return get_cwd(ctx)
    if os.path.isabs(path):
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(get_cwd(ctx), path))

# Fonction pour obtenir l'IP publique via Apify
async def get_public_ip():
    """Récupère l'IP publique via l'API Apify"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.apify.com/v2/public-ip', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('ip', 'unknown')
    except Exception as e:
        print(f"Erreur Apify: {e}")
    
    # Fallback sur une autre API si Apify échoue
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org?format=json', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('ip', 'unknown')
    except Exception as e:
        print(f"Erreur ipify: {e}")
    
    return 'unknown'

# Événement: Le bot est prêt
@bot.event
async def on_ready():
    print(f'{bot.user} connecté à Discord!')
    print(f'ID du bot: {bot.user.id}')
    
    # Obtenir l'IP publique via Apify
    ip_public = await get_public_ip()
    print(f"IP Publique: {ip_public}")
    
    # Créer un channel privé avec l'IP en nom (pour chaque serveur)
    for guild in bot.guilds:
        channel_name = f"server-{ip_public}"
        
        # Vérifier si le channel existe déjà
        channel_exists = discord.utils.find(lambda c: c.name == channel_name, guild.channels)
        
        if not channel_exists:
            try:
                # Créer le channel privé (catégorie texte)
                channel = await guild.create_text_channel(
                    channel_name,
                    topic=f"🖥️ Infos Serveur IP Publique: {ip_public}"
                )
                
                # Rendre le channel privé (visible uniquement au bot)
                await channel.edit(
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                )
                
                # Envoyer un message d'info
                os_name = f"{SYSTEM}"
                if DISTRO:
                    os_name += f" ({DISTRO.upper()})"
                
                embed = discord.Embed(
                    title="🤖 Bot Discord Système Connecté",
                    description=(
                        f"**IP Publique :** `{ip_public}`\n"
                        f"**Système :** `{os_name} {platform.release()}`\n"
                        f"**Serveur Discord :** `{guild.name}`\n"
                        f"**Salon privé créé pour la gestion distante.**"
                    ),
                    color=discord.Color.from_rgb(52, 152, 219)
                )
                embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
                embed.add_field(name="Statut du Bot", value="🟢 **En ligne & prêt à recevoir les commandes**", inline=False)
                embed.add_field(name="Créé le", value=datetime.now().strftime('%d/%m/%Y %H:%M:%S'), inline=True)
                embed.set_footer(text="Bot Discord Système • Création du salon automatique", icon_url="https://cdn-icons-png.flaticon.com/512/906/906334.png")
                await channel.send(embed=embed)

                # Embed commandes amélioré
                commands_embed = discord.Embed(
                    title="📖 Commandes Disponibles",
                    description="Voici les principales commandes administrateur :",
                    color=discord.Color.from_rgb(46, 204, 113)
                )
                commands_embed.add_field(
                    name="🖥️ Système",
                    value=(
                        "`!processes [nom]` : Processus en cours\n"
                        "`!kill [PID]` : Arrêter un processus\n"
                        "`!sysinfo` : Infos système\n"
                        "`!monitor` : CPU/RAM\n"
                        "`!netinfo` : Infos réseau\n"
                        "`!update` : Mise à jour système\n"
                        "`!shutdown` : Éteindre\n"
                        "`!reboot` : Redémarrer\n"
                    ),
                    inline=False
                )
                commands_embed.add_field(
                    name="⚙️ Fichiers & Shell",
                    value=(
                        "`!exec [cmd]` : Exécuter une commande\n"
                        "`!run [programme]` : Lancer un programme\n"
                        "`!pwd` : Dossier courant\n"
                        "`!cd [chemin]` : Changer de dossier\n"
                        "`!ls [chemin]` : Lister les fichiers\n"
                        "`!cat [fichier]` : Lire un fichier\n"
                        "`!download [url]` : Télécharger\n"
                        "`!search [motif]` : Recherche\n"
                    ),
                    inline=False
                )
                commands_embed.add_field(
                    name="🛠️ Divers",
                    value=(
                        "`!screenshot` : Capture écran\n"
                        "`!camera` : Photo webcam\n"
                        "`!clipboard` : Presse-papier\n"
                        "`!logs [service]` : Logs système\n"
                        "`!history` : Historique shell\n"
                        "`!alert [cpu/ram] [seuil]` : Alerte\n"
                        "`!firewall [args]` : Pare-feu\n"
                        "`!service [action] [nom]` : Service système\n"
                    ),
                    inline=False
                )
                commands_embed.add_field(
                    name="ℹ️ Discord",
                    value=(
                        "`!ping` : Latence\n"
                        "`!serverinfo` : Infos serveur\n"
                        "`!userinfo [@user]` : Infos utilisateur\n"
                        "`!kick`/`!ban`/`!clear`/`!announce`\n"
                    ),
                    inline=False
                )
                commands_embed.set_footer(text="Utilisez le préfixe '!' avant chaque commande. Tapez !help pour plus de détails.", icon_url="https://cdn-icons-png.flaticon.com/512/906/906334.png")
                await channel.send(embed=commands_embed)

                print(f"✅ Channel '{channel_name}' créé sur {guild.name}")
            except Exception as e:
                print(f"❌ Erreur lors de la création du channel: {e}")
        else:
            print(f"✅ Channel '{channel_name}' existe déjà sur {guild.name}")

# ==================== COMMANDES SYSTÈME ====================

# Commande: Afficher l'OS détecté
@bot.command(name='os')
@commands.is_owner()
async def show_os(ctx):
    """Affiche l'OS détecté"""
    embed = discord.Embed(
        title="🖥️ Système d'Exploitation",
        color=discord.Color.blue()
    )
    embed.add_field(name="OS", value=SYSTEM, inline=True)
    if DISTRO:
        embed.add_field(name="Distribution", value=DISTRO.upper(), inline=True)
    embed.add_field(name="Version", value=platform.release(), inline=True)
    embed.add_field(name="Architecture", value=platform.machine(), inline=True)
    await ctx.send(embed=embed)

# Commande: Voir les processus en cours
@bot.command(name='processes')
@commands.is_owner()
async def processes(ctx, search: str = None):
    """Affiche les processus en cours (optionnel: filtrer par nom)"""
    try:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if search is None or search.lower() in proc.info['name'].lower():
                    procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if not procs:
            await ctx.send("Aucun processus trouvé.")
            return
        
        # Limiter à 50 processus pour éviter les messages trop longs
        procs = sorted(procs, key=lambda x: x['memory_percent'], reverse=True)[:50]
        
        message = "```\n"
        message += "PID  | NOM                          | RAM (%)\n"
        message += "-" * 50 + "\n"
        for p in procs:
            message += f"{p['pid']:<4} | {p['name']:<28} | {p['memory_percent']:>6.2f}%\n"
        message += "```"
        
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Arrêter un processus
@bot.command(name='kill')
@commands.is_owner()
async def kill_process(ctx, pid: int):
    """Arrête un processus par son PID"""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.terminate()
        await ctx.send(f"✅ Processus {proc_name} (PID: {pid}) arrêté.")
    except psutil.NoSuchProcess:
        await ctx.send(f"❌ Processus avec PID {pid} non trouvé.")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Infos système
@bot.command(name='sysinfo')
@commands.is_owner()
async def sysinfo(ctx):
    """Affiche les infos du système"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        embed = discord.Embed(
            title="🖥️ Infos Système",
            color=discord.Color.blue()
        )
        embed.add_field(name="OS", value=f"{platform.system()} {platform.release()}", inline=False)
        embed.add_field(name="Processeur", value=platform.processor(), inline=False)
        embed.add_field(name="CPU", value=f"{cpu_percent}% utilisé", inline=True)
        embed.add_field(name="RAM", value=f"{memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB ({memory.percent}%)", inline=False)
        embed.add_field(name="Disque", value=f"{disk.used / (1024**3):.2f}GB / {disk.total / (1024**3):.2f}GB ({disk.percent}%)", inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Exécuter une commande système
@bot.command(name='exec')
@commands.is_owner()
async def execute_command(ctx, *, command: str):
    """Exécute une commande système"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout or result.stderr
        
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        
        await ctx.send(f"```\n{output}\n```")
    except subprocess.TimeoutExpired:
        await ctx.send("❌ Commande expirée (timeout).")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Démarrer un programme
@bot.command(name='run')
@commands.is_owner()
async def run_program(ctx, *, program: str):
    """Démarre un programme"""
    try:
        if platform.system() == "Windows":
            subprocess.Popen(program)
        else:
            subprocess.Popen(program, shell=True)
        await ctx.send(f"✅ Programme lancé: {program}")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Afficher les fichiers d'un répertoire
@bot.command(name='ls')
@commands.is_owner()
async def list_files(ctx, path: str = None):
    """Liste les fichiers d'un répertoire"""
    try:
        target_path = resolve_path(ctx, path)

        if not os.path.exists(target_path):
            await ctx.send(f"❌ Chemin non trouvé: {target_path}")
            return

        if not os.path.isdir(target_path):
            await ctx.send(f"❌ Ce chemin n'est pas un dossier: {target_path}")
            return
        
        files = os.listdir(target_path)
        if not files:
            await ctx.send(f"📁 Répertoire vide: {target_path}")
            return
        
        message = f"```\n📁 {target_path}\n" + "-" * 40 + "\n"
        for f in sorted(files)[:50]:
            if os.path.isdir(os.path.join(target_path, f)):
                message += f"📂 {f}/\n"
            else:
                message += f"📄 {f}\n"
        message += "```"
        
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Afficher le dossier courant
@bot.command(name='pwd')
@commands.is_owner()
async def pwd(ctx):
    """Affiche le dossier courant"""
    await ctx.send(f"📁 Dossier courant: `{get_cwd(ctx)}`")

# Commande: Changer de dossier
@bot.command(name='cd')
@commands.is_owner()
async def change_dir(ctx, *, path: str = None):
    """Change le dossier courant"""
    try:
        if not path:
            await ctx.send("❌ Merci de fournir un chemin.")
            return

        target_path = resolve_path(ctx, path)
        if not os.path.exists(target_path):
            await ctx.send(f"❌ Chemin non trouvé: {target_path}")
            return
        if not os.path.isdir(target_path):
            await ctx.send(f"❌ Ce chemin n'est pas un dossier: {target_path}")
            return

        set_cwd(ctx, target_path)
        await ctx.send(f"✅ Dossier courant: `{target_path}`")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Afficher le contenu d'un fichier
@bot.command(name='cat')
@commands.is_owner()
async def cat_file(ctx, *, path: str = None):
    """Affiche le contenu d'un fichier"""
    try:
        if not path:
            await ctx.send("❌ Merci de fournir un fichier.")
            return

        target_path = resolve_path(ctx, path)
        if not os.path.exists(target_path):
            await ctx.send(f"❌ Fichier non trouvé: {target_path}")
            return
        if os.path.isdir(target_path):
            await ctx.send(f"❌ Ce chemin est un dossier: {target_path}")
            return

        max_bytes = 50 * 1024
        file_size = os.path.getsize(target_path)
        if file_size > max_bytes:
            await ctx.send(f"❌ Fichier trop volumineux ({file_size} octets). Limite: {max_bytes}.")
            return

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            await ctx.send("📄 Fichier vide.")
            return

        if len(content) > 1900:
            content = content[:1900] + "\n... (contenu tronqué)"

        await ctx.send(f"```\n{content}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Mettre à jour le système
@bot.command(name='update')
@commands.is_owner()
async def update_system(ctx):
    """Met à jour le système (apt/pacman/yum)"""
    try:
        if SYSTEM == "Linux":
            if DISTRO == "debian":
                cmd = "sudo apt update && sudo apt upgrade -y"
            elif DISTRO == "arch":
                cmd = "sudo pacman -Syu --noconfirm"
            elif DISTRO == "fedora":
                cmd = "sudo dnf upgrade --refresh -y"
            else:
                cmd = "sudo apt update && sudo apt upgrade -y"
        elif SYSTEM == "Darwin":
            cmd = "softwareupdate -ia"
        else:
            await ctx.send("❌ Mise à jour automatique non supportée sur cet OS.")
            return
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        output = proc.stdout or proc.stderr
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Éteindre la machine
@bot.command(name='shutdown')
@commands.is_owner()
async def shutdown(ctx):
    """Éteint la machine"""
    await ctx.send("⚠️ Arrêt de la machine dans 5 secondes...")
    await asyncio.sleep(5)
    if SYSTEM == "Windows":
        os.system("shutdown /s /t 0")
    else:
        os.system("sudo shutdown now")

# Commande: Redémarrer la machine
@bot.command(name='reboot')
@commands.is_owner()
async def reboot(ctx):
    """Redémarre la machine"""
    await ctx.send("🔄 Redémarrage dans 5 secondes...")
    await asyncio.sleep(5)
    if SYSTEM == "Windows":
        os.system("shutdown /r /t 0")
    else:
        os.system("sudo reboot")

# Commande: Gérer un service système
@bot.command(name='service')
@commands.is_owner()
async def service_cmd(ctx, action: str, name: str):
    """Démarre/arrête/redémarre un service système"""
    try:
        if SYSTEM == "Linux":
            cmd = f"sudo systemctl {action} {name}"
        elif SYSTEM == "Windows":
            cmd = f"sc {action} {name}"
        else:
            await ctx.send("❌ Non supporté sur cet OS.")
            return
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = proc.stdout or proc.stderr
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Surveiller un fichier
import threading
@bot.command(name='watch')
@commands.is_owner()
async def watch_file(ctx, *, path: str):
    """Surveille un fichier et alerte en cas de modification"""
    import time
    target_path = resolve_path(ctx, path)
    if not os.path.exists(target_path):
        await ctx.send(f"❌ Fichier non trouvé: {target_path}")
        return
    await ctx.send(f"👀 Surveillance de {target_path} activée.")
    def watcher():
        last_mtime = os.path.getmtime(target_path)
        while True:
            time.sleep(2)
            try:
                mtime = os.path.getmtime(target_path)
                if mtime != last_mtime:
                    last_mtime = mtime
                    asyncio.run_coroutine_threadsafe(ctx.send(f"⚠️ Fichier modifié: {target_path}"), bot.loop)
            except Exception:
                break
    threading.Thread(target=watcher, daemon=True).start()

# Commande: Alerte sur seuil CPU/RAM
@bot.command(name='alert')
@commands.is_owner()
async def alert(ctx, resource: str, seuil: int):
    """Alerte si CPU ou RAM dépasse un seuil (%)"""
    await ctx.send(f"🔔 Surveillance {resource.upper()} > {seuil}% activée.")
    async def monitor():
        while True:
            await asyncio.sleep(5)
            if resource.lower() == "cpu":
                val = psutil.cpu_percent()
            elif resource.lower() == "ram":
                val = psutil.virtual_memory().percent
            else:
                await ctx.send("❌ Ressource inconnue (cpu/ram)")
                return
            if val > seuil:
                await ctx.send(f"⚠️ {resource.upper()} à {val}% !")
                break
    bot.loop.create_task(monitor())

# Commande: Télécharger un fichier
@bot.command(name='download')
@commands.is_owner()
async def download(ctx, url: str, dest: str = None):
    """Télécharge un fichier depuis Internet"""
    import aiohttp
    import aiofiles
    dest = dest or url.split("/")[-1]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    fpath = resolve_path(ctx, dest)
                    async with aiofiles.open(fpath, "wb") as f:
                        await f.write(await resp.read())
                    await ctx.send(f"✅ Fichier téléchargé: {fpath}")
                else:
                    await ctx.send(f"❌ Erreur HTTP: {resp.status}")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Recherche de fichier/texte
@bot.command(name='search')
@commands.is_owner()
async def search(ctx, *, pattern: str):
    """Recherche un fichier ou texte dans les fichiers du dossier courant"""
    import fnmatch
    results = []
    cwd = get_cwd(ctx)
    for root, dirs, files in os.walk(cwd):
        for f in files:
            if pattern in f:
                results.append(os.path.join(root, f))
            else:
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                        if pattern in file.read():
                            results.append(os.path.join(root, f))
                except Exception:
                    continue
        if len(results) > 20:
            break
    if not results:
        await ctx.send("Aucun résultat.")
    else:
        msg = "\n".join(results[:20])
        await ctx.send(f"```\n{msg}\n```")

# Commande: Liste des utilisateurs connectés
@bot.command(name='who')
@commands.is_owner()
async def who(ctx):
    """Liste les utilisateurs connectés (Linux/Unix)"""
    try:
        if SYSTEM == "Windows":
            cmd = "query user"
        else:
            cmd = "who"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = proc.stdout or proc.stderr
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Connexions réseau actives
@bot.command(name='netstat')
@commands.is_owner()
async def netstat(ctx):
    """Affiche les connexions réseau actives"""
    try:
        if SYSTEM == "Windows":
            cmd = "netstat -ano"
        else:
            cmd = "netstat -tunap"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = proc.stdout or proc.stderr
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Afficher/modifier le firewall (Linux ufw)
@bot.command(name='firewall')
@commands.is_owner()
async def firewall(ctx, *, args: str = "status"):
    """Affiche ou modifie les règles du pare-feu (ufw)"""
    try:
        if SYSTEM != "Linux":
            await ctx.send("❌ Firewall non supporté sur cet OS.")
            return
        cmd = f"sudo ufw {args}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        output = proc.stdout or proc.stderr
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")


# Commande: Screenshot du bureau (multi-OS, fallback si pyautogui/tkinter absent)
@bot.command(name='screenshot')
@commands.is_owner()
async def screenshot(ctx):
    """Prend une capture d'écran du bureau et l'envoie (s'adapte à l'OS, gère l'absence de tkinter/pyautogui)"""
    import tempfile
    import platform
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        # Essai pyautogui (si tkinter dispo)
        try:
            import pyautogui
            pyautogui.screenshot(tmp.name)
            await ctx.send(file=discord.File(tmp.name))
            tmp.close()
            os.unlink(tmp.name)
            return
        except Exception as e:
            print(f"pyautogui/tkinter indisponible: {e}")

        # Fallback Linux: import scrot
        if SYSTEM == "Linux":
            if shutil.which("scrot"):
                os.system(f"scrot {tmp.name}")
                await ctx.send(file=discord.File(tmp.name))
                tmp.close()
                os.unlink(tmp.name)
                return
            elif shutil.which("import"):
                os.system(f"import -window root {tmp.name}")
                await ctx.send(file=discord.File(tmp.name))
                tmp.close()
                os.unlink(tmp.name)
                return
            else:
                await ctx.send("❌ Aucun outil de capture trouvé (pyautogui/tkinter, scrot, import). Installez-en un pour activer la capture d'écran.")
                return
        # Fallback Windows: PowerShell
        elif SYSTEM == "Windows":
            ps_script = (
                "$img = [Windows.Graphics.Capture.GraphicsCaptureSession]::CreateFromVisual([Windows.UI.Xaml.Window]::Current.Content); "
                "$file = '{}'; $img.SaveAsFile($file)".format(tmp.name)
            )
            # PowerShell screenshot (nécessite Windows 10+)
            try:
                subprocess.run([
                    "powershell", "-Command",
                    "Add-Type -AssemblyName System.Windows.Forms; "
                    "$bmp = New-Object Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
                    "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
                    "$graphics.CopyFromScreen(0, 0, 0, 0, $bmp.Size); "
                    "$bmp.Save('{}');".format(tmp.name)
                ], check=True)
                await ctx.send(file=discord.File(tmp.name))
                tmp.close()
                os.unlink(tmp.name)
                return
            except Exception as e:
                await ctx.send("❌ Impossible de capturer l'écran (PowerShell/pyautogui absent)")
                return
        # Fallback macOS: screencapture
        elif SYSTEM == "Darwin":
            if shutil.which("screencapture"):
                os.system(f"screencapture {tmp.name}")
                await ctx.send(file=discord.File(tmp.name))
                tmp.close()
                os.unlink(tmp.name)
                return
            else:
                await ctx.send("❌ Aucun outil de capture trouvé (pyautogui/tkinter, screencapture)")
                return
        else:
            await ctx.send("❌ Non supporté sur cet OS.")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")
    finally:
        try:
            tmp.close()
            os.unlink(tmp.name)
        except Exception:
            pass

# Commande: Photo webcam (si dispo)
@bot.command(name='camera')
@commands.is_owner()
async def camera(ctx):
    """Prend une photo avec la webcam et l'envoie"""
    import cv2
    import tempfile
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(tmp.name, frame)
            await ctx.send(file=discord.File(tmp.name))
        else:
            await ctx.send("❌ Impossible de prendre la photo.")
        tmp.close()
        os.unlink(tmp.name)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Presse-papier
@bot.command(name='clipboard')
@commands.is_owner()
async def clipboard(ctx, *, text: str = None):
    """Affiche ou modifie le presse-papier"""
    try:
        import pyperclip
        if text:
            pyperclip.copy(text)
            await ctx.send("✅ Presse-papier modifié.")
        else:
            val = pyperclip.paste()
            await ctx.send(f"📋 {val}")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Logs système/service
@bot.command(name='logs')
@commands.is_owner()
async def logs(ctx, service: str = None):
    """Affiche les logs système ou d'un service"""
    try:
        if SYSTEM == "Linux":
            if service:
                cmd = f"journalctl -u {service} --no-pager -n 50"
            else:
                cmd = "dmesg | tail -n 50"
        elif SYSTEM == "Windows":
            cmd = "wevtutil qe System /c:20 /f:text /q:*[System[(Level=2)]]"
        else:
            await ctx.send("❌ Non supporté sur cet OS.")
            return
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        output = proc.stdout or proc.stderr
        if len(output) > 1900:
            output = output[:1900] + "\n... (résultat tronqué)"
        await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Historique des commandes (Linux)
@bot.command(name='history')
@commands.is_owner()
async def history(ctx):
    """Affiche l'historique des commandes shell (Linux)"""
    try:
        if SYSTEM == "Linux":
            home = os.path.expanduser("~")
            hist_path = os.path.join(home, ".bash_history")
            if os.path.exists(hist_path):
                with open(hist_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-20:]
                await ctx.send(f"```\n{''.join(lines)}\n```")
            else:
                await ctx.send("Aucun historique trouvé.")
        else:
            await ctx.send("❌ Non supporté sur cet OS.")
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Uptime du bot
@bot.command(name='uptime')
@commands.is_owner()
async def uptime(ctx):
    """Affiche le temps de fonctionnement du bot"""
    elapsed = int(time.time() - START_TIME)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    await ctx.send(
        f"⏱️ Uptime: {days}j {hours}h {minutes}m {seconds}s"
    )

# Commande: Redémarrer le bot
@bot.command(name='restart')
@commands.is_owner()
async def restart(ctx):
    """Redémarre le bot"""
    await ctx.send("🔄 Redémarrage en cours...")
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Infos réseau
@bot.command(name='netinfo')
@commands.is_owner()
async def netinfo(ctx):
    """Affiche les infos réseau"""
    try:
        net_io = psutil.net_io_counters()
        
        embed = discord.Embed(
            title="🌐 Infos Réseau",
            color=discord.Color.green()
        )
        embed.add_field(name="Octets envoyés", value=f"{net_io.bytes_sent / (1024**3):.2f}GB", inline=True)
        embed.add_field(name="Octets reçus", value=f"{net_io.bytes_recv / (1024**3):.2f}GB", inline=True)
        embed.add_field(name="Paquets envoyés", value=f"{net_io.packets_sent:,}", inline=True)
        embed.add_field(name="Paquets reçus", value=f"{net_io.packets_recv:,}", inline=True)
        embed.add_field(name="Erreurs entrantes", value=str(net_io.errin), inline=True)
        embed.add_field(name="Erreurs sortantes", value=str(net_io.errout), inline=True)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# Commande: Monitorer la CPU/RAM en temps réel
@bot.command(name='monitor')
@commands.is_owner()
async def monitor(ctx):
    """Affiche l'utilisation CPU/RAM"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Créer des barres de progression visuelles
        cpu_bar = "█" * int(cpu_percent / 5) + "░" * (20 - int(cpu_percent / 5))
        mem_bar = "█" * int(memory.percent / 5) + "░" * (20 - int(memory.percent / 5))
        
        embed = discord.Embed(
            title="⚡ Monitoring Système",
            color=discord.Color.orange()
        )
        embed.add_field(name="CPU", value=f"{cpu_bar} {cpu_percent}%", inline=False)
        embed.add_field(name="RAM", value=f"{mem_bar} {memory.percent}%", inline=False)
        embed.add_field(name="Mémoire utilisée", value=f"{memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB", inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erreur: {e}")

# ==================== COMMANDES DISCORD ====================

# Commande 1: Ping (test de latence)
@bot.command(name='ping')
async def ping(ctx):
    """Répond avec le ping du bot"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! 🏓 Latence: {latency}ms')

# Commande 2: Kick un utilisateur
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Pas de raison fournie"):
    """Kick un utilisateur du serveur"""
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Vous ne pouvez pas kick cet utilisateur (rôle trop élevé).")
        return
    
    await member.kick(reason=reason)
    await ctx.send(f'✅ {member} a été kick du serveur. Raison: {reason}')

# Commande 3: Ban un utilisateur
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Pas de raison fournie"):
    """Ban un utilisateur du serveur"""
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Vous ne pouvez pas ban cet utilisateur (rôle trop élevé).")
        return
    
    await member.ban(reason=reason)
    await ctx.send(f'✅ {member} a été ban du serveur. Raison: {reason}')

# Commande 4: Clear les messages
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """Supprime un nombre de messages du canal"""
    if amount > 100:
        await ctx.send("❌ Vous ne pouvez supprimer que 100 messages max.")
        return
    
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f'✅ {len(deleted)} messages supprimés!', delete_after=5)

# Commande 5: Envoyer un message d'annonce
@bot.command(name='announce')
@commands.has_permissions(administrator=True)
async def announce(ctx, *, message):
    """Envoie une annonce sur le serveur"""
    embed = discord.Embed(
        title="📢 Annonce",
        description=message,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Annoncé par {ctx.author}")
    await ctx.send(embed=embed)

# Commande 6: Afficher les infos du serveur
@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """Affiche les infos du serveur"""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📋 Infos du serveur: {guild.name}",
        color=discord.Color.green()
    )
    embed.add_field(name="ID", value=guild.id)
    embed.add_field(name="Propriétaire", value=guild.owner)
    embed.add_field(name="Membres", value=guild.member_count)
    embed.add_field(name="Canaux", value=len(guild.channels))
    embed.add_field(name="Rôles", value=len(guild.roles))
    await ctx.send(embed=embed)

# Commande 7: Afficher les infos d'un utilisateur
@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    """Affiche les infos d'un utilisateur"""
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"👤 Infos de {member}",
        color=member.color
    )
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Créé le", value=member.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="A rejoint le", value=member.joined_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Rôles", value=", ".join([r.mention for r in member.roles[1:]]) or "Aucun")
    await ctx.send(embed=embed)

# Gestion des erreurs de commande
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Vous n'avez pas les permissions pour utiliser cette commande.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Arguments manquants. Utilisez `!help` pour voir l'aide.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorer les commandes non trouvées
    else:
        await ctx.send(f"❌ Une erreur s'est produite: {error}")

# Lancer le bot
if __name__ == "__main__":
    setup_autostart()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Token manquant. Définissez la variable d'environnement DISCORD_TOKEN.")
        sys.exit(1)
    bot.run(TOKEN)
