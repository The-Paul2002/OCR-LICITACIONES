# DISEÑO — Laboratorio de OCR: clase UP + piloto Zaragoza

Documento de diseño. Define qué se construye, por qué, y cómo se sabe que está bien.
Claude Code genera los archivos a partir de aquí.

Fecha de diseño: 13 de octubre de 2026
Clase objetivo: miércoles 21 de octubre de 2026, 7:30–9:20 am

---

## 0. Resumen en una página

Se construye un laboratorio de OCR que corre en tres modos (Colab, CPU local, GPU local) y
resuelve un caso real: leer las bases escaneadas de una licitación pública peruana y
extraer datos estructurados de ellas.

El hilo conductor pedagógico es una sola idea, repetida en tres escalas:

> **Conocer tu hardware decide qué modelo puedes correr, y preprocesar bien la imagen rinde
> más que traer un modelo más grande.**

La clase no enseña comandos. Enseña a tomar decisiones técnicas y a diagnosticar leyendo
logs.

---

## 1. Hallazgos que fundamentan el diseño

Estos no son supuestos. Se verificaron sobre los archivos reales antes de diseñar.

### 1.1 El documento de prueba

`BASE-ESTANDAR-ILO-SEACE-OCR.pdf` — Bases Estándar, Licitación Pública de Obras
N° 05-2026-C-MPI, Municipalidad Provincial de Ilo (Moquegua). Documento público de SEACE.

| Propiedad medida | Valor | Por qué importa |
|---|---|---|
| Hojas físicas | 57 | Tamaño manejable para clase |
| Caracteres en la capa de texto | **0** | 100% escaneado: el triaje marcará todas las páginas |
| Imágenes embebidas por hoja | 9 a 63 | El escáner guardó mosaicos; hay que rasterizar, no extraer |
| Disposición | **2 páginas lógicas por hoja** | ~114 páginas lógicas; hay que partir la hoja |
| Orientación | **Rotado 90°** | Es exactamente el bug de las tablas apaisadas del caso original |
| Ruido | Firmas manuscritas en azul sobre el texto | Caso realista de escaneo degradado |

Este documento es, por accidente feliz, el mejor caso de enseñanza posible: contiene de
golpe los cuatro problemas que un pipeline de OCR debe resolver.

### 1.2 El entorno

- **Python 3.14.7 instalado — incompatible.** PaddlePaddle soporta 3.9 a 3.13. Este es el
  bloqueador número uno y se resuelve con un entorno virtual de Python 3.12.
- **RTX 3050 6 GB, Ampere sm_86, driver 581.86.** Arquitectura dentro de la lista estándar
  de los wheels oficiales. No aplica nada del procedimiento especial para RTX serie 50.
- **No hace falta instalar CUDA Toolkit.** El wheel lo trae; solo se exige el driver.
- **6 GB de VRAM es el mismo presupuesto del caso original** (GTX 1660 Ti). El fracaso del
  LLM de visión es reproducible aquí con el mismo resultado.

### 1.3 Detalle para una diapositiva de dos minutos

La RTX 3050 tiene Tensor Cores; la GTX 1660 Ti del caso original no los tiene. Misma VRAM,
distinto rendimiento en media precisión. Sirve para enseñar que "6 GB" no describe una GPU.

---

## 2. Arquitectura

```
                    data/raw/*.pdf
                          |
                     [ triaje.py ]  ¿esta página tiene capa de texto?
                       /        \
              sí (texto)         no (imagen)
                 |                    |
          extracción directa    [ preparar.py ]
                 |               rasterizar a DPI
                 |               partir hoja 2-up
                 |               corregir orientación
                 |                    |
                 |               [ ocr_run.py ]
                 |               PP-OCRv6 en CPU o GPU
                 \                   /
                  \                 /
                   texto + cajas + confianza
                          |
                    [ extraer.py ]
                   4 campos -> JSON / CSV
                          |
                   data/outputs/
```

`bench.py` y `doctor.py` son transversales: no participan del pipeline, lo miden y lo
diagnostican.

