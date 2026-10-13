# CLAUDE.md — Reglas del repositorio OCR (clase UP + piloto Zaragoza)

Este archivo lo lee Claude Code automáticamente. Son restricciones, no sugerencias.

---

## 1. Contexto del proyecto

Dos entregables comparten este repositorio:

1. **Clase práctica UP** — Semana 10 del curso Data Science con Python (Universidad del
   Pacífico). Práctica del **miércoles 21 de octubre de 2026, 7:30–9:20 am** (110 minutos).
   Tema del sílabo: *Document AI y voz: OCR, extracción estructurada y ASR*.
   Jefe de práctica: Paul Melo Ramos. Profesor del curso: Alexander Quispe Rojas.
2. **Piloto Zaragoza** — lectura automatizada de bases de licitación escaneadas. Esta
   carpeta es la versión reducida y reproducible; el proyecto grande vive aparte.

El público son estudiantes de Economía, no de Ingeniería de Sistemas. El código se lee en
clase en voz alta. Si una línea necesita explicación de más de una frase, está mal escrita.

---

## 2. Entorno real de la máquina objetivo

| Dato | Valor |
|---|---|
| Equipo | LAPTOP-ADFLMMCK |
| CPU | Intel i5-12450HX, 8 núcleos (4P + 4E) |
| RAM | 16 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, **6 GB VRAM**, arquitectura Ampere (**sm_86**) |
| Driver NVIDIA | 581.86 (reporta CUDA 13.0 como máximo soportado) |
| SO | Windows 11 Home Single Language 25H2 |
| Python del sistema | **3.14.7 — NO SIRVE para PaddlePaddle** |

**Consecuencia obligatoria:** todo corre dentro de `.venv` creado con **Python 3.12**.
PaddlePaddle soporta 3.9 a 3.13 únicamente. Nunca instalar nada con el Python 3.14 del
sistema salvo la herramienta `uv`.

---

## 3. Prohibiciones duras

1. **Nunca** instalar `paddlepaddle` y `paddlepaddle-gpu` en el mismo entorno. Si el código
   detecta ambos, debe abortar con un mensaje explícito. Conviven sin error y el resultado
   es que todo corre en CPU 40 veces más lento sin avisar.
2. **Nunca** usar `use_gpu=True`. Ese parámetro es de PaddleOCR 2.x. En 3.x el parámetro es
   `device="gpu"`. No mezclar documentación de versiones.
3. **Nunca** `pip install` sin `==`. Todas las versiones van fijadas. Una clase no se rompe
   por un release publicado el martes.
4. **Nunca** instalar CUDA Toolkit ni cuDNN a mano. El wheel de `paddlepaddle-gpu` los trae
   como dependencias pip. Solo hace falta el driver NVIDIA, que ya está.
5. **Nunca** extraer las imágenes embebidas del PDF para hacer OCR. Ver sección 5.
6. **Nunca** valores hardcodeados: rutas, DPI, modelo, device, umbrales y recortes viven en
   `config.yaml`.
7. **Nunca** escribir sobre los archivos de `data/raw/`. Son el original.
8. **Nunca** subir al repositorio: `.venv/`, pesos de modelos, PDFs de más de 10 MB,
   `data/processed/`, `logs/`. Van en `.gitignore`.

---

## 4. Convenciones de código

- Español en comentarios, mensajes de log y docstrings. Nombres de función en español
  también (`contar_paginas_imagen`, no `count_image_pages`). Los estudiantes leen español;
  el código del curso es material didáctico.
- Cada módulo de `src/` es ejecutable por sí solo (`python -m src.doctor`) y además
  importable sin efectos secundarios.
- Logging con el módulo `logging`, nunca `print()` para diagnóstico. Un `print()` solo para
  la salida que el usuario debe leer.
- **Siempre** `flush=True` o `logging` con handler sin buffer en procesos largos. Este bug
  ya costó horas en el proyecto original: Python bufferiza stdout cuando otro programa lo
  captura, y el detector de progreso nunca veía nada. El progreso se escribe a un archivo
  en `logs/`, y lo que vigila el progreso lee ese archivo, no la consola.
- Guardado incremental: un proceso de 40 páginas que se corta en la 38 no puede perder las
  37 anteriores. Cada página se escribe a disco apenas termina.
- Todo paso costoso cachea en disco y detecta lo ya hecho antes de recomputar.

---

## 5. Decisiones técnicas ya tomadas (no reabrir sin avisar)

### 5.1 Rasterizar la página, no extraer sus imágenes

El PDF de prueba tiene entre 9 y 63 imágenes embebidas **por página**: el escáner guardó
cada hoja partida en mosaicos. Extraer imágenes devuelve decenas de fragmentos inservibles.
La única vía correcta es **renderizar la página completa a un bitmap** con un DPI elegido.

> Analogía para clase: el PDF no guarda una foto de la hoja, guarda el rompecabezas
> desarmado. Si pides "las imágenes", te dan las piezas sueltas. Hay que pedir la foto del
> rompecabezas armado, que es lo que hace el renderizador.

### 5.2 `pypdfium2` para rasterizar, `pypdf` para triaje

No usar `pdf2image`: exige instalar Poppler aparte en Windows y rompe la clase. No usar
PyMuPDF por defecto: su licencia AGPL complica que un estudiante reutilice el código.
`pypdfium2` es pip puro, sin binarios del sistema, licencia permisiva.

### 5.3 El PDF de prueba viene a dos páginas por hoja y girado 90°

