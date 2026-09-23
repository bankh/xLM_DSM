"""
This script generates configuration files for experiments based on an Excel sheet.
It processes each use case, reads the Excel sheet, groups reference PDFs by R-type,
combines multiple PDFs if necessary, and creates configuration files for each experiment.

Usage:
    python generate_json.py [-h] [--use-case USE_CASE] [--relationship_type TYPE] 
                          [--pdf_dir DIR] [--output_dir DIR] [--excel_path PATH] 
                          [--openai_key KEY]

Arguments:
    --relationship_type   Type of relationship between components (e.g., electrical, mechanical)
    --use-case           Optional: Specific use case to process from the Excel file
    --pdf_dir            Directory containing the PDF files
    --output_dir         Output directory for configuration files
    --excel_path         Path to the Excel file containing experiment configurations
    --openai_key         OpenAI API key
    -h, --help           Show this help message and exit

Example:
    python generate_json.py --relationship_type electrical --use-case "3DPrinter" \
        --pdf_dir "../data/use_cases_large/3DPrinter/reference_pdfs" \
        --output_dir "../json/experiments" \
        --excel_path "../data/sample_experiments.xlsx" \
        --openai_key "your-openai-key-here"

The Excel file should be structured with:
- First sheet as a cover page
- Subsequent sheets representing different use cases
- Each use case sheet containing:
  * system_name: Name of the system being analyzed
  * application_domain: Domain of the system application
  * Model: LLM model configuration (e.g., "gpt-4+rag")
  * ID: Experiment identifier
  * Other configuration parameters as needed

The script will:
1. Read the Excel file and extract use case configurations
2. Group reference PDFs by R-type
3. Combine multiple PDFs if specified
4. Generate JSON configuration files for each experiment for the selected use case and model

"""
import pandas as pd
import json
from pathlib import Path
import glob
import argparse
from itertools import combinations
import os
import re
import pikepdf
import sys

def get_use_case_sheets(excel_path, selected_use_case=None):
    """
    Get all sheet names from the Excel file except the first sheet (cover page).
    If selected_use_case is provided, validate and return only that use case.
    
    Args:
        excel_path: Path to Excel file
        selected_use_case: Optional specific use case to process
    Returns:
        List of use case names from Excel sheets
    """
    try:
        # Read all sheet names
        all_sheets = pd.ExcelFile(excel_path).sheet_names
        # Skip the first sheet (cover page) and get use cases
        use_case_sheets = all_sheets[1:]
        
        if not use_case_sheets:
            print("WARNING: No use case sheets found in the Excel file")
            return []
            
        if selected_use_case:
            if selected_use_case in use_case_sheets:
                print(f"\nProcessing selected use case: {selected_use_case}")
                return [selected_use_case]
            else:
                available_cases = "\n- ".join(use_case_sheets)
                print(f"ERROR: Selected use case '{selected_use_case}' not found in Excel file.")
                print(f"Available use cases:\n- {available_cases}")
                return []
        else:
            print("\nFound Use Cases in Excel:")
            for sheet in use_case_sheets:
                print(f"- {sheet}")
            return use_case_sheets
            
    except Exception as e:
        print(f"Error reading Excel file {excel_path}: {str(e)}")
        return []

def get_reference_files(pdf_dir, use_case):
    """
    Get reference PDF files for a specific use case.
    Args:
        pdf_dir: Base directory containing all use case folders
        use_case: Name of the use case (matching Excel sheet name)
    Returns:
        List of PDF filenames
    """
    print(f"\nLooking for PDF files in: {pdf_dir}", flush=True)
    sys.stdout.flush()
    
    # Check if directory exists
    if not os.path.exists(pdf_dir):
        print(f"ERROR: Directory does not exist: {pdf_dir}", flush=True)
        sys.stdout.flush()
        return []
        
    # List directory contents for debugging
    print("\nDirectory contents:", flush=True)
    for file in os.listdir(pdf_dir):
        print(f"- {file}", flush=True)
    sys.stdout.flush()
    
    # Try to find all PDF files
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        print("WARNING: No PDF files found", flush=True)
        print(f"Directory path: {pdf_dir}", flush=True)
        sys.stdout.flush()
        return []
    
    # Sort files and remove any quotes from filenames
    pdf_files = sorted([os.path.basename(pdf).strip("'") for pdf in pdf_files])
    print("\nFound PDF files:", flush=True)
    for pdf in pdf_files:
        print(f"- {pdf}", flush=True)
    sys.stdout.flush()
    
    return pdf_files

