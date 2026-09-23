<div align="center" style="font-size: 22pt;" id="top"> 
  <h1 style="text-align: center;">Retrieval Augmented (Knowledge Graph), and Large Language Model-Driven Design Structure Matrix (DSM) Generation of Cyber-Physical Systems</h1>
  <a href="https://img.shields.io/badge/Made%20with-Python-1f425f.svg">
    <img src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg" alt="Badge: Made with Python"/>
  </a>
  <a href="https://img.shields.io/github/stars/bankh/xLM_DSM">
    <img src="https://img.shields.io/github/stars/bankh/xLM_DSM" alt="GitHub User's stars"/>
  </a>
  <a href="https://img.shields.io/github/forks/bankh/xLM_DSM">
    <img src="https://img.shields.io/github/forks/bankh/xLM_DSM" alt="GitHub forks"/>
  </a>
  <a href="https://img.shields.io/github/contributors-anon/bankh/xLM_DSM">
    <img src="https://img.shields.io/github/contributors-anon/bankh/xLM_DSM" alt="GitHub contributors"/>
  </a>
  <a href="https://github.com/bankh/xLM_DSM/blob/main/LICENSE">
    <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg" target="_blank" />
  </a>

[Features](#features) 📂 | [Folder Structure](#folder-structure) 🗂 | [Installation](#installation) 🛠️| [Usage](#usage) 🏃 | [Method and Configuration](#method-and-configuration) 🔨 | [Experimental Details Excel](#experimental-details-excel) 📊 | [Reference Classification](#reference-classification-step-1a) 📋 | [Citation](#citation) 📜 | [License](#license) 📝 | [Contact](#contact) 📫 | [References](#references) 📖
</div>

__Accompanying code for the paper:__ _Retrieval Augmented (Knowledge Graph), and Large Language Model-Driven Design Structure Matrix (DSM) Generation of Cyber-Physical Systems._  
**Abstract:** We explore the potential of Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and Graph-based RAG (GraphRAG) for generating Design Structure Matrices (DSMs). We test these methods on two distinct use cases—a power screwdriver and a CubeSat with known architectural references—evaluating their performance on two key tasks: determining relationships between predefined components, as well as identifying components and their subsequent relationships. We measure the performance by assessing each element of the DSM and overall architecture. Despite design and computational challenges, we identify opportunities for automated DSM generation, with all code publicly available.

## Features <a name="features"></a>
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the features</summary>

- Processes Excel sheets containing experiment configurations  

- Groups and combines reference PDFs by R-type  

- Generates JSON configuration files for experiments 

- Supports multiple use cases and models,  

- Handles LLM, LLM with RAG, and LLM with RAG or Graph-based inference types,  

[⬆️ Back to top](#top)
</details>

## Folder Structure <a name="folder-structure"></a> 
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the folder structure</summary>
The repository has the following structure:

```plaintext
xLM_DSM/
├── readMe.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── data/
│   ├── use_cases/
│   │    ├── powerscrewdriver/
│   │    │   └── reference_pdfs/
│   │    │          ... first-page preview (.png) of each reference; place the full PDFs here  
│   │    └── Spacecraft-CubeSat/
│   │        └── reference_pdfs/
│   │               ... first-page preview (.png) of each reference; place the full PDFs here  
│   ├── sample_experiments.xlsx
│   ├── UseCase_*.xlsx
│   ├── experiments.txt                     # Per-run DSM outputs of every reported configuration
│   ├── generate_unsure_report.py
│   ├── graphrag_test/                      # Task (i) GraphRAG workspaces and query logs (CS: CubeSat, PS: power screwdriver)
│   │    ├── CS/auto_*/
│   │    └── PS/auto_*/
│   └── results/                            # Metrics behind the paper's tables (see Results)
│       ├── dsm_metrics.xlsx
│       ├── dsm_metrics_formula.xlsx
│       ├── dsm_metrics_unsure.xlsx
│       ├── dsm_metrics_unsure_formula.xlsx
│       └── unsure_sensitivity_tables.csv
├── graphrag/  # Submodule (Microsoft GraphRAG). Initialize with `git submodule update --init --recursive` if cloning without `--recurse-submodules`
├── json/
│   ├── template_experiment_.json
│   └── experiments/
├── logs/
│   ├── Benchmark/
│   ├── classification/                     # R1/R2/R3 classification outputs (paper Appendix A)
│   └── Process/
│       ├── gt_cubesat.csv                  # Ground-truth DSMs
│       ├── gt_powerscrewdriver.csv
│       ├── i/                              # Task (i): predefined components (per-run outputs)
│       ├── ii/                             # Task (ii): component identification (+ final_component_mapping.csv)
│       └── unsure_dsm_cells_report*.csv    # Unsure ("2") cell counts, tasks (i) and (ii)
└── scripts/
    ├── classify_docs.py   # R-type classification (Ollama)
    ├── Modelfile.deepseek-r1-8b-optimized  # Ollama definition of the classifier model used for the paper
    ├── generate_json.py             # JSON config generation
    ├── Step2_DSM_LLM_RAG_GRAPHRAG.ipynb
    └── Step3_DSM_Analyze_Visualize.ipynb
```

The key files are:
- `readMe.md`: This file, containing project documentation and setup instructions
- `data/sample_experiments.xlsx`: **Created manually.** Defines use cases and experiment configurations for generate_json (sheets `Coversheet`, `CubeSat`, `PowerDrill`). See [Experimental Details Excel](#experimental-details-excel) below.
- `data/*.xlsx`: Other Excel files (e.g., UseCase_*.xlsx) with use case specifications
- `data/experiments.txt`: Per-run DSM matrices of every model × method × reference configuration reported in the paper (CubeSat-i/ii, powerscrewdriver-i/ii). Cell values: 0 = no interface, 1 = interface, 2 = unsure. Every configuration was run five times. `na` under a configuration marks one reported as N/A in the paper; in 12 configurations one of the five runs returned no matrix (listed as `na`), so those configurations list four matrices.
- `data/results/`: Metric workbooks and tables behind the paper's result tables (see [Results](#results))
- `data/graphrag_test/`: GraphRAG workspaces (settings, indexed outputs, query logs) of the task (i) GraphRAG runs
- `logs/Process/gt_*.csv`: Ground-truth DSMs (CubeSat 6×6, power screwdriver 7×7) used for every metric
- `json/template_experiment_.json`: Template JSON file for experiment configuration
- `scripts/classify_docs.py`: Classifies reference documents into R-types (R1/R2/R3) using local LLMs via Ollama
- `scripts/generate_json.py`: Generates experiment configurations from Excel sheets
- `scripts/Step2_DSM_LLM_RAG_GRAPHRAG.ipynb`: DSM generation with LLM, RAG, and GraphRAG
- `scripts/Step3_DSM_Analyze_Visualize.ipynb`: Analysis and visualization  

[⬆️ Back to top](#top)
</details>

## Installation <a name="Installation"></a> 
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Installation</summary>
**1.** Clone this repository (include `--recurse-submodules` to fetch the GraphRAG submodule required for Step 2):
```bash
git clone --recurse-submodules https://github.com/bankh/xLM_DSM.git
cd xLM_DSM
```
If you already cloned without submodules, run:
```bash
git submodule update --init --recursive
```

**2.** Download Conda, create and activate the virtual environment based on the required Python version (e.g., python=3.10):

```bash
$ curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh 
$ chmod +x Miniconda3-latest-Linux-x86_64.sh
$ bash Miniconda3-latest-Linux-x86_64.sh
# Create and activate the virtual environment (Python 3.10)
$ conda create --name {name_of_env} python=3.10 -y
$ conda activate {name_of_env}
```
__Note:__ We would recommend using individual virtual environment for each method. For example, you can create a virtual environment for baseline LLM-based DSM generation, another one for LLM-based DSM generation with RAG, and another one for LLM-based DSM generation with GraphRAG.  

**3.** Install required packages:

```bash
pip install -r requirements.txt
```

**4.** (For Step 1a classification only) Install and run [Ollama](https://ollama.ai) for local LLM inference:

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3:8b          # or llama3.3:70b-8k for better accuracy
ollama pull nomic-embed-text   # for embeddings
ollama serve                   # start the service
```

[⬆️ Back to top](#top)
</details>


## Usage <a name="usage"></a> 
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Usage</summary>

**Step 1a (Classification):** Classify references by R-type using a local LLM:
```bash
cd scripts
# From directory of PDFs (recommended)
python classify_docs.py --from-dir ../data/use_cases/powerscrewdriver/reference_pdfs --output-dir ../logs/classification --model llama3:8b

# Or from CSV file
python classify_docs.py my_references.csv --output-dir ../logs/classification --model llama3:8b
```

**Step 1b (JSON config):** Generate configuration files from the Excel workbook and the classified reference PDFs:
```bash
python generate_json.py --relationship_type mechanical --use-case PowerDrill \
  --pdf_dir ../data/use_cases/powerscrewdriver/reference_pdfs --output_dir ../json/experiments \
  --excel_path ../data/sample_experiments.xlsx
```
The R-type of each reference is read from its filename, which must follow the `[Author] R1-Title.pdf` pattern (see Step 1). The classify_docs output from Step 1a is used to check these labels; it is not read by generate_json.

**Step 2 & 3:** Run the Jupyter notebooks for DSM generation and analysis.

[⬆️ Back to top](#top)
</details>


### Method and Configuration <a name="method-and-configuration"></a>
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Method and Configuration</summary>

We have four steps to generate the DSM for a system of interest.  

**Step 1:** Download the reference documents and place them in `data/use_cases/{System-of-Interest}/reference_pdfs/`. Use filenames that encode ground-truth R-type for evaluation (e.g., `[Author] R1-Title.pdf`). The repository does not redistribute the reference documents. Each `reference_pdfs/` folder holds a first-page preview image of every reference used in the paper, named exactly as the PDF was named (`[Year Author] R-type-Title.png`). Obtain the documents from the sources listed under References of Use Cases and save each one next to its preview under the same name with the `.pdf` extension before running Step 1a or Step 1b.  

**Step 1a:** Run `classify_docs.py` to classify references by R-type using a local LLM (Ollama). R-types: R1 (expert knowledge), R2 (formal/normative: textbooks, standards), R3 (non-expert: crowdsourcing, DIY, vocational materials). See [Reference Classification](#reference-classification-step-1a) for details.  

**Step 1b:** Run `generate_json.py` to generate the configuration files for the experiments. It reads the use-case sheet of the Excel workbook (`--excel_path`) and groups the PDFs in `--pdf_dir` by the R-type encoded in their filenames (`[Author] R1-Title.pdf`), producing one JSON per experiment row, model, inference type, and R-type combination. The Step 1a classification output is used to verify the filename labels.  
```json
{
  "system_name": "PowerScrewdriver",
  "concept_name": "power screwdriver",
  "application_domain": "",
  "relationship_type": "mechanical",
  "api_keys": {
    "openai_api_key": "your-openai-api-key-here",
    "claude_api_key": "your-claude-api-key-here"
  },
  "selected_model": "gpt-3.5-turbo",
  "embedding_model": "text-embedding-3-small",
  "inference_type": "llm_rag",
  "output_directory": "../json/experiments/PowerScrewdriver",
  "vectorstore_directory": "../data/vectorstore",
  "reference_files": {
    "R1": [
      {"path": "path-to-R1-document-1.pdf", "description": "Description of the document 1"},
      {"path": "path-to-R1-document-2.pdf", "description": "Description of the document 2"}
    ],
    "R2": [
      {"path": "path-to-R2-document-1.pdf", "description": "Description of the document 1"},
      {"path": "path-to-R2-document-2.pdf", "description": "Description of the document 2"}
    ],
    "R3": [
      {"path": "path-to-R3-document-1.pdf", "description": "Description of the document 1"},
      {"path": "path-to-R3-document-2.pdf", "description": "Description of the document 2"}
    ]
  },
  "graph_config": {
    "uri": "neo4j://localhost:7687",
    "username": "neo4j",
    "password": "your-password",
    "database": "system_knowledge"
  }
}
```
The parameters are as follows:  
_system_name:_ The name of the system of interest (e.g., PowerScrewdriver, CubeSat).  
_concept_name:_ Natural-language name for prompts (e.g., "power screwdriver", "CubeSat nanosatellite").  
_application_domain:_ Domain of the system application (optional, can be empty).  
_relationship_type:_ The type of relationship to use for the experiment such as mechanical, electrical, functional, logical, etc.  
_selected_model:_ The LLM model to use for the experiment such as  
    [OpenAI](https://python.langchain.com/docs/integrations/providers/openai/): gpt-4o, gpt-4-turbo, gpt-3.5-turbo,  
    [Anthropic](https://python.langchain.com/docs/integrations/providers/anthropic/): claude-3-5-sonnet-20241022, claude-3-opus-20240307, claude-3-haiku-20240307,  
    [OllamaLLM](https://python.langchain.com/docs/integrations/llms/ollama/): ollama-llama-3-405B, ollama-llama-3-70B, ollama-llama-3-8B.  
_embedding_model:_ The embedding model for RAG/GraphRAG (e.g., text-embedding-3-small, nomic-embed-text).  
_inference_type:_ The type of inference: `llm` (baseline), `llm_rag` (RAG), or `llm_rag_graph` (GraphRAG).  
_output_directory:_ The path to the directory where the output will be saved.  
_vectorstore_directory:_ The path to the vector store for RAG/GraphRAG.  
_reference_files:_ Dict of R-type to list of `{path, description}` objects (R1, R2, R3 keys). Empty for `llm`.  
_graph_config:_ The configuration for the graph database (Neo4j); used when inference_type is `llm_rag_graph`.  

__Note:__ You can use any other LLM models that are supported by [LangChain](https://python.langchain.com/docs/integrations/providers/).  

**Step 2:** Run `Step2_DSM_LLM_RAG_GRAPHRAG.ipynb` to generate the DSM based on the experiment configurations generated in Step 1b.

**Step 3:** Run `Step3_DSM_Analyze_Visualize.ipynb` for analysis and visualization.

[⬆️ Back to top](#top)
</details>

### Experimental Details Excel <a name="experimental-details-excel"></a>
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Excel structure</summary>

`data/sample_experiments.xlsx` is **created and edited manually**. generate_json reads it to generate JSON experiment configs.

**Structure:**
- **First sheet:** Cover page (skipped by generate_json)
- **Subsequent sheets:** One per use case (`CubeSat` and `PowerDrill` in the sample workbook; select one with `--use-case`). Use `--pdf_dir` to point to the folder under `data/use_cases/` (e.g., `powerscrewdriver` or `Spacecraft-CubeSat`).

**Each use case sheet must contain:**
| Column | Description |
|--------|-------------|
| `system_name` | Name of the system (e.g., power screwdriver, CubeSat) |
| `application_domain` | Domain of the system application |
| `ID` | Experiment identifier (integer). Use "End of Experiment" to stop processing. |
| `Model` | LLM config, e.g. `gpt-3.5-turbo`, `gpt-3.5-turbo + RAG`, `gpt-3.5-turbo + RAG + GRAPH` |

generate_json generates one JSON config per row × model × inference type × R-type combination. R-type combinations (no_ref, R1, R2, R3, R1+R2, etc.) are derived from the classified PDFs, not from the Excel.

[⬆️ Back to top](#top)
</details>

### Reference Classification (Step 1a) <a name="reference-classification-step-1a"></a>
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Reference Classification</summary>

The classification script (`classify_docs.py`) categorizes references into R1, R2, or R3 using local LLMs via Ollama. **Classification is done by the LLM** (not by filenames); R-type in filenames is ground truth only for evaluation.

The classification runs reported in the accompanying paper (Appendix A) used the `deepseek-r1-8b-optimized:latest` model; their full outputs—per-document predictions, confusion matrices, and metrics for both use cases—are provided in `logs/classification/`.

**Classifier model definition.** `deepseek-r1-8b-optimized` is a local Ollama variant of `deepseek-r1:8b` (DeepSeek-R1-0528 distilled on Qwen3-8B, 8.2B parameters, Q4_K_M quantization). Its definition is provided in `scripts/Modelfile.deepseek-r1-8b-optimized`: context window `num_ctx` 32768, `top_k` 40, `top_p` 0.9, `repeat_penalty` 1.1; `classify_docs.py` sends the classification prompt with `temperature` 0.1, which overrides the temperature in the Modelfile. Embeddings: `nomic-embed-text`. To recreate the model and repeat the reported runs:
```bash
ollama pull deepseek-r1:8b
ollama create deepseek-r1-8b-optimized -f scripts/Modelfile.deepseek-r1-8b-optimized
cd scripts
python classify_docs.py --from-dir ../data/use_cases/powerscrewdriver/reference_pdfs --output-dir ../logs/classification --model deepseek-r1-8b-optimized:latest
python classify_docs.py --from-dir ../data/use_cases/Spacecraft-CubeSat/reference_pdfs --output-dir ../logs/classification --model deepseek-r1-8b-optimized:latest
```
The reference PDFs are not redistributed (first-page previews are in `reference_pdfs/`); place the source documents listed under [References of Use Cases](#references) in those folders before running.

**Usage:**
```bash
cd scripts
# From directory of PDFs (recommended) below where model is llama3:8b as example
python classify_docs.py --from-dir ../data/use_cases/powerscrewdriver/reference_pdfs --output-dir ../logs/classification_test --model llama3:8b

# Or from CSV file below where model is llama3:8b as example
python classify_docs.py my_references.csv --output-dir classified_results --model llama3:8b
```

**Options:** `--output-dir`, `--model`, `--ollama-url`, `--embedding-model`, `--temperature`, `--max-retries`, `--from-pdfs`, `--from-dir`, `--use-vision`, `--page`

#### Using DocumentLabeler Preprocessed Files

For improved text extraction quality (especially for GraphRAG), documents can be preprocessed using [DocumentLabeler](https://github.com/bankh/DocumentLabeler). `classify_docs.py` accepts `.txt` and `.md` files as well as PDFs, so the DocumentLabeler transcriptions can be classified directly:

```bash
# Preprocess PDFs with DocumentLabeler first (see DocumentLabeler repo)
# Then classify the transcribed text files:
python classify_docs.py --from-dir /path/to/documentlabeler/output --model llama3:8b
```

The transcriptions used for the paper's GraphRAG runs are provided under `data/graphrag_test/input/`.

**Output files** (include model name and timestamp in filename):
- `classification_results_{model}_{timestamp}.json` — detailed results
- `classification_summary_{model}_{timestamp}.csv` — summary
- `classification_statistics_{model}_{timestamp}.json` — counts by R-type
- `confusion_matrix_{model}_{timestamp}.csv` — when ground truth in filenames
- `classification_metrics_{model}_{timestamp}.json` — accuracy, precision, recall

**Troubleshooting:**
- Ollama not running: `ollama serve`
- Model not found: `ollama pull llama3:8b`
- Use smaller models (e.g., `llama3:8b`) for faster processing; larger models (e.g., `llama3.3:70b`) for better accuracy

[⬆️ Back to top](#top)
</details>

### Output
The system generates:  
- **Step 1a:** Classification results (JSON, CSV), confusion matrix, and metrics when ground truth is in filenames  
- **Step 1b:** JSON configuration files for each experiment (see sample above or check `./json/experiments/{use-case}`)  
- **Step 2 & 3:** Design Structure Matrix (DSM) in CSV format and Graphviz DOT format  

### Unsure DSM Cells Report
The file `logs/Process/unsure_dsm_cells_report.csv` reports per-model, per-configuration counts and percentages of DSM cells with value "2" (unsure) for both tasks and both use cases. Its `status` column marks whether a configuration is the one reported in the paper (`reported`) or an alternative run (`superseded`, `alternate_retriever`, `alternate_embedding`); `no_archived_runs` marks the task (i) GraphRAG configurations, whose outputs are the query logs under `data/graphrag_test/` rather than `detailed_results` JSON files. `logs/Process/unsure_dsm_cells_report_README.txt` documents the columns. The sensitivity of the metrics to the treatment of unsure cells is provided in `data/results/` (see [Results](#results)).

[⬆️ Back to top](#top)

## Results <a name="results"></a>
<details>
<summary>Click on the triangle icon to collapse (▼) or expand (▶) the Results</summary>
The full experimental results are reported in the accompanying paper (see [Citation](#citation)). Everything needed to reproduce them is in this repository.

**Inputs**
- `data/experiments.txt`: the per-run DSM matrices (every configuration was run five times) for every model × method (LLM; RAG with R1, R2, R3, R1-R2, R1-R3, R2-R3, R1-R2-R3; GraphRAG with R1-R2, R2-R3) × use case × task. Values are 0 (no interface), 1 (interface) and 2 (unsure). `na` marks a configuration reported as N/A in the paper; its runs are still archived under `logs/Process/` (`detailed_results_*.json`, key `individual_runs`). In 12 configurations one of the five runs returned no matrix (`na`); those configurations list four matrices and are reported as the mean over the four runs.
- `logs/Process/gt_cubesat.csv`, `logs/Process/gt_powerscrewdriver.csv`: the ground-truth DSMs.
- `logs/Process/ii/**/final_component_mapping.csv`: for task (ii), the mapping from ground-truth components to the model's predicted components, used to build the aligned matrices.
- `data/graphrag_test/`: the task (i) GraphRAG workspaces; the query logs (`logs/*_local_*.log`, `logs/cc_test_run_*.log`) hold the raw GraphRAG answers.

**Metrics (per run, then mean ± standard deviation over the runs)**
- TP, TN, FP and FN are counted over the cells predicted 0 or 1; unsure cells are excluded from these counts. Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2PR/(P+R), accuracy = (TP+TN)/(TP+TN+FP+FN), each 0 when its denominator is 0.
- Edit distance = Σ|G − M| over all cells (unsure cells kept as 2); spectral distance = L2 norm of the difference between the descending-sorted real eigenvalues of G and M.
- Task (ii) "raw" evaluates the matrix in the model's own component order; "aligned" re-indexes it through the component mapping (unmatched ground-truth components dropped).
- The standard deviation is the population standard deviation over the runs.

**Result files (`data/results/`)**
- `dsm_metrics.xlsx`: the metrics of every configuration (sheet `All experiments`, one row per configuration; one sheet per table with the averaged DSM, counts and metrics of each configuration). These are the values in the paper's per-configuration tables.
- `dsm_metrics_formula.xlsx`: the same workbook with every metric as a spreadsheet formula over the pasted run matrices and ground truths (only the eigenvalues are pasted, with in-sheet consistency checks), so each number can be traced in Excel or LibreOffice.
- `dsm_metrics_unsure.xlsx`, `dsm_metrics_unsure_formula.xlsx`: the same metrics under three treatments of the unsure cells (excluded from the denominators, scored as 0, scored as wrong), as values and as formulas.
- `unsure_sensitivity_tables.csv`: the rows of the paper's unsure-sensitivity tables, including the configurations reported as N/A (their runs are taken from the archived JSON files). The `accuracy_excluded_*` and `f1_excluded_*` columns keep the numeric exclusion-rule values for every row; the paper prints N/A in those two columns for the configurations that are not available in its main tables.

Benchmark runs are under `logs/Benchmark/` and the R1/R2/R3 classification outputs under `logs/classification/`.

[⬆️ Back to top](#top)
</details>

## License <a name="license"></a>
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

[⬆️ Back to top](#top)

## Citation <a name="citation"></a>
If you use this work in your research, please cite it as:
```bibtex
@misc{bank2026xlmdsm,
  title={Retrieval Augmented (Knowledge Graph), and Large Language Model-Driven Design Structure Matrix (DSM) Generation of Cyber-Physical Systems},
  author={Bank, Hasan Sinan and Herber, Daniel R.},
  year={2026},
  eprint={2602.16715},
  archivePrefix={arXiv},
  primaryClass={cs.AI},
  howpublished={\url{https://arxiv.org/abs/2602.16715}}
}
```

[⬆️ Back to top](#top)

## Contact <a name="contact"></a>
Sinan Bank - sinan.bank@colostate.edu  
Project Link: [https://github.com/bankh/xLM_DSM](https://github.com/bankh/xLM_DSM)

[⬆️ Back to top](#top)

## References of Use Cases <a name="references"></a>
**Power Tool: power screwdriver** (use case folder: `powerscrewdriver`)  
1- [R1] Tilstra, A. H., et al. (2012). A high-definition design structure matrix (HDDSM) for the quantitative assessment of product architecture. *Journal of Engineering Design*. https://www.tandfonline.com/doi/abs/10.1080/09544828.2012.706748  
2- [R1] Sinha, K. (2014). Structural complexity and its implications for design of cyber-physical systems. PhD thesis, MIT. https://dspace.mit.edu/handle/1721.1/89871  
3- [R2] Eppinger, S. D., & Browning, T. R. (2012). Design Structure Matrix Methods and Applications. MIT Press. https://doi.org/10.7551/mitpress/8896.001.0001  
4- [R2] Joshi, P. H. (2007). Machine Tools Handbook: Design and Operation. McGraw-Hill. https://colostate.primo.exlibrisgroup.com/permalink/01COLSU_INST/via34g/alma991031703102703361  
5- [R3] De Cristoforo, R. J. (1986). The Complete Book of Portable Power Tool Techniques. Sterling/Rodale. https://colostate.primo.exlibrisgroup.com/permalink/01COLSU_INST/via34g/alma991010070099703361  
6- [R3] Thiel, D. (2006). David Thiel's Power Tool Maintenance: Peak Performance and Safety for Life. Penguin. https://www.abebooks.co.uk/9781558707559/  
7- [R3] BCITO. BCATS Power Tools. New Zealand vocational training materials. https://bconstructive.co.nz/sites/default/files/2020-12/Power%20Tools%20STUDENT%2024350.pdf  
**Spacecraft: CubeSat** (use case folder: `Spacecraft-CubeSat`)  
8- [R1] Asundi, S. A., & Fitz-Coy, N. G. (2013). CubeSat mission design based on a systems engineering approach. In *2013 IEEE Aerospace Conference* (pp. 1-9). IEEE. https://doi.org/10.1109/AERO.2013.6496900  
9- [R1] Girardello, C., Tajmar, M., & Scharlemann, C. (2024). GREATCUBE+: conceptual design tool for CubeSat’s design. *CEAS Space Journal*, 16(3), 375-392. https://doi.org/10.1007/s12567-023-00509-9  
10- [R2] Eppinger, S. D., & Browning, T. R. (2012). Design Structure Matrix Methods and Applications. MIT Press. https://doi.org/10.7551/mitpress/8896.001.0001  
11- [R2] Cappelletti, C., Battistini, S., & Malphrus, B. K. (Eds.). (2020). CubeSat Handbook: From Mission Design to Operations. Academic Press. https://doi.org/10.1016/C2018-0-02366-X  
12- [R3] Thornburg, D. (n.d.). HyperDuino-based CubeSat: 6 steps (with pictures). Instructables. https://www.instructables.com/HyperDuino-based-CubeSat/  
13- [R3] Mandal, M. (n.d.). Launch-Ready SSTV CubeSat: 7 steps (with pictures). Instructables. https://www.instructables.com/Launch-Ready-SSTV-CubeSat/

[⬆️ Back to top](#top)
