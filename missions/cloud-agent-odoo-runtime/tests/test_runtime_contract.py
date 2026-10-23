# -*- coding: utf-8 -*-
"""Contrato del runtime local de Cloud Agents. No arranca Docker ni Odoo."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CURSOR = ROOT / ".cursor"
RUNTIME = CURSOR / "runtime"
TEMPLATE = RUNTIME / "odoo-local-compose.yml"
CONF = RUNTIME / "odoo.conf"
ENV_FILE = RUNTIME / "compose.env"
INSTALL = CURSOR / "install.sh"
START = CURSOR / "start.sh"
MATERIALIZE = CURSOR / "materialize-compose.sh"
DOCKERFILE = CURSOR / "Dockerfile"
ENV_JSON = CURSOR / "environment.json"
SENTINEL = "# cursor-cloud-runtime-generated: odoo16irg-local-v1"
COMPOSE_FLAGS = "--env-file .cursor/runtime/compose.env -f docker-compose.local.yml"
FORBIDDEN_HOSTS = (
    "odoobetairg.laramieuniversity.com",
    "app.institutoraimongaja.com",
)
DEPLOY_NAMES = (
    "odoo_latest",
    "pgodoo_latest",
    "dbfilestore",
    "nat16_pgodoo_latest",
)


class RuntimeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = (
            TEMPLATE,
            CONF,
            ENV_FILE,
            INSTALL,
            START,
            MATERIALIZE,
            DOCKERFILE,
            ENV_JSON,
        )
        missing = [str(path) for path in cls.paths if not path.is_file()]
        if missing:
            raise AssertionError("faltan archivos de runtime: %s" % ", ".join(missing))
        cls.texts = {path: path.read_text(encoding="utf-8") for path in cls.paths}

    def test_no_remote_hosts_or_deployment_names(self):
        blob = "\n".join(self.texts.values())
        for host in FORBIDDEN_HOSTS:
            self.assertNotIn(host, blob)
        scanned = "\n".join(
            self.texts[path] for path in (TEMPLATE, CONF, INSTALL, START, MATERIALIZE)
        )
        for name in DEPLOY_NAMES:
            self.assertNotIn(name, scanned)

    def test_compose_invocations_are_pinned(self):
        for path in (INSTALL, START):
            text = self.texts[path]
            self.assertNotIn("COMPOSE_FILE", text)
            self.assertNotIn("docker-compose.override.yml", text)
            self.assertNotIn("docker-compose.yml", text)
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "docker compose" not in stripped:
                    continue
                self.assertIn(COMPOSE_FLAGS, stripped, path)
                self.assertEqual(stripped.count("-f "), 1, stripped)

    def test_install_materializes_before_pull(self):
        code = "\n".join(
            line for line in self.texts[INSTALL].splitlines() if not line.strip().startswith("#")
        )
        materialize_at = code.find("materialize-compose.sh")
        pull_at = code.find(" pull")
        self.assertGreater(materialize_at, 0)
        self.assertGreater(pull_at, materialize_at)

    def test_template_is_local_only(self):
        text = self.texts[TEMPLATE]
        self.assertTrue(text.startswith(SENTINEL + "\n"))
        self.assertNotIn("${", text)
        self.assertNotIn("env_file", text)
        self.assertNotIn("network_mode:", text)
        self.assertNotIn("privileged:", text)
        self.assertNotIn("docker.sock", text)
        self.assertNotIn("external:", text)
        self.assertNotIn("./etc", text)
        self.assertNotIn("0.0.0.0", text)
        self.assertIn("127.0.0.1:8069:8069", text)
        self.assertIn("127.0.0.1:8072:8072", text)
        self.assertIn("./addons-extra:/mnt/extra-addons:ro", text)
        self.assertIn(
            "./.cursor/runtime/odoo.conf:/etc/odoo/odoo.conf:ro",
            text,
        )
        self.assertNotIn("environment:", self._service_block(text, "odoo_local"))
        self.assertIn("aliases:", self._service_block(text, "pgodoo_local"))
        self.assertIn("- db", self._service_block(text, "pgodoo_local"))
        published = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("- \"127.0.0.1:")
            or line.strip().startswith("- '127.0.0.1:")
        ]
        self.assertEqual(
            published,
            ['- "127.0.0.1:8069:8069"', '- "127.0.0.1:8072:8072"'],
        )
        self.assertEqual(text.count("\n    ports:\n"), 1)

    def test_conf_has_no_interpolation_and_points_at_local_db(self):
        text = self.texts[CONF]
        self.assertNotIn("${", text)
        self.assertIn("db_host = pgodoo_local", text)
        self.assertIn("admin_passwd = local-disposable", text)
        self.assertIn("list_db = False", text)
        self.assertNotIn("./etc", text)

    def test_scripts_do_not_interpolate_or_mount_repo_etc(self):
        for path in (INSTALL, START, MATERIALIZE):
            text = self.texts[path]
            self.assertNotIn("${", text, path)
            self.assertNotIn("env_file", text, path)
            self.assertNotIn("./etc", text, path)
            self.assertNotIn("docker.sock", text, path)

    def test_environment_json_shape(self):
        payload = json.loads(self.texts[ENV_JSON])
        self.assertEqual(payload["user"], "ubuntu")
        self.assertEqual(payload["build"]["dockerfile"], "Dockerfile")
        self.assertNotIn("context", payload["build"])
        self.assertNotIn("snapshot", payload)
        self.assertNotIn("$schema", payload)
        self.assertIn("[ -f .cursor/install.sh ]", payload["install"])
        self.assertIn("bash .cursor/install.sh", payload["install"])
        self.assertNotIn("|| true", payload["install"])
        self.assertIn("[ -f .cursor/start.sh ]", payload["start"])
        self.assertIn("bash .cursor/start.sh", payload["start"])
        ports = sorted(item["port"] for item in payload["ports"])
        self.assertEqual(ports, [8069, 8072])

    def test_materialize_respects_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "docker-compose.local.yml"
            runtime = root / ".cursor" / "runtime"
            runtime.mkdir(parents=True)
            shutil.copy(TEMPLATE, runtime / "odoo-local-compose.yml")
            self._materialize(root)
            first = destination.read_text(encoding="utf-8")
            self.assertTrue(first.startswith(SENTINEL + "\n"))
            self._materialize(root)
            self.assertEqual(destination.read_text(encoding="utf-8"), first)
            foreign = "services: {}\n# developer compose\n"
            destination.write_text(foreign, encoding="utf-8")
            self._materialize(root)
            self.assertEqual(destination.read_text(encoding="utf-8"), foreign)
            destination.write_text(SENTINEL + "\nold: true\n", encoding="utf-8")
            self._materialize(root)
            self.assertEqual(destination.read_text(encoding="utf-8"), first)

    def _materialize(self, root):
        completed = subprocess.run(
            ["bash", str(MATERIALIZE), str(root)],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )

    def _service_block(self, text, service):
        lines = text.splitlines()
        start = None
        for index, line in enumerate(lines):
            if line == "  %s:" % service:
                start = index
                break
        self.assertIsNotNone(start, service)
        block = []
        for line in lines[start + 1:]:
            if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
                break
            block.append(line)
        return "\n".join(block)


if __name__ == "__main__":
    unittest.main()
