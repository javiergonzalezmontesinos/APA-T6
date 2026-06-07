"""Normalizacion de expresiones horarias escritas en castellano."""

import re


PATRON_HORAS = re.compile(
    r"""
    (?<![\w:])
    (?:
        (?P<estandar_hora>[01]?\d|2[0-3])
        :
        (?P<estandar_minuto>[0-5]\d)
      |
        (?P<h_hora>[01]?\d|2[0-3])
        h
        (?:
            (?P<h_minuto>[0-5]?\d)m
        )?
        (?:
            \s+(?P<h_periodo>
                de\ la\ mañana |
                del\ mediodía |
                de\ la\ tarde |
                de\ la\ noche |
                de\ la\ madrugada
            )
        )?
      |
        (?P<hablada_hora>1[0-2]|[1-9])
        \s+
        (?:
            (?P<fraccion>
                en\ punto |
                y\ cuarto |
                y\ media |
                menos\ cuarto
            )
            (?:\s+(?P<hablada_periodo>
                de\ la\ mañana |
                del\ mediodía |
                de\ la\ tarde |
                de\ la\ noche |
                de\ la\ madrugada
            ))?
          |
            (?P<periodo_solo>
                de\ la\ mañana |
                del\ mediodía |
                de\ la\ tarde |
                de\ la\ noche |
                de\ la\ madrugada
            )
        )
    )
    (?![\w:]|\d)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _aplica_periodo(hora, periodo):
    """Convierte una hora de doce horas segun su periodo del dia."""
    if periodo is None:
        return hora % 12

    periodo = periodo.lower()
    rangos = {
        "de la mañana": range(4, 13),
        "del mediodía": (12, 1, 2, 3),
        "de la tarde": range(3, 9),
        "de la noche": (8, 9, 10, 11, 12, 1, 2, 3, 4),
        "de la madrugada": range(1, 7),
    }
    if hora not in rangos[periodo]:
        return None

    if periodo in ("del mediodía", "de la tarde") and hora != 12:
        return hora + 12
    if periodo == "de la noche":
        if hora == 12:
            return 0
        if hora >= 8:
            return hora + 12
    return hora


def _normaliza_coincidencia(coincidencia):
    """Devuelve la forma HH:MM de una expresion horaria valida."""
    grupos = coincidencia.groupdict()

    if grupos["estandar_hora"] is not None:
        hora = int(grupos["estandar_hora"])
        minuto = int(grupos["estandar_minuto"])
        return f"{hora:02d}:{minuto:02d}"

    if grupos["h_hora"] is not None:
        hora = int(grupos["h_hora"])
        minuto = int(grupos["h_minuto"] or 0)
        periodo = grupos["h_periodo"]
        if periodo:
            if not 1 <= hora <= 12:
                return coincidencia.group(0)
            hora = _aplica_periodo(hora, periodo)
            if hora is None:
                return coincidencia.group(0)
        return f"{hora:02d}:{minuto:02d}"

    hora = int(grupos["hablada_hora"])
    fraccion = (grupos["fraccion"] or "").lower()
    minuto = 0
    if fraccion == "y cuarto":
        minuto = 15
    elif fraccion == "y media":
        minuto = 30
    elif fraccion == "menos cuarto":
        hora = 12 if hora == 1 else hora - 1
        minuto = 45

    periodo = grupos["hablada_periodo"] or grupos["periodo_solo"]
    hora = _aplica_periodo(hora, periodo)
    if hora is None:
        return coincidencia.group(0)
    return f"{hora:02d}:{minuto:02d}"


def normalizaHoras(ficText, ficNorm):
    """Normaliza las expresiones horarias de ``ficText`` en ``ficNorm``."""
    with open(ficText, encoding="utf-8") as fichero_entrada:
        texto = fichero_entrada.read()

    texto_normalizado = PATRON_HORAS.sub(_normaliza_coincidencia, texto)

    with open(ficNorm, "w", encoding="utf-8") as fichero_salida:
        fichero_salida.write(texto_normalizado)
