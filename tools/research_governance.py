#!/usr/bin/env python3
"""Search ledger and prospective family preflight. Never opens market data."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

LEDGER = "research/SEARCH_LEDGER.json"
FREEZES = "research/SEARCH_FAMILY_FREEZES.json"
YEARS = {2020, 2021, 2022, 2023, 2024}
UNIT_RE = re.compile(r"^(?:#{2,6}\s+|-\s+\*\*)(?:(?:R\d{3}\s*/\s*)?|Hipótesis\s+)(H-ES-\d{3}|H\d{3})(.*)$", re.M)



def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe_path(root, relative, prefixes):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not any(relative.startswith(p) for p in prefixes):
        raise ValueError(f"invalid scoped path: {relative}")
    full = (root / path).resolve()
    if not full.is_relative_to(root.resolve()):
        raise ValueError("path escapes repository")
    return full


def report_path(root, relative):
    # The family tool cannot become an alternative route into an OOS report.
    if re.search(r"holdout|validation|oos|2025|2026", relative, re.I):
        raise ValueError("holdout reports require their separately authorized adapter")
    return safe_path(root, relative, ("results/development/",))


def read_development_report(root, relative):
    payload = json.loads(report_path(root, relative).read_text())
    if not str(payload.get("stage", "")).startswith("DEVELOPMENT"):
        raise ValueError(f"not a development report: {relative}")
    years = payload.get("loaded_years", payload.get("market_loaded_years"))
    if not isinstance(years, list) or not years or not set(years).issubset(YEARS):
        raise ValueError("unexpected loaded years")
    if payload.get("holdout_2025_loaded") is not False or payload.get("holdout_2026_loaded") is not False:
        raise ValueError("holdout discipline unavailable or failed")
    for key, value in payload.items():
        if "year" in key and isinstance(value, list) and value and not set(value).issubset(YEARS):
            raise ValueError("non-development context years")
    return payload


def declared_units(text):
    out = {}
    for match in UNIT_RE.finditer(text):
        key, tail = match.groups()
        if key in out:
            raise ValueError(f"duplicate declared ID: {key}")
        out[key] = tail.strip(" *:—-")
    return out


def alpha_for_index(index):
    if type(index) is not int or index < 1:
        raise ValueError("family index must be a positive integer")
    return 0.05 / (index * (index + 1))


def holm_adjust(pvalues):
    if not pvalues:
        raise ValueError("empty correction family")
    for p in pvalues.values():
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("invalid p-value")
    ordered = sorted(pvalues, key=lambda key: (pvalues[key], key))
    out, running = {}, 0.0
    for i, key in enumerate(ordered):
        running = max(running, (len(ordered) - i) * pvalues[key])
        out[key] = min(1.0, running)
    return out


def validate_family(root, family):
    required = {"id", "index", "question", "origin_units", "data_role", "members",
                "definition_files", "result_artifacts", "independent_inference_justification"}
    if not required.issubset(family):
        raise ValueError("incomplete family definition")
    alpha_for_index(family["index"])
    if family["data_role"] not in {"REUSED_DEVELOPMENT", "INDEPENDENT_EVALUATION"}:
        raise ValueError("unknown data role")
    if not family["question"] or not family["members"] or not family["definition_files"] or not family["result_artifacts"]:
        raise ValueError("empty family question, members, definitions or results")
    member_ids = []
    for member in family["members"]:
        if not {"id", "preregistration_path", "definition", "alternative", "endpoint"}.issubset(member):
            raise ValueError("incomplete member definition")
        if not all(member[k] for k in ("id", "definition", "alternative", "endpoint")):
            raise ValueError("empty member specification")
        safe_path(root, member["preregistration_path"], ("research/",))
        if member["preregistration_path"] not in family["definition_files"]:
            raise ValueError("member preregistration must be fingerprinted")
        if member.get("research_instrument") not in {"MES", "ES", "NQ", "MNQ"}:
            raise ValueError("research instrument must be explicit")
        if member.get("analysis_kind") not in {"DIRECTIONAL", "VOLATILITY", "STRATEGY"}:
            raise ValueError("analysis kind must be explicit")
        if member["analysis_kind"] == "STRATEGY":
            execution = member.get("execution_instrument")
            costs = member.get("costs", {})
            if execution not in {"MES", "ES", "NQ", "MNQ"} or costs.get("point_value_usd") != {"MES": 5, "ES": 50, "NQ": 20, "MNQ": 2}[execution]:
                raise ValueError("execution multiplier must match instrument")
            for key in ("commission_round_trip_usd", "slippage_round_trip_usd"):
                value = costs.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError("freeze instrument-specific commission/slippage")
            if execution != member["research_instrument"] and not member.get("transfer_validation_plan"):
                raise ValueError("cross-instrument strategy needs its own transfer validation plan")
        elif member.get("execution_instrument") is not None:
            raise ValueError("statistical effects are not execution strategies")
        member_ids.append(member["id"])
    if len(member_ids) != len(set(member_ids)):
        raise ValueError("duplicate family members")
    for path in family["definition_files"]:
        if not safe_path(root, path, ("research/", "tools/", "src/")).is_file():
            raise ValueError(f"missing definition file: {path}")
    for path in family["result_artifacts"]:
        report_path(root, path)
    if len(set(family["result_artifacts"])) != len(family["result_artifacts"]):
        raise ValueError("duplicate family result paths")
    if family["data_role"] == "INDEPENDENT_EVALUATION" and not family["independent_inference_justification"]:
        raise ValueError("independent evidence requires an untouched-data/inference justification")


def load_controls(root):
    return json.loads((root / LEDGER).read_text()), json.loads((root / FREEZES).read_text())


def validate_control_history(previous_ledger, previous_locks, ledger, locks):
    """A later commit cannot reset the baseline or delete/rewrite spent budgets."""
    for field in ("schema_version", "historical_baseline_commit", "historical_file_snapshots",
                  "historical_entrypoints", "historical_experiments", "historical_hypotheses", "planned_es_units", "recording_limit", "baseline_definition_paths"):
        if previous_ledger[field] != ledger[field]:
            raise ValueError(f"historical baseline rewritten: {field}")
    previous_versions = previous_ledger["version_changes"]
    if ledger["version_changes"][:len(previous_versions)] != previous_versions:
        raise ValueError("implementation version history must be append-only")
    for family_id, snapshot in previous_locks["families"].items():
        if locks["families"].get(family_id) != snapshot:
            raise ValueError("previously frozen family/budget cannot be rewritten or deleted")


def check_history_ref(root, ref):
    # Read control files only, never historical market/outcome files.
    if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        raise ValueError("history reference must be an exact commit SHA")
    subprocess.run(["git", "rev-parse", "--verify", ref + "^{commit}"], cwd=root,
                   check=True, capture_output=True)
    previous = []
    for path in (LEDGER, FREEZES):
        present = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=root,
                                 capture_output=True)
        if present.returncode:
            previous.append(None)
        else:
            raw = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=root,
                                 check=True, capture_output=True, text=True)
            previous.append(json.loads(raw.stdout))
    if previous == [None, None]:
        return  # First installation: no previous controls exist.
    if any(item is None for item in previous):
        raise ValueError("partial historical controls; refusing reset")
    validate_control_history(*previous, *load_controls(root))


def family_snapshot(root, family):
    validate_family(root, family)
    return {"family_sha256": canonical_digest(family),
            "definition_sha256": {p: digest(root / p) for p in family["definition_files"]},
            "index": family["index"], "alpha": alpha_for_index(family["index"]),
            "member_ids": sorted(m["id"] for m in family["members"])}


def get_family(ledger, family_id):
    found = [f for f in ledger["future_families"] if f["id"] == family_id]
    if len(found) != 1:
        raise ValueError("family must be registered exactly once")
    return found[0]


def validate_schedule(ledger, locks):
    families = ledger["future_families"]
    ids = [f["id"] for f in families]
    indices = sorted(f["index"] for f in families)
    if len(set(ids)) != len(ids) or indices != list(range(1, len(indices) + 1)):
        raise ValueError("family IDs/indices must be unique and consecutive")
    if set(locks["families"]) - set(ids):
        raise ValueError("spent/frozen family cannot be deleted")


def preflight_family(root, family_id):
    ledger, locks = load_controls(root)
    validate_schedule(ledger, locks)
    family = get_family(ledger, family_id)
    expected = family_snapshot(root, family)
    if locks["families"].get(family_id) != expected:
        raise ValueError("family is not frozen or its members/definitions/budget changed")
    return family


def freeze_family(root, family_id):
    ledger, locks = load_controls(root)
    validate_schedule(ledger, locks)
    family = get_family(ledger, family_id)
    if family_id in locks["families"]:
        raise ValueError("family allocation is immutable and cannot be recycled")
    if family["index"] != len(locks["families"]) + 1:
        raise ValueError("families must consume their allocations in index order")
    snapshot = family_snapshot(root, family)
    if any(report_path(root, p).exists() for p in family["result_artifacts"]):
        raise ValueError("cannot freeze after a declared outcome artifact exists")
    locks["families"][family_id] = snapshot
    (root / FREEZES).write_text(json.dumps(locks, indent=2, sort_keys=True) + "\n")
    return snapshot


def evaluate_metrics(family, metrics):
    expected = {m["id"] for m in family["members"]}
    if set(metrics) != expected:
        raise ValueError("whole-family results incomplete or contain unregistered members")
    pvalues = {}
    for key, item in metrics.items():
        if item.get("status") == "NOT_ESTIMABLE":
            pvalues[key] = 1.0
        else:
            pvalues[key] = item["p_value_two_sided"]
            if isinstance(item.get("effect"), bool) or not isinstance(item.get("effect"), (int, float)) or not math.isfinite(item["effect"]):
                raise ValueError("missing finite preregistered-direction effect")
    adjusted = holm_adjust(pvalues)
    alpha = alpha_for_index(family["index"])
    supported = [key for key in sorted(metrics) if adjusted[key] <= alpha
                 and metrics[key].get("status") != "NOT_ESTIMABLE" and metrics[key]["effect"] > 0]
    exploratory = family["data_role"] == "REUSED_DEVELOPMENT"
    if exploratory:
        status = "PROMISING_EXPLORATORY" if supported else "NOT_SUPPORTED_EXPLORATORY"
    else:
        if not family.get("independent_inference_justification"):
            raise ValueError("independent inference justification missing")
        status = "FAMILY_STATISTICAL_SUPPORT" if supported else "FAMILY_NOT_SUPPORTED"
    return {"family": family["id"], "alpha_allocation": alpha,
            "full_member_count": len(expected), "holm_adjusted_p": adjusted,
            "supported_members": supported, "status": status,
            "strategy_authorized": False,
            "validity_condition": "Formal error control requires valid selection-aware p-values; reused development remains exploratory."}


def evaluate_family(root, family_id):
    family = preflight_family(root, family_id)
    if family["data_role"] != "REUSED_DEVELOPMENT":
        raise ValueError("independent/OOS outcomes require a separately authorized adapter")
    metrics = {}
    for path in family["result_artifacts"]:
        report = read_development_report(root, path)
        part = report.get("family_metrics")
        if not isinstance(part, dict):
            raise ValueError("family report must supply explicit family_metrics")
        if set(metrics) & set(part):
            raise ValueError("duplicate member results across family blocks")
        metrics.update(part)
    return evaluate_metrics(family, metrics)


def git_blob_digest(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def build_registry(root):
    ledger, locks = load_controls(root)
    for record in ledger["historical_file_snapshots"]:
        p = safe_path(root, record["path"], ("research/", "config/"))
        if not p.is_file() or git_blob_digest(p) != record["git_blob_sha"]:
            raise ValueError("frozen historical definition/registry changed: " + record["path"])
    for record in ledger["historical_entrypoints"]:
        p = safe_path(root, record["path"], ("research/", "src/"))
        actual = git_blob_digest(p)
        if actual != record["git_blob_sha"]:
            versions = [v for v in ledger["version_changes"] if v.get("path") == record["path"]
                        and v.get("before") == record["git_blob_sha"] and v.get("after") == actual
                        and v.get("reason") and v.get("frozen_results_retained") is True]
            if len(versions) != 1:
                raise ValueError("unregistered implementation version: " + record["path"])
    validate_schedule(ledger, locks)
    legacy = {h["id"] for h in ledger["historical_hypotheses"]}
    future_ids, future_files, evaluations = set(), set(), []
    for family in ledger["future_families"]:
        preflight_family(root, family["id"])
        ids = {m["id"] for m in family["members"]}
        if ids & (legacy | future_ids):
            raise ValueError("reused or multiply assigned trial ID")
        future_ids |= ids
        future_files |= set(family["definition_files"])
        if any(report_path(root, p).exists() for p in family["result_artifacts"]):
            evaluations.append(evaluate_family(root, family["id"]))
        else:
            evaluations.append({"family": family["id"], "status": "FROZEN_AWAITING_RESULTS",
                                "alpha_allocation": alpha_for_index(family["index"]),
                                "full_member_count": len(ids), "strategy_authorized": False})
    if set(locks["families"]) != {f["id"] for f in ledger["future_families"]}:
        raise ValueError("spent/frozen family cannot be removed or left unregistered")
    baseline = set(ledger["baseline_definition_paths"])
    old_code = {v["path"] for v in ledger["historical_entrypoints"]}
    for p in (root / "research").rglob("*.md"):
        relative = str(p.relative_to(root))
        if relative in baseline or not re.search(r"PRE_REGISTRATION|(?:RESEARCH_)?PLAN|STRATEGY_FREEZE|ENGINE_SPEC", p.name):
            continue
        declared = declared_units(p.read_text())
        if relative not in future_files or not declared or set(declared) - future_ids:
            raise ValueError("unregistered new definition/variants: " + relative)
        for unit in declared:
            binding = [m for f in ledger["future_families"] for m in f["members"] if m["id"] == unit]
            if len(binding) != 1 or binding[0]["preregistration_path"] != relative:
                raise ValueError("hypothesis bound to wrong definition")
    for folder in ("research", "tools"):
        for p in (root / folder).rglob("*.py"):
            relative = str(p.relative_to(root))
            if p.name.startswith("test_") or not re.match(r"(?:r\d{3}|b\d{2}|run_(?:es|mes)_b\d+)", p.name, re.I):
                continue
            if relative not in old_code | future_files:
                raise ValueError("unregistered new implementation: " + relative)
    return {"schema_version": 1, "historical_baseline_commit": ledger["historical_baseline_commit"],
            "recording_limit": ledger["recording_limit"], "raw_market_data_loaded": False,
            "holdout_outcomes_loaded": False,
            "historical_global_adjustment": None, "strategy_authorized": False,
            "data_policy": {"MES": "2020-2025 already researched; 2026 final strategy holdout",
                            "ES": "2020-2024 development; 2025 candidate validation; 2026 final strategy holdout",
                            "this_control": "no raw data or historical outcome artifacts loaded"},
            "summary": {"mes_registered_experiments": len(ledger["historical_experiments"]),
                        "mes_declared_hypotheses": len(ledger["historical_hypotheses"]),
                        "es_planned_unrun_hypotheses": len(ledger["planned_es_units"]),
                        "future_families": len(evaluations),
                        "future_alpha_allocated": sum(v["alpha"] for v in locks["families"].values())},
            "historical_experiments": ledger["historical_experiments"],
            "historical_hypotheses": ledger["historical_hypotheses"],
            "planned_es_units": ledger["planned_es_units"],
            "future_family_freezes": locks["families"], "future_family_evaluations": evaluations}


def render_md(registry):
    s = registry["summary"]
    lines = ["# MES / ES Accumulated Search Registry", "",
             f"MES: **{s['mes_registered_experiments']} registered experiments**, **{s['mes_declared_hypotheses']} documented hypothesis definitions**.",
             f"ES: **{s['es_planned_unrun_hypotheses']} planned hypotheses**, not run. No ES signal is claimed validated.",
             f"Future frozen families: **{s['future_families']}**; accumulated alpha allocated: **{s['future_alpha_allocated']:.6f}**.", "",
             registry["recording_limit"], "",
             "MES 2025 has already been researched. ES 2025 remains separately gated; MES/ES are not independent replications of a shared S&P idea.",
             "2026 is reserved for a complete frozen strategy. Original status labels are retained for provenance and do not authorize a strategy.",
             "No raw market data or historical outcome artifacts were opened to generate this registry.", "",
             "| Experiment | Title | Original status | Dataset / prior exposure |",
             "|---|---|---|---|"]
    for r in registry["historical_experiments"]:
        values = [r[k].replace("|", "/") for k in ("experiment_id", "title", "status", "dataset")]
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## ES planned definitions", ""]
    for r in registry["planned_es_units"]:
        lines.append(f"- {r['id']}: {r['title']} — PRE_REGISTERED_NOT_RUN; operational specification/data gate still required.")
    lines += ["", "Future scientific families include all sides/horizons/thresholds/models and both instruments when they answer one selection question.",
              "Full-family Holm and a non-recyclable prospective budget apply; reused development evidence remains exploratory.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--freeze-family")
    action.add_argument("--preflight-family")
    action.add_argument("--evaluate-family")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.base_ref:
        check_history_ref(root, args.base_ref)
    if args.freeze_family:
        print(json.dumps(freeze_family(root, args.freeze_family), indent=2)); return
    if args.preflight_family:
        preflight_family(root, args.preflight_family)
        print(json.dumps({"preflight": args.preflight_family, "status": "PASS"})); return
    if args.evaluate_family:
        print(json.dumps(evaluate_family(root, args.evaluate_family), indent=2)); return
    registry = build_registry(root)
    if not args.check:
        out = root / "results/research_controls"
        out.mkdir(parents=True, exist_ok=True)
        (out / "SEARCH_REGISTRY.json").write_text(json.dumps(registry, indent=2) + "\n")
        (out / "SEARCH_REGISTRY.md").write_text(render_md(registry))
    print(json.dumps({"search_control": "PASS", **registry["summary"], "holdout_outcomes_loaded": False}, indent=2))


if __name__ == "__main__":
    main()
