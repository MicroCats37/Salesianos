"""Carga exacta del fixture de `mit/SALESIANOS`."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.competencias.domain.constants import EstadoCompetencia
from modules.competencias.domain.models import (
    Competencia,
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
)
from modules.eventos.domain.models import Edicion
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    Promocion,
)
from modules.usuarios.domain.models import Persona


EVENT_DATE = "2026-11-21"
FOOTBALL_GROUPS = {
    "A": (
        ["1999", "2007", "2009", "2011B"],
        [
            ("G3-A", "2007", "1999", "09:00", "A"),
            ("G3-B", "2009", "2011B", "09:00", "B"),
            ("G15-A", "2011B", "1999", "11:00", "A"),
            ("G15-B", "2007", "2009", "11:00", "B"),
            ("G30-B", "1999", "2009", "13:30", "B"),
            ("G42-A", "2007", "2011B", "15:30", "A"),
        ],
    ),
    "B": (
        ["1975", "1979", "1980", "1981"],
        [
            ("G3-C", "1980", "1979", "09:00", "C"),
            ("G3-D", "1975", "1981", "09:00", "D"),
            ("G18-C", "1981", "1980", "11:30", "C"),
            ("G18-D", "1975", "1979", "11:30", "D"),
            ("G30-C", "1975", "1980", "13:30", "C"),
            ("G30-D", "1979", "1981", "13:30", "D"),
        ],
    ),
    "C": (
        ["1986", "1987", "1990", "1991"],
        [
            ("G6-A", "1990", "1987", "09:30", "A"),
            ("G6-B", "1991", "1986", "09:30", "B"),
            ("G21-A", "1986", "1990", "12:00", "A"),
            ("G27-B", "1991", "1987", "13:00", "B"),
            ("G33-A", "1991", "1990", "14:00", "A"),
            ("G36-B", "1987", "1986", "14:30", "B"),
        ],
    ),
    "D": (
        ["2018", "2020", "2021", "2024"],
        [
            ("G6-C", "2018", "2024", "09:30", "C"),
            ("G6-D", "2021", "2020", "09:30", "D"),
            ("G12-D", "2020", "2024", "10:30", "D"),
            ("G15-C", "2018", "2021", "11:00", "C"),
            ("G33-C", "2024", "2021", "14:00", "C"),
            ("G33-D", "2018", "2020", "14:00", "D"),
        ],
    ),
    "E": (
        ["2002", "2006", "2008", "2011A"],
        [
            ("G9-A", "2006", "2008", "10:00", "A"),
            ("G9-B", "2002", "2011A", "10:00", "B"),
            ("G18-A", "2011A", "2006", "11:30", "A"),
            ("G18-B", "2002", "2008", "11:30", "B"),
            ("G30-A", "2002", "2006", "13:30", "A"),
            ("G33-B", "2008", "2011A", "14:00", "B"),
        ],
    ),
    "F": (
        ["2012", "2019", "2022", "2023"],
        [
            ("G9-C", "2023", "2012", "10:00", "C"),
            ("G9-D", "2022", "2019", "10:00", "D"),
            ("G15-D", "2012", "2022", "11:00", "D"),
            ("G21-C", "2019", "2012", "12:00", "C"),
            ("G21-D", "2023", "2022", "12:00", "D"),
            ("G39-C", "2023", "2019", "15:00", "C"),
        ],
    ),
    "G": (
        ["1988", "1993", "1997"],
        [
            ("G12-A", "1988", "1993", "10:30", "A"),
            ("G24-A", "1997", "1993", "12:30", "A"),
            ("G39-A", "1988", "1997", "15:00", "A"),
        ],
    ),
    "H": (
        ["1998", "2003", "2004"],
        [
            ("G12-B", "2004", "2003", "10:30", "B"),
            ("G24-B", "2003", "1998", "12:30", "B"),
            ("G42-B", "2004", "1998", "15:30", "B"),
        ],
    ),
    "I": (
        ["2013", "2016", "2017"],
        [
            ("G12-C", "2017", "2016", "10:30", "C"),
            ("G24-C", "2013", "2017", "12:30", "C"),
            ("G36-C", "2013", "2016", "14:30", "C"),
        ],
    ),
}

VOLLEY_GROUPS = {
    "A": (
        ["1987", "1996", "1986"],
        [
            ("VOL-1200-E", "1987", "1996", "12:00", "E"),
            ("VOL-1330-F", "1996", "1986", "13:30", "F"),
            ("VOL-1530-E", "1987", "1986", "15:30", "E"),
        ],
    ),
    "B": (
        ["2018", "2020", "2022"],
        [
            ("VOL-1200-F", "2018", "2020", "12:00", "F"),
            ("VOL-1300-E", "2018", "2022", "13:00", "E"),
            ("VOL-1500-E", "2022", "2020", "15:00", "E"),
        ],
    ),
    "C": (
        ["2007", "2006", "2004", "2002"],
        [
            ("VOL-1230-E", "2007", "2006", "12:30", "E"),
            ("VOL-1230-F", "2004", "2002", "12:30", "F"),
            ("VOL-1330-E", "2007", "2004", "13:30", "E"),
            ("VOL-1430-E", "2006", "2004", "14:30", "E"),
            ("VOL-1430-F", "2007", "2002", "14:30", "F"),
            ("VOL-1530-F", "2002", "2006", "15:30", "F"),
        ],
    ),
    "D": (
        ["2021", "2023", "2012"],
        [
            ("VOL-1300-F", "2021", "2023", "13:00", "F"),
            ("VOL-1400-E", "2023", "2012", "14:00", "E"),
            ("VOL-1500-F", "2021", "2012", "15:00", "F"),
        ],
    ),
}

BASKETBALL_GROUPS = {
    "A": (
        ["2008", "2002", "2000", "2004"],
        [
            ("BAS-0900", "2008", "2002", "09:00", "G"),
            ("BAS-1000", "2000", "2004", "10:00", "G"),
            ("BAS-1100", "2000", "2002", "11:00", "G"),
            ("BAS-1440", "2000", "2008", "14:40", "G"),
            ("BAS-1620", "2004", "2008", "16:20", "G"),
            ("BAS-1700", "2002", "2004", "17:00", "G"),
        ],
    ),
    "B": (
        ["2003", "2006", "2007"],
        [
            ("BAS-0920", "2003", "2006", "09:20", "G"),
            ("BAS-1200", "2007", "2003", "12:00", "G"),
            ("BAS-1640", "2007", "2006", "16:40", "G"),
        ],
    ),
    "C": (
        ["2017", "2025", "2021"],
        [
            ("BAS-0940", "2017", "2025", "09:40", "G"),
            ("BAS-1020", "2025", "2021", "10:20", "G"),
            ("BAS-1600", "2017", "2021", "16:00", "G"),
        ],
    ),
    "D": (
        ["1991", "1997", "1988"],
        [
            ("BAS-1040", "1991", "1997", "10:40", "G"),
            ("BAS-1140", "1988", "1997", "11:40", "G"),
            ("BAS-1220", "1988", "1991", "12:20", "G"),
        ],
    ),
    "E": (
        ["1994", "1986"],
        [
            ("BAS-1120", "1994", "1986", "11:20", "G"),
            ("BAS-1300", "1986", "1994", "13:00", "G"),
        ],
    ),
    "F": (
        ["2020", "2014", "2012"],
        [
            ("BAS-1240", "2020", "2014", "12:40", "G"),
            ("BAS-1320", "2012", "2014", "13:20", "G"),
            ("BAS-1540", "2020", "2012", "15:40", "G"),
        ],
    ),
}

COMPETITIONS = (
    (
        "F7M",
        "futbol-7-masculino",
        "Fútbol 7 Masculino Interpromociones",
        FOOTBALL_GROUPS,
        "",
        True,
    ),
    (
        "VOL",
        "voley-mixto",
        "Vóley Mixto Interpromociones",
        VOLLEY_GROUPS,
        "VOL-",
        False,
    ),
    (
        "BAS",
        "basquet-masculino",
        "Básquet Masculino Interpromociones",
        BASKETBALL_GROUPS,
        "BAS-",
        False,
    ),
)


class Command(BaseCommand):
    help = "Carga o reconcilia el fixture multideporte de referencia."

    @transaction.atomic
    def handle(self, *args, **options):
        edicion = (
            Edicion.objects.filter(estado="PUBLICADA").first()
            or Edicion.objects.first()
        )
        if edicion is None:
            raise CommandError("No existe una edición para cargar el torneo.")

        categoria, _ = Categoria.objects.get_or_create(
            edicion=edicion,
            nombre="Interpromociones",
            defaults={"promocion_desde": 1975, "promocion_hasta": 2025},
        )
        if categoria.promocion_hasta != 2025:
            categoria.promocion_hasta = 2025
            categoria.save(update_fields=["promocion_hasta"])

        total_groups = total_teams = total_matches = 0
        for sport_index, (
            code,
            slug,
            name,
            groups,
            prefix,
            has_bracket,
        ) in enumerate(COMPETITIONS, start=1):
            disciplina = Disciplina.objects.filter(edicion=edicion, slug=slug).first()
            paquete = Paquete.objects.filter(edicion=edicion, slug=slug).first()
            if disciplina is None or paquete is None:
                raise CommandError(
                    f"Falta el catálogo oficial para {name}. Ejecuta seed_catalogo."
                )

            names = [name]
            if code == "F7M":
                names.append("Fulbito Interpromociones")
            competencia = Competencia.objects.filter(
                edicion=edicion,
                nombre__in=names,
            ).first()
            if competencia is None:
                competencia = Competencia.objects.create(
                    edicion=edicion,
                    disciplina=disciplina,
                    categoria=categoria,
                    nombre=name,
                    fecha=EVENT_DATE,
                    estado=EstadoCompetencia.EN_CURSO,
                )
            else:
                competencia.disciplina = disciplina
                competencia.categoria = categoria
                competencia.nombre = name
                competencia.fecha = EVENT_DATE
                competencia.estado = EstadoCompetencia.EN_CURSO
                competencia.save()

            labels = list(
                dict.fromkeys(
                    label
                    for group_labels, _ in groups.values()
                    for label in group_labels
                )
            )
            label_index = {label: index for index, label in enumerate(labels)}

            for group_code, (group_labels, matches) in groups.items():
                group_id = group_code if not prefix else f"{code}-{group_code}"
                group, _ = GrupoTorneo.objects.update_or_create(
                    id=group_id,
                    defaults={"competencia": competencia},
                )
                total_groups += 1
                for label in group_labels:
                    promotion = Promocion.objects.filter(anio=int(label[:4])).first()
                    if promotion is None:
                        raise CommandError(
                            f"Falta la promoción {label[:4]} en el catálogo oficial."
                        )
                    persona, _ = Persona.objects.update_or_create(
                        tipo_documento="DNI",
                        numero_documento=(
                            f"99{label_index[label]:06d}"
                            if code == "F7M"
                            else f"9{sport_index}{label_index[label]:06d}"
                        ),
                        defaults={
                            "nombres": "Delegación",
                            "apellidos": f"{label} {code}",
                            "genero": "",
                        },
                    )
                    inscripcion, _ = Inscripcion.objects.get_or_create(
                        edicion=edicion,
                        responsable=persona,
                        paquete=paquete,
                        defaults={
                            "promocion": promotion,
                            "referencia": (
                                f"torneo-referencia-{edicion.slug}-{slug}-{label}"
                            ),
                            "cupos_solicitados": paquete.minimo_compra_inicial,
                        },
                    )
                    if inscripcion.promocion_id != promotion.id:
                        inscripcion.promocion = promotion
                        inscripcion.save(update_fields=["promocion"])
                    equipo, _ = Equipo.objects.update_or_create(
                        inscripcion=inscripcion,
                        disciplina=disciplina,
                        defaults={
                            "categoria": categoria,
                            "nombre": f"Promoción {label}",
                            "estado": "ACTIVO",
                        },
                    )
                    team_id = f"{prefix}{label}"
                    EquipoTorneo.objects.update_or_create(
                        id=team_id,
                        defaults={
                            "equipo": equipo,
                            "competencia": competencia,
                            "grupo": group,
                        },
                    )
                    total_teams += 1

                for match_id, home, away, start, court in matches:
                    scheduled = datetime.fromisoformat(
                        f"{EVENT_DATE}T{start}:00"
                    ).replace(tzinfo=ZoneInfo("America/Lima"))
                    PartidoTorneo.objects.update_or_create(
                        id=match_id,
                        defaults={
                            "competencia": competencia,
                            "grupo": group,
                            "etapa": "group",
                            "local_id": f"{prefix}{home}",
                            "visitante_id": f"{prefix}{away}",
                            "programado_en": scheduled,
                            "cancha": court,
                        },
                    )
                    total_matches += 1

            if has_bracket:
                for stage, count in (
                    ("round16", 8),
                    ("quarter", 4),
                    ("semi", 2),
                    ("final", 1),
                ):
                    for position in range(count):
                        PartidoTorneo.objects.get_or_create(
                            id=f"{stage}-{position + 1}",
                            defaults={
                                "competencia": competencia,
                                "etapa": stage,
                                "posicion": position,
                            },
                        )

        Disciplina.objects.filter(
            edicion=edicion,
            slug="fulbito",
            competencias__isnull=True,
            equipos__isnull=True,
            paquetes_vinculados__isnull=True,
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Fixture cargado: "
                f"3 competencias, {total_groups} grupos, "
                f"{total_teams} equipos y {total_matches} partidos de grupo."
            )
        )
