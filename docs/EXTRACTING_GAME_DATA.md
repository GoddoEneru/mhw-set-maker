# Récupérer les données directement depuis les fichiers du jeu

Ce document est un guide de référence pour remplacer (ou compléter) le pipeline de scraping actuel (`src/scraper.py` + `src/cleaner.py`, qui scrape game8.co) par une extraction directe des données depuis les fichiers de Monster Hunter Wilds. C'est un document de recherche/préparation : **aucun code n'a encore été écrit** pour ce pipeline. À reprendre une fois le jeu installé localement pour tester la chaîne d'extraction.

## Pourquoi

Le pipeline actuel dépend de la structure HTML de game8.co et de l'exactitude de son contenu. Extraire directement les fichiers du jeu donnerait des données de première main, plus fiables — mais avec deux contreparties : ça demande des outils externes à ce projet Python, et il faut relancer l'extraction après chaque patch du jeu (contrairement au scraper qui se met à jour tout seul).

Décision retenue : si ce pipeline est implémenté un jour, il **coexistera** avec le scraper actuel plutôt que de le remplacer — le scraper resterait la méthode par défaut, avec repli sur les CSV commités en cas d'échec (comme aujourd'hui), et l'extraction depuis les fichiers du jeu serait un moyen alternatif, lancé manuellement, de régénérer ces CSV.

## Vue d'ensemble de la chaîne d'extraction

Monster Hunter Wilds tourne sur le moteur RE Engine de Capcom (comme MH Rise, Resident Evil 2/3/4/7/8, DMC5...). Ses données sont packagées dans des archives `.pak` propriétaires, compressées et chiffrées.

```
fichiers du jeu (.pak, ex. re_chunk_000.pak)
   │  outil d'extraction PAK (Ekey/REE.PAK.Tool en C#/.NET, ou eigeen/ree-pak-rs en Rust)
   ▼
fichiers bruts RE Engine (.user.3 = tables de stats RSZ, .msg.23 = tables de texte/noms)
   │  REasy (seifhassine/REasy, GUI Python) ou RszTool pour les .user.3
   │  REMSG_Converter (dtlnor) pour les .msg.23
   ▼
dumps JSON (stats numériques d'un côté, noms/textes localisés de l'autre)
   │  script de fusion (à écrire plus tard) — jointure par ID
   ▼
armors.csv / decorations.csv / skills.csv / talismans.csv (même schéma qu'aujourd'hui)
```

Deux familles de fichiers à l'intérieur des `.pak` intéressent ce projet :
- **`.msg.*`** (ex. `.msg.23`) : tables de texte/localisation — noms d'armures, de skills, descriptions.
- **`.user.*`** (ex. `.user.3`), format **RSZ** ("Resource-SerialiZation") : objets de données structurées versionnés — stats d'armure (défense, résistances), skills + niveaux, tailles de slots de décoration, etc. Le binaire ne s'auto-décrit pas : il faut un schéma JSON par version de jeu pour savoir comment le lire (maintenu par la communauté).

## Outils recommandés

