import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import pandas as pd
import os
from datetime import datetime
import argparse

class EnhancedMetricBarPlotter:
    def __init__(self, metrics_df: pd.DataFrame):
        """
        Initialize the plotter with a DataFrame containing metrics and their standard deviations.
        
        Args:
            metrics_df: DataFrame with columns for experiment details and metrics
        """
        self.metrics_df = metrics_df
        self.metrics = self._parse_metrics()
        
        # Define color schemes matching the notebook
        self.performance_colors = {
            'f1': '#9B59B6',      # Purple for F1-Score
            'precision': '#2ECC71', # Green for Precision
            'recall': '#F1C40F',    # Yellow for Recall
            'accuracy': '#E67E22'   # Orange for Accuracy
        }
        
        self.confusion_colors = {
            'tp': '#3498DB',    # Blue
            'tn': '#2ECC71',    # Green
            'fp': '#FF5733',    # Orange-Red
            'fn': '#F1C40F'     # Yellow
        }

        self.distance_colors = {
            'edit_distance': '#3498DB',    # Blue
            'spectral_distance': '#FF5733'  # Orange-Red
        }
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = f'output_figs_'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _parse_metrics(self) -> Dict[str, Dict[str, tuple]]:
        """Parse the metrics DataFrame to extract means and standard deviations."""
        results = {}
        
        for _, row in self.metrics_df.iterrows():
            exp_name = row['Experiment']
            metrics = {}
            
            # Parse all metrics including distances
            for metric in ['TP', 'TN', 'FP', 'FN', 'Accuracy', 'Precision', 'Recall', 'F1', 'Edit_Distance', 'Spectral_Distance']:
                mean_str, std_str = row[metric].split('±')
                # Strip whitespace and convert to float
                mean_val = float(mean_str.strip())
                std_val = float(std_str.strip())
                metrics[metric.lower()] = (mean_val, std_val)
                
            results[exp_name] = metrics
            
        return results
    
    def _calculate_optimal_bar_width(self, metrics: List[str]) -> float:
        """Calculate optimal bar width based on the longest text label."""
        max_lines = 0
        max_chars_per_line = 0
        
        # Check all metrics for all experiments
        for exp_name, exp_metrics in self.metrics.items():
            for metric in metrics:
                mean, std = exp_metrics[metric]
                # Format label as it would appear in plot
                label = f'{mean:.3f}\n±{std:.3f}'
                lines = label.split('\n')
                max_lines = max(max_lines, len(lines))
                max_chars_per_line = max(max_chars_per_line, max(len(line) for line in lines))
        
        # Base width calculation:
        # - Each character needs roughly 0.05 units of width
        # - Add 20% padding
        base_width = max_chars_per_line * 0.05 * 1.2
        
        # Adjust for number of lines (more lines need wider bars)
        width_factor = 1 + (max_lines - 1) * 0.2
        
        return base_width * width_factor

    def _lighten_color(self, hex_color: str, factor: float = 0.7) -> str:
        """Convert hex color to a lighter version by adjusting RGB values.
        
        Args:
            hex_color: Hex color code (e.g., '#3498DB')
            factor: How much to lighten (0 to 1, higher means lighter)
        """
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Make it lighter
        lighter_rgb = [min(255, int(255 - ((255 - c) * (1 - factor)))) for c in rgb]
        
        # Convert back to hex
        return '#{:02x}{:02x}{:02x}'.format(*lighter_rgb)

    def _create_gradient_colors(self, base_color: str, n_models: int) -> List[str]:
        """Create a gradient of colors from a base color.
        
        Args:
            base_color: Hex color code (e.g., '#3498DB')
            n_models: Number of models to create gradients for
            
        Returns:
            List of hex color codes representing the gradient
        """
        # Convert hex to RGB
        base_color = base_color.lstrip('#')
        base_rgb = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Create gradient by adjusting the saturation and brightness
        gradient_colors = []
        for i in range(n_models):
            # Calculate factor for this position in gradient (0.5 to 1.5 for more contrast)
            factor = 0.5 + (1.0 * i / (n_models - 1)) if n_models > 1 else 1.0
            
            # Adjust RGB values
            rgb = tuple(min(255, int(c * factor)) for c in base_rgb)
            
            # Convert back to hex
            gradient_colors.append('#{:02x}{:02x}{:02x}'.format(*rgb))
            
        return gradient_colors

    def _get_experiment_group(self, exp_name: str) -> str:
        """Extract the model name from the experiment name.
        Format: CASE_{ID}_{MODEL_NAME}_...
        Returns the MODEL_NAME part to detect transitions between different models.
        """
        parts = exp_name.split('_')
        if len(parts) >= 3 and parts[0].upper() == 'CASE':
            return parts[2]  # Return the model name part (after CASE_{ID}_)
        return exp_name  # Fallback for unexpected format

    def _create_plot(self, metrics: List[str], save_path: Optional[str], figsize: tuple, title: str, alpha: float, light_factor: float, color_scheme: Dict[str, str]):
        """Create a bar plot for the specified metrics."""
        n_metrics = len(metrics)
        n_experiments = len(self.metrics)
        
        # For all-experiments plots, create subplots
        is_all_experiments = "All Experiments" in title
        if is_all_experiments:
            # Calculate figure size based on number of metrics
            bar_width = 1.5  # Fixed bar width for all-experiments
            bar_spacing = bar_width * 0.3  # Space between bars in same group
            group_spacing = bar_width * 2  # Space between experiment groups
            
            # Calculate total width needed
            total_width = n_experiments * bar_width + (n_experiments - 1) * bar_spacing
            subplot_height = 3  # Height for each subplot
            figsize = (total_width * 1.2, subplot_height * n_metrics)  # Add padding
            
            # Create figure with subplots stacked vertically (1 column, n_metrics rows)
            fig, axs = plt.subplots(n_metrics, 1, figsize=figsize)
            if n_metrics == 1:
                axs = [axs]
            
            # Add spacing between subplots
            plt.subplots_adjust(hspace=0.4)
            
            # Create each subplot
            for idx, (metric, ax) in enumerate(zip(metrics, axs)):
                max_y = 0  # Track maximum y value for this metric
                
                # Calculate positions for bars
                positions = [i * (bar_width + bar_spacing) for i in range(n_experiments)]
                
                # Create gradient colors for this metric based on actual number of experiments
                base_color = color_scheme[metric]
                gradient_colors = self._create_gradient_colors(base_color, n_experiments)
                

                
                # Get list of experiment names for transition detection
                exp_names = list(self.metrics.keys())
                current_model = None
                
                # Plot bars for each experiment
                for i, ((exp_name, exp_metrics), color) in enumerate(zip(self.metrics.items(), gradient_colors)):
                    mean, std = exp_metrics[metric]
                    x = positions[i]
                    
                    # Check for model transition
                    model = self._get_experiment_group(exp_name)
                    if current_model is not None and model != current_model:
                        # print(f"Model transition detected: {current_model} -> {model}")
                        # Add vertical separator line
                        separator_x = x - (bar_width/2 + bar_spacing/2)
                        ax.axvline(x=separator_x, color='#202020', linestyle='-', linewidth=2, alpha=0.8, zorder=5)
                    current_model = model
                    
                    # Update max_y
                    max_y = max(max_y, mean + std)
                    
                    # Create lighter version of the gradient color for error bars
                    lighter_color = self._lighten_color(color, light_factor)
                    
                    # Plot main bar
                    bar = ax.bar(x, mean, bar_width,
                               color=color,
                               zorder=2)[0]
                    
                    # Plot error bar extensions
                    lower_bound = max(0, mean-std)
                    ax.bar(x, std, bar_width,
                          bottom=lower_bound,
                          color=lighter_color,
                          alpha=alpha,
                          zorder=3)
                    ax.bar(x, std, bar_width,
                          bottom=mean,
                          color=lighter_color,
                          alpha=alpha,
                          zorder=3)
                    
                    # Add boundary markers - centered on the bar
                    marker_width = bar_width * 0.1
                    line_width = 5
                    marker_x = x + bar_width/2 - marker_width/2  # Center on bar using x position
                    
                    # Add markers
                    ax.plot([marker_x, marker_x + marker_width],
                           [lower_bound, lower_bound],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    ax.plot([marker_x, marker_x + marker_width],
                           [mean, mean],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    ax.plot([marker_x, marker_x + marker_width],
                           [mean + std, mean + std],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    
                    # Add value label using bar's dimensions as reference
                    label = f'{mean:.3f}\n±{std:.3f}'
                    ax.text(bar.get_x() + bar_width/2, mean * 0.05,  # Use 5% of bar height
                           label,
                           ha='center', va='bottom',
                           rotation=90,
                           fontsize=max(8, bar_width * 20),  # Adjusted multiplier for consistent ratio
                           weight='bold')
                
                # Set subplot title and limits
                ax.set_title(metric.upper())
                ax.set_ylim(0, max_y * 1.05)
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
                ax.set_ylabel('Score')
                
                # Set x-ticks at the bar positions
                ax.set_xticks(positions)
                
                # Only show x labels on bottom subplot
                if idx == n_metrics - 1:
                    # Position x labels at the bar positions
                    ax.set_xticklabels([exp.replace('_', '\n') for exp in self.metrics.keys()],
                                     rotation=0,
                                     ha='center',
                                     va='top')
                else:
                    ax.set_xticklabels([])
            
            # Add overall title
            fig.suptitle(title, y=1.02)
            
            plt.tight_layout()
            
            if save_path:
                full_path = os.path.join(self.output_dir, save_path)
                plt.savefig(full_path, dpi=300, bbox_inches='tight')
            else:
                plt.show()
                
            plt.close()
            
        else:
            fig, ax = plt.subplots(figsize=figsize)
            
            # Calculate optimal bar width based on text content
            bar_width = self._calculate_optimal_bar_width(metrics)
            # Calculate spacing between metric groups based on bar width
            group_spacing = bar_width * 1.2  # Reduced from 3 to 2 to decrease distance between bar groups
            index = np.arange(n_metrics) * group_spacing
            
            # Track maximum y value for axis limits
            max_y = 0
            
            for i, (exp_name, exp_metrics) in enumerate(self.metrics.items()):
                means = [exp_metrics[m][0] for m in metrics]
                stds = [exp_metrics[m][1] for m in metrics]
                
                # Update max_y considering both mean and std
                max_y = max(max_y, max(m + s for m, s in zip(means, stds)))
                
                position = index + i * bar_width
                
                # Create bars for each metric
                for j, (mean, std, metric) in enumerate(zip(means, stds, metrics)):
                    color = color_scheme[metric]
                    x = position[j]
                    
                    # Create lighter version of the color for error bars
                    lighter_color = self._lighten_color(color, light_factor)
                    
                    # Plot main bar first with lower zorder
                    bar = ax.bar(x, mean, bar_width,
                               color=color,
                               zorder=2)
                    
                    # Plot error bar extensions with lighter color and transparency on top
                    # Lower extension
                    lower_bound = max(0, mean-std)
                    ax.bar(x, std, bar_width,
                          bottom=lower_bound,
                          color=lighter_color,
                          alpha=alpha,
                          zorder=3)
                    # Upper extension
                    ax.bar(x, std, bar_width,
                          bottom=mean,
                          color=lighter_color,
                          alpha=alpha,
                          zorder=3)
                    
                    # Add boundary markers with highest zorder
                    marker_width = bar_width * 0.1  # Width of boundary markers
                    line_width = 5  # Much thicker boundary markers
                    # Position markers so their center aligns with the right edge of the bar
                    marker_x = (x + bar_width/2) - marker_width/2
                    
                    # Lower bound marker
                    ax.plot([marker_x, marker_x + marker_width], 
                           [lower_bound, lower_bound],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    
                    # Mean value marker (top of main bar)
                    ax.plot([marker_x, marker_x + marker_width], 
                           [mean, mean],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    
                    # Upper bound marker
                    ax.plot([marker_x, marker_x + marker_width], 
                           [mean + std, mean + std],
                           color='black',
                           linewidth=line_width,
                           zorder=4)
                    
                    # Removed the code that sets labels for the bars
                
                # Get all bars for this experiment group for value labels
                bars = [ax.patches[i * len(metrics) * 3 + j * 3 + 2] for j in range(len(metrics))]
                self._add_value_labels(ax, bars, exp_name, metrics)
            
            ax.set_ylabel('Score')
            ax.set_title(title)
            ax.set_xticks(index + bar_width * (n_experiments - 1) / 2)
            ax.set_xticklabels([m.upper().replace('_', ' ') for m in metrics])
            
            # Set y-axis limits based on metric type
            if 'accuracy' in metrics or 'f1' in metrics:
                ax.set_ylim(0, 1)
            elif metrics[0] in ['tp', 'tn', 'fp', 'fn']:  # Confusion matrix metrics
                # Add 5% padding to the maximum y value
                ax.set_ylim(0, max_y * 1.05)
            
            # Removed the legend
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            
            if save_path:
                full_path = os.path.join(self.output_dir, save_path)
                plt.savefig(full_path, dpi=300, bbox_inches='tight')
            else:
                plt.show()
            
            plt.close()
        
    def _add_value_labels(self, ax, bars, exp_name: str, metrics: List[str]):
        """Add value labels with the same style as the notebook"""
        y_offset = 0.05  # Text y-offset from bottom
        
        for bar, metric in zip(bars, metrics):
            height = bar.get_height()
            width = bar.get_width()
            x = bar.get_x() + width/2
            
            # Get the actual mean and std values from self.metrics
            mean, std = self.metrics[exp_name][metric]
            
            # Format label with both mean and std
            label = f'{mean:.3f}\n±{std:.3f}'
            
            # Add text with notebook styling
            ax.text(x, y_offset, label,
                   ha='center', va='bottom',
                   rotation=90,
                   fontsize=self._get_font_size(bar),
                   weight='bold',
                   transform=ax.get_xaxis_transform())

    def plot_confusion_metrics(self, 
                             save_path: Optional[str] = None,
                             figsize: tuple = (15, 8),
                             alpha: float = 0.8,
                             light_factor: float = 0.6,
                             title: str = "Confusion Matrix Metrics"):
        """Plot TP, TN, FP, FN metrics."""
        metrics = ['tp', 'tn', 'fp', 'fn']
        self._create_plot(metrics, save_path, figsize, title, alpha, light_factor, color_scheme=self.confusion_colors)
        
    def plot_performance_metrics(self,
                               save_path: Optional[str] = None,
                               figsize: tuple = (15, 8),
                               alpha: float = 0.8,
                               light_factor: float = 0.6,
                               title: str = "Performance Metrics"):
        """Plot accuracy, precision, recall, F1 metrics."""
        metrics = ['accuracy', 'precision', 'recall', 'f1']
        self._create_plot(metrics, save_path, figsize, title, alpha, light_factor, color_scheme=self.performance_colors)

    def plot_distance_metrics(self,
                            save_path: Optional[str] = None,
                            figsize: tuple = (15, 8),
                            alpha: float = 0.3,
                            light_factor: float = 0.7,
                            title: str = "Distance Metrics"):
        """Plot edit distance and spectral distance metrics."""
        metrics = ['edit_distance', 'spectral_distance']
        self._create_plot(metrics, save_path, figsize, title, alpha, light_factor, color_scheme=self.distance_colors)
        
    def _get_font_size(self, bar) -> float:
        """Calculate font size based on bar width"""
        # Adjust font size based on bar width with a reasonable minimum
        return max(16, bar.get_width() * 200)  # Doubled minimum from 8 to 16 and multiplier from 70 to 140

    def _format_experiment_name(self, name: str) -> str:
        """Format the experiment name for better readability in the legend."""
        parts = name.split('_')
        return '\n'.join(filter(None, parts))

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate metric plots from experiment results CSV')
    parser.add_argument('input_csv', type=str, help='Path to the input CSV file containing experiment results')
    args = parser.parse_args()
    
    # Verify the input file exists
    if not os.path.exists(args.input_csv):
        print(f"Error: Input file '{args.input_csv}' does not exist")
        return
    
    # Read the results CSV
    try:
        results_df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return
    
    # Create consolidated plotter for all experiments
    all_plotter = EnhancedMetricBarPlotter(results_df)
    
    # Create consolidated plots
    all_plotter.plot_confusion_metrics(
        save_path='all_experiments_confusion_metrics.png',
        title="Confusion Matrix Metrics - All Experiments"
    )
    print("Created consolidated confusion matrix metrics plot")
    
    all_plotter.plot_performance_metrics(
        save_path='all_experiments_performance_metrics.png',
        title="Performance Metrics - All Experiments"
    )
    print("Created consolidated performance metrics plot")

    all_plotter.plot_distance_metrics(
        save_path='all_experiments_distance_metrics.png',
        title="Distance Metrics - All Experiments"
    )
    print("Created consolidated distance metrics plot")
    
    # Create individual plots for each experiment
    for _, row in results_df.iterrows():
        experiment_df = pd.DataFrame([row])
        plotter = EnhancedMetricBarPlotter(experiment_df)
        
        safe_name = row['Experiment'].replace(' ', '_').lower()
        
        plotter.plot_confusion_metrics(
            save_path=f'individual_{safe_name}_confusion_metrics.png',
            title=f"Confusion Matrix Metrics\n{row['Experiment']}"
        )
        print(f"Created individual confusion matrix plot for {row['Experiment']}")
        
        plotter.plot_performance_metrics(
            save_path=f'individual_{safe_name}_performance_metrics.png',
            title=f"Performance Metrics\n{row['Experiment']}"
        )
        print(f"Created individual performance metrics plot for {row['Experiment']}")

        plotter.plot_distance_metrics(
            save_path=f'individual_{safe_name}_distance_metrics.png',
            title=f"Distance Metrics\n{row['Experiment']}"
        )
        print(f"Created individual distance metrics plot for {row['Experiment']}")

if __name__ == "__main__":
    main() 