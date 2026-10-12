# Vento e Vele in Godot: piano e prima guida

## 1. Che versione: Godot 4.7 (l'ultima 4.7.x stabile)

Da usare: **Godot 4.7.x "Standard" (GDScript, non la versione .NET/C#)**, l'ultima patch stabile
(a ottobre 2026 dovrebbe essere la 4.7.2: controlla su godotengine.org/download prima di
installare, e usa *la stessa identica versione* sul PC e nella build su GitHub).

Perché:

- **Ramo 4.x, non 3.x.** Il 3.x riceve solo manutenzione; tutto il lavoro nuovo (renderer,
  shader, UI, export web e Android) è sul 4.x.
- **GDScript, non C#.** Il gioco deve girare nel browser del telefono (GitHub Pages), e
  l'export Web con C# in Godot 4 non è supportato (almeno fino alle ultime versioni di cui ho
  notizia). GDScript esporta ovunque: web, Android, PC.
- **Renderer "Compatibility" (OpenGL ES 3 / WebGL 2).** È l'unico che gira nel browser ed è il
  più leggero sui telefoni. Per un gioco 2D a 1 bit non ci serve altro: il dither di oggi
  (`ditherPass`, Bayer 4×4) diventa uno shader di poche righe.
- **Export web single-thread.** Dalle 4.3 il web si può esportare senza thread, quindi senza
  le intestazioni COOP/COEP che GitHub Pages non permette di impostare. Così il gioco gira su
  Pages come oggi, senza server particolari.
- **Android nativo quando vorrai.** Lo stesso progetto esporta un APK (vibrazione vera,
  schermo intero vero, niente barra del browser).

## 2. Il piano, a fasi

Ogni fase finisce con qualcosa che giri sul telefono. Il prototipo HTML resta com'è (e resta
online) finché la versione Godot non lo raggiunge.

| Fase | Cosa | Corrisponde in `index.html` a |
|---|---|---|
| 0 | Progetto vuoto, layout da telefono, build automatica su GitHub Pages (questa guida) | — |
| 1 | Il look: mondo disegnato a bassa risoluzione + shader dither a 2 colori, palette giorno/notte | 1-bit rendering, Day and night |
| 2 | Il mare e la barca: mondo toroidale 5040 px, camera, scafo, timone (ruota), ancora sul mozzo | World setup, Boat, Ship's wheel, Input |
| 3 | Vento e vele: polari (`SAIL_POLAR_*`), corrente, scarroccio, le tre vele | Wind, Tuning delle vele |
| 4 | La mappa disegnata: `DRAWN_LAND` → poligoni Godot (collisioni + disegno), `MAP_LAYOUT` → una scena/risorsa | Drawn map, `MAP_LAYOUT_FILE` |
| 5 | Casa, villaggi, moli, ormeggio, mercato e magazzino | Home island, Villages, Village market |
| 6 | Pesca, tesori, bottiglie, naufrago | Fish banks, treasure spots, bottles |
| 7 | Pericoli: gorghi, mare bollente, tempeste, squali, folletti, torri costiere | Whirlpools, Storms, Sharks, Sea imps, towers |
| 8 | Il diario (logbook) con le sue pagine, la mappa a stanze, i cuori | Shopping list, Sea chart, Hearts |
| 9 | Suoni (prima campioni registrati, poi eventuale sintesi) e vibrazione | Sound, Haptics |
| 10 | Rifinitura, prestazioni, export Android | — |

Regole che porto dal prototipo:

- **Tuning e testi in un posto solo.** In Godot: un file `tuning.gd` (autoload, solo costanti)
  e i testi in un file di traduzione (`texts.csv`), così li modifichi a mano come oggi.
- **Mondo da file.** La terra disegnata e il layout restano dati (risorse `.tres`/JSON),
  l'editor della mappa può continuare a scriverli.
- **Build stamp e "What's new"** anche lì, nella prima schermata.

## 3. Prima guida: layout da telefono

### 3.1 Installa
1. Scarica Godot 4.7.x Standard (non .NET) da godotengine.org/download.
2. Da *Editor → Manage Export Templates* scarica i template della stessa versione.

### 3.2 Crea il progetto
1. Nuovo progetto in una cartella `godot/` dentro questo repository.
2. Renderer: **Compatibility**.

### 3.3 Project Settings (attiva "Advanced Settings" in alto a destra)
- *Display → Window → Size*: **Viewport Width 360, Viewport Height 800** (un telefono in verticale,
  in pixel CSS come oggi).