Verificado sobre `BASE-ESTANDAR-ILO-SEACE-OCR.pdf`: 57 hojas físicas A4 que contienen
aproximadamente 114 páginas lógicas, dos por hoja, y el contenido está rotado 90°. Además
hay firmas manuscritas en lapicero azul atravesando el texto.

El pipeline debe, en este orden: rasterizar → partir la hoja en dos mitades → corregir
orientación → OCR. Partir después de OCR no sirve: el modelo ya mezcló las dos páginas.

Verificado sobre el documento real, no asumido:

- **La rotación correcta es 270 grados**, no 90. Con 90 la página sale cabeza abajo.
- **La mitad inferior es la página de número menor.** Orden de lectura: inferior, luego
  superior.
- **El nombre de la entidad no está en la carátula.** Vive en el encabezado de la hoja
  física, que pertenece a la otra página lógica. Cualquier extracción de metadatos debe
  procesar **las dos mitades** de la hoja, no solo una.
- El encabezado está **cortado en el escaneo**: donde dice PROVINCIAL el OCR lee
  ROVINCIAL. Las expresiones regulares deben tolerarlo o fallarán.
- El documento original contiene la errata **"ASENTAMIENTO HUAMANO"**. Es de la
  Municipalidad, no del OCR. El texto de referencia la conserva tal cual.

Verificado al correr el pipeline completo el 13 de octubre de 2026. Corrige y amplía lo
anterior:

- **La rotación 270 se interpreta en sentido antihorario** (la convención de PIL).
  `imagen.rotate(270, expand=True)` deja la carátula derecha; con el signo invertido
  sale cabeza abajo.
- **El encabezado está peor de lo descrito.** El OCR no lee "MUNICIPALIDAD ROVINCIAL":
  lee dos líneas, `MUNICIPALIDAL` y `<OVINCIALDEILO`. La D final se leyó como L, la P y
  la R se perdieron, y los espacios desaparecieron. Un patrón que exija la palabra
  PROVINCIAL completa no coincide nunca.
- **El número de procedimiento no lleva "DE" en el encabezado**: dice "LICITACIÓN
  PÚBLICA OBRAS N° 05-2026-C-MPI". En la carátula interna sí lleva el "DE".
- **Los cuatro campos no están en una sola página.** La entidad vive en el encabezado
  de la hoja 1 (página lógica 2); el objeto, el número y el departamento están en la
  carátula interna, que es la **hoja 2, página lógica 3**. `hojas_metadatos` es `[1, 2]`.
- **El objeto de contratación lo devuelve el OCR partido en una palabra por línea**,
  porque en el original es un cartel grande. El patrón tiene que correr sobre saltos de
  línea (`re.DOTALL`) y conviene anclarlo al final en "DEPARTAMENTO DE \<nombre\>".
- **PaddleX instala handlers en el logger raíz.** Sin `logger.propagate = False` cada
  línea de log sale tres veces y la salida es ilegible en clase.
- **Aviso benigno de cuDNN:** el wheel está compilado contra cuDNN 9.9 y el que trae es
  9.5. Paddle imprime un `WARNING` al iniciar; la GPU funciona igual, verificado con el
  chequeo 6 del doctor (+350 MiB de VRAM). No tocar nada: ver la prohibición 4.

### 5.4 DPI: el parámetro que nadie ajusta y que más importa

Como cada página lógica ocupa media hoja A4, está reducida a un factor lineal de ~0.707.
Para que la página lógica quede a 300 DPI efectivos, la hoja física debe renderizarse a
**~425 DPI**. Por eso `dpi_fisico` es un parámetro de `config.yaml`, no una constante.

### 5.5 Índice de instalación de PaddlePaddle

Con driver 581.86 sobre sm_86 sirven cu118, cu126, cu129 y cu130. Se fija **cu126** por ser
el más probado. Si falla, el fallback documentado es cu129.

---

## 6. Criterios de aceptación transversales

Ningún módulo se da por terminado si no cumple:

- Corre dos veces seguidas y la segunda no recomputa lo ya cacheado.
- Corre en una máquina sin GPU sin lanzar excepción (degrada a CPU, pero **lo dice en voz
  alta** en el log; el silencio es el enemigo de este repositorio).
- Sus parámetros salen de `config.yaml`.
- Imprime progreso. Un proceso silencioso de 10 minutos es un proceso roto.

---

## 7. Qué hacer si algo falla

1. Leer el log antes de cambiar código. El proyecto original diagnosticó su peor bug
   leyendo tres líneas de log (`offloaded 0/37 layers to GPU`), no adivinando.
2. Si falla la instalación de Paddle, no intentar rutas creativas (compilar, wheels de
   terceros, Docker). En sm_86 el camino oficial funciona; si no funciona, el problema es
   el entorno, no el paquete.
3. Si un paso tarda más de lo previsto en `PLAN_60MIN.md`, aplicar el corte que ese
   documento indica y seguir. La clase es el martes; un entorno perfecto el miércoles por
   la tarde no sirve de nada.

---

## 8. Documentos de referencia en esta carpeta

| Archivo | Qué contiene |
|---|---|
| `DISEÑO.md` | Arquitectura, especificación archivo por archivo, criterios de aceptación |
| `PLAN_60MIN.md` | Runbook de instalación con comandos exactos y puntos de corte |
| `GUION_CLASE_110MIN.md` | Guion de la sesión del 21 de octubre, bloque por bloque |

Leer `DISEÑO.md` antes de crear cualquier archivo de `src/`.
