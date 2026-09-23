#!/usr/bin/env python3
"""Generate logs/Process/unsure_dsm_cells_report.csv from primary experiment outputs.

Sources (no dependency on any hand-assembled file):
  - logs/Process/<task>/<domain>/**/detailed_results_*.json  (individual_runs matrices)
  - logs/Process/<task>/<domain>/**/average_matrix_*.json    (GraphRAG runs, same schema)
  - logs/Process/i/powerscrewdriver/LLM/MultiModelExp_llm_*.log (baseline runs stored as log lines)

Unsure = cell value 2 in the per-run predicted matrices.

Each (task, domain, config, model) may have several experiments (re-runs, old/
directories, retriever variants). All are emitted, with a `status` column:
  reported             -> the experiment whose metrics the paper reports
                          (latest non-old run; k_4 retriever for task-i RAG)
  superseded           -> an earlier run replaced by a re-run (incl. old/ dirs)
  alternate_retriever  -> task-i power screwdriver RAG sweeps with k != 4
  alternate_embedding  -> nomic-embed-text (net/) retriever variants
  no_archived_runs     -> task-i GraphRAG: per-run matrices were not archived;
                          metrics in the paper come from the computed results
                          table (experiment_results_case_i_20250407_183320.csv)

Also writes unsure_dsm_cells_report_task_i.csv (task i, reported rows only,
in the original 9-column schema).
"""
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "logs" / "Process"
OUT_FULL = BASE / "unsure_dsm_cells_report.csv"
OUT_TASK_I = BASE / "unsure_dsm_cells_report_task_i.csv"

FIELDS = ["task", "model", "domain", "reference_combo", "n_runs", "cells_per_matrix",
          "total_cells", "unsure_count", "unsure_pct", "experiment", "status"]


def canon_model(raw):
    """Normalize the model token from an experiment directory name."""
    return raw.removeprefix("ollama:")


def canon_config(cfg):
    """Directory config name -> report naming (llm_graph_rag_* -> llm_rag_graph_*)."""
    m = re.match(r"llm_graph_rag_refs_(.+)$", cfg)
    if m:
        return "llm_rag_graph_refs_" + m.group(1).upper()
    return cfg


def mat_stats(mat):
    """(n_cells, n_unsure, 'RxC') for a list-of-lists matrix, else None."""
    if not isinstance(mat, list) or not mat or not isinstance(mat[0], list):
        return None
    cells = sum(len(row) for row in mat)
    unsure = sum(1 for row in mat for v in row if v == 2)
    return cells, unsure, f"{len(mat)}x{len(mat[0])}"


def summarize_runs(matrices):
    n_runs = total = unsure = 0
    dims = Counter()
    for mat in matrices:
        st = mat_stats(mat)
        if st is None:
            continue
        c, u, d = st
        n_runs += 1
        total += c
        unsure += u
        dims[c] += 1
    cells_per_matrix = dims.most_common(1)[0][0] if dims else 0
    return n_runs, cells_per_matrix, total, unsure


records = []

# --- JSON-backed experiments -------------------------------------------------
json_files = list(BASE.rglob("detailed_results_*.json"))
have_detailed = {p.parent for p in json_files}
json_files += [p for p in BASE.rglob("average_matrix_*.json") if p.parent not in have_detailed]

for jf in sorted(json_files):
    parts = jf.relative_to(BASE).parts
    task, domain = parts[0], parts[1]
    variant = "/".join(parts[2:-3])
    expdir, config = parts[-3], parts[-2]
    m = re.match(r"experiment_llm(?:_graph)?(?:_rag)?_(.+?)_(\d{8}-\d{6})$", expdir)
    model_raw, ts = (m.group(1), m.group(2)) if m else (expdir, "")
    try:
        data = json.load(open(jf))
    except (json.JSONDecodeError, OSError):
        continue
    n_runs, cpm, total, unsure = summarize_runs(
        r.get("matrix") for r in data.get("individual_runs", []))
    if n_runs == 0:
        continue
    records.append(dict(
        task=task, model=canon_model(model_raw), domain=domain,
        reference_combo=canon_config(config), n_runs=n_runs, cells_per_matrix=cpm,
        total_cells=total, unsure_count=unsure,
        unsure_pct=round(100 * unsure / total, 1),
        experiment=ts, _variant=variant, _old="old" in parts))

# --- task-i power screwdriver baselines (log files only) ----------------------
for lf in sorted((BASE / "i" / "powerscrewdriver" / "LLM").glob("MultiModelExp_llm_*.log")):
    m = re.match(r"MultiModelExp_llm_(.+)_(\d{8}-\d{6})\.log$", lf.name)
    if not m:
        continue
    mats = []
    for line in open(lf, errors="replace"):
        mm = re.search(r"INFO - Matrix: (\[\[.*\]\])\s*$", line)
        if mm:
            try:
                mats.append(ast.literal_eval(mm.group(1)))
            except (ValueError, SyntaxError):
                pass
    n_runs, cpm, total, unsure = summarize_runs(mats)
    if n_runs == 0:
        continue
    records.append(dict(
        task="i", model=canon_model(m.group(1)), domain="powerscrewdriver",
        reference_combo="llm_refs_baseline", n_runs=n_runs, cells_per_matrix=cpm,
        total_cells=total, unsure_count=unsure,
        unsure_pct=round(100 * unsure / total, 1),
        experiment=m.group(2), _variant="LLM", _old=False))

# --- status assignment ---------------------------------------------------------
groups = defaultdict(list)
for r in records:
    groups[(r["task"], r["domain"], r["model"], r["reference_combo"])].append(r)

for group in groups.values():
    for r in group:
        v = r["_variant"]
        if r["_old"]:
            r["status"] = "superseded"
        elif "/net/" in f"/{v}/":
            r["status"] = "alternate_embedding"
        elif re.search(r"/k_?\d+$", v) and not v.endswith(("k_4", "k4")):
            r["status"] = "alternate_retriever"
        else:
            r["status"] = None  # candidate for reported
    candidates = [r for r in group if r["status"] is None]
    if candidates:
        latest = max(candidates, key=lambda r: r["experiment"])
        for r in candidates:
            r["status"] = "reported" if r is latest else "superseded"

# --- task-i GraphRAG placeholders (runs not archived; metrics in results CSV) --
for domain in ("CubeSat", "powerscrewdriver"):
    for model in ("gpt-4-turbo-preview", "mixtral:8x22b-6k", "llama3.3:70b-8k", "deepseek-r1:14b-5k"):
        for combo in ("llm_rag_graph_refs_R1_R2", "llm_rag_graph_refs_R2_R3"):
            records.append(dict(
                task="i", model=model, domain=domain, reference_combo=combo,
                n_runs="", cells_per_matrix="", total_cells="", unsure_count="",
                unsure_pct="", experiment="", status="no_archived_runs"))

records.sort(key=lambda r: (r["task"], r["domain"], r["model"],
                            r["reference_combo"], str(r["experiment"])))

with open(OUT_FULL, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    w.writerows(records)

task_i_fields = FIELDS[:9]
with open(OUT_TASK_I, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=task_i_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(r for r in records if r["task"] == "i" and r["status"] == "reported")

n_rep = sum(1 for r in records if r["status"] == "reported")
print(f"wrote {len(records)} rows to {OUT_FULL.name} "
      f"({n_rep} reported, {len(records) - n_rep} other)")
