# PLAN_60MIN — Runbook de instalación

Objetivo: dejar los tres modos funcionando (Colab, CPU local, GPU local) en una hora, con
puntos de corte explícitos para no quedarse atascado.

Máquina objetivo: LAPTOP-ADFLMMCK, Windows 11, RTX 3050 6 GB, driver 581.86.
Carpeta de trabajo: `C:\Users\LENOVO\Documents\PAUL\UP\OCR`

---

## Antes de empezar: los dos hechos que cambian el plan

### Hecho 1 — No hay que instalar CUDA Toolkit

La documentación oficial de PaddlePaddle lo dice de forma explícita: Paddle soporta la
instalación sin depender de CUDA y cuDNN, y los gestiona automáticamente; solo hay que
asegurar que el driver local cumpla el requisito.

> Analogía: el CUDA Toolkit es la **fábrica** de juguetes. El wheel de `paddlepaddle-gpu`
> ya trae los **juguetes hechos**. Tú quieres jugar, no fabricar. Instalar la fábrica de
> 3 GB para jugar con algo que ya viene en la caja es el error clásico.

| Pieza | ¿Necesaria? | Por qué |
|---|---|---|
| Driver NVIDIA | Sí, obligatorio | Es lo único que el wheel no puede traer. Ya está: 581.86 |
| CUDA Toolkit (nvcc) | **No** | Solo si compilaras Paddle desde fuente |
| cuDNN manual | **No** | Entra como dependencia pip del wheel |
| Visual Studio Build Tools | **No** | Solo para compilar |

El driver 581.86 supera con holgura el mínimo de cualquier índice (cu126 exige 550.54.14 en
Windows). Esto ya está resuelto. **Ahorro: 30 minutos y 3 GB.**

### Hecho 2 — Python 3.14.7 no sirve, y es el bloqueador real

PaddlePaddle soporta **Python 3.9 a 3.13**. La 3.14 está fuera. Si se intenta instalar con
ella, el error no dirá "versión no soportada": dirá que no encuentra una distribución que
cumpla el requisito, que es confuso y hace perder veinte minutos.

No hay que desinstalar la 3.14. Se crea un entorno virtual con Python 3.12 al lado.

> Analogía: no hay que botar la laptop porque el cargador no entra. Hay que conseguir el
> cargador correcto y dejar el otro guardado.

---

## Cronograma con puntos de corte

| Min | Paso | Resultado esperado | Si falla |
|---|---|---|---|
| 0–2 | Verificar driver | ya verificado: 581.86 | — |
| 2–7 | Instalar `uv` y crear venv 3.12 | `python --version` dice 3.12.x | **Corte A:** instalar Python 3.12 con winget |
| 7–22 | Instalar `paddlepaddle-gpu` | descarga de ~1 GB | **Corte B:** si pasa de 22 min, cancelar y seguir en CPU |
| 22–26 | Verificar GPU | `run_check` dice GPU | **Corte C:** revisar índice o wheel duplicado |
| 26–34 | Instalar PaddleOCR y primera inferencia | descarga de pesos, texto en pantalla | — |
| 34–45 | Benchmark CPU vs GPU | dos números y VRAM moviéndose | — |
| 45–55 | Notebook de Colab | mismo flujo en T4 | — |
| 55–60 | Congelar versiones y README | `requirements.lock.txt` | — |

**Trabajar en paralelo.** Los 15 minutos del paso 7–22 son descarga pura. No mirar la
barra: abrir otra ventana y preparar el documento de prueba y el Colab mientras tanto.

---

## Paso a paso

Todo en **PowerShell**, desde la carpeta del proyecto.

### Paso 1 — Entorno con Python 3.12 (minutos 2–7)

```powershell
cd C:\Users\LENOVO\Documents\PAUL\UP\OCR

# uv descarga y gestiona versiones de Python por su cuenta. Es la vía más rápida.
python -m pip install --user uv

# Crea el venv con Python 3.12; si no lo tiene, lo descarga solo.
uv venv --python 3.12 .venv

.\.venv\Scripts\Activate.ps1
python --version        # debe decir 3.12.x, NO 3.14
python -m pip install --upgrade pip
```

