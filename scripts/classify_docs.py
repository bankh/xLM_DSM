#!/usr/bin/env python3
"""
Reference Classification Script for xLM_DSM Project

This script categorizes references from a CSV file using local models.
It follows the R-type classification system:
- R1: Expert knowledge (research papers, expert reports, etc.)
- R2: Formal and normative knowledge (textbooks, standards, etc.)
- R3: Non-expert knowledge (crowdsourcing, internet solutions, etc.)
"""

import os
import re
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
from datetime import datetime
import base64

# LangChain imports for local models
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
 
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reference_classification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ClassificationConfig:
    """Configuration for reference classification."""
    csv_file_path: Optional[str]
    output_dir: str = "classified_references"
    model_name: str = "llama3.3:70b-8k"  # Default local model
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 1200
    chunk_overlap: int = 300
    max_retries: int = 3
    temperature: float = 0.1
    batch_size: int = 5
    use_vision: bool = False
    vision_page: int = 1
    
    # R-type definitions
    r_type_definitions: Dict[str, str] = field(default_factory=lambda: {
        "R1": "Expert knowledge: Research papers, expert reports, peer-reviewed articles, technical specifications from domain experts, academic publications, industry expert documentation",
        "R2": "Formal and normative knowledge: Textbooks, standards, regulations, official documentation, formal procedures, institutional guidelines, technical manuals from authoritative sources",
        "R3": "Non-expert knowledge: Crowdsourcing solutions, internet-based design solutions, community forums, user-generated content, informal documentation, DIY guides, online tutorials"
    })

