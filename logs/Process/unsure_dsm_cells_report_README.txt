Unsure DSM Cells Report - Documentation
=======================================

Files: unsure_dsm_cells_report.csv          (full report, tasks i and ii, both use cases)
       unsure_dsm_cells_report_task_i.csv   (task i subset, 80 configurations with archived runs)

TASK SCOPE
----------
- Task (i): Components are given; the model fills DSM cells (0/1/2) for relationships.
  Data under xLM_DSM/logs/Process/i/.
- Task (ii): The model identifies components and their relationships.
  Data under xLM_DSM/logs/Process/ii/. Unsure cells are counted on the raw (unaligned) matrices.

The full report contains 166 task (i) and 165 task (ii) configurations. The "status" column
indicates whether a configuration is the one reported in the paper:
  reported            - configuration and runs used for the paper's tables
  superseded          - earlier run replaced by a later one
  alternate_retriever - run with a different retriever setting
  alternate_embedding - run with a different embedding model
  no_archived_runs    - task (i) GraphRAG configurations: no detailed_results JSON; the raw query
                        logs are under data/graphrag_test/<CS|PS>/auto_*/logs/

EXPERIMENT COVERAGE
------------------
To verify whether this is the complete set for task (i), see:
  xLM_DSM/data/experiments.txt

That file lists the full experiment set (CubeSat-i, CubeSat-ii, powerscrewdriver-i, 
powerscrewdriver-ii) with model outputs. This CSV aggregates unsure cell counts from
detailed_results_*.json files under xLM_DSM/logs/Process/i/ and ii/ for each model, domain,
and reference combination.

SCOPE OF THE TASK (i) SUBSET FILE
---------------------------------
- CubeSat: LLM baseline, RAG (R1, R2, R3, R1-R2, R1-R3, R2-R3, R1-R2-R3), GraphRAG (R1-R2, R2-R3)
- Power screwdriver: LLM baseline and RAG configurations (the power screwdriver GraphRAG
  rows appear only in the full report, with status no_archived_runs)

COLUMNS
-------
task:       "i" = predefined components; "ii" = component identification
model:      LLM model identifier
domain:     CubeSat or powerscrewdriver
reference_combo: llm_refs_baseline, llm_rag_refs_*, llm_rag_graph_refs_*
n_runs:     Number of experiment runs (typically 5)
cells_per_matrix: DSM size (36 for 6x6 CubeSat, 49 for 7x7 power screwdriver)
total_cells: n_runs * cells_per_matrix
unsure_count: Number of cells with value "2" (unsure) across all runs
unsure_pct:  Percentage of total_cells that are unsure
experiment:  (full report only) experiment identifier from data/experiments.txt
status:      (full report only) see TASK SCOPE above
