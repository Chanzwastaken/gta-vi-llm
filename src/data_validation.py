"""
Data Validation Module for YouTube Comments.

This module provides validation checks including language detection,
bot/spam detection, and toxicity scoring.
"""

import sys
import os
import logging
import argparse
from typing import Dict, Any
import pandas as pd
import numpy as np
from langdetect import detect, DetectorFactory, LangDetectException
from detoxify import Detoxify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_config, setup_logging, ensure_dir, ProgressTracker

# Set seed for consistent language detection
DetectorFactory.seed = 0


class LanguageDetector:
    """Detect language of text."""
    
    def __init__(self, target_language: str = 'en', confidence_threshold: float = 0.8):
        """
        Initialize language detector.
        
        Args:
            target_language: Target language code (e.g., 'en')
            confidence_threshold: Minimum confidence for language detection
        """
        self.target_language = target_language
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language of text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with language code and confidence
        """
        if not text or len(text.strip()) < 3:
            return {
                'language': 'unknown',
                'is_target_language': False,
                'confidence': 0.0
            }
        
        try:
            lang = detect(text)
            is_target = lang == self.target_language
            
            return {
                'language': lang,
                'is_target_language': is_target,
                'confidence': 1.0  # langdetect doesn't provide confidence
            }
        
        except LangDetectException:
            return {
                'language': 'unknown',
                'is_target_language': False,
                'confidence': 0.0
            }


class SpamDetector:
    """Detect spam and bot-like comments."""
    
    def __init__(self):
        """Initialize spam detector."""
        self.logger = logging.getLogger(__name__)
        
        # Spam indicators
        self.spam_keywords = [
            'subscribe', 'check out my channel', 'click here', 'free money',
            'make money', 'work from home', 'buy now', 'limited offer',
            'congratulations', 'you won', 'claim your prize', 'gift card'
        ]
        
        # Repetitive pattern threshold
        self.repetition_threshold = 0.5
    
    def detect_spam(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if comment is spam or bot-generated.
        
        Args:
            text: Comment text
            metadata: Additional metadata (like_count, etc.)
            
        Returns:
            Dictionary with spam detection results
        """
        flags = []
        score = 0.0
        
        if not text:
            return {'is_spam': False, 'spam_score': 0.0, 'flags': []}
        
        text_lower = text.lower()
        
        # Check for spam keywords
        keyword_count = sum(1 for keyword in self.spam_keywords if keyword in text_lower)
        if keyword_count > 0:
            flags.append('spam_keywords')
            score += 0.3 * keyword_count
        
        # Check for excessive capitalization
        if metadata.get('uppercase_ratio', 0) > 0.7:
            flags.append('excessive_caps')
            score += 0.2
        
        # Check for repetitive characters
        if self._is_repetitive(text):
            flags.append('repetitive_pattern')
            score += 0.3
        
        # Check for excessive URLs
        if metadata.get('urls_found', 0) > 2:
            flags.append('excessive_urls')
            score += 0.4
        
        # Very short comments with URLs are likely spam
        if metadata.get('urls_found', 0) > 0 and metadata.get('word_count', 0) < 5:
            flags.append('short_with_url')
            score += 0.3
        
        is_spam = score > 0.5
        
        return {
            'is_spam': is_spam,
            'spam_score': min(score, 1.0),
            'spam_flags': flags
        }
    
    def _is_repetitive(self, text: str) -> bool:
        """
        Check if text has repetitive patterns.
        
        Args:
            text: Input text
            
        Returns:
            True if text is repetitive
        """
        if len(text) < 10:
            return False
        
        # Check for repeated characters
        char_counts = {}
        for char in text:
            if char.isalnum():
                char_counts[char] = char_counts.get(char, 0) + 1
        
        if char_counts:
            max_count = max(char_counts.values())
            if max_count / len(text) > self.repetition_threshold:
                return True
        
        # Check for repeated words
        words = text.lower().split()
        if len(words) > 3:
            unique_words = len(set(words))
            if unique_words / len(words) < 0.5:
                return True
        
        return False


class ToxicityDetector:
    """Detect toxic and harmful content."""
    
    def __init__(self, mild_threshold: float = 0.5, severe_threshold: float = 0.8):
        """
        Initialize toxicity detector.
        
        Args:
            mild_threshold: Threshold for mild toxicity
            severe_threshold: Threshold for severe toxicity
        """
        self.mild_threshold = mild_threshold
        self.severe_threshold = severe_threshold
        self.logger = logging.getLogger(__name__)
        
        # Load Detoxify model
        self.logger.info("Loading toxicity detection model...")
        self.model = Detoxify('original')
        self.logger.info("Toxicity model loaded")
    
    def detect_toxicity(self, text: str) -> Dict[str, Any]:
        """
        Detect toxicity in text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with toxicity scores and classification
        """
        if not text or len(text.strip()) < 3:
            return {
                'toxicity_score': 0.0,
                'toxicity_level': 'Safe',
                'categories': {}
            }
        
        try:
            # Get predictions
            results = self.model.predict(text)
            
            # Get maximum toxicity score
            toxicity_score = results['toxicity']
            
            # Classify toxicity level
            if toxicity_score >= self.severe_threshold:
                toxicity_level = 'Severe Toxic'
            elif toxicity_score >= self.mild_threshold:
                toxicity_level = 'Mild Toxic'
            else:
                toxicity_level = 'Safe'
            
            return {
                'toxicity_score': float(toxicity_score),
                'toxicity_level': toxicity_level,
                'categories': {
                    'obscene': float(results.get('obscene', 0)),
                    'threat': float(results.get('threat', 0)),
                    'insult': float(results.get('insult', 0)),
                    'identity_hate': float(results.get('identity_hate', 0)),
                    'severe_toxic': float(results.get('severe_toxic', 0))
                }
            }
        
        except Exception as e:
            self.logger.warning(f"Toxicity detection failed: {e}")
            return {
                'toxicity_score': 0.0,
                'toxicity_level': 'Unknown',
                'categories': {}
            }