def extract_rtype(filename):
    """
    Extract R-type from filename with pattern [Year Author] RX-Title.pdf
    Returns the R number as string
    """
    try:
        match = re.search(r'] R(\d+)-', filename)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting R-type from {filename}: {str(e)}")
        return None

def group_references_by_type(reference_files):
    """
    Group reference files by their R-type.
    Returns a dictionary where keys are R-types and values are lists of filenames.
    """
    r_type_groups = {}
    
    for filename in reference_files:
        r_type = extract_rtype(filename)
        if r_type:
            if r_type not in r_type_groups:
                r_type_groups[r_type] = []
            r_type_groups[r_type].append(filename)
    
    # Sort files within each group
    for r_type in r_type_groups:
        r_type_groups[r_type].sort()
        
    return r_type_groups

def combine_pdfs(input_paths, output_path):
    """
    Combine multiple PDFs into a single file using pikepdf.
    """
    try:
        # Create a new PDF
        pdf = pikepdf.Pdf.new()
        total_pages = 0
        
        for input_path in input_paths:
            try:
                src = pikepdf.Pdf.open(input_path)
                num_pages = len(src.pages)
                total_pages += num_pages
                print(f"Adding: {os.path.basename(input_path)} ({num_pages} pages)")
                pdf.pages.extend(src.pages)
            except Exception as e:
                print(f"Error adding {os.path.basename(input_path)}: {str(e)}")
                continue
        
        # Only save if we have added pages
        if total_pages > 0:
            print(f"Writing combined file to: {output_path}")
            pdf.save(output_path)
            print(f"Successfully created combined PDF: {os.path.basename(output_path)}")
            print(f"Total pages in combined document: {total_pages}")
            return True
        else:
            print("No PDFs were successfully added to merge")
            return False
            
    except Exception as e:
        print(f"Error during PDF combination: {str(e)}")
        return False

def get_reference_combinations(r_type_groups, pdf_dir, use_case):
    """
    Generate all possible combinations of reference groups.
    """
    r_types = sorted(r_type_groups.keys())
    all_combinations = []
    reference_path = pdf_dir
    
    # Create combined PDFs for groups with multiple files
    for r_type, files in r_type_groups.items():
        if len(files) > 1:
            input_paths = [os.path.join(reference_path, f) for f in files]
            output_path = os.path.join(reference_path, f'R{r_type}_combined.pdf')
            
            print(f"\nCombining PDFs for R{r_type}...")
            success = combine_pdfs(input_paths, output_path)
            
            if not success:
                print(f"Warning: Failed to create combined PDF for R{r_type}")
    
    # Generate combinations
    for r in range(len(r_types) + 1):
        for combo in combinations(r_types, r):
            files = []
            for r_type in combo:
                files.extend(r_type_groups[r_type])
                if len(r_type_groups[r_type]) > 1:
                    combined_path = os.path.join(reference_path, f'R{r_type}_combined.pdf')
                    if os.path.exists(combined_path):
                        files.append(f'R{r_type}_combined.pdf')
            all_combinations.append(files)
    
    return all_combinations

def parse_model_string(model_string):
    """
    Parse the model string to determine model name and inference types.
    """
    parts = [p.strip().lower() for p in model_string.split('+')]
    model = parts[0]
    if 'rag' in parts and 'graph' in parts:
        inference_types = ['llm_rag_graph']
    elif 'rag' in parts:
        inference_types = ['llm_rag']
    else:
        inference_types = ['llm']
    return model, inference_types

