# GUION DE CLASE — OCR y extracción estructurada

Curso: Data Science con Python, Universidad del Pacífico, 2026-II
Semana 10 — *Document AI y voz: OCR, extracción estructurada y ASR*
Sesión de práctica: **miércoles 21 de octubre de 2026, 7:30–9:20 am** (110 minutos)
Jefe de práctica: Paul Melo Ramos

---

## Idea única de la sesión

Si al salir el estudiante recuerda una sola frase, que sea esta:

> **Conocer tu hardware decide qué modelo puedes correr. Y arreglar la imagen rinde más que
> traer un modelo más grande.**

Todo lo demás —comandos, parámetros, nombres de modelos— es consecuencia.

---

## Preparación antes de entrar al aula

- Proyector conectado y probado con pantalla dividida: a la izquierda la consola, a la
  derecha `nvidia-smi` actualizándose cada segundo.
- Brave cerrado. Ocupa VRAM y ensucia la demostración.
- Video de respaldo de 3 minutos de la demo GPU, por si la laptop falla.
- Pesos de PP-OCRv6 ya descargados en la laptop y en un Drive del curso.
- El PDF `BASE-ESTANDAR-ILO-SEACE-OCR.pdf` abierto en una ventana, sin hacer scroll
  todavía.

---

## Los tres carriles

El estudiante elige al entrar. El objetivo es que **nadie termine la clase sin haber hecho
un OCR**.

| Carril | Para quién | Qué corre | Riesgo |
|---|---|---|---|
| A — Colab | la mayoría | PP-OCRv6 sobre GPU T4 gratuita | depende del internet del aula |
| B — Local CPU | quien no tenga GPU | PP-OCRv6 nivel `tiny` o `small` | ninguno, solo lentitud |
| C — Local GPU | quien tenga tarjeta NVIDIA | PP-OCRv6 `medium` con `paddlepaddle-gpu` | alto, pero es el aprendizaje real |

Importante decirlo en voz alta al inicio: **los tres carriles corren el mismo código**. Lo
único que cambia es la máquina. Eso es, en sí mismo, la lección de la clase.

---

## Bloque 0 — El gancho (7:30–7:38, 8 min)

**Objetivo:** que el problema se entienda antes que la solución.

Proyectar el PDF de las bases de la Municipalidad Provincial de Ilo. Intentar seleccionar
el texto con el mouse. No se puede: no hay texto, hay una foto.

Luego mostrar dos cosas más del mismo documento, sin explicarlas todavía:

1. Está **girado 90°**. Hay que inclinar la cabeza para leerlo.
2. Cada hoja tiene **dos páginas** del documento original, una sobre la otra.
3. Hay **firmas en lapicero azul** atravesando el texto.

Frase de cierre del bloque:

> "Esto no es un ejemplo de laboratorio. Es un documento público real, descargado de SEACE,
> y una empresa tiene siete días hábiles para leer 114 páginas así y presentar
> observaciones. Eso es lo que vamos a automatizar hoy."

---

## Bloque 1 — Triaje: la regla de oro (7:38–7:48, 10 min)

**Objetivo:** que nunca hagan OCR de más.

Los dos tipos de PDF:

| PDF con capa de texto | PDF escaneado (imagen) |
|---|---|
| El texto es seleccionable | Es una foto: no hay texto |
| Se extrae gratis e instantáneo | Requiere OCR |

> **Regla de oro:** usar OCR **solo** en las páginas que son imagen. En el resto, extracción
> directa.

Mini-ejercicio de 4 minutos, en Colab:

```
python -m src.triaje
```

Sobre el documento de la clase el resultado es extremo y limpio: **57 páginas, 0 con texto,
57 imagen**. Cero por ciento aprovechable sin OCR.

Para que vean el otro caso, el notebook genera al vuelo un PDF mixto de dos páginas, una
nativa y una rasterizada, y el triaje las separa.

**Pregunta al salón (no retórica, esperar respuesta):** si de un documento de 500 páginas
solo 20 son escaneadas, ¿cuánto se ahorra haciendo triaje primero? Dejar que calculen.

---

## Bloque 2 — Instalación por carriles (7:48–8:06, 18 min)

