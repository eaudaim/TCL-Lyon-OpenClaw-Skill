# tcl-lyon — OpenClaw Skill

Un skill [OpenClaw](https://openclaw.ai) pour interroger les horaires du réseau TCL (Transports en Commun Lyonnais) en langage naturel, depuis une base de données GTFS locale.

> **Conçu pour les modèles locaux (Ollama)** — fonctionne sans API cloud, sans connexion internet, et produit des réponses fiables même sur des modèles légers (testé sur un 20B).

---

## Fonctionnalités

- Prochains passages à un arrêt (toutes lignes ou filtré par ligne)
- Premier passage de la journée
- Dernier passage de la soirée
- Recherche d'arrêts par nom partiel
- Informations sur une ligne (type, nom complet)
- Gestion des horaires après minuit (GTFS > 24h)
- Gestion des exceptions calendaires (jours fériés, services spéciaux)

## Couverture

- **653 lignes** : bus, métro, tram, funiculaire, trolleybus
- **8 863 arrêts**
- **Horaires théoriques** sur 60 jours glissants (pas de temps réel)
- Source : données GTFS publiques fournies par Sytral / transport.data.gouv.fr

---

## Installation

### 1. Créer le dossier du skill

```bash
mkdir -p ~/.openclaw/skills/tcl-lyon
```

### 2. Copier les fichiers du skill

```bash
cp SKILL.md tcl_tool.py ~/.openclaw/skills/tcl-lyon/
```

### 3. Télécharger les données GTFS

Rendez-vous sur [transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/horaires-theoriques-du-reseau-transports-en-commun-lyonnais).

> ⚠️ **Important :** Ignorer les ressources officielles en haut de page (données potentiellement obsolètes). Faire défiler jusqu'à la section **"Community resources"** et télécharger le fichier **"GTFS modifié by Google Maps"** — c'est la version mise à jour quotidiennement.

Extraire le ZIP dans un dossier de votre choix.

### 4. Importer les données GTFS dans SQLite

Depuis le dossier contenant les fichiers `.txt` GTFS :

```bash
python3 import_gtfs.py /chemin/vers/dossier/gtfs
# ou si vous êtes déjà dans le dossier GTFS :
python3 /chemin/vers/tcl-lyon/import_gtfs.py .
```

Le script :
- Importe toutes les tables utiles (ignore `shapes.txt` qui ne sert pas aux horaires)
- Insère les données par batch de 10 000 lignes
- Crée les index nécessaires pour des requêtes instantanées

L'import prend environ 30 secondes. La base résultante pèse ~150 Mo.

### 5. Vérifier l'installation

```bash
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py departures "Bellecour"
```

---

## Utilisation

### Via OpenClaw (langage naturel)

```
"Quels sont les prochains passages du bus 31 à Saint-Rambert ?"
"À quelle heure passe le dernier métro D à Vieux Lyon ce soir ?"
"Quel est le premier tram T1 de la journée à Laurent Bonnevay ?"
"C'est quoi la ligne C14 ?"
```

### Via slash command (pour forcer l'usage du skill)

Si votre agent préfère web_search pour les questions d'horaires, utilisez la slash command pour forcer le skill :

```
/tcl_lyon Dernier métro D à Bellecour ce soir ?
```

### En ligne de commande directe

```bash
# Prochains départs
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py departures "Bellecour"
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py departures "Part-Dieu" 10
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py departures "St-Rambert" 5 --line 31

# Premier passage de la journée
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py first "Valmy" --line D
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py first "Valmy" "Gare de Vénissieux" --line D

# Dernier passage de la soirée
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py last "Bellecour" --line D
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py last "Gare de Vaise" "Cité Edouard Herriot" --line 31

# Infos sur une ligne
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py line "D"
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py line "T2"

# Recherche d'arrêts
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py stops "Vaise"
python3 ~/.openclaw/skills/tcl-lyon/tcl_tool.py stops "Part-Dieu"
```

### Options communes

| Option | Description |
|--------|-------------|
| `--line NOM` | Filtre par numéro/nom de ligne (ex: `31`, `D`, `T2`) |
| `limit` (departures uniquement) | Nombre de résultats (défaut: 5) |

---

## Mise à jour automatique

Les données GTFS évoluent quotidiennement. Pour automatiser la mise à jour, ajoutez un cron job OpenClaw ou un script shell à planifier :

```bash
#!/bin/bash
# update_tcl_gtfs.sh
SKILL_DIR="$HOME/.openclaw/skills/tcl-lyon"
TMP_DIR=$(mktemp -d)

# Télécharger et extraire (adapter l'URL selon la source)
wget -q -O "$TMP_DIR/gtfs.zip" "<URL_GTFS>"
unzip -q "$TMP_DIR/gtfs.zip" -d "$TMP_DIR/gtfs"

# Reimporter
python3 "$SKILL_DIR/import_gtfs.py" "$TMP_DIR/gtfs"

# Nettoyage
rm -rf "$TMP_DIR"
```

---

## Limites connues

- **Horaires théoriques uniquement** — pas de données temps réel (retards, suppressions). L'API SIRI Lite de data.grandlyon.com est actuellement hors service suite à la fusion des réseaux TCL/Cars du Rhône/Libellule (2025).
- **Réseau TCL uniquement** — ne couvre pas les lignes Cars du Rhône ou Libellule même si elles partagent des arrêts avec TCL.
- **Comportement des modèles locaux** — les modèles < 14B peuvent avoir tendance à préférer web_search. Utiliser la slash command `/tcl_lyon` en cas de biais.

---

## Structure des fichiers

```
tcl-lyon/
├── SKILL.md        # Skill OpenClaw (instructions pour l'agent)
├── tcl_tool.py     # Script Python de requêtes GTFS
├── tcl.db          # Base SQLite (à générer, non incluse)
└── README.md       # Ce fichier
```

---

## Données

Source : [transport.data.gouv.fr](https://transport.data.gouv.fr) — données ouvertes Sytral/TCL, licence ODbL.
