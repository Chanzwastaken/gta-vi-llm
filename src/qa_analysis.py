"""
Quality Assurance Analysis for Labeled Data.

This module provides comprehensive QA checks including label distribution,
consistency analysis, inter-annotator agreement, and quality metrics.
"""

import sys
import os
import logging
import argparse
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_config, setup_logging, ensure_dir
from src.report_generator import ReportGenerator


class QAAnalyzer:
    """Analyze quality of labeled data."""
    
    def __init__(self):
        """Initialize QA analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_label_distribution(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Analyze distribution of labels across categories.
        
        Args:
            df: Labeled dataframe
            
        Returns:
            Dictionary of label distributions
        """
        self.logger.info("Analyzing label distributions...")
        
        distributions = {}
        label_columns = ['sentiment', 'toxicity', 'emotion', 'relevance', 'intent']
        
        for col in label_columns:
            if col in df.columns:
                distributions[col] = df[col].value_counts()
                
                # Log distribution
                self.logger.info(f"\n{col.upper()} Distribution:")
                for label, count in distributions[col].items():
                    pct = 100 * count / len(df)
                    self.logger.info(f"  {label}: {count} ({pct:.1f}%)")
        
        return distributions
    
    def detect_inconsistencies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect inconsistent labels for identical text.
        
        Args:
            df: Labeled dataframe
            
        Returns:
            Dataframe of inconsistent labels
        """
        self.logger.info("Detecting inconsistencies...")
        
        # Merge with original text
        if 'text_clean' not in df.columns:
            self.logger.warning("text_clean column not found")
            return pd.DataFrame()
        
        # Group by text and check for different labels
        inconsistencies = []
        
        text_groups = df.groupby('text_clean')
        
        for text, group in text_groups:
            if len(group) > 1:
                # Check each label category
                for col in ['sentiment', 'toxicity', 'emotion', 'relevance', 'intent']:
                    if col in group.columns:
                        unique_labels = group[col].nunique()
                        if unique_labels > 1:
                            inconsistencies.append({
                                'text': text,
                                'category': col,
                                'labels': group[col].tolist(),
                                'annotators': group['annotator_id'].tolist() if 'annotator_id' in group.columns else [],
                                'count': len(group)
                            })
        
        inconsistency_df = pd.DataFrame(inconsistencies)
        
        if len(inconsistency_df) > 0:
            self.logger.warning(f"Found {len(inconsistency_df)} inconsistencies")
        else:
            self.logger.info("No inconsistencies found")
        
        return inconsistency_df
    
    def calculate_inter_annotator_agreement(
        self,
        df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate Cohen's Kappa for inter-annotator agreement.
        
        Args:
            df: Labeled dataframe with multiple annotators
            
        Returns:
            Dictionary of kappa scores per category
        """
        self.logger.info("Calculating inter-annotator agreement...")
        
        if 'annotator_id' not in df.columns:
            self.logger.warning("annotator_id column not found")
            return {}
        
        # Get comments labeled by multiple annotators
        comment_counts = df.groupby('comment_id').size()
        multi_labeled = comment_counts[comment_counts > 1].index
        
        if len(multi_labeled) == 0:
            self.logger.warning("No comments labeled by multiple annotators")
            return {}
        
        kappa_scores = {}
        
        for col in ['sentiment', 'toxicity', 'emotion', 'relevance', 'intent']:
            if col not in df.columns:
                continue
            
            # Get pairs of annotations for the same comment
            pairs = []
            
            for comment_id in multi_labeled:
                group = df[df['comment_id'] == comment_id]
                labels = group[col].tolist()
                
                # Create all pairs
                for i in range(len(labels)):
                    for j in range(i + 1, len(labels)):
                        pairs.append((labels[i], labels[j]))
            
            if len(pairs) > 0:
                labels1 = [p[0] for p in pairs]
                labels2 = [p[1] for p in pairs]
                
                try:
                    kappa = cohen_kappa_score(labels1, labels2)
                    kappa_scores[col] = kappa
                    
                    # Interpret kappa
                    if kappa < 0:
                        interpretation = "Poor (worse than random)"
                    elif kappa < 0.2:
                        interpretation = "Slight"
                    elif kappa < 0.4:
                        interpretation = "Fair"
                    elif kappa < 0.6:
                        interpretation = "Moderate"
                    elif kappa < 0.8:
                        interpretation = "Substantial"
                    else:
                        interpretation = "Almost Perfect"
                    
                    self.logger.info(f"{col}: κ = {kappa:.3f} ({interpretation})")
                
                except Exception as e:
                    self.logger.warning(f"Could not calculate kappa for {col}: {e}")
        
        return kappa_scores
    
    def analyze_annotator_bias(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze potential annotator bias.
        
        Args:
            df: Labeled dataframe
            
        Returns:
            Dataframe of annotator statistics
        """
        self.logger.info("Analyzing annotator bias...")
        
        if 'annotator_id' not in df.columns:
            self.logger.warning("annotator_id column not found")
            return pd.DataFrame()
        
        annotator_stats = []
        
        for annotator in df['annotator_id'].unique():
            annotator_df = df[df['annotator_id'] == annotator]
            
            stats = {
                'annotator_id': annotator,
                'total_labels': len(annotator_df)
            }
            
            # Calculate label distributions
            for col in ['sentiment', 'toxicity', 'emotion', 'relevance', 'intent']:
                if col in df.columns:
                    dist = annotator_df[col].value_counts(normalize=True)
                    for label, pct in dist.items():
                        stats[f'{col}_{label}'] = pct
            
            annotator_stats.append(stats)
        
        return pd.DataFrame(annotator_stats)
    
    def check_label_quality(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Perform comprehensive quality checks.
        
        Args:
            df: Labeled dataframe
            
        Returns:
            Dictionary of quality metrics
        """
        self.logger.info("Performing quality checks...")
        
        quality_metrics = {
            'total_labeled': len(df),
            'unique_annotators': df['annotator_id'].nunique() if 'annotator_id' in df.columns else 0,
        }
        
        # Check for missing labels
        label_columns = ['sentiment', 'toxicity', 'emotion', 'relevance', 'intent']
        for col in label_columns:
            if col in df.columns:
                missing = df[col].isna().sum()
                quality_metrics[f'{col}_missing'] = missing
        
        # Check for suspicious patterns
        # E.g., all labels the same
        for col in label_columns:
            if col in df.columns:
                most_common = df[col].value_counts().iloc[0] if len(df[col].value_counts()) > 0 else 0
                quality_metrics[f'{col}_most_common_pct'] = 100 * most_common / len(df)
        
        return quality_metrics
    
    def generate_qa_report(
        self,
        df: pd.DataFrame,
        output_path: str
    ):
        """
        Generate comprehensive QA report.
        
        Args:
            df: Labeled dataframe
            output_path: Output HTML file path
        """
        self.logger.info("Generating QA report...")
        
        # Perform all analyses
        distributions = self.analyze_label_distribution(df)
        inconsistencies = self.detect_inconsistencies(df)
        kappa_scores = self.calculate_inter_annotator_agreement(df)
        annotator_stats = self.analyze_annotator_bias(df)
        quality_metrics = self.check_label_quality(df)
        
        # Create visualizations
        self._create_visualizations(df, distributions, output_path)
        
        # Generate HTML report
        self._create_html_report(
            df,
            distributions,
            inconsistencies,
            kappa_scores,
            annotator_stats,
            quality_metrics,
            output_path
        )
        
        self.logger.info(f"QA report saved to {output_path}")
    
    def _create_visualizations(
        self,
        df: pd.DataFrame,
        distributions: Dict[str, pd.Series],
        output_path: str
    ):
        """Create and save visualizations."""
        output_dir = os.path.dirname(output_path)
        ensure_dir(output_dir)
        
        # Set style
        sns.set_style("whitegrid")
        
        # Create distribution plots
        for category, dist in distributions.items():
            fig, ax = plt.subplots(figsize=(10, 6))
            dist.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title(f'{category.title()} Distribution')
            ax.set_xlabel(category.title())
            ax.set_ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plot_path = os.path.join(output_dir, f'{category}_distribution.png')
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
    
    def _create_html_report(
        self,
        df: pd.DataFrame,
        distributions: Dict[str, pd.Series],
        inconsistencies: pd.DataFrame,
        kappa_scores: Dict[str, float],
        annotator_stats: pd.DataFrame,
        quality_metrics: Dict[str, any],
        output_path: str
    ):
        """Create HTML QA report."""
        from jinja2 import Template
        from datetime import datetime
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>QA Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        .metric { display: inline-block; margin: 10px; padding: 20px; background: #e3f2fd; border-radius: 8px; }
        .warning { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }
        .success { background-color: #d4edda; padding: 10px; border-left: 4px solid #28a745; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Quality Assurance Report</h1>
        <p>Generated: {{ timestamp }}</p>
        
        <h2>Summary Metrics</h2>
        <div class="metric">
            <strong>Total Labeled:</strong> {{ metrics.total_labeled }}
        </div>
        <div class="metric">
            <strong>Unique Annotators:</strong> {{ metrics.unique_annotators }}
        </div>
        
        <h2>Label Distributions</h2>
        {% for category, dist in distributions.items() %}
        <h3>{{ category.title() }}</h3>
        <table>
            <tr><th>Label</th><th>Count</th><th>Percentage</th></tr>
            {% for label, count in dist.items() %}
            <tr>
                <td>{{ label }}</td>
                <td>{{ count }}</td>
                <td>{{ "%.1f"|format(100 * count / metrics.total_labeled) }}%</td>
            </tr>
            {% endfor %}
        </table>
        {% endfor %}
        
        {% if kappa_scores %}
        <h2>Inter-Annotator Agreement (Cohen's Kappa)</h2>
        <table>
            <tr><th>Category</th><th>Kappa Score</th><th>Interpretation</th></tr>
            {% for category, kappa in kappa_scores.items() %}
            <tr>
                <td>{{ category.title() }}</td>
                <td>{{ "%.3f"|format(kappa) }}</td>
                <td>
                    {% if kappa >= 0.8 %}Almost Perfect
                    {% elif kappa >= 0.6 %}Substantial
                    {% elif kappa >= 0.4 %}Moderate
                    {% elif kappa >= 0.2 %}Fair
                    {% else %}Slight{% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if inconsistencies|length > 0 %}
        <h2>Inconsistencies Found</h2>
        <div class="warning">
            <strong>Warning:</strong> {{ inconsistencies|length }} inconsistencies detected
        </div>
        <table>
            <tr><th>Text</th><th>Category</th><th>Conflicting Labels</th></tr>
            {% for idx, row in inconsistencies.iterrows() %}
            <tr>
                <td>{{ row.text[:100] }}...</td>
                <td>{{ row.category }}</td>
                <td>{{ row.labels }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <div class="success">
            <strong>Success:</strong> No inconsistencies detected
        </div>
        {% endif %}
        
        <p style="text-align: right; color: #888; margin-top: 30px;">
            Generated on {{ timestamp }}
        </p>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        html = template.render(
            distributions=distributions,
            inconsistencies=inconsistencies,
            kappa_scores=kappa_scores,
            annotator_stats=annotator_stats,
            metrics=quality_metrics,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Perform QA analysis on labeled data"
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input labeled CSV file'
    )
    parser.add_argument(
        '--output',
        default='data/qa_report.html',
        help='Output QA report HTML file'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Load data
    logger.info(f"Loading labeled data from {args.input}")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} labeled comments")
    
    # Perform QA analysis
    analyzer = QAAnalyzer()
    analyzer.generate_qa_report(df, args.output)
    
    logger.info("QA analysis complete")


if __name__ == "__main__":
    main()