> Analogía para clase: el triaje es la enfermera que decide quién pasa a emergencia. No
> todos los pacientes necesitan cirugía. OCR es la cirugía: cara y lenta. Solo se opera a
> quien lo necesita.

---

## 3. Estructura de archivos a generar

```
C:\Users\LENOVO\Documents\PAUL\UP\OCR\
├── CLAUDE.md                     (ya existe)
├── DISEÑO.md                     (ya existe)
├── PLAN_60MIN.md                 (ya existe)
├── GUION_CLASE_110MIN.md         (ya existe)
├── README.md                     ← generar
├── config.yaml                   ← generar
├── requirements.lock.txt         ← generar tras instalar
├── .gitignore                    ← generar
├── src/
│   ├── __init__.py
│   ├── doctor.py                 ← generar
│   ├── triaje.py                 ← generar
│   ├── preparar.py               ← generar
│   ├── ocr_run.py                ← generar
│   ├── extraer.py                ← generar
│   └── bench.py                  ← generar
├── notebooks/
│   ├── 01_ocr_licitaciones_clase.ipynb   (YA EXISTE — es el notebook de la práctica)
│   └── 00_colab_clase.ipynb      ← opcional; el anterior ya cubre Colab
├── data/
│   ├── raw/                      BASE-ESTANDAR-ILO-SEACE-OCR.pdf
│   ├── processed/                PNG por página, texto crudo
│   └── outputs/                  CSV, JSON, tablas del benchmark
├── fallas/
│   └── README.md                 ← generar (guion del laboratorio de fallas)
└── logs/
```

---

## 4. Especificación módulo por módulo

### 4.1 `config.yaml`

Único lugar con valores ajustables. Estructura mínima:

```yaml
rutas:
  pdf_entrada: data/raw/BASE-ESTANDAR-ILO-SEACE-OCR.pdf
  procesados: data/processed
  salidas: data/outputs
  logs: logs

render:
  dpi_fisico: 425          # hoja física; 425 deja la página lógica cerca de 300 DPI
  dos_por_pagina: true     # partir cada hoja en dos páginas lógicas
  eje_corte: horizontal    # las dos páginas están una sobre otra
  rotacion: auto           # auto | 0 | 90 | 180 | 270

ocr:
  motor: paddleocr
  version_modelo: PP-OCRv6
  nivel: medium            # tiny | small | medium
  idioma: es
  device: gpu              # gpu | cpu   (PaddleOCR 3.x: device, NO use_gpu)
  usar_clasificador_orientacion: true
  usar_desenrollado: false
  umbral_confianza: 0.80

benchmark:
  paginas_calentamiento: 2
  paginas_medidas: 10
  condiciones_dpi: [150, 300, 425]
  condiciones_device: [cpu, gpu]
  niveles: [tiny, small, medium]

extraccion:
  campos:
    - entidad_convocante
    - numero_procedimiento
    - objeto_contratacion
    - departamento
```

**Criterio de aceptación:** cambiar `device: gpu` a `device: cpu` en el YAML debe cambiar
dónde corre el OCR, sin tocar una línea de Python.

---

### 4.2 `src/doctor.py` — el semáforo de GPU

El módulo más importante del repositorio y el primero que se escribe. No hace OCR: responde
una sola pregunta, *¿la GPU está realmente disponible y en uso?*

Existe porque PaddlePaddle **no lanza error cuando la GPU falla**: cae a CPU en silencio y
sigue funcionando. El usuario cree que tiene aceleración y no la tiene.

> Analogía para clase: tienes bicicleta y auto. Le dices al chofer "llévame". Si la llave
> del auto no está colgada, no te avisa: te lleva en bicicleta. Llegas tarde y nunca te
> enteras de que existía el auto.

Imprime seis líneas, cada una con estado OK o FALLA y una explicación de una línea:

