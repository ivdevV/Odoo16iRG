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


def paragraphs(source: str) -> list[str]:
    """Return normalized Markdown paragraphs, preserving local relationships."""
    return [normalized(block) for block in re.split(r"\n\s*\n", source) if block.strip()]


def paragraph_matches(source: str, *patterns: str) -> bool:
    """Require all regex relationships to occur in one policy paragraph."""
    return any(all(re.search(pattern, block) for pattern in patterns) for block in paragraphs(source))


def token_pattern(token: str) -> str:
    """Match a policy token without accepting substrings such as PR/proyecto."""
    return rf"(?<!\w){re.escape(normalized(token))}(?!\w)"


def verification_example(source: str) -> tuple[bool, bool]:
    """Validate the explicitly labelled verification.json example and skip details."""
    fence = re.compile(r"```json\s*\n(.*?)```", flags=re.DOTALL | re.IGNORECASE)
    for match in fence.finditer(source):
        introduction = normalized(source[max(0, match.start() - 240) : match.start()])
        if not re.search(r"(?:ejemplo|example)[^.\n]*verification\.json", introduction):
            continue
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or set(payload) < {"status", "checks"}:
            continue
        if payload["status"] not in {"passed", "failed"}:
            continue
        checks = payload["checks"]
        if not isinstance(checks, list) or not checks:
            continue
        skips_justified = True
        for check in checks:
            if not isinstance(check, dict):
                break
            if not isinstance(check.get("name"), str) or not check["name"].strip():
                break
            if check.get("result") not in {"pass", "fail", "skipped"}:
                break
            if not isinstance(check.get("detail"), str):
                break
            if check["result"] == "skipped" and not check["detail"].strip():
                skips_justified = False
        else:
            return True, skips_justified
    return False, False