- *Display → Window → Size → Mode*: Windowed; *Window Width/Height Override* 360×800 per provare
  sul PC con una finestra da telefono.
- *Display → Window → Stretch*: **Mode `canvas_items`**, **Aspect `expand`** (su telefoni più
  alti o più larghi si vede più mare, niente bande nere), Scale Mode `fractional`.
- *Display → Window → Handheld → Orientation*: **Portrait**.
- *Rendering → Textures → Canvas Textures → Default Texture Filter*: **Nearest** (pixel netti).
- *Input Devices → Pointing → Emulate Touch From Mouse*: **On** (provi il tocco col mouse).

### 3.4 Struttura della scena principale
```
Main (Node)
├─ World (SubViewportContainer, stretch on, stretch_shrink 3)   ← il mare a bassa risoluzione
│  └─ SubViewport (texture filter Nearest)
│     └─ … mare, isole, barca, Camera2D …
├─ Dither (ColorRect a tutto schermo con lo shader 1-bit)        ← fase 1
└─ HUD (CanvasLayer)                                              ← controlli a risoluzione piena
   ├─ Hearts (in alto a sinistra)
   ├─ Logbook (in basso a sinistra)
   ├─ Wheel (in basso al centro)
   └─ Crank / Sling / Sail (in basso a destra / a sinistra)
```
Con `stretch_shrink 3` il mondo è disegnato a 1/3 della risoluzione e ingrandito con pixel netti,
come fa oggi il buffer `GW×GH`; l'HUD resta nitido. Per l'HUD usa i **Container** di Godot
(ancore *Bottom Left / Bottom Wide / Bottom Right*) e i *margini di sicurezza*
(`DisplayServer.get_display_safe_area()`) per notch e barra dei gesti.

## 4. Prima guida: build automatica su GitHub (Pages)

### 4.1 Preset di esportazione
1. *Project → Export → Add… → Web*. Nome del preset: **Web**.
2. *Thread Support*: **off** (niente COOP/COEP, gira su Pages).
3. Export Path: `build/web/index.html`.
4. Salva: nasce `godot/export_presets.cfg`, **va committato** (non contiene segreti per il web).

### 4.2 Il workflow
Un file `.github/workflows/godot-web.yml` che a ogni push su `master`:
1. scarica Godot headless e i template della stessa versione;
2. esporta il preset "Web";
3. pubblica su Pages **il sito di oggi più la versione Godot in `/godot/`**, così il prototipo
   resta a `…/Sail---Prototype/` e la nuova versione sta a `…/Sail---Prototype/godot/`.

```yaml
name: Godot web build
on:
  push:
    branches: [master]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency: { group: pages, cancel-in-progress: true }
env:
  GODOT_VERSION: 4.7.2   # la stessa del tuo editor
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Godot e template
        run: |
          V=$GODOT_VERSION
          wget -q https://github.com/godotengine/godot/releases/download/$V-stable/Godot_v$V-stable_linux.x86_64.zip
          wget -q https://github.com/godotengine/godot/releases/download/$V-stable/Godot_v$V-stable_export_templates.tpz
          unzip -q Godot_v$V-stable_linux.x86_64.zip && mv Godot_v$V-stable_linux.x86_64 godot-bin
          mkdir -p ~/.local/share/godot/export_templates/$V.stable
          unzip -q Godot_v$V-stable_export_templates.tpz
          mv templates/* ~/.local/share/godot/export_templates/$V.stable/
      - name: Esporta
        run: |
          mkdir -p godot/build/web
          ./godot-bin --headless --path godot --import || true
          ./godot-bin --headless --path godot --export-release "Web" build/web/index.html
      - name: Sito = prototipo + Godot in /godot/
        run: |
          mkdir -p site && rsync -a --exclude .git --exclude godot --exclude site ./ site/
          mkdir -p site/godot && cp -r godot/build/web/* site/godot/
          touch site/.nojekyll
      - uses: actions/upload-pages-artifact@v3
        with: { path: site }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: '${{ steps.d.outputs.page_url }}' }
    steps:
      - id: d
        uses: actions/deploy-pages@v4
```

### 4.3 Da fare una volta su GitHub
*Settings → Pages → Build and deployment → Source*: **GitHub Actions** (invece di
"Deploy from a branch"). Da lì in poi ogni push pubblica entrambe le versioni; lo stato della
build si vede nella scheda *Actions*.

### 4.4 Android (più avanti, fase 10)
Stesso workflow con un preset "Android" e un keystore salvato nei *Secrets* del repository:
l'APK esce come file scaricabile dalla build, da installare sul telefono.