class DataValidator:
    """Validate and flag comment data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data validator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize detectors
        lang_config = config.get('language', {})
        self.language_detector = LanguageDetector(
            target_language=lang_config.get('target_language', 'en'),
            confidence_threshold=lang_config.get('confidence_threshold', 0.8)
        )
        
        self.spam_detector = SpamDetector()
        
        tox_config = config.get('toxicity', {})
        self.toxicity_detector = ToxicityDetector(
            mild_threshold=tox_config.get('threshold_mild', 0.5),
            severe_threshold=tox_config.get('threshold_severe', 0.8)
        )
    
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate entire dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with validation flags
        """
        self.logger.info(f"Starting validation for {len(df)} comments")
        
        df_validated = df.copy()
        
        # Language detection
        self.logger.info("Detecting languages...")
        with ProgressTracker(len(df), "Language detection") as pbar:
            lang_results = []
            for text in df_validated['text_clean']:
                lang_results.append(self.language_detector.detect_language(text))
                pbar.update(1)
        
        df_validated['language'] = [r['language'] for r in lang_results]
        df_validated['is_english'] = [r['is_target_language'] for r in lang_results]
        
        # Spam detection
        self.logger.info("Detecting spam...")
        with ProgressTracker(len(df), "Spam detection") as pbar:
            spam_results = []
            for idx, row in df_validated.iterrows():
                metadata = {
                    'uppercase_ratio': row.get('uppercase_ratio', 0),
                    'urls_found': row.get('urls_found', 0),
                    'word_count': row.get('word_count', 0)
                }
                spam_results.append(
                    self.spam_detector.detect_spam(row['text_clean'], metadata)
                )
                pbar.update(1)
        
        df_validated['is_spam'] = [r['is_spam'] for r in spam_results]
        df_validated['spam_score'] = [r['spam_score'] for r in spam_results]
        
        # Toxicity detection (batch processing for efficiency)
        self.logger.info("Detecting toxicity...")
        with ProgressTracker(len(df), "Toxicity detection") as pbar:
            tox_results = []
            for text in df_validated['text_clean']:
                tox_results.append(self.toxicity_detector.detect_toxicity(text))
                pbar.update(1)
        
        df_validated['toxicity_score'] = [r['toxicity_score'] for r in tox_results]
        df_validated['toxicity_level'] = [r['toxicity_level'] for r in tox_results]
        
        # Overall quality flag
        df_validated['is_high_quality'] = (
            df_validated['is_english'] &
            ~df_validated['is_spam'] &
            (df_validated['toxicity_level'] == 'Safe')
        )
        
        self.logger.info(f"Validation complete")
        self.logger.info(f"High quality comments: {df_validated['is_high_quality'].sum()}")
        
        return df_validated
    
    def save_validated_data(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save validated dataframe.
        
        Args:
            df: Validated dataframe
            output_path: Output file path
        """
        ensure_dir(os.path.dirname(output_path))
        df.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"Saved validated data to {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Validate YouTube comments data"
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
        help='Output CSV file path (defaults to input with _validated suffix)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_config = config.get('logging', {})
    logger = setup_logging(
        log_level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/data_validation.log')
    )
    
    # Get file paths
    input_path = args.input or config['paths']['clean_data']
    if args.output:
        output_path = args.output
    else:
        output_path = input_path.replace('.csv', '_validated.csv')
    
    logger.info(f"Loading data from {input_path}")
    
    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} comments")
        
        # Validate data
        validator = DataValidator(config)
        df_validated = validator.validate_dataframe(df)
        
        # Save validated data
        validator.save_validated_data(df_validated, output_path)
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total comments: {len(df_validated)}")
        logger.info(f"English comments: {df_validated['is_english'].sum()} ({100*df_validated['is_english'].mean():.1f}%)")
        logger.info(f"Spam comments: {df_validated['is_spam'].sum()} ({100*df_validated['is_spam'].mean():.1f}%)")
        logger.info(f"Toxic comments: {(df_validated['toxicity_level'] != 'Safe').sum()} ({100*(df_validated['toxicity_level'] != 'Safe').mean():.1f}%)")
        logger.info(f"High quality: {df_validated['is_high_quality'].sum()} ({100*df_validated['is_high_quality'].mean():.1f}%)")
        logger.info(f"Output file: {output_path}")
        logger.info("="*50)
    
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