| Étape | Outil | Type | Notes |
|---|---|---|---|
| Extraction des `.pak` | [Ekey/REE.PAK.Tool](https://github.com/Ekey/REE.PAK.Tool) | C#/.NET, CLI | Piloté par des "Projects" (listes de hash) par jeu, dossier `Projects/` du repo |
| Extraction des `.pak` (alternative) | [eigeen/ree-pak-rs](https://github.com/eigeen/ree-pak-rs) | Rust, CLI/GUI | Plus rapide, gère GDeflate/zstd (utilisés par Wilds pour les textures) |
| Lecture des `.user.3` (RSZ) | [seifhassine/REasy](https://github.com/seifhassine/REasy) | Python/Qt, GUI | Explicitement listé compatible Monster Hunter Wilds, export JSON |
| Lecture des `.user.3` (alternative) | [czastack/RszTool](https://github.com/czastack/RszTool) | Python, lib | — |
| Lecture des `.msg.23` | [dtlnor/REMSG_Converter](https://github.com/dtlnor/REMSG_Converter) | Python, lib/CLI | Export CSV ou JSON, gère le multi-langue |

**À étudier en premier** : [LartTyler/mhdb-wilds-data](https://github.com/LartTyler/mhdb-wilds-data) — toolkit Rust qui fait déjà exactement cette chaîne (extraction + fusion RSZ/MSG → JSON) spécifiquement pour Monster Hunter Wilds, utilisé par le site communautaire mhwilds.wiki-db.com. Son dossier `/output/merged` contient potentiellement des dumps déjà prêts à inspecter comme référence de schéma — un bon point de départ avant même de lancer sa propre extraction.

**Point d'attention Wilds-spécifique** : Wilds tourne sur une version plus récente du moteur que MH Rise/World (nouveau format de clé PAK, textures en GDeflate). Vérifier que l'outil choisi a explicitement été mis à jour pour Wilds, pas seulement pour "RE Engine" en général — ex. [REToolCustom](https://github.com/SlickAmogus/REToolCustom) ajoute ce support explicitement.

## Correspondance avec le schéma CSV actuel

L'app consomme ces schémas exacts (voir `CLAUDE.md` et `src/data/*.csv`) — tout nouveau pipeline doit produire ces mêmes colonnes :

- **`armors.csv`** : `Armor,Defense,Armor_type,Skill_1_name,Skill_1_lvl,Skill_2_name,Skill_2_lvl,Skill_3_name,Skill_3_lvl,Decoration_slot_1_size,Decoration_slot_2_size,Decoration_slot_3_size`
- **`decorations.csv`** : `Decoration_name,Decoration_size,Skill_1_name,Skill_1_lvl`
- **`skills.csv`** : `Skill,Type,Effect,skill_max_level`
- **`talismans.csv`** : `Talisman,Rarity,Skill_name,Skill_lvl`

Point important : la quasi-totalité de la logique regex de `src/cleaner.py` (décodage des glyphes `①②③`, séparation de chaînes de skills fusionnées, correction des niveaux manquants, gestion des formats `"Lv."` vs `"Lv"` incohérents) existe uniquement pour compenser les bizarreries du HTML de game8.co. Si les dumps JSON exposent déjà des champs structurés (id skill + niveau entier, taille de slot entière), tout ce parsing devient inutile — il ne resterait qu'un mapping nom-de-champ → nom-de-colonne à écrire.

## Points d'attention légaux et bonnes pratiques

- Capcom cible officiellement les mods qui affectent le jeu **en ligne** (triche, corruption de sauvegarde, classements) — voir la [mise en garde officielle de Capcom sur la modification de données](https://www.monsterhunter.com/wilds/en-us/topics/unauthorized-modification-data/). Rien n'indique que l'extraction locale en lecture seule pour un usage personnel soit visée, mais l'EULA reste large et ne fait pas d'exception explicite.
- Norme communautaire constante (Kiranico, MHWorldData, mhdb-wilds-data) : ne pas redistribuer les assets bruts extraits (textures, modèles 3D, dumps complets). Publier uniquement des tables dérivées (stats, noms, niveaux) sous forme CSV/JSON est une pratique établie et tolérée — c'est exactement ce que fait déjà ce projet avec les CSV commités.
- Recommandation concrète : garder les dumps bruts (JSON complets, fichiers `.pak` extraits) uniquement en local, ne committer dans ce repo que les CSV finaux dérivés, comme c'est déjà le cas aujourd'hui.

## Effort et maintenance, comparé au scraper actuel

- Mise en place initiale plus lourde : installer et lancer des outils externes (C#/.NET ou Rust) en dehors de ce projet Python, obtenir une liste de hash / un schéma RSZ à jour pour la version du jeu installée.
- Contrairement au scraper (qui se met à jour tout seul à chaque chargement de page), il faudra **relancer l'extraction manuellement après chaque patch du jeu** si le format de fichier ou les hash changent.

## Prochaine étape (pas encore faite)

Une fois le jeu installé et l'extraction testée manuellement (obtenir un premier dump JSON via la chaîne ci-dessus) :

1. Inspecter la structure réelle des dumps JSON obtenus (les noms de champs peuvent différer de ce que ce guide anticipe).
2. Écrire un script Python de fusion/mapping (ex. `src/game_data_importer.py`) qui prend ces dumps JSON en entrée et écrit les CSV finaux dans `src/data/`, en réutilisant les mêmes noms de colonnes et fichiers cibles que `Cleaner` aujourd'hui.
3. Décider du déclenchement : commande manuelle (script à lancer à la main après une extraction) plutôt qu'automatique au chargement de la page, contrairement au scraper actuel.