class ReferenceClassifier:
    """Class for classifying references using local models."""
    
    def __init__(self, config: ClassificationConfig):
        self.config = config
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self._setup_models()
        
    def _setup_models(self):
        """Initialize local models."""
        try:
            # Initialize Ollama Chat model
            self.llm = ChatOllama(
                model=self.config.model_name,
                base_url=self.config.ollama_base_url,
                temperature=self.config.temperature
            )
            logger.info(f"Initialized LLM with model: {self.config.model_name}")
            
            # Initialize embeddings
            self.embeddings = OllamaEmbeddings(
                model=self.config.embedding_model,
                base_url=self.config.ollama_base_url
            )
            logger.info(f"Initialized embeddings with model: {self.config.embedding_model}")
            
        except Exception as e:
            logger.error(f"Error setting up models: {str(e)}")
            raise
    
    def load_csv_data(self) -> pd.DataFrame:
        """Load reference data from CSV file."""
        try:
            df = pd.read_csv(self.config.csv_file_path)
            logger.info(f"Loaded CSV with {len(df)} references")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise

    def build_dataframe_from_inputs(self, file_paths: List[str]) -> pd.DataFrame:
        """Build a DataFrame compatible with the classifier from provided file paths."""
        rows: List[Dict] = []
        for index, file_path in enumerate(file_paths):
            path_obj = Path(file_path)
            if not path_obj.exists():
                logger.warning(f"Input file not found and will be skipped: {file_path}")
                continue
            if path_obj.suffix.lower() not in [".pdf", ".txt", ".md"]:
                logger.warning(f"Unsupported input file type (skipped): {file_path}")
                continue
            rows.append({
                "id": f"ref_{index + 1}",
                "title": path_obj.stem,
                "authors": "",
                "source": path_obj.parent.name,
                "year": "",
                "description": "",
                "file_path": str(path_obj)
            })
        df = pd.DataFrame(rows, columns=["id","title","authors","source","year","description","file_path"])
        logger.info(f"Built DataFrame from direct inputs with {len(df)} references")
        return df

    def render_pdf_page_to_image(self, pdf_path: str, page_number: int, dpi: int = 180) -> Optional[str]:
        """Render a specific PDF page to a temporary PNG image and return its path.

        Returns None if rendering is not possible (missing dependency or file).
        """
        try:
            import fitz  # PyMuPDF
        except Exception:
            logger.error("Vision mode requires PyMuPDF. Install with: pip install pymupdf")
            return None

        try:
            pdf_path_obj = Path(pdf_path)
            if not pdf_path_obj.exists():
                logger.warning(f"PDF not found for vision mode: {pdf_path}")
                return None

            page_index = max(1, page_number) - 1
            with fitz.open(str(pdf_path_obj)) as doc:
                if page_index < 0 or page_index >= len(doc):
                    logger.warning(f"Requested page {page_number} out of range (1-{len(doc)}). Using page 1.")
                    page_index = 0
                page = doc.load_page(page_index)
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                output_dir = Path(self.config.output_dir) / "_vision_pages"
                output_dir.mkdir(parents=True, exist_ok=True)
                out_path = output_dir / f"{pdf_path_obj.stem}_page{page_index + 1}.png"
                pix.save(str(out_path))
                return str(out_path)
        except Exception as e:
            logger.error(f"Error rendering PDF page for vision mode: {str(e)}")
            return None
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return ""
        
        try:
            if file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
                documents = loader.load()
                return " ".join([doc.page_content for doc in documents])
            elif file_path.suffix.lower() in ['.txt', '.md']:
                loader = TextLoader(str(file_path))
                documents = loader.load()
                return " ".join([doc.page_content for doc in documents])
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return ""
    
    def create_classification_prompt(self, reference_info: Dict, extracted_text: str = "") -> str:
        """Create a prompt for classifying a reference. Strips R-type from title to avoid leaking ground truth."""
        title_for_prompt = self._strip_ground_truth_from_title(reference_info.get('title', 'N/A'))
        prompt = f"""
You are an expert at categorizing technical references and documents. Your task is to classify the following reference into one of three categories based on the type of knowledge it contains.

REFERENCE INFORMATION:
Title: {title_for_prompt}
Authors: {reference_info.get('authors', 'N/A')}
Source: {reference_info.get('source', 'N/A')}
Year: {reference_info.get('year', 'N/A')}
Description: {reference_info.get('description', 'N/A')}

EXTRACTED TEXT (first 1000 characters):
{extracted_text[:1000] if extracted_text else 'No text available'}

CLASSIFICATION CATEGORIES:
R1 - Expert Knowledge: Research papers, expert reports, peer-reviewed articles, technical specifications from domain experts, academic publications, industry expert documentation

R2 - Formal and Normative Knowledge: Textbooks, standards, regulations, official documentation, formal procedures, institutional guidelines, technical manuals from authoritative sources

R3 - Non-expert Knowledge: Crowdsourcing solutions, internet-based design solutions, community forums, user-generated content, informal documentation, DIY guides, online tutorials

INSTRUCTIONS:
1. Analyze the reference information and extracted text
2. Consider the source, authors, and content type
3. Classify into R1, R2, or R3 based on the knowledge type
4. Provide a confidence score (0-1) for your classification
5. Give a brief reasoning for your classification

RESPONSE FORMAT:
Return your response in JSON format:
{{
    "classification": "R1|R2|R3",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this reference fits this category"
}}

CLASSIFICATION:
"""
        return prompt
    
    def classify_reference(self, reference_info: Dict, extracted_text: str = "") -> Dict:
        """Classify a single reference."""
        prompt = self.create_classification_prompt(reference_info, extracted_text)
        
        for attempt in range(self.config.max_retries):
            try:
                # If vision mode enabled and a PDF is provided, render a page and include as image input
                if self.config.use_vision and reference_info.get('file_path', '').lower().endswith('.pdf'):
                    image_path = self.render_pdf_page_to_image(reference_info['file_path'], self.config.vision_page)
                    if image_path:
                        try:
                            with open(image_path, "rb") as img_f:
                                b64 = base64.b64encode(img_f.read()).decode("utf-8")
                            data_url = f"data:image/png;base64,{b64}"
                        except Exception as enc_err:
                            logger.warning(f"Failed to base64-encode image; falling back to text-only. Error: {enc_err}")
                            data_url = None

                        if data_url:
                            msg = HumanMessage(content=[
                                {"type": "image_url", "image_url": {"url": data_url}},
                                {"type": "text", "text": f"Classify the reference using the content of this page image (page {self.config.vision_page}).\n\n" + prompt}
                            ])
                            response = self.llm([msg])
                        else:
                            response = self.llm([HumanMessage(content=prompt)])
                    else:
                        response = self.llm([HumanMessage(content=prompt)])
                else:
                    response = self.llm([HumanMessage(content=prompt)])
                result = response.content.strip()
                
                # Try to parse JSON response
                try:
                    classification_result = json.loads(result)
                    return {
                        'reference_id': reference_info.get('id', 'unknown'),
                        'title': reference_info.get('title', ''),
                        'classification': classification_result.get('classification', 'UNKNOWN'),
                        'confidence': classification_result.get('confidence', 0.0),
                        'reasoning': classification_result.get('reasoning', ''),
                        'original_info': reference_info
                    }
                except json.JSONDecodeError:
                    # Fallback parsing for non-JSON responses
                    lines = result.split('\n')
                    classification = 'UNKNOWN'
                    confidence = 0.0
                    reasoning = result
                    
                    for line in lines:
                        if 'R1' in line or 'R2' in line or 'R3' in line:
                            if 'R1' in line:
                                classification = 'R1'
                            elif 'R2' in line:
                                classification = 'R2'
                            elif 'R3' in line:
                                classification = 'R3'
                    
                    return {
                        'reference_id': reference_info.get('id', 'unknown'),
                        'title': reference_info.get('title', ''),
                        'classification': classification,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'original_info': reference_info
                    }
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for reference {reference_info.get('title', 'unknown')}: {str(e)}")
                if attempt == self.config.max_retries - 1:
                    return {
                        'reference_id': reference_info.get('id', 'unknown'),
                        'title': reference_info.get('title', ''),
                        'classification': 'ERROR',
                        'confidence': 0.0,
                        'reasoning': f'Classification failed after {self.config.max_retries} attempts: {str(e)}',
                        'original_info': reference_info
                    }
        
        return None
    
    def process_references(self, df: pd.DataFrame) -> List[Dict]:
        """Process all references in the CSV file."""
        results = []
        total_references = len(df)
        
        logger.info(f"Starting classification of {total_references} references")
        
        for index, row in df.iterrows():
            logger.info(f"Processing reference {index + 1}/{total_references}: {row.get('title', 'Unknown')}")
            
            # Extract reference information
            reference_info = {
                'id': row.get('id', f'ref_{index}'),
                'title': row.get('title', ''),
                'authors': row.get('authors', ''),
                'source': row.get('source', ''),
                'year': row.get('year', ''),
                'description': row.get('description', ''),
                'file_path': row.get('file_path', '')
            }
            
            # Extract text if file path is provided
            extracted_text = ""
            if reference_info['file_path']:
                extracted_text = self.extract_text_from_file(reference_info['file_path'])
            
            # Classify the reference
            classification_result = self.classify_reference(reference_info, extracted_text)
            if classification_result:
                results.append(classification_result)
            
            # Log progress
            if (index + 1) % 10 == 0:
                logger.info(f"Processed {index + 1}/{total_references} references")
        
        return results
    
    def save_results(self, results: List[Dict]):
        """Save classification results to files."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        json_file = output_dir / f"classification_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved detailed results to: {json_file}")
        
        # Save summary as CSV
        summary_data = []
        for result in results:
            summary_data.append({
                'reference_id': result['reference_id'],
                'title': result['title'],
                'classification': result['classification'],
                'confidence': result['confidence'],
                'reasoning': result['reasoning']
            })
        
        summary_df = pd.DataFrame(summary_data)
        csv_file = output_dir / f"classification_summary_{timestamp}.csv"
        summary_df.to_csv(csv_file, index=False)
        logger.info(f"Saved summary to: {csv_file}")
        
        # Generate statistics
        self._generate_statistics(results, output_dir, timestamp)
        
        # Generate confusion matrix when ground truth is in filenames
        self._generate_confusion_matrix(results, output_dir, timestamp)
        
        return json_file, csv_file
    
    def _generate_statistics(self, results: List[Dict], output_dir: Path, timestamp: str):
        """Generate classification statistics."""
        classifications = [r['classification'] for r in results]
        r1_count = classifications.count('R1')
        r2_count = classifications.count('R2')
        r3_count = classifications.count('R3')
        error_count = classifications.count('ERROR')
        unknown_count = classifications.count('UNKNOWN')
        
        total = len(results)
        
        stats = {
            'total_references': total,
            'R1_count': r1_count,
            'R2_count': r2_count,
            'R3_count': r3_count,
            'error_count': error_count,
            'unknown_count': unknown_count,
            'R1_percentage': (r1_count / total * 100) if total > 0 else 0,
            'R2_percentage': (r2_count / total * 100) if total > 0 else 0,
            'R3_percentage': (r3_count / total * 100) if total > 0 else 0,
            'error_percentage': (error_count / total * 100) if total > 0 else 0,
            'unknown_percentage': (unknown_count / total * 100) if total > 0 else 0
        }
        
        # Save statistics
        stats_file = output_dir / f"classification_statistics_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Print statistics
        logger.info("Classification Statistics:")
        logger.info(f"Total references: {total}")
        logger.info(f"R1 (Expert Knowledge): {r1_count} ({stats['R1_percentage']:.1f}%)")
        logger.info(f"R2 (Formal/Normative): {r2_count} ({stats['R2_percentage']:.1f}%)")
        logger.info(f"R3 (Non-expert): {r3_count} ({stats['R3_percentage']:.1f}%)")
        logger.info(f"Errors: {error_count} ({stats['error_percentage']:.1f}%)")
        logger.info(f"Unknown: {unknown_count} ({stats['unknown_percentage']:.1f}%)")
        
        logger.info(f"Statistics saved to: {stats_file}")
    
    def _extract_ground_truth_from_title(self, title: str) -> Optional[str]:
        """Extract ground-truth R-type from filename/title (e.g., R1, R2, R3). Returns None if not found."""
        match = re.search(r'\bR([123])\b', title)
        return f"R{match.group(1)}" if match else None
    
    def _strip_ground_truth_from_title(self, title: str) -> str:
        """Remove R-type prefix from title so we do not leak ground truth to the model."""
        return re.sub(r'\bR[123]-?\s*', '', title).strip()
    
    def _generate_confusion_matrix(self, results: List[Dict], output_dir: Path, timestamp: str):
        """Compute and log confusion matrix when ground truth is available in filenames."""
        # Build lists of predicted and ground truth, skipping entries without ground truth
        y_pred: List[str] = []
        y_true: List[str] = []
        labels = ["R1", "R2", "R3"]
        
        for r in results:
            gt = self._extract_ground_truth_from_title(r.get("title", ""))
            if gt is None:
                continue
            pred = r.get("classification", "UNKNOWN")
            if pred not in labels:
                continue  # Skip ERROR, UNKNOWN for confusion matrix
            y_true.append(gt)
            y_pred.append(pred)
        
        if not y_true:
            logger.info("No ground truth found in filenames (R1/R2/R3); skipping confusion matrix.")
            return
        
        try:
            from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
        except ImportError:
            logger.warning("sklearn not installed; computing confusion matrix manually.")
            # Manual confusion matrix
            cm_dict: Dict[str, Dict[str, int]] = {lbl: {l: 0 for l in labels} for lbl in labels}
            for gt, pred in zip(y_true, y_pred):
                cm_dict[gt][pred] = cm_dict[gt].get(pred, 0) + 1
            cm = [[cm_dict[gt][pred] for pred in labels] for gt in labels]
            accuracy = sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true)
        else:
            cm = confusion_matrix(y_true, y_pred, labels=labels)
            accuracy = accuracy_score(y_true, y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average=None)
        
        # Save confusion matrix as CSV
        cm_df = pd.DataFrame(cm, index=labels, columns=labels)
        cm_df.index.name = "Ground Truth"
        cm_csv = output_dir / f"confusion_matrix_{timestamp}.csv"
        cm_df.to_csv(cm_csv)
        logger.info(f"Confusion matrix saved to: {cm_csv}")
        
        # Log to file and console
        logger.info("Confusion Matrix (rows=ground truth, cols=predicted):")
        logger.info(f"\n{cm_df.to_string()}")
        logger.info(f"Accuracy (vs ground truth in filenames): {accuracy:.2%} ({sum(a == b for a, b in zip(y_true, y_pred))}/{len(y_true)})")
        
        # Save extended metrics JSON
        metrics = {
            "accuracy": float(accuracy),
            "n_with_ground_truth": len(y_true),
            "n_total": len(results),
            "confusion_matrix": cm_df.to_dict(),
        }
        try:
            prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average=None)
            metrics["precision_per_class"] = {labels[i]: float(prec[i]) for i in range(len(labels))}
            metrics["recall_per_class"] = {labels[i]: float(rec[i]) for i in range(len(labels))}
            metrics["f1_per_class"] = {labels[i]: float(f1[i]) for i in range(len(labels))}
        except Exception:
            pass
        
        metrics_file = output_dir / f"classification_metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Classification metrics saved to: {metrics_file}")
    
    def run_classification(self, df: Optional[pd.DataFrame] = None):
        """Main method to run the classification process."""
        logger.info("Starting reference classification process")
        
        # Load CSV data if not provided
        if df is None:
            if not self.config.csv_file_path:
                raise ValueError("No input provided: csv_file_path is None and no DataFrame passed to run_classification.")
            df = self.load_csv_data()
        
        # Process references
        results = self.process_references(df)
        
        # Save results
        json_file, csv_file = self.save_results(results)
        
        logger.info("Classification process completed successfully")
        logger.info(f"Results saved to: {self.config.output_dir}")
        
        return results


def main():
    """Main function to run the classification script."""
    parser = argparse.ArgumentParser(description='Classify references using local models (CSV or direct PDF/TXT/MD)')
    parser.add_argument('csv_file', nargs='?', 
                        default=None, 
                        help='Path to the CSV file containing reference information (optional if using --from-pdfs/--from-dir)')
    parser.add_argument('--output-dir', 
                        default='classified_references', 
                        help='Output directory for results')
    parser.add_argument('--model', 
                        default='llama3.3:70b-8k', 
                        help='Ollama model name to use')
    parser.add_argument('--ollama-url', 
                        default='http://localhost:11434', 
                        help='Ollama base URL')
    parser.add_argument('--embedding-model', 
                        default='nomic-embed-text', help='Embedding model name')
    parser.add_argument('--temperature', 
                        type=float, default=0.1, 
                        help='Model temperature')
    parser.add_argument('--max-retries', 
                        type=int, default=3, 
                        help='Maximum retry attempts')
    parser.add_argument('--from-pdfs', 
                        nargs='+', 
                        default=None, 
                        help='One or more PDF/TXT/MD files to classify directly')
    parser.add_argument('--from-dir', 
                        default=None, 
                        help='Directory to scan for PDF/TXT/MD files recursively')
    parser.add_argument('--use-vision', 
                        action='store_true', 
                        help='Use a vision model and classify from a rendered PDF page image')
    parser.add_argument('--page', 
                        type=int, 
                        default=1, 
                        help='PDF page number to use in vision mode (1-based)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = ClassificationConfig(
        csv_file_path=args.csv_file,
        output_dir=args.output_dir,
        model_name=args.model,
        ollama_base_url=args.ollama_url,
        embedding_model=args.embedding_model,
        temperature=args.temperature,
        max_retries=args.max_retries,
        use_vision=args.use_vision,
        vision_page=args.page
    )
    
    # Resolve inputs
    direct_files: List[str] = []
    if args.from_pdfs:
        direct_files.extend(args.from_pdfs)
    if args.from_dir:
        base = Path(args.from_dir)
        if not base.exists():
            parser.error(f"--from-dir path does not exist: {args.from_dir}")
        for pattern in ["*.pdf", "*.txt", "*.md"]:
            for p in base.rglob(pattern):
                direct_files.append(str(p))

    if not direct_files and not args.csv_file:
        parser.error('Provide either a CSV file or use --from-pdfs / --from-dir')

    # Run classification
    classifier = ReferenceClassifier(config)
    if direct_files:
        df = classifier.build_dataframe_from_inputs(direct_files)
        results = classifier.run_classification(df)
    else:
        results = classifier.run_classification()
    
    print(f"\nClassification completed! Results saved to: {config.output_dir}")
    print(f"Total references processed: {len(results)}")

if __name__ == "__main__":
    main()