def create_reference_files_structure(pdf_dir, 
                                     r_type=None
                                     ):
    """
    Create a structured dictionary of reference files with their descriptions
    """
    reference_files = {}
    
    if not os.path.exists(pdf_dir):
        print(f"Warning: PDF directory {pdf_dir} does not exist")
        return reference_files

    # Get all PDF files in the directory
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    # Group files by R-type
    for pdf_file in pdf_files:
        # Extract R-type from filename if present, default to R1 if not found
        r_type_match = re.search(r'R[123]', pdf_file)
        file_r_type = r_type_match.group(0) if r_type_match else 'R1'
        
        if file_r_type not in reference_files:
            reference_files[file_r_type] = []
            
        # Create file entry with path and description
        file_entry = {
            "path": os.path.join(pdf_dir, pdf_file),
            "description": f"Documentation from {pdf_file}"
        }
        
        reference_files[file_r_type].append(file_entry)
    
    return reference_files

def generate_config(excel_path, 
                    use_case, 
                    relationship_type, 
                    pdf_dir, 
                    output_dir='./json/experiments'
                    ):
    """
    Generate JSON configuration file for the specified use case
    """
    config = {
        "system_name": use_case,
        "relationship_type": relationship_type,
        "api_keys": {
            "openai_api_key": "your-openai-key-here",
            "claude_api_key": "your-claude-api-key-here"
        },
        "selected_model": "gpt-3.5-turbo",
        "inference_type": "llm_rag",
        "output_directory": f"{output_dir}/{use_case}",
        "reference_files": create_reference_files_structure(pdf_dir),
        "graph_config": {
            "uri": "neo4j://localhost:7687",
            "username": "neo4j",
            "password": "your-password",
            "database": "system_knowledge"
        }
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(f"{output_dir}/{use_case}", exist_ok=True)
    
    # Write configuration to JSON file
    config_path = f"{output_dir}/{use_case}/config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Generated configuration file: {config_path}")
    return config