| # | Chequeo | Cómo | Resultado esperado |
|---|---|---|---|
| 1 | Driver | ejecutar `nvidia-smi`, parsear nombre de GPU y versión de driver | `RTX 3050`, driver `581.86` |
| 2 | Wheel único | listar paquetes instalados y verificar que exista `paddlepaddle-gpu` y **no** `paddlepaddle` | solo el GPU |
| 3 | Compilación CUDA | `paddle.is_compiled_with_cuda()` | `True` |
| 4 | Dispositivo activo | `paddle.device.get_device()` | `gpu:0` |
| 5 | Prueba del framework | `paddle.utils.run_check()` | verificación exitosa sobre GPU |
| 6 | **Prueba real** | una inferencia OCR breve mientras se muestrea `nvidia-smi` | la VRAM sube varios cientos de MB sobre la línea base |

El chequeo 6 es el único que no se puede falsificar. Los cinco anteriores pueden dar verde
y aun así el objeto `PaddleOCR` correr en CPU, porque falta el parámetro `device`.

**Detalle del entorno real:** la línea base de VRAM no es cero. El navegador Brave ya ocupa
~141 MiB en esta máquina. `doctor.py` debe medir la línea base antes de cargar el modelo y
reportar el delta, no el absoluto.

**Criterios de aceptación:**
- Corre en menos de 15 segundos.
- En una máquina sin GPU imprime seis líneas coherentes y termina con código 0, señalando
  que el modo disponible es CPU.
- Si detecta los dos wheels instalados, aborta con un mensaje que nombra el problema y el
  comando de desinstalación.

---

### 4.3 `src/triaje.py` — la regla de oro

Clasifica cada página del PDF en `texto` o `imagen`, y produce un reporte.

Regla: una página se considera `texto` si su capa de texto supera un umbral de caracteres
(por defecto 50); en caso contrario es `imagen` y necesita OCR.

Salida: `data/outputs/triaje.csv` con columnas `pagina, caracteres, imagenes_embebidas,
clase` y un resumen impreso del tipo *"57 páginas: 0 con texto, 57 imagen → 100% requiere
OCR"*.

**Valor pedagógico:** sobre el PDF real da un resultado extremo y limpio (0 y 57). Para que
los estudiantes vean el otro caso, el notebook incluye además un PDF mixto generado al
vuelo (una página de texto nativo y una rasterizada).

**Criterio de aceptación:** sobre un PDF mixto preparado a propósito, clasifica
correctamente ambas clases.

---

### 4.4 `src/preparar.py` — donde se gana la pelea

Convierte hojas de PDF en imágenes listas para OCR. Tres pasos en este orden:

1. **Rasterizar** con `pypdfium2` al `dpi_fisico` de la configuración.
2. **Partir** la hoja en dos páginas lógicas si `dos_por_pagina: true`. El corte es por la
   mitad del eje indicado. Debe guardar ambas mitades con nombres que preserven el orden
   lógico (`h057_p114.png`), porque el orden de lectura importa para el informe.
3. **Corregir orientación**. Con `rotacion: auto` se delega al clasificador de orientación
   de PaddleOCR; con un valor fijo se rota con la librería de imagen antes del OCR.

Guarda en `data/processed/` y **no recomputa** lo que ya existe.

> Analogía para clase: es la diferencia entre darle al lector un libro abierto y derecho, o
> darle una fotocopia doble, chueca y al revés. El lector es el mismo. El resultado no.

**Criterio de aceptación:** la salida sobre la hoja física 3 son dos PNG, cada uno con una
sola página lógica, derecha y legible a ojo.

---

### 4.5 `src/ocr_run.py` — la inferencia

Envuelve PaddleOCR. Una función principal que recibe una ruta de imagen y devuelve una
lista de resultados con `texto`, `caja` (4 puntos) y `confianza`.

Puntos no negociables:
- El objeto `PaddleOCR` se construye **una sola vez** y se reutiliza. Reconstruirlo por
  página recarga el modelo y arruina cualquier medición.
- El parámetro es `device=config.ocr.device`. Nunca `use_gpu`.
- Al construirlo registra en el log qué dispositivo quedó activo, leído del propio Paddle,
  no de la configuración. Lo que importa es dónde corrió, no dónde se pidió correr.
- Escribe el resultado de cada página a disco apenas termina.

