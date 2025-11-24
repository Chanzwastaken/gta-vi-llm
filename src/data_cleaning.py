"""
Data Cleaning Module for YouTube Comments.

This module provides functions to clean and normalize text data,
including HTML removal, emoji handling, URL extraction, and text normalization.
"""

import re
import sys
import os
import logging
import argparse
from typing import List, Tuple, Optional
import pandas as pd
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_config, setup_logging, ensure_dir


class TextCleaner:
    """Clean and normalize text data."""
    
    def __init__(self, config: dict):
        """
        Initialize text cleaner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config['cleaning']
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        self.whitespace_pattern = re.compile(r'\s+')
    
    def remove_html(self, text: str) -> str:
        """
        Remove HTML tags from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without HTML tags
        """
        if not self.config['remove_html']:
            return text
        
        soup = BeautifulSoup(text, 'lxml')
        return soup.get_text()
    
    def remove_urls(self, text: str) -> Tuple[str, List[str]]:
        """
        Remove URLs from text and extract them.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (cleaned text, list of extracted URLs)
        """
        if not self.config['remove_urls']:
            return text, []
        
        urls = self.url_pattern.findall(text)
        cleaned = self.url_pattern.sub('', text)
        return cleaned, urls
    
    def remove_emojis(self, text: str) -> str:
        """
        Remove emojis from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without emojis
        """
        if not self.config['remove_emojis']:
            return text
        
        return self.emoji_pattern.sub('', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace (collapse multiple spaces, trim).
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        if not self.config['normalize_whitespace']:
            return text
        
        # Replace multiple whitespace with single space
        text = self.whitespace_pattern.sub(' ', text)
        # Strip leading/trailing whitespace
        return text.strip()
    
    def validate_length(self, text: str) -> bool:
        """
        Check if text length is within acceptable range.
        
        Args:
            text: Input text
            
        Returns:
            True if length is valid, False otherwise
        """
        length = len(text)
        return self.config['min_length'] <= length <= self.config['max_length']
    
    def clean_text(self, text: str) -> Tuple[str, dict]:
        """
        Apply all cleaning steps to text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (cleaned text, metadata dictionary)
        """
        if pd.isna(text) or not isinstance(text, str):
            return "", {"valid": False, "reason": "empty_or_invalid"}
        
        metadata = {
            "original_length": len(text),
            "urls_found": [],
            "valid": True,
            "reason": ""
        }
        
        # Remove HTML
        text = self.remove_html(text)
        
        # Remove URLs
        text, urls = self.remove_urls(text)
        metadata["urls_found"] = urls
        
        # Remove emojis
        text = self.remove_emojis(text)
        
        # Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # Validate length
        if not self.validate_length(text):
            metadata["valid"] = False
            metadata["reason"] = "invalid_length"
        
        metadata["cleaned_length"] = len(text)
        
        return text, metadata


class DataCleaner:
    """Clean and preprocess comment dataset."""
    
    def __init__(self, config: dict):
        """
        Initialize data cleaner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.text_cleaner = TextCleaner(config)
        self.logger = logging.getLogger(__name__)
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean entire dataframe of comments.
        
        Args:
            df: Input dataframe
            
        Returns:
            Cleaned dataframe
        """
        self.logger.info(f"Starting cleaning process for {len(df)} comments")
        
        # Create a copy
        df_clean = df.copy()
        
        # Clean text
        self.logger.info("Cleaning text...")
        results = df_clean['text'].apply(self.text_cleaner.clean_text)
        
        df_clean['text_clean'] = results.apply(lambda x: x[0])
        df_clean['cleaning_metadata'] = results.apply(lambda x: x[1])
        
        # Extract metadata fields
        df_clean['original_length'] = df_clean['cleaning_metadata'].apply(
            lambda x: x.get('original_length', 0)
        )
        df_clean['cleaned_length'] = df_clean['cleaning_metadata'].apply(
            lambda x: x.get('cleaned_length', 0)
        )
        df_clean['urls_found'] = df_clean['cleaning_metadata'].apply(
            lambda x: len(x.get('urls_found', []))
        )
        df_clean['is_valid_length'] = df_clean['cleaning_metadata'].apply(
            lambda x: x.get('valid', False)
        )
        
        # Remove invalid comments
        initial_count = len(df_clean)
        df_clean = df_clean[df_clean['is_valid_length']].copy()
        removed_count = initial_count - len(df_clean)
        self.logger.info(f"Removed {removed_count} comments due to invalid length")
        
        # Remove duplicates
        self.logger.info("Removing duplicates...")
        df_clean = self.remove_duplicates(df_clean)
        
        # Drop temporary columns
        df_clean = df_clean.drop(columns=['cleaning_metadata'])
        
        self.logger.info(f"Cleaning complete: {len(df_clean)} comments remaining")
        
        return df_clean
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate comments.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe without duplicates
        """
        initial_count = len(df)
        
        # Remove exact duplicates based on comment_id
        df = df.drop_duplicates(subset=['comment_id'], keep='first')
        
        # Remove duplicates based on cleaned text (keep the one with more likes)
        df = df.sort_values('like_count', ascending=False)
        df = df.drop_duplicates(subset=['text_clean'], keep='first')
        
        removed_count = initial_count - len(df)
        self.logger.info(f"Removed {removed_count} duplicate comments")
        
        return df
    
    def add_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add text-based features to dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with additional features
        """
        self.logger.info("Adding text features...")
        
        df['word_count'] = df['text_clean'].str.split().str.len()
        df['char_count'] = df['text_clean'].str.len()
        df['avg_word_length'] = df['char_count'] / df['word_count'].replace(0, 1)
        df['uppercase_ratio'] = df['text_clean'].apply(
            lambda x: sum(1 for c in x if c.isupper()) / len(x) if len(x) > 0 else 0
        )
        df['has_question'] = df['text_clean'].str.contains('?', regex=False)
        df['has_exclamation'] = df['text_clean'].str.contains('!', regex=False)
        df['sentence_count'] = df['text_clean'].apply(
            lambda x: len(re.split(r'[.!?]+', x))
        )
        
        return df
    
    def save_cleaned_data(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save cleaned dataframe to CSV.
        
        Args:
            df: Cleaned dataframe
            output_path: Output file path
        """
        ensure_dir(os.path.dirname(output_path))
        df.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"Saved cleaned data to {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Clean YouTube comments data"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--input',
        default=None,
        help='Input CSV file path (overrides config)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file path (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_config = config.get('logging', {})
    logger = setup_logging(
        log_level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/data_cleaning.log')
    )
    
    # Get file paths
    input_path = args.input or config['paths']['raw_data']
    output_path = args.output or config['paths']['clean_data']
    
    logger.info(f"Loading data from {input_path}")
    
    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} comments")
        
        # Clean data
        cleaner = DataCleaner(config)
        df_clean = cleaner.clean_dataframe(df)
        
        # Add features
        df_clean = cleaner.add_text_features(df_clean)
        
        # Save cleaned data
        cleaner.save_cleaned_data(df_clean, output_path)
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("CLEANING SUMMARY")
        logger.info("="*50)
        logger.info(f"Input comments: {len(df)}")
        logger.info(f"Output comments: {len(df_clean)}")
        logger.info(f"Removed: {len(df) - len(df_clean)} ({100*(len(df)-len(df_clean))/len(df):.1f}%)")
        logger.info(f"Average length: {df_clean['cleaned_length'].mean():.1f} characters")
        logger.info(f"Average words: {df_clean['word_count'].mean():.1f} words")
        logger.info(f"Output file: {output_path}")
        logger.info("="*50)
    
    except Exception as e:
        logger.error(f"Cleaning failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
