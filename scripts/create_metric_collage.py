#!/usr/bin/env python3
import os
import re
import argparse
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class MetricCollageCreator:
    """Creates a collage of metric plots with specific layout requirements."""
    
    def __init__(self, input_folder: str, output_path: str = "metric_collage.png"):
        """
        Initialize the collage creator.
        
        Args:
            input_folder: Path to folder containing metric plot images
            output_path: Path to save the final collage
        """
        self.input_folder = input_folder
        self.output_path = output_path
        
        # Define domains in the order they should appear
        self.domains = ["cubesat", "power_screwdriver"]
        
        # Define model order for display - Updated to include GraphRAG
        self.model_order = [
            "LLM", 
            "R1", "R2", "R3", 
            "R1-R2", "R1-R3", "R2-R3", "R1-R2-R3",
            "GraphRAG_R1-R2", "GraphRAG_R2-R3"
        ]
        
        # Define metric types
        self.metric_types = ["performance_metrics", "distance_metrics"]
        
        # Define display names for methods - Updated with GraphRAG
        self.method_display_names = {
            "LLM": "LLM",
            "R1": "RAG R1",
            "R2": "RAG R2",
            "R3": "RAG R3",
            "R1-R2": "RAG R1-R2",
            "R1-R3": "RAG R1-R3",
            "R2-R3": "RAG R2-R3",
            "R1-R2-R3": "RAG R1-R2-R3",
            "GraphRAG_R1-R2": "GraphRAG R1-R2",
            "GraphRAG_R2-R3": "GraphRAG R2-R3"
        }
        
        # Define LLM model preference order (higher priority models first)
        self.llm_model_preference = [
            "gpt-4-turbo-preview",
            "gpt-4o",
            "llama3.3:70b-8k",
            "mixtral:8x22b-5k",
            "deepseek-r1:14b-5k"
        ]
        
        # Define LLM models to use for each method (to ensure variety)
        self.method_to_llm_model = {
            "LLM": "gpt-4-turbo-preview",
            "R1": "llama3.3:70b-8k",
            "R2": "mixtral:8x22b-5k",
            "R3": "deepseek-r1:14b-5k",
            "R1-R2": "gpt-4o",
            "R1-R3": "llama3.3:70b-8k",
            "R2-R3": "mixtral:8x22b-5k",
            "R1-R2-R3": "deepseek-r1:14b-5k"
        }
        
        # Storage for images by LLM model
        self.images_by_llm_model = {}
        
        # Track which LLM models have complete data for each domain
        self.complete_llm_models = []
        
        # Font sizes
        self.title_font_size = int(550)  # 0.9 times smaller than before
        self.label_font_size = int(375)   # 2x larger for row labels (vertical text)
        self.method_label_font_size = int(375)  # 2x larger for metric labels
        self.llm_model_label_font_size = int(375)  # 2x larger for model names
        self.domain_label_font_size = int(450)  # 2x larger for domain labels
        
        # Set up fonts
        try:
            # Use DejaVuSans-Bold which is available on the system
            self.title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.title_font_size)
            self.label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.label_font_size)
            self.method_label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.method_label_font_size)
            self.llm_model_label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.llm_model_label_font_size)
            self.domain_label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.domain_label_font_size)
            print(f"Using DejaVuSans fonts with title size: {self.title_font_size}")
        except IOError as e:
            # Log the error and fall back to default font
            print(f"Error loading fonts: {e}")
            print("Falling back to default font")
            self.title_font = ImageFont.load_default()
            self.label_font = ImageFont.load_default()
            self.method_label_font = ImageFont.load_default()
            self.llm_model_label_font = ImageFont.load_default()
            self.domain_label_font = ImageFont.load_default()
    
    def parse_filename(self, filename: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse filename to extract domain, model, and metric type.
        
        Args:
            filename: Name of the image file
            
        Returns:
            Tuple of (domain, model, metric_type) or None if parsing fails
        """
        # First, check if this is an "all_experiments" file - we'll skip these
        if filename.startswith("all_experiments"):
            return None
            
        # Extract domain part
        domain_match = re.search(r'(cubesat|power_screwdriver)', filename)
        if not domain_match:
            return None
        domain = domain_match.group(1)
        
        # Extract metric type
        metric_match = re.search(r'(performance_metrics|distance_metrics|confusion_metrics)\.png$', filename)
        if not metric_match:
            return None
        metric_type = metric_match.group(1)
        
        # Skip confusion metrics as they're not part of our collage
        if metric_type == "confusion_metrics":
            return None
        
        # Extract model/method - Handle all patterns
        if "_llm_experiments" in filename:
            model = "LLM"
        elif "_rag_experiments_" in filename:
            # Look for R1, R2, R3, R1-R2, etc. patterns
            model_match = re.search(r'_rag_experiments_(r[1-3](?:-r[1-3])*)_', filename)
            if not model_match:
                return None
            model = model_match.group(1).upper()
        elif "graphrag" in filename.lower():
            # Look for both patterns: graphrag_r1-r2 and graphrag_experiments_r1-r2
            # Try first pattern (with "experiments")
            model_match = re.search(r'graphrag_experiments_(r[1-3](?:-r[1-3])*)_', filename.lower())
            if not model_match:
                # Try second pattern (without "experiments")
                model_match = re.search(r'graphrag_(r[1-3](?:-r[1-3])*)_', filename.lower())
                if not model_match:
                    return None
            model = f"GraphRAG_{model_match.group(1).upper()}"
        else:
            return None
        
        return domain, model, metric_type
    
    def load_images(self) -> bool:
        """
        Load and categorize all images from the input folder.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.input_folder):
            print(f"Error: Input folder '{self.input_folder}' does not exist")
            return False
        
        # First pass: identify all valid files and their metadata
        valid_files = []
        
        # Track all available LLM models
        available_llm_models = set()
        
        for filename in os.listdir(self.input_folder):
            if not filename.lower().endswith('.png'):
                continue
                
            parsed = self.parse_filename(filename)
            if not parsed:
                print(f"Skipping file: '{filename}' (doesn't match expected pattern)")
                continue
                
            domain, method, metric_type = parsed
            
            # Check if this is a method we're interested in
            if method not in self.model_order:
                print(f"Warning: Unknown model '{method}' in file '{filename}', skipping")
                continue
                
            # Extract the LLM model name to differentiate between files with the same method
            llm_model = "unknown"
            llm_match = re.search(r'individual_case_\d+_([^_]+)', filename)
            if llm_match:
                llm_model = llm_match.group(1)
                available_llm_models.add(llm_model)
                
            valid_files.append((filename, domain, method, metric_type, llm_model))
        
        print(f"\nAvailable LLM models: {', '.join(sorted(available_llm_models))}")
        
        # Organize files by LLM model, domain, method, and metric type
        files_by_llm_model = {}
        for filename, domain, method, metric_type, llm_model in valid_files:
            if llm_model not in files_by_llm_model:
                files_by_llm_model[llm_model] = {}
            
            if domain not in files_by_llm_model[llm_model]:
                files_by_llm_model[llm_model][domain] = {}
            
            if method not in files_by_llm_model[llm_model][domain]:
                files_by_llm_model[llm_model][domain][method] = {}
            
            files_by_llm_model[llm_model][domain][method][metric_type] = filename
        
        # We don't need complete models - we'll use all of them and show blanks where needed
        # Sort available models based on preference order
        sorted_llm_models = []
        for preferred_model in self.llm_model_preference:
            for model in available_llm_models:
                if preferred_model in model and model not in sorted_llm_models:
                    sorted_llm_models.append(model)
        
        # Add any remaining models not in preference list
        for model in available_llm_models:
            if model not in sorted_llm_models:
                sorted_llm_models.append(model)
        
        self.complete_llm_models = sorted_llm_models
        print(f"\nUsing all LLM models (even those with missing data): {', '.join(sorted_llm_models)}")
        
        # Create a blank image to use for missing data
        sample_img = None
        # Find at least one valid image first to determine size
        for llm_model in files_by_llm_model:
            for domain in files_by_llm_model[llm_model]:
                for method in files_by_llm_model[llm_model][domain]:
                    for metric_type in files_by_llm_model[llm_model][domain][method]:
                        filename = files_by_llm_model[llm_model][domain][method][metric_type]
                        try:
                            sample_img = Image.open(os.path.join(self.input_folder, filename))
                            sample_img = sample_img.rotate(-90, expand=True)
                            break
                        except:
                            continue
                    if sample_img:
                        break
                if sample_img:
                    break
            if sample_img:
                break
                
        if not sample_img:
            print("Error: Could not find any valid images to determine size")
            return False
            
        # Create blank image with same dimensions
        blank_img = Image.new('RGB', sample_img.size, 'white')
        draw = ImageDraw.Draw(blank_img)
        
        # Create a more professional looking blank image
        # Add a light gray border
        border_width = 2
        border_color = (200, 200, 200)  # Light gray
        draw.rectangle(
            [(border_width, border_width), 
             (blank_img.width - border_width, blank_img.height - border_width)], 
            outline=border_color, width=border_width
        )
        
        # Add "No Data" text in the center
        font_size = int(blank_img.height * 0.1)  # 10% of height
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Add text centered
        text = "No Data Available"
        text_color = (100, 100, 100)  # Medium gray
        draw.text(
            (blank_img.width // 2, blank_img.height // 2),
            text,
            fill=text_color,
            font=font,
            anchor="mm"
        )
        
        # Add cross-hatch pattern in very light gray
        line_color = (230, 230, 230)  # Very light gray
        line_spacing = 20
        
        # Draw diagonal lines in both directions
        for i in range(-blank_img.height, blank_img.width + blank_img.height, line_spacing):
            # Draw diagonal lines (top-left to bottom-right)
            start_x = max(0, i)
            start_y = max(0, -i)
            end_x = min(i, blank_img.width)
            end_y = min(blank_img.height, blank_img.width - i + blank_img.height)
            draw.line([(start_x, start_y), (end_x, end_y)], fill=line_color, width=1)
            
            # Draw diagonal lines (top-right to bottom-left)
            start_x = min(blank_img.width, blank_img.width - i)
            start_y = max(0, i - blank_img.width)
            end_x = max(0, blank_img.width - i - blank_img.height)
            end_y = min(blank_img.height, i)
            draw.line([(start_x, start_y), (end_x, end_y)], fill=line_color, width=1)
        
        # Load images for all models, using blanks for missing data
        for llm_model in self.complete_llm_models:
            print(f"\nLoading images for LLM model: {llm_model}")
            
            # Initialize storage for this LLM model
            self.images_by_llm_model[llm_model] = {}
            
            # Create structure for all domains and methods
            for domain in self.domains:
                self.images_by_llm_model[llm_model][domain] = {}
                for method in self.model_order:
                    self.images_by_llm_model[llm_model][domain][method] = {}
            
            # Load available images or use blanks
            for domain in self.domains:
                for method in self.model_order:
                    for metric_type in self.metric_types:
                        # Check if this combination exists
                        try:
                            if (domain in files_by_llm_model.get(llm_model, {}) and
                                method in files_by_llm_model[llm_model][domain] and
                                metric_type in files_by_llm_model[llm_model][domain][method]):
                                
                                filename = files_by_llm_model[llm_model][domain][method][metric_type]
                                img_path = os.path.join(self.input_folder, filename)
                                
                                try:
                                    # Load and rotate the image
                                    img = Image.open(img_path)
                                    img = img.rotate(-90, expand=True)
                                    self.images_by_llm_model[llm_model][domain][method][metric_type] = img
                                    print(f"Added {domain} - {method} - {metric_type} (from {llm_model})")
                                except Exception as e:
                                    print(f"Error loading image '{filename}': {e}")
                                    print(f"Using blank image for {domain} - {method} - {metric_type} (from {llm_model})")
                                    self.images_by_llm_model[llm_model][domain][method][metric_type] = blank_img.copy()
                            else:
                                print(f"Missing data for {domain} - {method} - {metric_type} (from {llm_model})")
                                self.images_by_llm_model[llm_model][domain][method][metric_type] = blank_img.copy()
                        except Exception as e:
                            print(f"Error processing {domain} - {method} - {metric_type} (from {llm_model}): {e}")
                            self.images_by_llm_model[llm_model][domain][method][metric_type] = blank_img.copy()
        
        return True
    
    def create_collage(self) -> bool:
        """
        Create the collage with the specified layout.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.complete_llm_models:
            print("Error: No LLM models found")
            return False
            
        # Find a valid image to determine dimensions
        sample_img = None
        for llm_model in self.complete_llm_models:
            for domain in self.domains:
                for method in self.model_order:
                    for metric_type in self.metric_types:
                        if metric_type in self.images_by_llm_model.get(llm_model, {}).get(domain, {}).get(method, {}):
                            sample_img = self.images_by_llm_model[llm_model][domain][method][metric_type]
                            break
                    if sample_img:
                        break
                if sample_img:
                    break
            if sample_img:
                break
                
        if not sample_img:
            print("Error: No valid images found")
            return False
            
        img_width, img_height = sample_img.size
        
        # Calculate dimensions for the collage
        n_methods = len(self.model_order)
        n_llm_models = len(self.complete_llm_models)
        n_domains = len(self.domains)
        n_metrics = len(self.metric_types)
        
        # Heights and widths for various elements
        title_height = 80 * 10  # Increased to provide more space for the title
        method_label_width = 100 * 6  # Wider for much larger vertical text
        model_label_height = 50 * 5  # Taller for much larger model labels
        domain_label_height = 50 * 9  # Increased to provide more space for domain labels
        
        # Calculate total width and height
        # Each cell contains both metrics side by side
        cell_width = img_width * n_metrics
        total_width = method_label_width + (cell_width * n_llm_models * n_domains)
        total_height = title_height + model_label_height + domain_label_height + (img_height * n_methods)
        
        # Create a blank canvas for the collage
        collage = Image.new('RGB', (total_width, total_height), 'white')
        draw = ImageDraw.Draw(collage)
        
        # Add title
        title = "Metric Comparison Across Methods, Models, and Domains"
        # Center the title in the middle of the title section, but a bit higher up to create more space below
        draw.text((total_width // 2, title_height // 3), title, fill='black', font=self.title_font, anchor='mm')
        
        # Add domain labels at the top (spanning multiple columns)
        for d, domain in enumerate(self.domains):
            # Calculate position for domain label
            domain_start_x = method_label_width + (d * n_llm_models * cell_width)
            domain_end_x = domain_start_x + (n_llm_models * cell_width)
            domain_center_x = (domain_start_x + domain_end_x) // 2
            # Position domain labels in the upper portion of their section to create more space below
            domain_y = title_height - (model_label_height // 10)
            
            # Format domain name for display
            domain_label = domain.replace("_", " ").upper()
            
            # Draw domain label
            draw.text((domain_center_x, domain_y), domain_label, fill='black', font=self.domain_label_font, anchor='mm')
        
        # Add LLM model labels below domain labels
        for d, domain in enumerate(self.domains):
            for m, llm_model in enumerate(self.complete_llm_models):
                # Calculate position for model label
                model_x = method_label_width + (d * n_llm_models * cell_width) + (m * cell_width) + (cell_width // 2)
                # Position model labels in the lower portion of their section for more separation from domain labels
                model_y = title_height + model_label_height + (domain_label_height // 3)
                
                # Draw model label
                draw.text((model_x, model_y), llm_model, fill='black', font=self.llm_model_label_font, anchor='mm')
                
                # Add metric type labels (distance on left, performance on right)
                dist_x = method_label_width + (d * n_llm_models * cell_width) + (m * cell_width) + (img_width // 2)
                perf_x = method_label_width + (d * n_llm_models * cell_width) + (m * cell_width) + img_width + (img_width // 2)
                metric_y = title_height + model_label_height + domain_label_height + (img_height // 4)
                
                draw.text((dist_x, metric_y), "Distance", fill='black', font=self.method_label_font, anchor='mm')
                draw.text((perf_x, metric_y), "Performance", fill='black', font=self.method_label_font, anchor='mm')
        
        # Add method labels on the left and place images
        for r, method in enumerate(self.model_order):
            # Calculate position for method label
            method_y = title_height + model_label_height + domain_label_height + (r * img_height) + (img_height // 2)
            
            # Draw method label
            method_label = self.method_display_names.get(method, method)
            
            # Vertical text - rotate the text 90 degrees counterclockwise
            method_label_img = Image.new('RGBA', (img_height, method_label_width), (255, 255, 255, 0))
            method_label_draw = ImageDraw.Draw(method_label_img)
            method_label_draw.text((img_height // 2, method_label_width // 2), method_label, fill='black', font=self.label_font, anchor='mm')
            method_label_img = method_label_img.rotate(90, expand=True)
            
            # Paste the rotated text onto the collage
            # The vertical position should be aligned with the row's top edge
            vertical_paste_y = title_height + model_label_height + domain_label_height + (r * img_height)
            collage.paste(method_label_img, (0, vertical_paste_y), method_label_img)
            
            # Place images for this method
            for d, domain in enumerate(self.domains):
                for m, llm_model in enumerate(self.complete_llm_models):
                    # Calculate base position for this cell
                    base_x = method_label_width + (d * n_llm_models * cell_width) + (m * cell_width)
                    base_y = title_height + model_label_height + domain_label_height + (r * img_height)
                    
                    # Place distance metrics on the left
                    dist_img = self.images_by_llm_model[llm_model][domain][method].get("distance_metrics")
                    if dist_img:
                        collage.paste(dist_img, (base_x, base_y))
                    
                    # Place performance metrics on the right
                    perf_img = self.images_by_llm_model[llm_model][domain][method].get("performance_metrics")
                    if perf_img:
                        collage.paste(perf_img, (base_x + img_width, base_y))
        
        # Save the collage
        try:
            collage.save(self.output_path)
            print(f"Collage saved to {self.output_path}")
            return True
        except Exception as e:
            print(f"Error saving collage: {e}")
            return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Create a collage of metric plots')
    parser.add_argument('--input_folder', help='Path to folder containing metric plot images')
    parser.add_argument('--output', '-o', default='metric_collage.png',
                       help='Path to save the output collage (default: metric_collage.png)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create collage
    creator = MetricCollageCreator(args.input_folder, args.output)
    if creator.load_images():
        creator.create_collage()
    else:
        print("Failed to create collage")

if __name__ == "__main__":
    main() 