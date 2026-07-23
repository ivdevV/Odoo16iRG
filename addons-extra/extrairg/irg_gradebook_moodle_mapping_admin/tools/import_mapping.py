from pathlib import Path

from ..services.mapping_import import MAX_FILE_SIZE, MappingImportService


def _read_bounded(path):
    source = Path(path)
    if not source.is_absolute():
        raise ValueError("La ruta del CSV debe ser absoluta: %s" % source)
    with source.open("rb") as stream:
        payload = stream.read(MAX_FILE_SIZE + 1)
    if len(payload) > MAX_FILE_SIZE:
        raise ValueError("El CSV supera el límite de 10 MiB: %s" % source)
    return payload


def analyze_paths(env, courses_path, assignments_path):
    return MappingImportService(env).analyze_bytes(
        _read_bounded(courses_path), _read_bounded(assignments_path)
    )


def apply_plan(env, plan):
    return MappingImportService(env).apply_plan(plan)
