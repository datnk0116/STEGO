#!/usr/bin/env python3
"""Validate STEGO provenance, Git history, evidence hashes and documentation status."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from dataclasses import dataclass, field
from pathlib import Path

PROVENANCE = "results/verification/provenance.json"
GATE_JSON = "results/verification/quality-gate.json"
GATE_LOG = "results/logs/quality-gate-tests.log"
MANIFEST = "results/artifact_manifest.json"
DOCS = ("README.md", "report/REPORT.md", "docs/QUALITY_GATE.md", "docs/QUALITY_ASSURANCE_PLAN.md", "docs/DEFENSE_QA.md", "results/README.md")
START, END = "<!-- PROVENANCE_STATUS_START -->", "<!-- PROVENANCE_STATUS_END -->"
HIST_START, HIST_END = "<!-- HISTORICAL_PROVENANCE_START -->", "<!-- HISTORICAL_PROVENANCE_END -->"
STATUS_BODY = "**Verification provenance:** The canonical run record is results/verification/provenance.json. tested_commit identifies the source revision actually executed. The evidence-packaging commit and current HEAD are derived from Git history by scripts/check_provenance_consistency.py; they are not copied into this snapshot. Documentation-only changes do not stale the technical gate. Changes to source, tests, challenge data, dependencies, artifact manifest, or gate implementation do. Submission-package freshness is assessed separately."
OLD_REFS = ("a040e3863145038b786ba6719629e636fdf2e565", "a040e38", "3bb2b57790d164a6997ee1afe157a0fc7a8a8807", "3bb2b57")
GATE_OUTPUTS = {PROVENANCE, GATE_JSON, GATE_LOG}
TECH_EXACT = {"requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile", "Pipfile.lock", "setup.cfg", "tox.ini", "pytest.ini", ".python-version", "Dockerfile", "Makefile", "setup.py", "environment.yml", ".gitmodules", MANIFEST, "scripts/verify_reproducibility.py", "scripts/check_provenance_consistency.py"}
TECH_PREFIX = ("src/", "tests/", "data/", ".github/workflows/")
PACKAGE_EXACT = {"README.md", "requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile", "Pipfile.lock", "Dockerfile", "Makefile", "setup.py", "environment.yml", "scripts/build_submission.py", "report/REPORT.md"}
PACKAGE_PREFIX = ("src/", "tests/", "scripts/", "data/", "docs/", "references/", "report/")
RESULT_PREFIX = ("results/blue3/", "results/sleepy_alarm/", "results/steganalysis/")

@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[tuple[str, bool, str]] = field(default_factory=list)
    derived: dict = field(default_factory=dict)
    @property
    def passed(self): return not self.errors
    def add(self, name, ok, detail, warning=False):
        self.checks.append((name, ok, detail))
        if not ok: (self.warnings if warning else self.errors).append(f"{name}: {detail}")

def run(root, *args, check=True):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.rstrip()

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError(f"Expected JSON object: {path}")
    return value

def commit_exists(root, value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{40}", value)) and subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=root, capture_output=True).returncode == 0

def ancestor(root, a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=root, capture_output=True).returncode == 0

def blob(root, commit, path):
    p = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=root, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None

def evidence_commit(root, tested, head, expected_blobs):
    for sha in run(root, "rev-list", "--reverse", "--ancestry-path", f"{tested}..{head}").splitlines():
        if all(blob(root, sha, path) == value for path, value in expected_blobs.items()): return sha
    return None

def dirty_paths(root):
    out = []
    for line in run(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(line) > 3:
            path = line[3:].strip().strip('"')
            out.append(path.split(" -> ", 1)[-1])
    return out

def changed(root, a, b):
    return sorted(x for x in run(root, "diff", "--name-only", a, b).splitlines() if x)

def classify(paths):
    result = {"technical_gate": [], "submission_package": [], "experiment_results": [], "documentation_only": []}
    for path in paths:
        if path in GATE_OUTPUTS: continue
        if path.startswith("results/submission/"):
            result["submission_package"].append(path)
            continue
        if path in TECH_EXACT or path.startswith(TECH_PREFIX): result["technical_gate"].append(path)
        elif path in PACKAGE_EXACT or path.startswith(PACKAGE_PREFIX): result["submission_package"].append(path)
        elif path.startswith(RESULT_PREFIX) or path.startswith("results/"): result["experiment_results"].append(path)
        elif path.endswith(".md"): result["documentation_only"].append(path)
    return result

def doc_status(text):
    if text.count(START) != 1 or text.count(END) != 1: return None
    return text[text.index(START) + len(START):text.index(END)].strip()

def without_historical(text):
    return re.sub(re.escape(HIST_START) + r".*?" + re.escape(HIST_END), "", text, flags=re.S)

def check_docs(root, report):
    bodies = []
    for rel in DOCS:
        path = root / rel
        if not path.is_file():
            report.add(f"Documentation {rel}", False, "missing")
            continue
        text = path.read_text(encoding="utf-8")
        body = doc_status(text)
        report.add(f"Documentation {rel}", body == STATUS_BODY, "canonical status block synchronized" if body == STATUS_BODY else "missing, duplicated or inconsistent status block")
        if body is not None: bodies.append(body)
        legacy = [x for x in OLD_REFS if x in without_historical(text)]
        report.add(f"Historical references {rel}", not legacy, "no unlabeled legacy revisions" if not legacy else f"legacy references outside historical block: {legacy}")
    ok = len(bodies) == len(DOCS) and len(set(bodies)) == 1 and bodies[0] == STATUS_BODY
    report.add("Documentation blocks agree", ok, "all six blocks are identical" if ok else "documentation status blocks differ or are missing")

def validate_repository(root, pre_commit=False, require_submission_package=False):
    root = Path(root).resolve()
    report = Report()
    try: prov = read_json(root / PROVENANCE)
    except Exception as exc:
        report.add("Canonical provenance", False, str(exc))
        return report
    report.add("Canonical provenance", True, "loaded")
    required = {"schema_version", "snapshot_type", "verification_id", "created_at_utc", "repository", "branch", "tested_commit", "working_tree_before_run", "evidence_files", "artifacts", "quality_gate", "limitations", "submission_package"}
    missing = sorted(required - prov.keys())
    report.add("Required fields", not missing, "complete" if not missing else f"missing {missing}")
    report.add("Schema version", prov.get("schema_version") == 1, "version 1" if prov.get("schema_version") == 1 else "expected version 1")
    kind = prov.get("snapshot_type")
    report.add("Snapshot type", kind in {"generated_run", "retrospective_migration"}, "recognized" if kind in {"generated_run", "retrospective_migration"} else "unknown snapshot type")
    if kind == "retrospective_migration":
        report.add("Historical run ID", prov.get("verification_id") is None, "unknown run ID kept null" if prov.get("verification_id") is None else "do not invent historical run ID")
    elif kind == "generated_run":
        report.add("Generated run ID", isinstance(prov.get("verification_id"), str) and bool(prov.get("verification_id")), "present" if prov.get("verification_id") else "missing")
    try:
        gate = read_json(root / GATE_JSON)
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if not isinstance(manifest, list): raise ValueError("manifest must be an array")
    except Exception as exc:
        report.add("Gate JSON / manifest", False, str(exc))
        return report
    try:
        head = run(root, "rev-parse", "HEAD")
        tested = prov.get("tested_commit", "")
        exists = commit_exists(root, tested)
        report.add("Tested commit exists", exists, tested if exists else f"invalid or unavailable: {tested}")
        is_ancestor = ancestor(root, tested, head) if exists else False
        if exists: report.add("Tested commit is ancestor of HEAD", is_ancestor, "yes" if is_ancestor else "no")
        report.derived["current_head"] = head
    except Exception as exc:
        report.add("Git history", False, str(exc))
        return report
    report.add("Gate tested commit", gate.get("git", {}).get("commit") == tested, "matches canonical snapshot" if gate.get("git", {}).get("commit") == tested else "does not match")
    report.add("Gate timestamp", gate.get("created_at_utc") == prov.get("created_at_utc"), "matches" if gate.get("created_at_utc") == prov.get("created_at_utc") else "does not match")
    report.add("Gate branch", gate.get("git", {}).get("branch") == prov.get("branch"), "matches" if gate.get("git", {}).get("branch") == prov.get("branch") else "does not match")
    working = prov.get("working_tree_before_run", {})
    if pre_commit:
        report.add("Pre-run state", working.get("captured") is True and working.get("clean") is True, "clean state captured" if working.get("captured") is True and working.get("clean") is True else "must be captured and clean")
        report.add("Tested HEAD", tested == head, "current HEAD was tested" if tested == head else "tested commit differs from HEAD")
    elif working.get("captured") is not True:
        report.add("Historical pre-run state", False, "not recorded; post-generation status cannot reconstruct it", warning=True)

    expected_blobs = {}
    for key, rel in (("quality_gate_json", GATE_JSON), ("quality_gate_log", GATE_LOG), ("artifact_manifest", MANIFEST)):
        item = prov.get("evidence_files", {}).get(key, {})
        path = root / rel
        ok = item.get("path") == rel and path.is_file() and item.get("sha256") == sha256(path)
        report.add(f"Evidence hash {key}", ok, "matches" if ok else f"missing or mismatch: {rel}")
        if path.is_file(): expected_blobs[rel] = run(root, "hash-object", rel)

    manifest_artifacts = {x.get("path"): x for x in prov.get("artifacts", []) if isinstance(x, dict)}
    gate_artifacts = gate.get("artifact_integrity", {})
    artifacts_ok = bool(manifest)
    for item in manifest:
        rel = item.get("path")
        path = root / rel if isinstance(rel, str) else None
        if path is None or not path.is_file():
            artifacts_ok = False
            report.add(f"Artifact {rel}", False, "missing or invalid")
            continue
        size, digest = path.stat().st_size, sha256(path)
        match = size == item.get("bytes") and digest == item.get("sha256") and manifest_artifacts.get(rel, {}).get("bytes") == size and manifest_artifacts.get(rel, {}).get("sha256") == digest
        artifacts_ok = artifacts_ok and match
        report.add(f"Artifact integrity {rel}", match, "size/hash match" if match else "manifest/provenance mismatch")
        gate_item = next((x for x in gate_artifacts.values() if x.get("path") == rel), None)
        gate_match = bool(gate_item and gate_item.get("passed") is True and gate_item.get("actual_bytes") == size and gate_item.get("actual_sha256") == digest)
        artifacts_ok = artifacts_ok and gate_match
        report.add(f"Gate artifact record {rel}", gate_match, "matches" if gate_match else "missing or inconsistent")
    report.add("Artifact manifest coverage", len(manifest) == len(manifest_artifacts) and bool(manifest), "all artifacts represented" if len(manifest) == len(manifest_artifacts) and manifest else "coverage mismatch")

    tests = gate.get("unit_tests", {})
    ran, expected = tests.get("tests_run"), tests.get("expected_test_methods")
    tests_ok = tests.get("passed") is True and tests.get("exit_code") == 0 and isinstance(ran, int) and ran == expected
    log_path = root / GATE_LOG
    log_text = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    match = re.search(r"Ran\s+(\d+)\s+tests?", log_text)
    log_count = int(match.group(1)) if match else None
    log_ok = log_text.rstrip().endswith("OK")
    report.add("Unit tests", tests_ok, f"{ran}/{expected}; exit={tests.get('exit_code')}" if tests_ok else "failed or count mismatch")
    report.add("Gate log", log_count == ran and log_ok, f"{log_count} tests; OK={log_ok}" if log_count == ran and log_ok else "log and JSON disagree")
    decoders = gate.get("official_decoder_verification", {})
    blue = decoders.get("blue3", {}).get("exact_match") is True
    audio = decoders.get("sleepy_alarm_reference_assisted", {}).get("exact_match") is True
    report.add("Blue 3 decoder", blue, "exact match" if blue else "not exact")
    report.add("Sleepy Alarm reference-assisted decoder", audio, "exact match" if audio else "not exact")
    overall = gate.get("overall_passed") is True and tests_ok and artifacts_ok and blue and audio
    report.add("Quality gate", overall, "PASS agrees with underlying evidence" if overall else "FAIL or inconsistent")
    summary = prov.get("quality_gate", {})
    expected_summary = {"tests_passed": tests_ok, "tests_run": ran, "tests_expected": expected, "exit_code": tests.get("exit_code"), "artifact_integrity_passed": artifacts_ok, "blue3_exact_match": blue, "sleepy_alarm_reference_assisted_exact_match": audio, "overall_passed": overall}
    report.add("Canonical summary", all(summary.get(k) == v for k, v in expected_summary.items()), "matches gate JSON" if all(summary.get(k) == v for k, v in expected_summary.items()) else "differs from gate JSON")
    check_docs(root, report)

    if pre_commit:
        unexpected = sorted(set(dirty_paths(root)) - GATE_OUTPUTS)
        report.add("Pre-commit dirty paths", not unexpected, "only gate outputs changed" if not unexpected else f"unexpected: {unexpected}")
        report.derived["evidence_commit"] = None
        report.derived["technical_gate_freshness"] = "PRE_COMMIT_SNAPSHOT"
    else:
        ev = evidence_commit(root, tested, head, expected_blobs) if exists and is_ancestor else None
        report.add("Evidence commit", ev is not None, ev or "no descendant stores the exact gate JSON/log/manifest blobs")
        report.derived["evidence_commit"] = ev
        if ev:
            historic = kind == "retrospective_migration"
            p_blob, head_blob = blob(root, ev, PROVENANCE), blob(root, head, PROVENANCE)
            if historic:
                relation_ok = head_blob is not None and p_blob is None
                detail = "migration snapshot is committed after historical evidence" if relation_ok else "retrospective snapshot must be added after the historical evidence commit"
            else:
                relation_ok = p_blob is not None and p_blob == head_blob
                detail = "same provenance blob in evidence commit and HEAD" if relation_ok else "provenance is missing or differs at evidence commit"
            report.add("Provenance/evidence relationship", relation_ok, detail)
        paths = changed(root, tested, head) if exists and is_ancestor else []
        classes = classify(paths)
        report.derived["changed_paths_after_tested_commit"] = paths
        report.derived["change_classification"] = classes
        fresh = not classes["technical_gate"]
        report.add("Technical gate freshness", fresh, "no technical changes after tested commit" if fresh else f"stale: {classes['technical_gate']}")
        report.add("Experiment result freshness", not classes["experiment_results"], "unchanged" if not classes["experiment_results"] else f"changed: {classes['experiment_results']}", warning=True)
        pkg = prov.get("submission_package", {})
        built = pkg.get("built_from_commit")
        pkg_paths = []
        if isinstance(built, str) and commit_exists(root, built) and ancestor(root, built, head):
            c = classify(changed(root, built, head))
            pkg_paths = c["technical_gate"] + c["submission_package"]
        package_ok = pkg.get("status") == "verified" and isinstance(built, str) and not pkg_paths
        package_state = "FRESH" if package_ok else ("STALE" if pkg_paths else "NOT_VERIFIED")
        report.derived["submission_package_freshness"] = package_state
        report.add("Submission package", package_ok or not require_submission_package, "verified and unchanged" if package_ok else package_state, warning=not require_submission_package)
        relevant = [p for p in dirty_paths(root) if p in GATE_OUTPUTS or p in DOCS or p.startswith(("src/", "tests/", "data/", "scripts/", "report/", "docs/", "results/submission/"))]
        report.add("Working tree", not relevant, "relevant files committed" if not relevant else f"uncommitted: {relevant}")
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pre-commit", action="store_true")
    parser.add_argument("--require-submission-package", action="store_true")
    args = parser.parse_args(argv)
    report = validate_repository(args.root, pre_commit=args.pre_commit, require_submission_package=args.require_submission_package)
    print("PROVENANCE VALIDATION (PRE-COMMIT)" if args.pre_commit else "PROVENANCE VALIDATION (STRICT)")
    for name, ok, detail in report.checks: print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    for warning in report.warnings: print(f"[WARN] {warning}")
    if report.derived: print("DERIVED STATE\n" + json.dumps(report.derived, indent=2, ensure_ascii=False))
    print(f"Overall: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1

if __name__ == "__main__": raise SystemExit(main())