def create_config_files(args):
    """
    Create configuration files for each use case based on Excel sheet data.
    """
    # Get use cases from Excel sheets, considering the selected use case if provided
    use_cases = get_use_case_sheets(args.excel_path, args.use_case)
    
    if not use_cases:
        return
    
    for use_case in use_cases:
        print(f"\nProcessing use case: {use_case}")
        
        try:
            # Read the specific use case sheet
            df = pd.read_excel(args.excel_path, sheet_name=use_case)
            
            # Add debug prints
            print("\nDataFrame head:")
            print(df.head())
            print("\nColumn names (exact):", [col for col in df.columns])
            
            # Extract system_name and application_domain from the sheet
            # Modified to handle case sensitivity and whitespace
            domain_col = next((col for col in df.columns if col.lower().strip() == 'application_domain'), None)
            system_col = next((col for col in df.columns if col.lower().strip() == 'system_name'), None)
            
            system_name = df[system_col].iloc[0] if system_col else use_case
            application_domain = df[domain_col].iloc[0] if domain_col else ""
            
            # Debug print
            print(f"\nExtracted values:")
            print(f"system_name: {system_name}")
            print(f"application_domain: {application_domain}")
            
            if pd.isna(application_domain):
                print("WARNING: application_domain is NaN")
                application_domain = ""
                
        except Exception as e:
            print(f"Error reading sheet '{use_case}': {str(e)}")
            continue
        
        # Get references and group by R-type
        reference_files = get_reference_files(args.pdf_dir, use_case)
        r_type_groups = group_references_by_type(reference_files)
        
        print("\nR-type groups found:")
        for r_type, files in r_type_groups.items():
            print(f"\nR{r_type} group:")
            for f in files:
                print(f"- {f}")
        
        ref_combinations = get_reference_combinations(r_type_groups, args.pdf_dir, use_case)
        
        base_config = {
            "system_name": system_name,
            "application_domain": application_domain,
            "relationship_type": args.relationship_type,
            "api_keys": {
                "openai_api_key": args.openai_key,
                "claude_api_key": "your-claude-api-key-here"
            },
            "selected_model": "",
            "inference_type": "",
            # "output_directory": f"{args.output_dir.replace('../', './')}/{use_case}",
            "output_directory": f"{args.output_dir}/{use_case}",
            "reference_files": create_reference_files_structure(args.pdf_dir),
            "graph_config": {
                "uri": "neo4j://localhost:7687",
                "username": "neo4j",
                "password": "your-password",
                "database": "system_knowledge"
            }
        }
        
        # Create output directory
        Path(f"{args.output_dir}/{use_case}").mkdir(parents=True, exist_ok=True)
        
        # Process each row in the sheet
        for idx, row in df.iterrows():
            if isinstance(row['ID'], str) and row['ID'] == 'End of Experiment':
                break
                
            if pd.isna(row['Model']) or pd.isna(row['ID']):
                continue
            
            model_name, inference_types = parse_model_string(row['Model'])
            
            for inference_type in inference_types:
                config = base_config.copy()
                config['selected_model'] = model_name
                config['inference_type'] = inference_type
                
                if inference_type == 'llm':
                    # For LLM, always empty references
                    config['reference_files'] = {}
                    filename = f'{args.output_dir}/{use_case}/{use_case}_experiment_{row["ID"]}_{inference_type}.json'
                    with open(filename, 'w') as f:
                        json.dump(config, f, indent=4)
                else:
                    # For RAG/Graph, include empty reference case and all combinations
                    # First create the no_ref version
                    config['reference_files'] = {}
                    filename = f'{args.output_dir}/{use_case}/{use_case}_experiment_{row["ID"]}_{inference_type}_no_ref.json'
                    with open(filename, 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    # Then create versions with references
                    for ref_combo in ref_combinations:
                        if not ref_combo:  # Skip empty combination as we handled it above
                            continue
                            
                        config = base_config.copy()
                        config['selected_model'] = model_name
                        config['inference_type'] = inference_type
                        
                        # Create structured reference files
                        structured_refs = {}
                        for file in ref_combo:
                            r_type = extract_rtype(file)
                            if r_type:
                                r_key = f'R{r_type}'
                                if r_key not in structured_refs:
                                    structured_refs[r_key] = []
                                structured_refs[r_key].append({
                                    "path": os.path.join(args.pdf_dir, file),
                                    "description": f"Documentation from {file}"
                                })
                        config['reference_files'] = structured_refs
                        
                        # Create identifier based on R-types present
                        r_types_present = set()
                        for file in ref_combo:
                            r_type = extract_rtype(file)
                            if r_type:
                                r_types_present.add(f'R{r_type}')
                        combo_str = '_'.join(sorted(r_types_present))
                        
                        filename = f'{args.output_dir}/{use_case}/{use_case}_experiment_{row["ID"]}_{inference_type}_{combo_str}.json'
                        with open(filename, 'w') as f:
                            json.dump(config, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description='Generate configuration files for experiments')
    parser.add_argument("--relationship_type", required=True, 
                      help="Type of relationship between components (e.g., electrical, mechanical)")
    parser.add_argument("--use-case", required=False,
                      default="3DPrinter",
                      help="Specific use case to process (if not provided, all use cases will be processed)")
    parser.add_argument("--pdf_dir", required=False,
                      default="../data/use_cases_large/3DPrinter/reference_pdfs",
                      help="Directory containing the PDF files")
    parser.add_argument("--output_dir", required=False,
                      default="../json/experiments",
                      help="Output directory for configuration files")
    parser.add_argument("--excel_path", required=False,
                      default="../data/experimental_details.xlsx",
                      help="Path to the Excel file containing experimental details")
    parser.add_argument("--openai_key", required=False,
                      default="your-openai-key-here",
                      help="OpenAI API key")
    
    args = parser.parse_args()
    
    create_config_files(args)

if __name__ == "__main__":
    main()
