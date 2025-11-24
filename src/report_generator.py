"""
HTML Report Generator for Data Quality Analysis.

This module generates interactive HTML reports with visualizations
for data quality metrics and statistics.
"""

import sys
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jinja2 import Template

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import ensure_dir


class ReportGenerator:
    """Generate HTML reports for data quality analysis."""
    
    def __init__(self):
        """Initialize report generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_quality_report(
        self,
        df: pd.DataFrame,
        output_path: str,
        title: str = "Data Quality Report"
    ) -> None:
        """
        Generate comprehensive data quality report.
        
        Args:
            df: Dataframe to analyze
            output_path: Output HTML file path
            title: Report title
        """
        self.logger.info(f"Generating quality report for {len(df)} comments")
        
        # Calculate statistics
        stats = self._calculate_statistics(df)
        
        # Generate visualizations
        plots = self._generate_plots(df)
        
        # Generate HTML
        html = self._create_html_report(title, stats, plots)
        
        # Save report
        ensure_dir(os.path.dirname(output_path))
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Report saved to {output_path}")
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics."""
        stats = {
            'total_comments': len(df),
            'date_range': f"{df['published_at'].min()} to {df['published_at'].max()}" if 'published_at' in df.columns else 'N/A',
            'avg_length': df['cleaned_length'].mean() if 'cleaned_length' in df.columns else 0,
            'avg_words': df['word_count'].mean() if 'word_count' in df.columns else 0,
            'total_likes': df['like_count'].sum() if 'like_count' in df.columns else 0,
        }
        
        # Language statistics
        if 'is_english' in df.columns:
            stats['english_pct'] = 100 * df['is_english'].mean()
            stats['english_count'] = df['is_english'].sum()
        
        # Spam statistics
        if 'is_spam' in df.columns:
            stats['spam_pct'] = 100 * df['is_spam'].mean()
            stats['spam_count'] = df['is_spam'].sum()
        
        # Toxicity statistics
        if 'toxicity_level' in df.columns:
            stats['safe_pct'] = 100 * (df['toxicity_level'] == 'Safe').mean()
            stats['mild_toxic_pct'] = 100 * (df['toxicity_level'] == 'Mild Toxic').mean()
            stats['severe_toxic_pct'] = 100 * (df['toxicity_level'] == 'Severe Toxic').mean()
        
        # Quality statistics
        if 'is_high_quality' in df.columns:
            stats['high_quality_pct'] = 100 * df['is_high_quality'].mean()
            stats['high_quality_count'] = df['is_high_quality'].sum()
        
        return stats
    
    def _generate_plots(self, df: pd.DataFrame) -> Dict[str, str]:
        """Generate plotly visualizations."""
        plots = {}
        
        # Text length distribution
        if 'cleaned_length' in df.columns:
            fig = px.histogram(
                df,
                x='cleaned_length',
                nbins=50,
                title='Text Length Distribution',
                labels={'cleaned_length': 'Character Count'},
                color_discrete_sequence=['#636EFA']
            )
            plots['length_dist'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Word count distribution
        if 'word_count' in df.columns:
            fig = px.histogram(
                df,
                x='word_count',
                nbins=50,
                title='Word Count Distribution',
                labels={'word_count': 'Word Count'},
                color_discrete_sequence=['#EF553B']
            )
            plots['word_dist'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Language distribution
        if 'language' in df.columns:
            lang_counts = df['language'].value_counts().head(10)
            fig = px.bar(
                x=lang_counts.index,
                y=lang_counts.values,
                title='Top 10 Languages',
                labels={'x': 'Language', 'y': 'Count'},
                color_discrete_sequence=['#00CC96']
            )
            plots['language_dist'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Toxicity distribution
        if 'toxicity_level' in df.columns:
            tox_counts = df['toxicity_level'].value_counts()
            fig = px.pie(
                values=tox_counts.values,
                names=tox_counts.index,
                title='Toxicity Distribution',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            plots['toxicity_dist'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Spam score distribution
        if 'spam_score' in df.columns:
            fig = px.histogram(
                df,
                x='spam_score',
                nbins=30,
                title='Spam Score Distribution',
                labels={'spam_score': 'Spam Score'},
                color_discrete_sequence=['#AB63FA']
            )
            plots['spam_dist'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Comments over time
        if 'published_at' in df.columns:
            df_time = df.copy()
            df_time['published_at'] = pd.to_datetime(df_time['published_at'])
            df_time['date'] = df_time['published_at'].dt.date
            time_counts = df_time.groupby('date').size().reset_index(name='count')
            
            fig = px.line(
                time_counts,
                x='date',
                y='count',
                title='Comments Over Time',
                labels={'date': 'Date', 'count': 'Number of Comments'},
                color_discrete_sequence=['#FFA15A']
            )
            plots['time_series'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        return plots
    
    def _create_html_report(
        self,
        title: str,
        stats: Dict[str, Any],
        plots: Dict[str, str]
    ) -> str:
        """Create HTML report from template."""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #636EFA;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }
        .stat-card .value {
            font-size: 28px;
            font-weight: bold;
        }
        .plot-container {
            margin: 30px 0;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 8px;
        }
        .timestamp {
            text-align: right;
            color: #888;
            font-size: 12px;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        
        <h2>Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Comments</h3>
                <div class="value">{{ "{:,}".format(stats.total_comments) }}</div>
            </div>
            {% if stats.english_count is defined %}
            <div class="stat-card">
                <h3>English Comments</h3>
                <div class="value">{{ "{:,}".format(stats.english_count) }}</div>
                <div>{{ "%.1f"|format(stats.english_pct) }}%</div>
            </div>
            {% endif %}
            {% if stats.high_quality_count is defined %}
            <div class="stat-card">
                <h3>High Quality</h3>
                <div class="value">{{ "{:,}".format(stats.high_quality_count) }}</div>
                <div>{{ "%.1f"|format(stats.high_quality_pct) }}%</div>
            </div>
            {% endif %}
            <div class="stat-card">
                <h3>Average Length</h3>
                <div class="value">{{ "%.0f"|format(stats.avg_length) }}</div>
                <div>characters</div>
            </div>
            <div class="stat-card">
                <h3>Average Words</h3>
                <div class="value">{{ "%.1f"|format(stats.avg_words) }}</div>
                <div>words per comment</div>
            </div>
            {% if stats.spam_count is defined %}
            <div class="stat-card">
                <h3>Spam Detected</h3>
                <div class="value">{{ "{:,}".format(stats.spam_count) }}</div>
                <div>{{ "%.1f"|format(stats.spam_pct) }}%</div>
            </div>
            {% endif %}
        </div>
        
        <h2>Visualizations</h2>
        
        {% for plot_name, plot_html in plots.items() %}
        <div class="plot-container">
            {{ plot_html|safe }}
        </div>
        {% endfor %}
        
        <div class="timestamp">
            Generated on {{ timestamp }}
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        html = template.render(
            title=title,
            stats=stats,
            plots=plots,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return html


if __name__ == "__main__":
    import argparse
    from src.utils import load_config, setup_logging
    
    parser = argparse.ArgumentParser(description="Generate data quality report")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output HTML file')
    parser.add_argument('--title', default='Data Quality Report', help='Report title')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Generate report
    generator = ReportGenerator()
    generator.generate_quality_report(df, args.output, args.title)
    
    logger.info(f"Report generated: {args.output}")