**Criterio de aceptación:** el mismo PNG procesado con `device: cpu` y con `device: gpu`
produce el mismo texto. Solo cambia el tiempo.

---

### 4.6 `src/bench.py` — medir sin autoengañarse

> Analogía para clase: cronometrar cuánto tarda tu mamá en servir la sopa, pero arrancar el
> cronómetro cuando todavía está prendiendo la cocina. El primer plato siempre parece
> lentísimo. La primera inferencia incluye cargar el modelo a la VRAM e inicializar CUDA.

Protocolo obligatorio:
1. Descartar las primeras `paginas_calentamiento` páginas.
2. Medir `paginas_medidas` páginas, el mismo conjunto en todas las condiciones.
3. Reportar **mediana** de segundos por página, no promedio: un pico aislado no debe mover
   la conclusión.
4. Muestrear VRAM con `nvidia-smi` en un hilo aparte y reportar el pico menos la línea base.
5. Reportar también **calidad**, no solo velocidad. Una configuración que acelera y empeora
   la transcripción no es una mejora.

Matriz de condiciones: `device` × `dpi` × `nivel de modelo`. Salida a
`data/outputs/benchmark.csv` y una tabla impresa en consola.

**Advertencia operativa:** cerrar el navegador antes de medir. Brave ocupa VRAM y compite
por el GPU.

**Criterio de aceptación:** dos corridas consecutivas del benchmark dan medianas dentro de
un 15% una de otra. Si no, la medición no es reproducible y el resultado no sirve.

---

### 4.7 `src/extraer.py` — de texto a datos

Toma el texto OCR de las primeras páginas lógicas y extrae cuatro campos a JSON y CSV:

| Campo | Valor esperado en el documento de prueba |
|---|---|
| `entidad_convocante` | Municipalidad Provincial de Ilo |
| `numero_procedimiento` | Licitación Pública de Obras N° 05-2026-C-MPI |
| `objeto_contratacion` | Ampliación del servicio de movilidad urbana en las vías locales del Sector II (PROMUVI IV), Asentamiento Humano Nuevo Ilo |
| `departamento` | Moquegua |

Dos implementaciones, y la comparación entre ambas **es** la lección:

- **Vía A — reglas.** Expresiones regulares sobre el texto OCR. Rápida, gratis, frágil ante
  una errata del OCR.
- **Vía B — modelo de lenguaje.** Se le entrega el texto OCR y se le pide JSON con esos
  cuatro campos. Robusta ante erratas, cuesta tokens.

**Regla de verificación heredada del proyecto original:** todo valor extraído debe existir
literalmente en el texto OCR. Si no existe, se marca `sin_verificar: true`. Un modelo que
"corrige" el número de licitación y acierta es tan peligroso como uno que lo inventa.

**Criterio de aceptación:** los cuatro campos salen correctos sobre el documento de prueba
por la vía B, y el reporte indica cuáles de ellos la vía A también acertó.

---

### 4.8 Notebooks

**`01_ocr_licitaciones_clase.ipynb` — ya construido y validado.** Es el material de la
práctica. 40 celdas (21 de explicación, 19 de código), **autocontenido**: no importa nada de
`src/`, así que funciona en Colab sin clonar el repositorio. Sigue los mismos siete bloques
del guion de clase, en el mismo orden, y lleva el doctor de GPU incorporado.

Tres decisiones de robustez que conviene no deshacer:

- **Cascada defensiva al construir `PaddleOCR`.** Prueba cuatro combinaciones de parámetros
  y se queda con la primera que funcione, informando cuál fue. La API de PaddleOCR cambia
  entre versiones menores de la 3.x y una clase no puede caerse por eso.
- **Lector de resultados tolerante.** Normaliza la salida a `(textos, confianzas, cajas)`
  aceptando las distintas formas que devuelven las versiones 3.x.
- **Plan B si no hay PDF.** Si el estudiante no tiene el documento, el notebook **genera**
  uno con los mismos cuatro defectos (escaneado, girado, dos por hoja). Nadie se queda sin
  clase por no haber descargado un archivo.

