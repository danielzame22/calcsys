# CALC//SYS — APK Build Guide

App Python + Kivy con:
- **Solver matemático** (ecuaciones, integrales, derivadas, etc.) via Claude AI
- **Sudoku diario** con sistema de racha (🔥 streak)

---

## Estructura del proyecto

```
calcsys/
├── main.py              # Entry point
├── theme.py             # Colores y fuentes
├── storage.py           # Persistencia JSON
├── sudoku_engine.py     # Generador/solver de sudoku (puro Python)
├── buildozer.spec       # Config para compilar APK
├── data.json            # Se crea automáticamente al correr
└── screens/
    ├── solver.py        # Pantalla del solver
    ├── sudoku.py        # Pantalla del sudoku
    └── nav.py           # Barra de navegación inferior
```

---

## Opción A — Compilar APK con Google Colab (RECOMENDADO, sin instalar nada)

1. Ve a https://colab.research.google.com
2. Crea un nuevo notebook y ejecuta estas celdas:

```python
# Celda 1 — Instalar buildozer
!pip install buildozer
!sudo apt-get install -y \
    python3-pip build-essential git python3 python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev \
    openjdk-17-jdk unzip
```

```python
# Celda 2 — Subir y descomprimir el proyecto
from google.colab import files
uploaded = files.upload()  # Sube calcsys.zip
import zipfile
with zipfile.ZipFile('calcsys.zip', 'r') as z:
    z.extractall('.')
import os; os.chdir('calcsys')
```

```python
# Celda 3 — Compilar (tarda ~20-40 min la primera vez)
!buildozer -v android debug
```

```python
# Celda 4 — Descargar APK
from google.colab import files
import glob
apks = glob.glob('bin/*.apk')
files.download(apks[0])
```

---

## Opción B — Compilar en Linux / WSL2

### Requisitos
- Ubuntu 20.04+ o WSL2 con Ubuntu
- Python 3.9+

### Pasos

```bash
# 1. Instalar dependencias del sistema
sudo apt update
sudo apt install -y python3-pip build-essential git python3 python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev \
    openjdk-17-jdk unzip autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 cmake

# 2. Instalar buildozer
pip3 install --user buildozer cython==0.29.33

# 3. Entrar al directorio del proyecto
cd calcsys/

# 4. Compilar APK (primera vez tarda bastante — descarga Android SDK/NDK)
buildozer android debug

# 5. El APK queda en:
ls bin/*.apk
```

---

## Correr en desktop (para probar sin compilar)

```bash
pip install kivy
cd calcsys/
python main.py
```

---

## Instalar APK en el celular

1. Copia el `.apk` al celular (por cable, Drive, WhatsApp, etc.)
2. En Android: Ajustes → Seguridad → Activar "Fuentes desconocidas"
3. Abre el `.apk` desde el administrador de archivos
4. Instalar ✓

---

## Notas

- El **Solver** llama a la API de Anthropic — necesita internet.
- El **Sudoku** funciona 100% offline.
- La racha se guarda en `data.json` en el dispositivo.
- El puzzle del día es el mismo para todos (basado en la fecha).