**Objetivo:** que todos tengan algo corriendo. El profesor recorre el salón; los carriles
avanzan en paralelo.

Tres cosas que decir al grupo antes de soltarlos, porque son los tres errores que van a
cometer:

1. **No hay que instalar CUDA.** PaddlePaddle lo gestiona solo; basta el driver NVIDIA.
   Quien abra la página de descarga de NVIDIA acaba de perder media hora.
2. **La versión de Python importa.** PaddlePaddle soporta 3.9 a 3.13. Quien tenga 3.14 debe
   crear un entorno con 3.12. (Contar que a mí me pasó esta semana.)
3. **Nunca instalar los dos paquetes.** `paddlepaddle` y `paddlepaddle-gpu` conviven sin
   error, y el resultado es que todo corre en CPU 40 veces más lento sin avisar.

El punto 3 es el que vuelve en el bloque 6 como falla sembrada. Sembrarlo ahora en la
cabeza y no explicarlo del todo.

Verificación por carril, idéntica para todos:

```
python -m src.doctor
```

Seis líneas, cada una OK o FALLA. Quien tenga seis OK pasa al bloque siguiente; quien tenga
una FALLA llama al profesor y lee la línea en voz alta.

---

## Bloque 3 — Primer OCR y lectura del resultado (8:06–8:21, 15 min)

**Objetivo:** entender que el OCR no devuelve texto, devuelve **texto más geometría más
confianza**, y que esos tres datos valen igual.

Una sola página lógica del documento de Ilo. Una llamada. Una salida.

Lo que hay que hacer leer con detenimiento es la estructura del resultado:

| Campo | Qué es | Para qué sirve |
|---|---|---|
| `texto` | la cadena reconocida | lo obvio |
| `caja` | cuatro puntos en la imagen | permite resaltar en el original lo que la IA afirma |
| `confianza` | número entre 0 y 1 | permite decidir qué revisa un humano |

> Analogía: no es un lector que te cuenta el libro. Es un lector que además te señala con el
> dedo en qué parte de la página está cada frase, y te dice qué tan seguro está de cada una.

**Esto desbloquea la idea más valiosa de la clase**, y conviene decirla aquí: la confianza
permite escalar por costo. Se corre el modelo barato en todo, y solo las páginas donde dudó
se reenvían al modelo caro.

> Analogía: el profesor corrige rápido todos los exámenes y solo vuelve a revisar con calma
> los que quedaron entre 10 y 12. No pierde tiempo con los de 18 ni con los de 5.

---

## Bloque 4 — El momento GPU (8:21–8:41, 20 min)

**Objetivo:** que vean la diferencia con sus propios ojos, medida, no contada.

Pantalla dividida: consola a la izquierda, `nvidia-smi -l 1` a la derecha.

### 4.1 La medición honesta (5 min)

Antes de medir, explicar por qué el benchmark ingenuo miente.

> Analogía: cronometras cuánto tarda tu mamá en servir la sopa, pero arrancas el cronómetro
> cuando todavía está prendiendo la cocina. El primer plato siempre parece lentísimo.

La primera inferencia incluye cargar el modelo a la VRAM e inicializar CUDA. Por eso el
protocolo descarta dos páginas de calentamiento, mide diez, y reporta la **mediana**, no el
promedio.

### 4.2 La medición (8 min)

```
python -m src.bench
```

Resultado esperado, en el orden en que se debe mirar:

1. La VRAM de la derecha sube cuando arranca el modo GPU y se queda plana en modo CPU.
2. La mediana de segundos por página cae de forma drástica.
3. El texto reconocido es **el mismo**. Solo cambia el tiempo.

Referencia del caso real que da origen a esta clase, sobre una GTX 1660 Ti de 6 GB:
~45 s por página en CPU contra ~1 s en GPU; un rango de 42 páginas pasó de 32 minutos a
cerca de 1 minuto.

**Números medidos en la laptop de la clase** (RTX 3050, 13 de octubre de 2026), sobre
páginas lógicas a 425 DPI, con el protocolo del `bench`:

