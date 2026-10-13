# Laboratorio de fallas

Tres fallas sembradas. El estudiante recibe **el síntoma** y debe encontrar la causa
**leyendo el log**, no adivinando.

Esto es lo que separa una clase de un tutorial de YouTube. Un tutorial muestra el camino
cuando todo funciona. Un ingeniero pasa el 80% del tiempo en el caso en que no.

> **Regla del laboratorio:** antes de cambiar una línea de código, leer el log. Están en
> `logs/`, uno por módulo. El proyecto original diagnosticó su peor bug leyendo tres
> líneas de log, no probando cosas al azar.

Bloque 6 de la clase, 10 minutos. Si falta tiempo, se corre solo la falla 1.

---

## Falla 1 — El fallback mudo

**La más cara de las tres, y la que de verdad pasa en proyectos reales.**

### Cómo se siembra

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

Ahora están instalados **los dos** wheels: `paddlepaddle` y `paddlepaddle-gpu`.

### El síntoma

Todo funciona. No hay ningún error en pantalla. Pero:

- El benchmark tarda unos 40 veces más.
- La ventana de `nvidia-smi` no se mueve: la VRAM queda plana.

### Lo que el estudiante debe encontrar

```powershell
python -m pip list | findstr paddle     # aparecen dos líneas, no una
python -m src.doctor                    # el chequeo 2 aborta y nombra el problema
```

En `logs/ocr_run.log` la línea que lo delata es:

```
Dispositivo pedido: gpu | dispositivo real segun Paddle: cpu
ATENCION: se pidio GPU y Paddle reporta cpu. Esto es el fallback mudo...
```

### La cura

```powershell
python -m pip uninstall -y paddlepaddle
python -m src.doctor                    # seis líneas, todas OK
```

### La lección

> La GPU falla **en silencio**. Hay que medir, no suponer.

Nótese que no hay ningún error en pantalla. El silencio es el problema. Esto es lo más
caro que le puede pasar a alguien en un proyecto real: creer que tiene aceleración y no
tenerla, durante semanas.

Por eso existe `doctor.py`, y por eso su chequeo 6 hace una inferencia real y mide la
VRAM en vez de preguntarle a la librería si cree que tiene GPU.

---

## Falla 2 — La página girada

**Esta sale gratis: el documento real ya viene girado 90°.**

### Cómo se siembra

En `config.yaml`:

```yaml
render:
  rotacion: 0                          # antes: 270
ocr:
  usar_clasificador_orientacion: false # antes: true
```

Luego borrar la caché para forzar el recómputo y correr:

```powershell
Remove-Item data\processed\h001_p*.png, data\processed\ocr\h001_p*.* -ErrorAction SilentlyContinue
python -m src.preparar 1
python -m src.ocr_run
```

### El síntoma

La salida es basura de este tipo:

```
SOSORAOOS CS OORSOD
```

Letras sueltas, sin palabras reconocibles. La confianza promedio se desploma, y el log
de `ocr_run` lo avisa:

```
h001_p002.png: 41 de 44 lineas por debajo de la confianza 0.80
```

### Lo que el estudiante debe encontrar

Abrir el PNG de `data/processed/` y mirarlo. Está de costado. El modelo está leyendo
texto vertical como si fuera horizontal.

### La cura

Devolver `rotacion: 270` y `usar_clasificador_orientacion: true`. Repetir. Mismo
modelo, misma máquina, mismo todo — y ahora el texto sale legible.

### La lección

> **Preprocesar vence a traer un modelo más grande.**

No se cambió de modelo. Es el mismo modelo con la imagen arreglada.

Hay un dato publicado que lo confirma: en Wild-OmniDocBench, que usa **fotos** de las
mismas páginas en vez de escaneos limpios, el mejor modelo de todos cae de 91.93 a
72.19 puntos. **Veinte puntos de caída por calidad de imagen.** No hay modelo que
compense una mala imagen.

---

## Falla 3 — El techo de hardware

**La reproducción del fracaso que dio origen a toda esta historia.**

> ⚠️ Preparar esta falla **antes** de la clase. Nunca descargar gigabytes en el aula.

### Cómo se siembra

La versión barata y segura, que no requiere descargar nada: subir el DPI hasta que la
memoria no alcance.

En `config.yaml`:

```yaml
render:
  dpi_fisico: 900        # antes: 425
```

```powershell
python -m src.preparar 1
python -m src.ocr_run
```

### El síntoma

Una de dos, según la máquina:

- `ResourceExhaustedError` / `Out of memory` de Paddle, o
- lentitud extrema: la página tarda minutos en vez de segundos.

### La lección, y la mejor diapositiva de la clase

El caso original intentó usar un **modelo de visión** de 3 mil millones de parámetros
para leer estas mismas páginas, en una GPU de 6 GB. El log dijo:

```
offloaded 0/37 layers to GPU
compute graph ... size = "6.7 GiB"
total memory  ... size = "10.1 GiB"
```

**Pregunta al salón:** el modelo era de 3 mil millones de parámetros, que en 4 bits
pesa unos 2 GB. ¿De dónde salieron los otros 8?

**Respuesta:** de la imagen. Un modelo de visión convierte una página en miles de
fragmentos visuales, y la memoria la dominan esos fragmentos, no los pesos.

> **Regla práctica:** en modelos de visión para documentos, la VRAM no la decide el
> tamaño del modelo, la decide la **resolución de la página**. Duplicar el DPI puede
> cuadruplicar la memoria.

`offloaded 0/37 layers to GPU` significa que ni una sola capa entró en la tarjeta. Todo
corrió en CPU. Tres líneas de log, y el diagnóstico completo. Nadie tuvo que adivinar.

---

## Cómo volver al estado bueno

Después del laboratorio, restaurar `config.yaml`:

```yaml
render:
  dpi_fisico: 425
  rotacion: 270
ocr:
  usar_clasificador_orientacion: true
```

Y verificar que el entorno quedó limpio:

```powershell
python -m pip list | findstr paddle     # UNA línea: paddlepaddle-gpu
python -m src.doctor                    # seis líneas, todas OK
```

---

## Las tres lecciones juntas

| Falla | Síntoma | Lección |
|---|---|---|
| 1. Fallback mudo | todo funciona, 40× más lento, VRAM plana | la GPU falla sin avisar; **medir, no suponer** |
| 2. Página girada | `SOSORAOOS CS OORSOD` | **preprocesar vence a modelo más grande** |
| 3. Techo de hardware | memoria agotada o lentitud extrema | **el hardware decide qué es posible** |

Las tres comparten una moraleja: el programa no te avisa. El log sí, si lo lees.
