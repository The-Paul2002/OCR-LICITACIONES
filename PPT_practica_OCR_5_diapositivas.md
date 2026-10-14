# Práctica OCR: de PDF escaneado a datos

Guion para elaborar un PPT de 5 diapositivas. Base: la presentación de Alexander Quispe
("De PDFs escaneados a informes legales con IA") y el notebook
`01_ocr_licitaciones_clase.ipynb`.

Duración de la práctica: 110 minutos (miércoles 21 de octubre, 7:30–9:20 am).

---

## Diapositiva 1 — Estructura de la práctica

**Título:** Hoy construimos un OCR que corre en tu máquina

**Contenido (cronograma de bloques):**

| Bloque | Qué hacemos | Min |
|---|---|---|
| 0 | Preparar el entorno y verificar la GPU (doctor) | 15 |
| 1 | Triaje: ¿qué páginas son imagen? | 10 |
| 2 | Preparar la imagen: rasterizar, partir, enderezar | 15 |
| 3 | Primer OCR: texto, cajas y confianza | 15 |
| 4 | El momento GPU: CPU contra GPU, medido | 20 |
| 5 | De texto a datos: 4 campos, reglas contra modelo | 20 |
| 6 | Laboratorio de fallas | 10 |
| Cierre | Entregable y lecciones | 5 |

**Idea que debe quedar:**

> Conocer tu hardware decide qué modelo puedes correr. Y arreglar la imagen rinde más
> que traer un modelo más grande.

**Notas para el orador:**

- Los tres carriles corren el mismo código: Colab (GPU T4), CPU local y GPU local.
- Nadie termina sin haber hecho un OCR. Si falla la instalación, se pasa a Colab.
- Mencionar el entregable: un CSV con cuatro campos, y el tiempo por página que tomó
  en su carril. Esa segunda parte obliga a medir.

---

## Diapositiva 2 — El problema real

**Título:** Un PDF escaneado que no se puede copiar

**Contenido:**

- Documento: Licitación Pública de Obras N° 05-2026-C-MPI, Municipalidad Provincial de
  Ilo (Moquegua). Documento público de SEACE.
- 57 hojas físicas, unas 114 páginas lógicas.
- Cero caracteres de texto seleccionable: es una foto.
- Cuatro problemas a la vez:

| Problema | Consecuencia |
|---|---|
| Escaneado | Hay que hacer OCR |
| Dos páginas por hoja | Hay que partir la hoja |
| Girado 270 grados | Hay que enderezar antes del OCR |
| Firmas en lapicero azul | Ruido sobre el texto |

**Analogía para el público:**

> Es como un libro que alguien fotocopió, pegó dos páginas en una hoja, la giró de lado
> y le escribió encima. Lo lees igual, pero necesitas primero ordenarlo.

**Notas para el orador:**

- Mostrar el intento de seleccionar el texto con el mouse. No se puede.
- Contar que una empresa tiene plazo para presentar observaciones sobre estas bases.
  Por eso el tiempo importa.

---

## Diapositiva 3 — Triaje y preparación de la imagen

**Título:** Primero decidir, después leer

**Contenido, parte A — triaje (regla de oro):**

- PDF con capa de texto: se extrae gratis e instantáneo.
- PDF escaneado: requiere OCR.
- **Usar OCR solo donde hay imagen.**
- Resultado sobre el documento: 0 hojas con texto, 57 con imagen.

**Contenido, parte B — preparación (en este orden):**

1. Rasterizar la hoja completa a 425 DPI. No extraer las imágenes embebidas: el escáner
   las partió en mosaicos.
2. Partir la hoja en dos páginas lógicas.
3. Enderezar con 270 grados. Con 90 la página sale cabeza abajo.

**Por qué 425 DPI:** cada página ocupa media hoja, así que queda reducida. Para que
quede cerca de 300 DPI efectivos, la hoja se renderiza a 425.

**Analogía para el público:**

> Extraer las imágenes de un escaneo es como pedir las piezas sueltas de un rompecabezas.
> Rasterizar es pedir la foto del rompecabezas armado.

**Notas para el orador:**

- Mostrar las cuatro rotaciones en una grilla y que el alumno elija mirando.
- Este es el bloque donde se gana la calidad. Recordar la cifra del dato publicado:
  en fotos de documentos, el mejor modelo cae de 91.9 a 72.2 puntos.

---

## Diapositiva 4 — El momento GPU

**Título:** La misma página, dos tiempos

**Contenido:**