| Condición | mediana s/página | VRAM que ocupó cargar el modelo |
|---|---|---|
| GPU, nivel `tiny` | **0.73** | +1479 MiB |
| CPU, nivel `tiny` | **24–31** | 0 (plana) |
| GPU, nivel `medium` | ~7.8 | +350 MiB |
| CPU, nivel `medium` | no termina en varios minutos | — |

**Factor de aceleración medido con `tiny`: 33x.** Y el dato que remata el bloque: las
dos condiciones devolvieron **19 líneas con confianza 0.917**. Idénticas. Solo cambió
el tiempo — que es exactamente lo que había que demostrar.

Tres cosas que decir en voz alta al proyectar esto:

1. El texto es **el mismo**. Mírenlo en la tabla: misma cantidad de líneas, misma
   confianza. La GPU no lee mejor, lee más rápido.
2. `medium` en CPU directamente **no es usable**. Eso no es un detalle: es la lección
   de la clase en forma de cronómetro. El hardware decide qué modelo puedes correr.
3. La columna `corrio` dice dónde corrió **de verdad**, deducido de si la VRAM se movió
   al cargar el modelo. No de lo que la librería afirma. Ese es todo el punto.

> **Antes del bloque:** poner `ocr.nivel: tiny` en `config.yaml`. Así los dos carriles
> miden el mismo modelo y el bloque entra en los 20 minutos. Con `medium` no entra.

**Honestidad sobre la reproducibilidad:** dos corridas consecutivas del modo rápido
dieron 31.05 y 24.08 s/página en CPU — un 22% de diferencia, por encima del 15% que el
diseño exige. El modo rápido mide solo 3 páginas y el CPU es sensible a lo que más
corra en la máquina. Si hace falta un número defendible, correr el protocolo completo
(10 páginas) con todo lo demás cerrado. En GPU la dispersión fue mínima.

Advertencia honesta que hay que decir: parte de ese 40x es "GPU buena" y parte es "CPU mal
configurada". Un CPU con inferencia optimizada acorta bastante esa brecha. Prometer 40x sin
matices es vender humo.

### 4.3 Provocar el fallback mudo (7 min)

En vivo, construir el objeto OCR **sin** el parámetro `device`. Todo funciona. Nada avisa.
La VRAM de la derecha no se mueve. El tiempo se multiplica.

> "Esto es lo más caro que les puede pasar en un proyecto real: creer que tienen aceleración
> y no tenerla. Y fíjense que no hay ningún error en pantalla. El silencio es el problema."

Dejarlo así. El bloque 6 lo retoma.

---

## Bloque 5 — Mini-proyecto: "Zaragoza chico" (8:41–9:06, 25 min)

**Objetivo:** recorrer el pipeline completo de extremo a extremo, en escala de juguete.

El estudiante abre `notebooks/01_mini_zaragoza.ipynb` y ejecuta los cinco pasos sobre
**una sola página lógica** del documento de Ilo:

| Paso | Qué hace | Minutos |
|---|---|---|
| 1. Triaje | confirma que la página es imagen | 2 |
| 2. Preparación | rasteriza, parte la hoja en dos, endereza | 6 |
| 3. OCR | texto, cajas, confianza | 5 |
| 4. Extracción | cuatro campos a JSON | 8 |
| 5. Entrega | CSV y tabla en pantalla | 4 |

Los cuatro campos a extraer:

| Campo | Valor correcto en el documento |
|---|---|
| Entidad convocante | Municipalidad Provincial de Ilo |
| Número de procedimiento | Licitación Pública de Obras N° 05-2026-C-MPI |
| Objeto de la contratación | Ampliación del servicio de movilidad urbana, Sector II (PROMUVI IV), A.H. Nuevo Ilo |
| Departamento | Moquegua |

### El paso 2 es donde está la lección

Deliberadamente, el notebook corre primero el OCR **sin** partir la hoja ni enderezarla. El
resultado es basura. Luego activa la preparación y el resultado es legible.

> "Noten que no cambiamos de modelo. Es el mismo modelo, con la imagen arreglada. Hay un
> dato publicado que lo confirma: cuando a estos modelos se les dan fotos de documentos en
> vez de escaneos limpios, el mejor de todos cae de 91.9 a 72.2 puntos. Veinte puntos. No
> hay modelo que compense una mala imagen."

### La regla de verificación

