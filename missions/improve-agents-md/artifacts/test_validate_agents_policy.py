#!/usr/bin/env python3
"""Regression tests for the executable AGENTS.md policy contract."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_agents_policy import validate


VALID_POLICY = r"""
# AGENTS.md - Odoo16iRG

El flujo canónico exacto es:
`Plan -> Implementación/TDD -> Review -> Validación -> Documentación -> Publicación autorizada`.

## Implementación/TDD

El codificador es propietario de TDD: escribe y ejecuta RED antes de modificar código
de producción; después implementa el mínimo cambio y ejecuta GREEN.

## Validación independiente

El validador es independiente del codificador y no edita ni corrige código de
producción. Solo verifica el resultado y emite evidencia.

Si un gate falla, reabre la fase de Implementación para que el codificador corrija.
La corrección y el escalado de capacidad son decisiones separadas; corregir no
implica escalar automáticamente.

## Misiones proporcionales

Las consultas de solo lectura no crean misión (`none`). Los cambios triviales usan
misión ligera (`light`). Features, bugfixes, seguridad o cambios cross-module usan
misión completa (`full`).

Toda misión usa `execution.md` y evidencia concisa. `diff.patch` es opcional porque
Git conserva el diff canónico.

El siguiente bloque es el ejemplo canónico de `verification.json`:

```json
{
  "status": "passed",
  "checks": [
    {"name": "unit_tests", "result": "pass", "detail": "12 passed"},
    {"name": "integration_tests", "result": "skipped", "detail": "No aplica: cambio documental"},
    {"name": "lint", "result": "fail", "detail": "Ejemplo del estado permitido"}
  ]
}
```

`status` solo admite `passed` o `failed`. Cada `result` solo admite `pass`, `fail`
o `skipped`; todo skip requiere una justificación no vacía en `detail`.

La knowledge base canónica está en
`.agents/knowledge/odoo_development_modding/artifacts/`.

## Runtime

Las pruebas locales usan `docker-compose.local.yml`. En un worktree se aplica un
overlay que monta el código aislado. Al finalizar se ejecuta cleanup de fixtures y
se restaura el servicio original; cleanup y restauración forman parte de la evidencia.

## Publicación

Commit, push y PR son acciones separadas: autorizar commit no autoriza push ni PR;
autorizar push tampoco autoriza PR.

Cada autorización de push es de un solo uso y queda ligada al remoto, rama y alcance
concretos indicados. Después de usarla, o ante cambios materiales, se exige una
autorización nueva.

## Seguridad

