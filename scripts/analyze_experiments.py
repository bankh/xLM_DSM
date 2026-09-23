import numpy as np
from typing import List, Dict, Tuple, Optional
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExperimentContext:
    case: str = ""
    model: str = ""
    domain: str = ""
    experiment_type: str = ""
    reference_type: str = ""

class ExperimentAnalyzer:
    def __init__(self, experiments_file: str):
        self.experiments_file = experiments_file
        self.experiments = self._parse_experiments()
        
    def _parse_experiments(self) -> Dict[str, List[np.ndarray]]:
        """Parse the experiments file and extract matrices for each experiment."""
        experiments = defaultdict(list)
        current_case = ""
        current_model = ""
        current_domain = ""
        current_type = ""
        current_method = ""
        
        # Define expected matrix sizes
        domain_sizes = {
            'CubeSat-i': (6, 6),
            'Power Screwdriver-i': (7, 7)
        }
        
        with open(self.experiments_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Update state based on line content
            if 'Case' in line:
                case_match = re.match(r'Case\s+(\d+)', line)
                if case_match:
                    current_case = f"Case_{case_match.group(1)}"
                    # Reset all other states when case changes
                    current_model = ""
                    current_domain = ""
                    current_type = ""
                    current_method = ""
                continue
            
            # Update model name
            if any(model in line.lower() for model in ['gpt', 'llama', 'mixtral', 'deepseek']):
                current_model = line.strip()
                # Reset experiment type and method when model changes
                current_type = ""
                current_method = ""
                continue
            
            # Update domain
            if line in ['CubeSat-i', 'Power Screwdriver-i']:
                print(f"Domain changed from {current_domain} to {line.strip()}")
                if current_domain != line.strip():  # Domain change
                    current_domain = line.strip()
                    current_type = ""  # Reset type and method on domain change
                    current_method = ""
                continue
            # elif 'CubeSat-' in line or 'PowerDrill-' in line:
            #     current_domain = ""  # Skip non-case-i domains
            #     continue
            
            # Update experiment type
            if any(exp in line for exp in ['LLM Experiments', 'RAG Experiments', 'GraphRAG']):
                current_type = line.strip()
                current_method = ""  # Reset method when type changes
                continue
            
            # Update method (R1, R2, etc.)
            if line.startswith('R') and not line.startswith('RAG'):
                current_method = line.strip()
                continue
            
            # Skip 'na' matrices
            if line.strip().lower() == 'na':
                continue
            
            # Parse matrix if we have valid context
            if line.startswith('Matrix:') and all([current_case, current_model, current_domain]):
                matrix_str = line.replace('Matrix:', '').strip()
                try:
                    matrix = np.array(eval(matrix_str))
                    # Validate matrix size for domain
                    expected_size = domain_sizes.get(current_domain)
                    if matrix.shape != expected_size:
                        print(f"Warning: Skipping matrix with wrong size {matrix.shape} for domain {current_domain}")
                        continue
                        
                    # Create experiment identifier from current state
                    exp_parts = [current_case, current_model, current_domain]
                    if current_type:
                        exp_parts.append(current_type)
                    if current_method:
                        exp_parts.append(current_method)
                    
                    exp_id = '_'.join(exp_parts)
                    print(f"Adding matrix for {exp_id}")
                    experiments[exp_id].append(matrix)
                except Exception as e:
                    print(f"Failed to parse matrix: {matrix_str}")
                    print(f"Error: {str(e)}")
                
        return dict(experiments)
    
    def compute_edit_distance(self, pred_matrix: np.ndarray, true_matrix: np.ndarray) -> float:
        """Compute edit distance (L1 norm) between predicted and true matrices."""
        return float(np.sum(np.abs(true_matrix - pred_matrix)))
    
    def compute_spectral_distance(self, pred_matrix: np.ndarray, true_matrix: np.ndarray) -> float:
        """Compute spectral distance between predicted and true matrices."""
        # Compute eigenvalues
        vals_gt = np.linalg.eigvals(true_matrix)
        vals_pred = np.linalg.eigvals(pred_matrix)
        
        # Sort descending by real part
        sort_gt = np.sort(vals_gt.real)[::-1]
        sort_pred = np.sort(vals_pred.real)[::-1]
        
        # Euclidean (L2) distance
        return float(np.sqrt(np.sum((sort_gt - sort_pred)**2)))
    
    def compute_metrics(self, pred_matrix: np.ndarray, true_matrix: np.ndarray) -> Dict[str, float]:
        """Compute metrics between predicted and true matrices."""
        # Convert matrices to binary format (0 and 1)
        pred_binary = (pred_matrix > 0).astype(int)
        true_binary = (true_matrix > 0).astype(int)
        
        # Flatten matrices for metric computation
        pred_flat = pred_binary.flatten()
        true_flat = true_binary.flatten()
        
        # Compute TP, TN, FP, FN
        tp = np.sum((pred_flat == 1) & (true_flat == 1))
        tn = np.sum((pred_flat == 0) & (true_flat == 0))
        fp = np.sum((pred_flat == 1) & (true_flat == 0))
        fn = np.sum((pred_flat == 0) & (true_flat == 1))
        
        # Compute edit and spectral distances
        edit_dist = self.compute_edit_distance(pred_matrix, true_matrix)
        spectral_dist = self.compute_spectral_distance(pred_matrix, true_matrix)
        
        metrics = {
            'accuracy': accuracy_score(true_flat, pred_flat),
            'precision': precision_score(true_flat, pred_flat, zero_division=0),
            'recall': recall_score(true_flat, pred_flat, zero_division=0),
            'f1': f1_score(true_flat, pred_flat, zero_division=0),
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
            'edit_distance': edit_dist,
            'spectral_distance': spectral_dist
        }
        
        return metrics
    
    def analyze_experiment(self, experiment_name: str, ground_truth_cubesat: np.ndarray, ground_truth_powerscrewdriver: np.ndarray) -> Tuple[Dict[str, float], Dict[str, float], List[Dict[str, float]]]:
        """Analyze a single experiment and return metrics with standard deviation and individual run metrics."""
        if experiment_name not in self.experiments:
            return {}, {}, []
            
        matrices = self.experiments[experiment_name]
        all_metrics = []
        individual_metrics = []  # Store metrics for each individual run
        
        # Determine which ground truth to use based on domain
        ground_truth = ground_truth_cubesat if 'CubeSat' in experiment_name else ground_truth_powerscrewdriver
        expected_shape = ground_truth.shape
        
        for i, matrix in enumerate(matrices):
            if matrix.shape != expected_shape:
                print(f"Skipping matrix with incompatible shape {matrix.shape} for {experiment_name}")
                continue
            metrics = self.compute_metrics(matrix, ground_truth)
            all_metrics.append(metrics)
            
            # Store individual run metrics with run number and experiment name
            individual_run_metrics = metrics.copy()
            individual_run_metrics['experiment_id'] = experiment_name
            individual_run_metrics['run_number'] = i
            individual_metrics.append(individual_run_metrics)
            
        if not all_metrics:  # Skip if no valid matrices were found
            return {}, {}, []
            
        # Calculate mean and std for each metric
        mean_metrics = {}
        std_metrics = {}
        
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'tp', 'tn', 'fp', 'fn', 'edit_distance', 'spectral_distance']:
            values = [m[metric] for m in all_metrics]
            mean_metrics[metric] = np.mean(values)
            std_metrics[metric] = np.std(values)
            
        return mean_metrics, std_metrics, individual_metrics
    
    def analyze_all_experiments(self, ground_truth_cubesat: np.ndarray, ground_truth_powerscrewdriver: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze all experiments and return results as two DataFrames: one for averages and one for individual runs."""
        results = []
        individual_results = []
        
        for exp_name in self.experiments.keys():
            mean_metrics, std_metrics, individual_metrics = self.analyze_experiment(exp_name, ground_truth_cubesat, ground_truth_powerscrewdriver)
            
            if mean_metrics:  # Skip empty results
                # Average results
                result = {
                    'Experiment': exp_name,
                    'TP': f"{mean_metrics['tp']:.1f} ± {std_metrics['tp']:.1f}",
                    'TN': f"{mean_metrics['tn']:.1f} ± {std_metrics['tn']:.1f}",
                    'FP': f"{mean_metrics['fp']:.1f} ± {std_metrics['fp']:.1f}",
                    'FN': f"{mean_metrics['fn']:.1f} ± {std_metrics['fn']:.1f}",
                    'Accuracy': f"{mean_metrics['accuracy']:.4f} ± {std_metrics['accuracy']:.4f}",
                    'Precision': f"{mean_metrics['precision']:.4f} ± {std_metrics['precision']:.4f}",
                    'Recall': f"{mean_metrics['recall']:.4f} ± {std_metrics['recall']:.4f}",
                    'F1': f"{mean_metrics['f1']:.4f} ± {std_metrics['f1']:.4f}",
                    'Edit_Distance': f"{mean_metrics['edit_distance']:.4f} ± {std_metrics['edit_distance']:.4f}",
                    'Spectral_Distance': f"{mean_metrics['spectral_distance']:.4f} ± {std_metrics['spectral_distance']:.4f}"
                }
                results.append(result)
                
                # Individual run results - ensure experiment_id is first column
                for run_metric in individual_metrics:
                    ordered_metrics = {
                        'experiment_id': run_metric['experiment_id'],
                        'run_number': run_metric['run_number'],
                        'TP': run_metric['tp'],
                        'TN': run_metric['tn'],
                        'FP': run_metric['fp'],
                        'FN': run_metric['fn'],
                        'Accuracy': run_metric['accuracy'],
                        'Precision': run_metric['precision'],
                        'Recall': run_metric['recall'],
                        'F1': run_metric['f1'],
                        'Edit_Distance': run_metric['edit_distance'],
                        'Spectral_Distance': run_metric['spectral_distance']
                    }
                    individual_results.append(ordered_metrics)
                
        # Create DataFrames with columns in correct order
        results_df = pd.DataFrame(results)
        individual_results_df = pd.DataFrame(individual_results)
        
        # Ensure column order for individual results
        column_order = ['experiment_id', 'run_number', 'TP', 'TN', 'FP', 'FN', 'Accuracy', 
                       'Precision', 'Recall', 'F1', 'Edit_Distance', 'Spectral_Distance']
        individual_results_df = individual_results_df[column_order]
        
        return results_df, individual_results_df

def main():
    # Create timestamp for file names
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Example usage
    analyzer = ExperimentAnalyzer('xLM_DSM_wip/data/experiments.txt')
    
    # Save parsed experiments to CSV with timestamp
    experiment_data = []
    for exp_name, matrices in analyzer.experiments.items():
        for i, matrix in enumerate(matrices):
            # Convert matrix to string format without extra whitespace or newlines
            matrix_str = str(matrix.tolist()).replace(' ', '').replace('\n', '')
            experiment_data.append({
                'experiment_id': exp_name,
                'matrix_index': i,
                'matrix': matrix_str
            })
    
    # Create DataFrame and save to CSV with timestamp
    exp_df = pd.DataFrame(experiment_data)
    clean_csv_path = f'experiment_clean_{timestamp}.csv'
    exp_df.to_csv(clean_csv_path, index=False)
    print(f"\nParsed experiments saved to {clean_csv_path}")
    
    # Define ground truth matrices
    ground_truth_cubesat = np.array([
        [1, 1, 1, 1, 1, 1],
        [1, 1, 0, 0, 1, 1],
        [1, 0, 1, 0, 0, 0],
        [1, 0, 0, 1, 0, 1],
        [1, 1, 0, 0, 1, 1],
        [1, 1, 0, 0, 0, 1]
    ])
    
    ground_truth_powerscrewdriver = np.array([
        [1, 1, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 0, 1, 1],
        [0, 1, 1, 0, 1, 1, 0],
        [0, 0, 0, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1],
        [1, 1, 0, 1, 1, 1, 1],
    ])
    
    # Analyze all experiments
    results_df, individual_results_df = analyzer.analyze_all_experiments(ground_truth_cubesat, ground_truth_powerscrewdriver)
    
    # Print average results
    print("\nExperiment Results (Case i only):")
    print("Note: Case ii (Identification and classification) will be analyzed separately.")
    print(results_df.to_string(index=False))
    
    # Save average results to CSV with timestamp
    results_csv_path = f'experiment_results_case_i_{timestamp}.csv'
    results_df.to_csv(results_csv_path, index=False)
    print(f"\nAverage results saved to {results_csv_path}")
    
    # Save individual run results to CSV with timestamp
    individual_results_csv_path = f'experiment_results_individual_runs_case_i_{timestamp}.csv'
    individual_results_df.to_csv(individual_results_csv_path, index=False)
    print(f"Individual run results saved to {individual_results_csv_path}")

if __name__ == "__main__":
    main() 