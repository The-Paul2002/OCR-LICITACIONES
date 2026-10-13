"""Utilidades compartidas: carga de configuracion y logging.

Este modulo no hace trabajo propio. Existe para que ningun otro modulo tenga que
repetir como se lee `config.yaml` ni como se configura el log.

Regla del repositorio: todo valor ajustable sale de `config.yaml`. Si un modulo
necesita un numero, lo pide aqui.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import yaml

# Raiz del proyecto: este archivo vive en <raiz>/src/comun.py
RAIZ = Path(__file__).resolve().parent.parent


def cargar_config(ruta: str | Path | None = None) -> dict[str, Any]:
    """Devuelve el contenido de config.yaml como diccionario."""
    ruta = Path(ruta) if ruta else RAIZ / "config.yaml"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe {ruta}. Este archivo es obligatorio: todos los parametros "
            "del pipeline salen de ahi."
        )
    with open(ruta, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ruta_absoluta(valor: str | Path) -> Path:
    """Convierte una ruta de config.yaml (relativa a la raiz) en ruta absoluta."""
    p = Path(valor)
    return p if p.is_absolute() else RAIZ / p


def configurar_logging(nombre: str, config: dict[str, Any] | None = None) -> logging.Logger:
    """Configura logging a consola y a archivo, sin buffer.

    El archivo de log importa mas que la consola: cuando otro programa captura la
    salida estandar, Python la bufferiza y el progreso no se ve nunca. Por eso cada
    modulo escribe tambien a `logs/<nombre>.log` con flush inmediato.
    """
    config = config or cargar_config()
    dir_logs = ruta_absoluta(config["rutas"]["logs"])
    dir_logs.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(nombre)
    if logger.handlers:  # ya configurado; importar dos veces no debe duplicar lineas
        return logger

    logger.setLevel(logging.INFO)
    # PaddleX instala sus propios handlers en el logger raiz. Sin esto, cada linea
    # nuestra sale tres veces y la salida se vuelve ilegible en clase.
    logger.propagate = False
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Consola: stdout con flush inmediato en cada registro.
    consola = logging.StreamHandler(sys.stdout)
    consola.setFormatter(formato)
    consola.flush = sys.stdout.flush  # type: ignore[method-assign]
    logger.addHandler(consola)

    # Archivo: se reabre en cada emision para que el progreso sea legible en vivo.
    archivo = _HandlerSinBuffer(dir_logs / f"{nombre}.log")
    archivo.setFormatter(formato)
    logger.addHandler(archivo)

    return logger


class _HandlerSinBuffer(logging.FileHandler):
    """FileHandler que hace flush despues de cada linea.

    Un proceso de 40 paginas que escribe su progreso a un archivo bufferizado es un
    proceso silencioso. Este bug ya costo horas en el proyecto original.
    """

    def __init__(self, ruta: Path) -> None:
        super().__init__(ruta, mode="a", encoding="utf-8", delay=False)

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def preparar_directorios(config: dict[str, Any]) -> None:
    """Crea las carpetas de salida declaradas en config.yaml si no existen."""
    for clave in ("procesados", "salidas", "logs"):
        ruta_absoluta(config["rutas"][clave]).mkdir(parents=True, exist_ok=True)
