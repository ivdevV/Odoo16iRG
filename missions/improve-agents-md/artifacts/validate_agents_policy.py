#!/usr/bin/env python3
"""Validate the executable policy contract defined for Odoo16iRG's AGENTS.md."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "AGENTS.md"


def normalized(value: str) -> str:
    """Return case-folded text without accents and with collapsed whitespace."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents)


def has_all(text: str, *terms: str) -> bool:
    return all(normalized(term) in text for term in terms)


def parse_verification_example(source: str) -> bool:
    """Accept only a fenced, strict-JSON verification contract example."""
    for candidate in re.findall(r"```json\s*\n(.*?)```", source, flags=re.DOTALL | re.IGNORECASE):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and {"status", "checks"}.issubset(payload):
            return True
    return False


def validate(source: str) -> list[tuple[str, str]]:
    text = normalized(source)
    failures: list[tuple[str, str]] = []

    def require(name: str, condition: bool, detail: str) -> None:
        if not condition:
            failures.append((name, detail))

    require(
        "project_identity",
        "odoo16irg" in text
        and not re.search(r"\[(?:nombre|indicar|adaptar)[^\]]*\]", text),
        "use the real Odoo16iRG name and remove editorial placeholders",
    )
    lifecycle = re.search(
        r"plan\s*(?:→|->)\s*implementacion\s*/\s*tdd\s*(?:→|->)\s*review"
        r"\s*(?:→|->)\s*validacion\s*(?:→|->)\s*documentacion"
        r"\s*(?:→|->)\s*publicacion\s+autorizada",
        text,
    )
    require("lifecycle", lifecycle is not None, "declare the exact six-stage canonical lifecycle")
    require(
        "coder_tdd",
        has_all(text, "codificador", "TDD", "RED", "GREEN"),
        "assign RED and GREEN TDD ownership to the coder",
    )
    require(
        "independent_validator",
        has_all(text, "validador", "independiente")
        and has_all(text, "no", "corrige", "codigo de produccion"),
        "make validation independent and forbid production-code corrections by the validator",
    )
    require(
        "gate_rework",
        has_all(text, "gate", "fall", "reabre", "implementacion")
        and has_all(text, "escalado", "correccion", "separad"),
        "reopen implementation on failed gates and separate correction from escalation",
    )
    require(
        "mission_levels",
        ("sin mision" in text or "no crean mision" in text)
        and has_all(text, "mision ligera", "mision completa"),
        "define proportional none, light and full mission levels",
    )
    require(
        "mission_artifacts",
        has_all(text, "execution.md", "evidencia concisa", "diff.patch", "opcional"),
        "use execution.md, concise evidence and an optional diff.patch",
    )
    require(
        "verification_json",
        parse_verification_example(source),
        "include a fenced verification.json example parseable by json.loads",
    )
    require(
        "check_results",
        has_all(text, "pass", "fail", "skipped")
        and has_all(text, "skip", "justificacion"),
        "allow pass/fail/skipped results and require skip justification",
    )
    require(
        "knowledge_path",
        ".agents/knowledge/odoo_development_modding/artifacts/" in source,
        "set the canonical reusable-knowledge path",
    )
    require(
        "worktree_runtime",
        has_all(text, "docker-compose.local.yml", "worktree", "overlay", "restaur")
        and ("cleanup" in text or "limpieza" in text or "limpiar" in text),
        "specify compose worktree overlay, cleanup and restoration",
    )
    require(
        "publication_separation",
        has_all(text, "commit", "push", "PR")
        and (
            has_all(text, "commit", "push", "pr", "no autoriza")
            or has_all(text, "commit", "push", "pr", "separad")
        ),
        "distinguish commit, push and PR authorization",
    )
    require(
        "single_use_push",
        has_all(text, "push", "remoto", "rama", "alcance")
        and ("una sola" in text or "un solo uso" in text or "una unica" in text)
        and ("ok nuevo" in text or "autorizacion nueva" in text),
        "make push authorization single-use and bind it to remote, branch and scope",
    )
    require(
        "server_security",
        has_all(text, "servidor", "ui", "acciones protegidas")
        and ("no sustituyen" in text or "nunca sustituyen" in text),
        "require server-side controls for protected actions, beyond UI restrictions",
    )
    return failures


def main() -> int:
    if not POLICY.is_file():
        print(f"[ERROR] policy not found: {POLICY}")
        return 2

    failures = validate(POLICY.read_text(encoding="utf-8"))
    if not failures:
        print("PASS: AGENTS.md satisfies all policy contracts")
        return 0

    print(f"FAIL: AGENTS.md is missing {len(failures)} policy contract(s)")
    for name, detail in failures:
        print(f"- {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