Funciona sin GPU: el doctor detecta el caso, fija `device="cpu"` y el notebook continúa
avisándolo en voz alta.

**`00_colab_clase.ipynb`** — ya no es necesario. El notebook anterior detecta Colab solo y
cubre el carril A. Queda como opcional.

---

### 4.9 `fallas/README.md` — el laboratorio de diagnóstico

Tres fallas sembradas. El estudiante recibe el síntoma y debe diagnosticar leyendo el log.
Esto es lo que separa una clase de un tutorial de YouTube.

| Falla | Cómo se siembra | Síntoma visible | Qué debe aprender |
|---|---|---|---|
| 1. Fallback mudo | instalar también `paddlepaddle` CPU | todo funciona, 40 veces más lento, VRAM no se mueve | la GPU falla sin avisar; medir, no suponer |
| 2. Página girada | desactivar la corrección de orientación | salida tipo `SOSORAOOS CS OORSOD` | preprocesar vence a modelo más grande |
| 3. Techo de hardware | renderizar a 900 DPI o cargar un modelo de visión | memoria agotada o lentitud extrema | la VRAM decide qué es posible |

La falla 2 sale gratis: el documento real ya viene girado. Basta con apagar el clasificador.

---

## 5. Lo que NO se construye hoy

Explícito para que Claude Code no se desvíe:

- Nada de servidor Node/Express. El proyecto grande lo tiene; la clase no lo necesita.
- Nada de generación LaTeX. El mini-proyecto termina en CSV y tabla en pantalla.
- Nada de agente legal que redacte observaciones. Se reemplaza por extracción de 4 campos.
- Nada de PaddleOCR.js en el navegador. Evaluado y descartado para esta fecha: es un paquete
  npm que exige construir y desplegar una aplicación, no una página lista para abrir. Queda
  como mejora posterior.
- Nada de PaddleOCR-VL ni modelos de visión en la ruta crítica. Entran solo como falla 3,
  controlada, y preparada con anticipación.

---

## 6. Reducción del proyecto real a escala de clase

| Proyecto Zaragoza real | Versión de clase |
|---|---|
| 110+ páginas de bases | 1 página lógica |
| Capítulos III y IV completos | una sola tabla o una carátula |
| Agente legal que redacta observaciones | extracción de 4 campos a JSON |
| Informe LaTeX membretado | un CSV y una tabla impresa |
| Aplicación Node + Express | un notebook |

La clave pedagógica: el estudiante recorre **los mismos cinco pasos** del proyecto real
—triaje, preparación, OCR, estructuración, entrega— en escala de juguete. Cuando en los
últimos cinco minutos se le muestre la aplicación real, reconoce cada pieza.

---

## 7. Ideas de extensión, ordenadas por relación esfuerzo/impacto

No entran en la clase. Son el siguiente paso del piloto Zaragoza y sirven como ideas de
innovación para los estudiantes.

### 7.1 Escalamiento por confianza
Correr el modelo barato en todas las páginas y reenviar al modelo caro **solo** las páginas
donde el barato dudó, usando el score de confianza por línea que PaddleOCR ya devuelve.

> Analogía: el profesor corrige rápido todos los exámenes y solo vuelve a revisar con calma
> los que quedaron entre 10 y 12. No pierde tiempo con los de 18 ni con los de 5.

Métrica a reportar: costo promedio por documento y porcentaje de páginas escaladas.

### 7.2 Detector automático de disposición 2-up
El documento de prueba obligó a descubrir a mano que venía a dos páginas por hoja. Un
detector que lo infiera (por simetría de la densidad de tinta o por la posición de los
números de página) ahorra ese descubrimiento en cada documento nuevo. No existe en ninguna
librería de las revisadas.

### 7.3 Trazabilidad visual de cada cita
Guardar, junto a cada dato extraído, su página y su caja de coordenadas. En la aplicación,
hacer clic en una observación resalta el recorte exacto de la imagen original. Convierte
"confía en la IA" en "verifica en dos segundos", y es la demostración más convincente
posible frente a un abogado.

