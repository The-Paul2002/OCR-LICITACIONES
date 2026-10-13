# Laboratorio de OCR — clase UP + piloto Zaragoza

[![Abrir el notebook de clase en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/patrickmelorr-lang/OCR-LICITACIONES/blob/main/notebooks/00_colab_clase.ipynb)
[![Abrir el mini-proyecto en Colab](https://img.shields.io/badge/Colab-mini--proyecto-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/patrickmelorr-lang/OCR-LICITACIONES/blob/main/notebooks/01_mini_zaragoza.ipynb)

Lectura automatizada de bases de licitación escaneadas. Caso real: las bases de la
Licitación Pública de Obras N° 05-2026-C-MPI de la Municipalidad Provincial de Ilo,
descargadas de SEACE.

> **Estudiantes: empiecen por el primer badge.** Abre el notebook de la clase en Colab,
> sin instalar nada. Acuérdense de poner el entorno en **GPU T4** antes de correr:
> *Entorno de ejecución → Cambiar tipo de entorno de ejecución → T4 GPU*.

Material de la **Semana 10** del curso Data Science con Python (Universidad del
Pacífico): *Document AI y voz: OCR, extracción estructurada y ASR*.

---

## La idea única

> **Conocer tu hardware decide qué modelo puedes correr. Y arreglar la imagen rinde más
> que traer un modelo más grande.**

Todo lo demás —comandos, parámetros, nombres de modelos— es consecuencia.

---

## Los tres carriles

Los tres corren **el mismo código**. Lo único que cambia es la máquina.

| Carril | Para quién | Qué corre |
|---|---|---|
| A — Colab | la mayoría | PP-OCRv6 sobre GPU T4 gratuita |
| B — Local CPU | quien no tenga GPU | PP-OCRv6 nivel `tiny` o `small` |
| C — Local GPU | quien tenga tarjeta NVIDIA | PP-OCRv6 `medium` con `paddlepaddle-gpu` |

---

## Instalación (carril C, GPU local)

Requiere **Python 3.12**. El 3.14 no sirve: PaddlePaddle soporta 3.9 a 3.13.
No hace falta instalar CUDA Toolkit ni cuDNN — el wheel los trae como dependencias pip.
Solo se necesita el driver NVIDIA.

```powershell
cd C:\Users\LENOVO\Documents\PAUL\UP\OCR

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version        # debe decir 3.12.x

python -m pip install paddlepaddle-gpu==3.3.0 `
  -i https://www.paddlepaddle.org.cn/packages/stable/cu126/ `
  --extra-index-url https://pypi.org/simple

python -m pip install "paddleocr==3.7.0" "pypdfium2==4.30.0" "pypdf==5.1.0" `
  "pyyaml==6.0.2" "pillow==11.0.0" "pandas==2.2.3"
```

Para el carril B (CPU), cambiar el primer `pip install` por:

```powershell
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

> **Nunca los dos a la vez.** `paddlepaddle` y `paddlepaddle-gpu` conviven sin lanzar
> error, y el resultado es que todo corre en CPU 40 veces más lento sin avisar.
> `doctor.py` aborta si detecta ambos.

Runbook completo con puntos de corte: [`PLAN_60MIN.md`](PLAN_60MIN.md).

---

## Correrlo en VS Code

La carpeta `.vscode/` ya trae el intérprete, los lanzadores y las extensiones
recomendadas. No hay que configurar nada a mano.

```powershell
cd C:\Users\LENOVO\Documents\PAUL\UP\OCR
code .
```

Al abrirla, VS Code ofrece instalar las extensiones necesarias (Python, Jupyter,
Pylance). Aceptar. Después:

### Correr un módulo

`Ctrl+Shift+D` abre **Ejecutar y depurar**. El desplegable de arriba tiene el pipeline
en orden, de `1. doctor` a `7. ensayo cronometrado`. Se elige uno y se lanza con `F5`.

También sirve la terminal integrada, que ya arranca con el venv activado:

```powershell
python -m src.doctor
```

> Si el prompt no muestra `(.venv)` al inicio de la línea, se está usando el Python
> 3.14 del sistema y nada va a funcionar. `Ctrl+Shift+P` → *Python: Select Interpreter*
> → el de `.venv\Scripts\python.exe`.

### Correr un notebook

Abrir `notebooks/01_mini_zaragoza.ipynb` y elegir el kernel **Python 3.12 (OCR UP)**
arriba a la derecha. Las celdas se corren con `Shift+Enter`.

La primera celda se encarga de moverse a la raíz del proyecto, así que el notebook
funciona igual abierto desde `notebooks/`.

> Los notebooks necesitan `ipykernel`, que ya está en el venv. Si VS Code pide
> instalarlo, es que el kernel seleccionado no es el del proyecto.

---

## Uso

Cada módulo se ejecuta por sí solo y es importable sin efectos secundarios.

```powershell
python -m src.doctor        # 1. ¿la GPU está realmente en uso?
python -m src.triaje        # 2. ¿qué páginas necesitan OCR?
python -m src.preparar 1    # 3. rasterizar, partir la hoja, enderezar
python -m src.ocr_run       # 4. texto + cajas + confianza
python -m src.extraer       # 5. cuatro campos a JSON y CSV
python -m src.bench rapido  #    medir CPU vs GPU
```

El orden importa: cada paso consume la salida del anterior. Todos cachean en disco, así
que correrlos dos veces no recomputa lo ya hecho.

### Qué hace cada módulo

| Módulo | Qué responde |
|---|---|
| `doctor.py` | ¿la GPU está disponible **y en uso**? Seis chequeos; el sexto no se puede falsificar |
| `triaje.py` | ¿qué páginas son imagen y necesitan OCR? Las de texto se extraen gratis |
| `preparar.py` | rasteriza la hoja, la parte en dos páginas lógicas, corrige la rotación |
| `ocr_run.py` | corre PP-OCRv6 y devuelve texto, geometría y confianza por línea |
| `bench.py` | mide con protocolo honesto: calentamiento, mediana, VRAM, y **calidad** |
| `extraer.py` | cuatro campos a JSON/CSV por dos vías: reglas y modelo de lenguaje |

---

## Configuración

Todo valor ajustable vive en [`config.yaml`](config.yaml). Ningún parámetro está
hardcodeado en el código Python.

Cambiar `ocr.device` de `gpu` a `cpu` en el YAML cambia dónde corre el OCR, sin tocar
una línea de Python. Eso es el criterio de aceptación del archivo.

Los parámetros que más importan:

| Parámetro | Por qué importa |
|---|---|
| `render.dpi_fisico: 425` | cada página lógica ocupa media hoja A4, reducida a un factor lineal de ~0.707. A 425 DPI de hoja física, la página lógica queda cerca de 300 DPI efectivos |
| `render.rotacion: 270` | verificado sobre el documento real. Con 90 la página sale cabeza abajo |
| `render.orden_mitades` | la mitad **inferior** es la página de número menor. Si se invierte, el informe sale desordenado |
| `ocr.device` | `gpu` o `cpu`. En PaddleOCR 3.x el parámetro es `device`, **nunca** `use_gpu` |
| `ocr.nivel` | `tiny` (1.5 M params, 73.5%), `small` (7.7 M, 81.3%), `medium` (34.5 M, 83.2%) |

---

## El documento de prueba

`data/raw/BASE-ESTANDAR-ILO-SEACE-OCR.pdf` es, por accidente feliz, el mejor caso de
enseñanza posible: contiene de golpe los cuatro problemas que un pipeline de OCR debe
resolver.

| Propiedad medida | Valor | Por qué importa |
|---|---|---|
| Hojas físicas | 57 | tamaño manejable para clase |
| Caracteres en la capa de texto | **0** | 100% escaneado: el triaje marca todas las páginas |
| Imágenes embebidas por hoja | 9 a 63 | el escáner guardó mosaicos: hay que rasterizar, no extraer |
| Disposición | **2 páginas lógicas por hoja** | ~114 páginas lógicas; hay que partir la hoja |
| Orientación | **rotado 90°** (se corrige con 270°) | el bug clásico de las tablas apaisadas |
| Ruido | firmas manuscritas en azul sobre el texto | caso realista de escaneo degradado |

### Por qué rasterizar y no extraer las imágenes

> El PDF no guarda una foto de la hoja, guarda el **rompecabezas desarmado**. Si pides
> "las imágenes", te dan las piezas sueltas. Hay que pedir la foto del rompecabezas
> armado, que es lo que hace el renderizador.

---

## Estructura

```
├── config.yaml                 todos los parámetros ajustables
├── src/
│   ├── comun.py                carga de config y logging sin buffer
│   ├── doctor.py               semáforo de GPU
│   ├── triaje.py               ¿qué necesita OCR?
│   ├── preparar.py             rasterizar, partir, enderezar
│   ├── ocr_run.py              inferencia PP-OCRv6
│   ├── bench.py                medición honesta
│   └── extraer.py              texto → datos estructurados
├── notebooks/
│   ├── 00_colab_clase.ipynb    carril sin instalación
│   └── 01_mini_zaragoza.ipynb  el mini-proyecto completo
├── fallas/README.md            laboratorio de diagnóstico
├── data/raw/                   el original, nunca se escribe
├── data/processed/             PNG por página, texto crudo
├── data/outputs/               CSV, JSON, tablas del benchmark
└── logs/                       un log por módulo
```

---

## Si algo falla

1. **Leer el log antes de cambiar código.** Están en `logs/`, uno por módulo. El
   proyecto original diagnosticó su peor bug leyendo tres líneas de log
   (`offloaded 0/37 layers to GPU`), no adivinando.
2. **`python -m src.doctor`** antes que nada. Si el chequeo 6 falla, el OCR está
   corriendo en CPU aunque se haya pedido GPU.
3. Si falla la instalación de Paddle, no intentar rutas creativas (compilar, wheels de
   terceros, Docker). En sm_86 el camino oficial funciona; si no funciona, el problema
   es el entorno, no el paquete.

### Dos cosas que ya pasaron y están resueltas

**`WARNING: ... compiled with CUDNN 9.9, but CUDNN version in your machine is 9.5`**
Es benigno. La GPU funciona igual: verificado con el chequeo 6 del doctor, que midió
+350 MiB de VRAM. No instalar cuDNN a mano.

**`(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support`** al correr en CPU
Es un bug del ejecutor PIR de Paddle con oneDNN en Windows. `ocr_run.py` ya lo evita
pasando `enable_mkldnn=False` cuando `device == "cpu"`. Si aparece, es que el código se
saltó `construir_ocr()` y creó el objeto `PaddleOCR` por su cuenta.

---

## Documentos de este repositorio

| Archivo | Qué contiene |
|---|---|
| [`DISEÑO.md`](DISEÑO.md) | arquitectura, especificación archivo por archivo, criterios de aceptación |
| [`PLAN_60MIN.md`](PLAN_60MIN.md) | runbook de instalación con comandos exactos y puntos de corte |
| [`GUION_CLASE_110MIN.md`](GUION_CLASE_110MIN.md) | guion de la sesión, bloque por bloque |
| [`fallas/README.md`](fallas/README.md) | las tres fallas sembradas y su diagnóstico |
| [`CLAUDE.md`](CLAUDE.md) | reglas del repositorio |

---

## Contexto de modelos, a octubre de 2026

El hallazgo central contradice la intuición:

> Los mejores modelos de OCR abiertos hoy son modelos **pequeños y dedicados a
> documentos**, no VLM grandes. En OmniDocBench v1.6, PaddleOCR-VL-1.6 (0.9B) obtiene
> 96.34 y GLM-OCR (0.9B) 95.22, por encima de Qwen3-VL-235B con 89.78.

Y el más útil para licitaciones:

> En Wild-OmniDocBench, que usa **fotos** de las mismas páginas, PaddleOCR-VL cae de
> 91.93 a 72.19. Veinte puntos de caída por calidad de imagen.

Traducción: invertir en preprocesamiento rinde más que cambiar de modelo. El documento
de prueba, con sus firmas encima y su rotación, lo demuestra en vivo.

---

Jefe de práctica: Paul Melo Ramos · Profesor del curso: Alexander Quispe Rojas