- Primero, el doctor de GPU: seis chequeos. Los cinco primeros pueden dar verde y aun
  así correr en CPU. Solo el sexto, la VRAM medida, no se puede falsificar.
- Benchmark: descartar páginas de calentamiento, medir la mediana y vigilar la VRAM.
- Referencia del caso original (GTX 1660 Ti de 6 GB):

| Modo | Una página densa | Rango de 42 páginas |
|---|---|---|
| CPU | unos 45 s | unos 32 min |
| GPU | unos 1 s | unos 1 min |

**El fallback mudo:**

> PaddlePaddle no lanza error cuando la GPU falla. Cae a CPU en silencio y sigue
> funcionando. Tienes una bicicleta y un auto en la cochera: si la llave del auto no
> está, el chofer te lleva en bicicleta sin decirte nada.

**Advertencia para decir en voz alta:**

> Parte de ese 40x es GPU buena y parte es CPU mal configurada. Prometer 40x sin matices
> es vender humo.

**Notas para el orador:**

- Pantalla dividida: consola a la izquierda, `nvidia-smi` a la derecha.
- Mostrar a propósito el caso sin el parámetro `device`: todo funciona, la VRAM no
  se mueve.
- Recordar: se usa `device="gpu"`. El parámetro `use_gpu` es de versiones anteriores.

---

## Diapositiva 5 — De texto a datos, y cierre

**Título:** El modelo propone, la regla verifica

**Contenido, parte A — extracción de cuatro campos:**

| Campo | Valor en el documento |
|---|---|
| Entidad convocante | Municipalidad Provincial de Ilo |
| Número de procedimiento | Licitación Pública de Obras N° 05-2026-C-MPI |
| Objeto | Ampliación del servicio de movilidad urbana (PROMUVI IV) |
| Departamento | Moquegua |

**Contenido, parte B — dos vías y una regla:**

- Vía A, reglas (expresiones regulares): gratis, pero se rompe con una errata del OCR.
  En el encabezado, el OCR lee "ROVINCIAL" en vez de "PROVINCIAL".
- Vía B, modelo de lenguaje: robusto ante erratas, pero puede "corregir" el texto.
- **Regla de verificación:** todo valor debe existir literalmente en el texto del OCR.
  Si no existe, se marca SIN VERIFICAR.

**Lo que pasó en la prueba con el modelo:** corrigió "ROVINCIAL" a "PROVINCIAL" y acertó,
pero la regla lo marcó como SIN VERIFICAR. Un modelo que corrige y acierta es tan
peligroso como uno que inventa, porque la próxima vez puede fallar.

**Seis lecciones transferibles (cierre):**

1. Define el problema antes de elegir la herramienta.
2. Conoce tus límites de hardware: deciden qué es posible.
3. La herramienta del tamaño del problema.
4. Híbrido: lo barato y masivo en local, el modelo caro solo donde agrega valor.
5. Itera y diagnostica: los fracasos enseñan.
6. Humano al centro: la IA propone, la persona decide.

**Dato para cerrar:** en el ranking OmniDocBench v1.6 de 2026, los tres primeros son
modelos de 0.9 a 1.2 mil millones de parámetros (PaddleOCR-VL-1.6 con 96.34). Un modelo
de 235 mil millones obtiene 89.78. El especializado le gana al generalista en su terreno.

**Notas para el orador:**

- Terminar con el entregable: el CSV y la respuesta a "¿en qué carril corriste y cuántos
  segundos por página te tomó?".

---

## Fuentes para la diapositiva de cierre y el guion

- Presentación de Alexander Quispe y Abigail Quispe, "De PDFs escaneados a informes
  legales con IA", Universidad del Pacífico, 1 de junio de 2026 (casos de GTX 1660 Ti,
  VRAM, 40x, fallback y lecciones).
- Documento de práctica: Licitación Pública de Obras N° 05-2026-C-MPI, Municipalidad
  Provincial de Ilo, Bases Estándar, SEACE.
- Instalación de PaddlePaddle y requisitos de Python y driver:
  https://www.paddlepaddle.org.cn/documentation/docs/en/install/index_en.html
- PaddleOCR-VL NVIDIA Blackwell y tutorial de instalación:
  http://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-NVIDIA-Blackwell.html
- PP-OCRv6, niveles y precisiones: https://huggingface.co/blog/PaddlePaddle/pp-ocrv6
- Ranking OmniDocBench v1.6 (comparativa de modelos OCR 2026):
  https://www.docsumo.com/blog/best-ocr-models