Antes de cerrar el bloque, imponer la regla que viene del proyecto real:

> Todo dato extraído debe existir **literalmente** en el texto del OCR. Si no existe, se
> marca como "sin verificar". Un modelo que corrige el número de licitación y acierta es
> tan peligroso como uno que lo inventa, porque la próxima vez va a corregir y fallar.

---

## Bloque 6 — Laboratorio de fallas (9:06–9:16, 10 min)

**Objetivo:** diagnosticar leyendo logs, no adivinando. Esto es lo que diferencia una clase
de un tutorial de YouTube.

Tres fallas ya sembradas en `fallas/`. Se da el síntoma; ellos encuentran la causa.

| # | Síntoma que verán | Causa | Lección |
|---|---|---|---|
| 1 | Todo funciona, 40 veces más lento, la VRAM no se mueve | los dos wheels de Paddle instalados | la GPU falla en silencio; hay que medir |
| 2 | Salida tipo `SOSORAOOS CS OORSOD` | corrección de orientación apagada | preprocesar vence a modelo grande |
| 3 | Memoria agotada o lentitud extrema | se pidió más VRAM de la que hay | el hardware decide qué es posible |

La falla 2 sale gratis: el documento real ya viene girado.

La falla 3 es la reproducción del fracaso que dio origen a toda esta historia. Mostrar las
tres líneas del log original, que son la mejor diapositiva de la clase:

```
offloaded 0/37 layers to GPU
compute graph ... size = "6.7 GiB"
total memory  ... size = "10.1 GiB"
```

Pregunta al salón: el modelo era de 3 mil millones de parámetros, que en 4 bits pesa unos
2 GB. ¿De dónde salieron los otros 8?

Respuesta: de la imagen. Un modelo de visión convierte una página en miles de fragmentos
visuales, y la memoria la dominan esos fragmentos, no los pesos.

> **Regla práctica:** en modelos de visión para documentos, la VRAM no la decide el tamaño
> del modelo, la decide la resolución de la página. Duplicar el DPI puede cuadruplicar la
> memoria.

---

## Bloque 7 — Cierre (9:16–9:20, 4 min)

Mostrar 60 segundos de la aplicación real: PDF de 110 páginas entrando, informe saliendo.
Que reconozcan cada pieza que acaban de construir en miniatura.

Las seis lecciones transferibles, leídas rápido:

1. Definir el problema antes de elegir la herramienta.
2. Conocer los límites de hardware: deciden qué es posible.
3. La herramienta del tamaño del problema. No traer un cañón para matar una mosca.
4. Híbrido: lo barato y masivo en local, el modelo caro solo donde agrega valor.
5. Iterar y diagnosticar. Los fracasos enseñan.
6. Humano al centro. La IA propone, la persona decide.

El dato que cierra y sorprende, porque contradice la intuición:

> En el ranking público de parsing de documentos, los tres primeros puestos de 2026 los
> tienen modelos de menos de 1.3 mil millones de parámetros. Un modelo de 235 mil millones
> queda por debajo. El pequeño especializado le gana al gigante generalista en su propio
> terreno.

### Entregable de la sesión

El CSV con los cuatro campos extraídos, más una línea de respuesta: *¿en qué modo corriste,
y cuántos segundos por página te tomó?* Esa segunda parte es la que importa: obliga a haber
medido.

### Puente con lo que viene

- **Semana 11 (27–28 oct), Agentes:** el OCR es la herramienta que un agente llama. El paso
  natural es exponer este pipeline como servidor MCP, que es el tema de la semana 4.
- **Proyecto final:** el sílabo exige usar al menos dos herramientas del curso. OCR más
  extracción estructurada es una combinación completa por sí sola, y hay muchísimo
  documento público peruano escaneado esperando.

---

## Plan B por bloque

| Si falla | Entonces |
|---|---|
| El internet del aula | USB con pesos y PDF; carril B (CPU local) pasa a ser el principal |
| La laptop del profesor | video grabado de la demo GPU, 3 minutos |
| Un carril entero | los tres corren el mismo código; se migra al carril que funcione |
| El tiempo | el bloque 6 se recorta a una sola falla, la número 1 |

El único bloque que no se puede sacrificar es el 4: es el que justifica la clase.