**Corte A.** Si `uv` no se instala o no puede descargar Python 3.12:

```powershell
winget install -e --id Python.Python.3.12
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación por política de ejecución:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

> Nota: a partir de aquí, **toda** orden se ejecuta con el venv activado. El indicador
> `(.venv)` debe estar visible al inicio de la línea. Si no está, se está instalando en el
> Python 3.14 y nada va a funcionar.

---

### Paso 2 — PaddlePaddle GPU (minutos 7–22)

El índice depende de la versión de CUDA que el driver soporta. Driver 581.86 reporta
CUDA 13.0, así que sirven cu118, cu126, cu129 y cu130. Se elige **cu126** por ser el más
probado sobre arquitectura Ampere.

```powershell
python -m pip install paddlepaddle-gpu==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
```

**Fallback de dependencias.** Ese índice reemplaza a PyPI por completo. Si pip se queja de
que no encuentra un paquete que no es de Paddle, agregar PyPI como índice secundario
manteniendo el de Paddle como principal:

```powershell
python -m pip install paddlepaddle-gpu==3.3.0 `
  -i https://www.paddlepaddle.org.cn/packages/stable/cu126/ `
  --extra-index-url https://pypi.org/simple
```

**Fallback de índice.** Si cu126 da problemas, probar cu129. No probar wheels de terceros
ni compilar: en sm_86 el camino oficial funciona, y si no funciona el problema es el
entorno.

**Corte B.** Si a los 22 minutos sigue descargando: cancelar, instalar la versión CPU
(`python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/`)
y continuar con el resto del plan. La GPU se arma esta noche sin presión. La clase funciona
con Colab y CPU; el modo GPU local se puede presentar con un video grabado.

> Regla dura: **jamás** tener instalados `paddlepaddle` y `paddlepaddle-gpu` a la vez.
> Si hubo que instalar la versión CPU y luego se instala la GPU, desinstalar primero:
> `python -m pip uninstall -y paddlepaddle`

---

### Paso 3 — Verificar que la GPU esté realmente en uso (minutos 22–26)

```powershell
python -c "import paddle; print(paddle.is_compiled_with_cuda()); print(paddle.device.get_device()); paddle.utils.run_check()"
```

Debe imprimir `True`, luego `gpu:0`, y terminar con el mensaje de verificación exitosa
mencionando GPU.

**Corte C.** Si dice `False` o `cpu`, hay exactamente tres causas posibles, en orden de
probabilidad:

1. Se instaló `paddlepaddle` (CPU) en vez de `paddlepaddle-gpu`. Verificar con
   `python -m pip list | findstr paddle`.
2. Están los dos instalados. Desinstalar el de CPU.
3. El venv activo no es el correcto. Verificar `python --version` y el prefijo `(.venv)`.

No hay cuarta causa. No perder tiempo buscando una.

---

### Verificado el 13 de octubre de 2026 en la máquina objetivo

El runbook de arriba corrió completo. Tres cosas que pasaron y no estaban previstas:

| Lo que pasó | Qué significa | Qué se hizo |
|---|---|---|
| Python 3.12.10 ya estaba instalado | el **Corte A no hizo falta**, ni `uv`. `py -3.12 -m venv .venv` y listo | se ahorraron 5 minutos |
| Paddle avisa `compiled with CUDNN 9.9, but CUDNN version in your machine is 9.5` | aviso benigno. La GPU funciona: el chequeo 6 del doctor midió **+350 MiB** de VRAM | **no tocar nada.** Ver prohibición 4 |
| Forzar `device: cpu` con el wheel GPU reventaba en cada inferencia | bug del ejecutor PIR con oneDNN en Windows: `ConvertPirAttribute2RuntimeAttribute not support` | `ocr_run.py` pasa `enable_mkldnn=False` cuando `device == "cpu"` |

Ese último es el que importa para la clase: **sin él, el carril B no existe.**

Tiempos medidos en esta máquina, sobre una página lógica a 425 DPI:

| Condición | s/página |
|---|---|
| GPU, nivel `medium` | ~7.8 |
| CPU, nivel `tiny` | ~68 |

Nótese que el CPU corre un modelo **más chico** y aun así tarda nueve veces más. Para
el carril B en clase conviene además bajar el DPI, o el bloque 5 no entra en el tiempo.

---

### Paso 4 — PaddleOCR y primera inferencia (minutos 26–34)

```powershell
python -m pip install "paddleocr>=3.7" pypdfium2 pypdf pyyaml pillow pandas
```

PP-OCRv6 requiere PaddleOCR 3.7.0 o posterior. La primera ejecución descarga los pesos
(decenas de MB, no gigabytes: ese es justamente el argumento del caso).

Primera prueba, sobre una página ya rasterizada:

```powershell
python -m src.doctor
```

El chequeo 6 del doctor hace la inferencia real y vigila la VRAM. Ese es el único que
prueba algo.

---

### Paso 5 — Benchmark (minutos 34–45)

**Cerrar Brave antes de medir.** En el `nvidia-smi` de esta máquina el navegador ya ocupa
141 MiB de VRAM y compite por el GPU. Una medición con el navegador abierto no es
comparable con otra sin él.

```powershell
python -m src.bench
```

En una ventana aparte, para verlo en vivo:

```powershell
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv -l 1
```

Esa ventana lateral es, además, la mejor diapositiva de la clase: la VRAM subiendo cuando
arranca el OCR en GPU y quedándose plana cuando corre en CPU.

---

### Paso 6 — Colab (minutos 45–55)

En Colab, con entorno de ejecución T4:

```python
!python -m pip install paddlepaddle-gpu==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
!python -m pip install "paddleocr>=3.7" pypdfium2 pypdf
```

Correr el mismo `doctor` y el mismo OCR. El valor pedagógico es que **es el mismo código**:
cambia la máquina, no el programa.

---

### Paso 7 — Congelar (minutos 55–60)

```powershell
python -m pip freeze > requirements.lock.txt
```

Desde este momento, ninguna instalación va sin versión fija. La clase es el martes y un
release publicado el lunes no puede romperla.

Verificación final, los cinco puntos:

```powershell
python --version                      # 3.12.x
python -m pip list | findstr paddle   # solo paddlepaddle-gpu, una línea
python -m src.doctor                  # seis líneas, todas OK
python -m src.triaje                  # 57 páginas, 0 con texto, 57 imagen
python -m src.bench                   # tabla CPU vs GPU
```

---

## Preparación de los días previos

| Día | Tarea | Por qué |
|---|---|---|
| T-7 (14 oct) | Congelar versiones; subir el repo | Base estable |
| T-6 (15 oct) | Subir los pesos de PP-OCRv6 a un Drive del curso | 25 estudiantes descargando a la vez en el salón no va a funcionar |
| T-5 (16 oct) | Probar el repo en una máquina sin GPU | Verificar que el doctor distingue bien los dos casos |
| T-4 (17 oct) | Grabar video de 3 minutos de la demo GPU | Plan B si la laptop falla en vivo |
| T-3 (18 oct) | Preparar la falla 3 (modelo de visión) con el modelo ya descargado | Nunca descargar gigabytes en clase |
| T-2 (19 oct) | Ensayo completo cronometrado | Siempre sobra o falta 20 minutos |
| T-1 (20 oct) | Subir material al repositorio del curso | La teoría es el martes 20; la práctica el miércoles 21 |

**Pregunta abierta que cambia el plan del salón:** si el internet del aula no aguanta 25
descargas simultáneas, Colab deja de ser la red de seguridad y hay que llevar los pesos y
el PDF en USB. Conviene confirmarlo antes del lunes.