### 7.4 Semáforo de legibilidad por página
Un mapa de calor de confianza por página que le dice al revisor humano qué páginas conviene
leer con sus propios ojos. Barato de implementar, alto valor percibido.

### 7.5 Diff de bases integradas
Tras la etapa de consultas, la Entidad publica las bases integradas. Hoy alguien las compara
a ojo contra las originales. OCR de ambas más un diff estructural responde en segundos qué
cambió y qué observación fue acogida. Valor de negocio directo, y ningún tutorial de OCR lo
enseña.

### 7.6 Suite de regresión de calidad
Las páginas anotadas a mano del benchmark no sirven solo una vez: son el conjunto de prueba
permanente. Cada vez que cambie una versión de PaddleOCR se corre y se ve si mejoró o
empeoró. Esto es exactamente lo que pide la semana 12 del sílabo sobre evaluación de
productos de datos.

---

## 8. Contexto de modelos, a octubre de 2026

Para la parte teórica de la clase. El hallazgo central contradice la intuición y vale como
diapositiva principal:

> Los mejores modelos de OCR abiertos hoy son modelos pequeños y dedicados a documentos, no
> VLM grandes. En OmniDocBench v1.6, PaddleOCR-VL-1.6 (0.9B) obtiene 96.34, MinerU2.5-Pro
> (1.2B) 95.75 y GLM-OCR (0.9B) 95.22, por encima de Qwen3-VL-235B con 89.78.

Es la validación empírica de la moraleja del caso original: la herramienta del tamaño del
problema, no un cañón para matar una mosca.

El segundo hallazgo, el más útil para licitaciones:

> En Wild-OmniDocBench, que usa **fotos** de las mismas páginas, PaddleOCR-VL cae de 91.93 a
> 72.19 y MinerU2.5 de 90.67 a 70.91. Veinte puntos de caída por calidad de imagen.

Traducción: invertir en preprocesamiento rinde más que cambiar de modelo. El documento de
prueba, con sus firmas encima y su rotación, lo demuestra en vivo.

Niveles de PP-OCRv6, útiles para enseñar el compromiso tamaño/precisión:

| Nivel | Parámetros | Hmean detección | Precisión reconocimiento |
|---|---|---|---|
| tiny | 1.5 M | 80.6% | 73.5% |
| small | 7.7 M | 84.1% | 81.3% |
| medium | 34.5 M | 86.2% | 83.2% |

---

## 9. Orden de construcción

Estricto. Cada paso depende del anterior.

1. `config.yaml`, `.gitignore`, `README.md`
2. `src/doctor.py` — nada se construye encima de una GPU no verificada
3. `src/triaje.py`
4. `src/preparar.py`
5. `src/ocr_run.py`
6. `src/bench.py`
7. `src/extraer.py`
8. `notebooks/01_mini_zaragoza.ipynb`
9. `notebooks/00_colab_clase.ipynb`
10. `fallas/README.md`
11. `requirements.lock.txt` congelado al final

---

## 10. Fuentes

- Guía de instalación de PaddlePaddle (versiones de Python soportadas; CUDA y cuDNN
  gestionados automáticamente; índices cu118/cu126/cu129/cu130) —
  https://www.paddlepaddle.org.cn/documentation/docs/en/install/index_en.html
- Instalación de PaddleOCR (requisitos de versión de driver por índice) —
  https://www.paddleocr.ai/latest/en/version3.x/installation.html
- Releases de PaddleOCR, v3.5.0 y v3.7.0 (PaddleOCR.js, PP-OCRv6) —
  https://github.com/PaddlePaddle/PaddleOCR/releases
- PP-OCRv6, niveles tiny/small/medium y precisiones —
  https://huggingface.co/blog/PaddlePaddle/pp-ocrv6
- Despliegue en navegador, PaddleOCR.js —
  http://www.paddleocr.ai/main/en/version3.x/deployment/browser.html
- Comparativa de modelos OCR 2026 con benchmarks publicados —
  https://www.docsumo.com/blog/best-ocr-models
- Mejores modelos OCR abiertos 2026 —
  https://roboflow.com/blog/best-open-source-ocr-models