Las restricciones de UI no sustituyen los controles del servidor para acciones
protegidas; toda acción protegida exige autorización server-side.
"""


def failure_names(source: str) -> set[str]:
    return {name for name, _detail in validate(source)}


def replace_json_example(source: str, payload: str) -> str:
    start = source.index("```json\n") + len("```json\n")
    end = source.index("```", start)
    return source[:start] + payload + "\n" + source[end:]


class PolicyValidatorTests(unittest.TestCase):
    def assert_rejects(self, source: str, contract: str) -> None:
        self.assertIn(contract, failure_names(source))

    def test_accepts_a_conforming_policy(self) -> None:
        self.assertEqual([], validate(VALID_POLICY))

    def test_rejects_editorial_placeholders(self) -> None:
        for placeholder in (
            "TODO",
            "PENDIENTE",
            "[TODO]",
            "[PENDIENTE]",
            "<NOMBRE_PROYECTO>",
            "[NOMBRE DEL PROYECTO]",
        ):
            with self.subTest(placeholder=placeholder):
                self.assert_rejects(VALID_POLICY + "\n" + placeholder, "project_identity")

    def test_rejects_negated_lifecycle(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace("El flujo canónico exacto es:", "El flujo canónico no es:"),
            "lifecycle",
        )

    def test_rejects_tdd_not_owned_by_coder(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace(
                "El codificador es propietario de TDD:",
                "El codificador no es propietario de TDD; el validador lo ejecuta:",
            ),
            "coder_tdd",
        )

    def test_rejects_validator_that_edits_production(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace(
                "no edita ni corrige código de\nproducción",
                "sí edita y corrige código de\nproducción",
            ),
            "independent_validator",
        )

    def test_rejects_valid_independence_clause_followed_by_contradiction(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nComo excepción, el validador también puede editar y corregir código de "
            "producción antes de emitir evidencia."
        )
        self.assert_rejects(invalid, "independent_validator")

    def test_rejects_failed_gate_that_does_not_reopen_implementation(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace("reabre la fase de Implementación", "no reabre la fase de Implementación"),
            "gate_rework",
        )

    def test_rejects_correction_equated_with_escalation(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace(
                "son decisiones separadas; corregir no\nimplica escalar automáticamente",
                "son la misma decisión; corregir siempre\nimplica escalar automáticamente",
            ),
            "gate_rework",
        )

    def test_rejects_valid_gate_clause_followed_by_contradiction(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nEn tareas urgentes, si un gate falla no reabre la fase de Implementación; "
            "validación continúa igualmente."
        )
        self.assert_rejects(invalid, "gate_rework")

    def test_rejects_valid_tdd_clause_followed_by_conflicting_owner(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nEl validador es responsable de TDD y ejecuta RED y GREEN después del "
            "codificador."
        )
        self.assert_rejects(invalid, "coder_tdd")

    def test_rejects_inverted_mission_proportionality(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace(
                "Las consultas de solo lectura no crean misión (`none`). Los cambios triviales usan\nmisión ligera (`light`). Features, bugfixes, seguridad o cambios cross-module usan\nmisión completa (`full`).",
                "Las consultas de solo lectura usan misión completa (`full`). Los cambios triviales usan\nmisión completa (`full`). Features y bugfixes no crean misión (`none`) y usan\nmisión ligera (`light`).",
            ),
            "mission_levels",
        )

    def test_rejects_mandatory_diff_patch(self) -> None:
        self.assert_rejects(
            VALID_POLICY.replace("`diff.patch` es opcional", "`diff.patch` no es opcional"),
            "mission_artifacts",
        )

    def test_rejects_unlabelled_or_malformed_verification_examples(self) -> None:
        malformed = VALID_POLICY.replace(
            "El siguiente bloque es el ejemplo canónico de `verification.json`:",
            "Ejemplo genérico de datos:",
        )
        self.assert_rejects(malformed, "verification_json")

    def test_rejects_invalid_verification_schema_types(self) -> None:
        mutations = (
            ('"status": "passed"', '"status": true'),
            ('"checks": [', '"checks": {"items": ['),
            ('  ]\n}', '  ]}\n}'),
            ('{"name": "unit_tests", "result": "pass", "detail": "12 passed"}', '"pass"'),
            ('"result": "pass"', '"result": "ok"'),
        )
        for old, new in mutations:
            with self.subTest(replacement=new):
                self.assert_rejects(VALID_POLICY.replace(old, new, 1), "verification_json")

    def test_rejects_non_object_verification_root(self) -> None:
        self.assert_rejects(replace_json_example(VALID_POLICY, "[]"), "verification_json")

    def test_rejects_checks_that_are_not_a_list_of_objects(self) -> None:
        invalid_payloads = (
            '{"status": "passed", "checks": {}}',
            '{"status": "passed", "checks": ["pass"]}',
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_rejects(replace_json_example(VALID_POLICY, payload), "verification_json")

    def test_rejects_missing_required_json_keys_even_with_extra_keys(self) -> None:
        invalid_payloads = (
            '{"checks": [], "task": "demo"}',
            '{"status": "passed", "task": "demo"}',
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_rejects(replace_json_example(VALID_POLICY, payload), "verification_json")

    def test_rejects_skip_without_justification(self) -> None:
        invalid = VALID_POLICY.replace(
            '{"name": "integration_tests", "result": "skipped", "detail": "No aplica: cambio documental"}',
            '{"name": "integration_tests", "result": "skipped", "detail": ""}',
        )
        self.assert_rejects(invalid, "verification_json")
        self.assert_rejects(invalid, "check_results")

    def test_rejects_non_exclusive_check_result_policy(self) -> None:
        invalid = VALID_POLICY.replace(
            "Cada `result` solo admite `pass`, `fail`\no `skipped`",
            "Cada `result` admite cualquier valor, incluidos `pass`, `fail`\no `skipped`",
        )
        self.assert_rejects(invalid, "check_results")

    def test_rejects_noncanonical_knowledge_path(self) -> None:
        invalid = VALID_POLICY.replace(
            ".agents/knowledge/odoo_development_modding/artifacts/",
            ".agents/knowledge/artifacts/",
        )
        self.assert_rejects(invalid, "knowledge_path")

    def test_rejects_negated_worktree_runtime_contract(self) -> None:
        invalid = VALID_POLICY.replace(
            "En un worktree se aplica un\noverlay que monta el código aislado.",
            "En un worktree no se aplica un\noverlay que monte el código aislado.",
        )
        self.assert_rejects(invalid, "worktree_runtime")

    def test_rejects_valid_runtime_clause_followed_by_no_overlay_exception(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nPara cambios documentales, el worktree no usa overlay y no requiere "
            "cleanup ni restauración del servicio."
        )
        self.assert_rejects(invalid, "worktree_runtime")

    def test_pr_must_be_a_token_not_a_substring_of_proyecto(self) -> None:
        invalid = VALID_POLICY.replace("push y PR son acciones separadas", "push y proyecto son acciones separadas")
        invalid = invalid.replace("ni PR", "ni proyecto").replace("autoriza PR", "autoriza proyecto")
        self.assert_rejects(invalid, "publication_separation")

    def test_rejects_publication_authorization_contradiction(self) -> None:
        invalid = VALID_POLICY.replace(
            "autorizar commit no autoriza push ni PR;\nautorizar push tampoco autoriza PR",
            "autorizar commit autoriza push y PR;\nautorizar push también autoriza PR",
        )
        self.assert_rejects(invalid, "publication_separation")

    def test_rejects_valid_publication_clause_followed_by_bundled_authorization(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nEn cambios triviales, autorizar commit también autoriza push y PR."
        )
        self.assert_rejects(invalid, "publication_separation")

    def test_rejects_reusable_or_unscoped_push_authorization(self) -> None:
        invalid = VALID_POLICY.replace(
            "Cada autorización de push es de un solo uso y queda ligada al remoto, rama y alcance\nconcretos indicados.",
            "Cada autorización de push es reutilizable y no queda ligada al remoto, rama ni alcance\nconcretos indicados.",
        )
        self.assert_rejects(invalid, "single_use_push")

    def test_rejects_valid_push_clause_followed_by_reusable_authorization(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nLa autorización de push es reutilizable para cualquier remoto, rama y alcance."
        )
        self.assert_rejects(invalid, "single_use_push")

    def test_ui_must_be_a_token_not_a_substring_of_build(self) -> None:
        invalid = VALID_POLICY.replace(
            "Las restricciones de UI no sustituyen los controles del servidor para acciones\nprotegidas; toda acción protegida exige autorización server-side.",
            "El build no sustituye los controles del servidor para acciones protegidas;\ntoda acción protegida exige autorización server-side.",
        )
        self.assert_rejects(invalid, "server_security")

    def test_rejects_ui_only_security(self) -> None:
        invalid = VALID_POLICY.replace(
            "Las restricciones de UI no sustituyen los controles del servidor para acciones\nprotegidas; toda acción protegida exige autorización server-side.",
            "Las restricciones de UI sustituyen los controles del servidor para acciones\nprotegidas; ninguna acción protegida exige autorización server-side.",
        )
        self.assert_rejects(invalid, "server_security")

    def test_rejects_valid_server_clause_followed_by_ui_only_exception(self) -> None:
        invalid = VALID_POLICY + (
            "\n\nPara acciones internas protegidas, las restricciones de UI sí sustituyen "
            "los controles del servidor y bastan por sí solas."
        )
        self.assert_rejects(invalid, "server_security")


if __name__ == "__main__":
    unittest.main()