def validate(source: str) -> list[tuple[str, str]]:
    text = normalized(source)
    line_text = "\n".join(normalized(line) for line in source.splitlines())
    failures: list[tuple[str, str]] = []
    verification_valid, skips_justified = verification_example(source)

    def require(name: str, condition: bool, detail: str) -> None:
        if not condition:
            failures.append((name, detail))

    require(
        "project_identity",
        re.search(token_pattern("Odoo16iRG"), text) is not None
        and not re.search(
            r"(?m)^\s*(?:[-*]\s*)?(?:todo|pendiente)(?:\s*:.*)?\s*$"
            r"|<\s*(?:nombre|indicar|adaptar)[^>]*>"
            r"|\[\s*(?:nombre|indicar|adaptar)[^\]]*\]"
            r"|nombre[_ -]+del?[_ -]+proyecto",
            line_text,
        ),
        "use the real Odoo16iRG name and remove editorial placeholders",
    )
    lifecycle_chain = (
        r"plan\s*(?:→|->)\s*implementacion\s*/\s*tdd\s*(?:→|->)\s*review"
        r"\s*(?:→|->)\s*validacion\s*(?:→|->)\s*documentacion"
        r"\s*(?:→|->)\s*publicacion\s+autorizada"
    )
    require(
        "lifecycle",
        paragraph_matches(
            source,
            r"flujo\s+canonico(?:\s+exacto)?\s+(?:es|sera)\s*:",
            lifecycle_chain,
        ),
        "declare the exact six-stage canonical lifecycle",
    )
    require(
        "coder_tdd",
        paragraph_matches(
            source,
            r"(?:codificador|implementador)\s+(?:es\s+)?(?:el\s+)?(?:propietari[oa]|responsable)"
            r"(?:\s+de)?\s+tdd",
            r"red.{0,80}(?:antes|previo).{0,80}(?:codigo\s+de\s+produccion|produccion|implement)",
            r"(?:despues|luego|entonces).{0,80}(?:implement|cambio).{0,80}green",
        ),
        "assign RED and GREEN TDD ownership to the coder",
    )
    require(
        "independent_validator",
        paragraph_matches(
            source,
            r"validador.{0,50}independiente|independiente.{0,50}validador",
            r"no\s+(?:edita(?:\s+ni|\s+o)?\s+)?corrige.{0,30}codigo\s+de\s+produccion"
            r"|no\s+edita.{0,30}codigo\s+de\s+produccion",
        ),
        "make validation independent and forbid production-code corrections by the validator",
    )
    require(
        "gate_rework",
        paragraph_matches(
            source,
            r"gate.{0,20}fall[ao]\s*,?\s*reabre.{0,30}implementacion",
            r"(?:correccion.{0,40}escalado|escalado.{0,40}correccion).{0,50}(?:separad|distint)",
            r"(?:corregir|correccion).{0,30}no.{0,30}(?:implica|requiere).{0,20}escalar",
        ),
        "reopen implementation on failed gates and separate correction from escalation",
    )
    require(
        "mission_levels",
        paragraph_matches(
            source,
            r"(?:solo\s+lectura|read.only).{0,30}(?:no\s+crea[n]?\s+mision|sin\s+mision|none)",
            r"(?:trivial|documentacion|configuracion).{0,40}(?:mision\s+ligera|light)",
            r"(?:feature|bugfix|seguridad|cross.module|cambio\s+de\s+comportamiento).{0,80}(?:mision\s+completa|full)",
        ),
        "define proportional none, light and full mission levels",
    )
    require(
        "mission_artifacts",
        paragraph_matches(
            source,
            r"execution\.md",
            r"evidencia\s+concisa",
            r"`?diff\.patch`?\s+(?:es\s+)?opcional",
        ),
        "use execution.md, concise evidence and an optional diff.patch",
    )
    require(
        "verification_json",
        verification_valid and skips_justified,
        "include an explicitly labelled, schema-valid verification.json example",
    )
    require(
        "check_results",
        verification_valid
        and skips_justified
        and paragraph_matches(
            source,
            r"(?:result|resultado).{0,30}solo\s+admite.{0,30}" + token_pattern("pass")
            + r".{0,20}" + token_pattern("fail") + r".{0,20}" + token_pattern("skipped"),
            r"(?:skip|skipped).{0,50}(?:requiere|exige).{0,30}justificacion",
        ),
        "allow pass/fail/skipped results and require skip justification",
    )
    require(
        "knowledge_path",
        ".agents/knowledge/odoo_development_modding/artifacts/" in source,
        "set the canonical reusable-knowledge path",
    )
    require(
        "worktree_runtime",
        paragraph_matches(
            source,
            r"docker.compose\.local\.yml",
            r"worktree\s+(?:se\s+aplica|usa|requiere).{0,20}(?:un\s+)?overlay",
            r"(?:cleanup|limpieza|limpiar).{0,100}restaur",
        ),
        "specify compose worktree overlay, cleanup and restoration",
    )
    require(
        "publication_separation",
        paragraph_matches(
            source,
            token_pattern("commit"),
            token_pattern("push"),
            token_pattern("PR"),
            r"(?:acciones|autorizaciones).{0,30}separad",
            r"autorizar\s+commit.{0,20}no\s+autoriza\s+push.{0,20}" + token_pattern("PR"),
            r"autorizar\s+push.{0,20}(?:no|tampoco)\s+autoriza\s+" + token_pattern("PR"),
        ),
        "distinguish commit, push and PR authorization",
    )
    require(
        "single_use_push",
        paragraph_matches(
            source,
            r"autorizacion\s+de\s+push.{0,30}(?:un\s+solo\s+uso|una\s+sola\s+vez|uso\s+unico)",
            r"(?:ligad[ao]|vinculad[ao]|limitad[ao]).{0,20}remoto.{0,20}rama.{0,20}alcance",
            r"(?:despues\s+de\s+usarla|cambio.{0,20}material).{0,80}(?:autorizacion\s+nueva|ok\s+nuevo)",
        ),
        "make push authorization single-use and bind it to remote, branch and scope",
    )
    require(
        "server_security",
        paragraph_matches(
            source,
            r"(?:restricciones|permisos|controles).{0,20}" + token_pattern("UI")
            + r".{0,20}(?:no|nunca)\s+sustituyen",
            r"controles?\s+(?:del\s+servidor|server.side).{0,30}acciones?\s+protegidas?",
            r"accion\s+protegida.{0,30}(?:exige|requiere).{0,30}(?:autorizacion|control).{0,20}(?:server.side|servidor)",
        ),
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
