"""
Model Inference Utilities.

This module provides utilities for loading trained models and making predictions.
"""

import os
import json
from typing import List, Dict, Tuple
import torch
import pandas as pd
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification


class CommentClassifier:
    """Inference wrapper for trained comment classification models."""
    
    def __init__(self, model_path: str):
        """
        Initialize classifier from saved model.
        
        Args:
            model_path: Path to saved model directory
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model and tokenizer
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # Load label map
        label_map_path = os.path.join(model_path, 'label_map.json')
        with open(label_map_path, 'r') as f:
            self.label_map = json.load(f)
        
        # Create reverse map (index to label)
        self.idx_to_label = {v: k for k, v in self.label_map.items()}
    
    def predict(self, text: str, return_probabilities: bool = False) -> Dict:
        """
        Predict label for a single text.
        
        Args:
            text: Input text
            return_probabilities: Whether to return class probabilities
            
        Returns:
            Dictionary with prediction and optionally probabilities
        """
        # Tokenize
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=1)
            predicted_idx = torch.argmax(probabilities, dim=1).item()
        
        result = {
            'text': text,
            'predicted_label': self.idx_to_label[predicted_idx],
            'confidence': probabilities[0][predicted_idx].item()
        }
        
        if return_probabilities:
            result['probabilities'] = {
                self.idx_to_label[i]: prob.item()
                for i, prob in enumerate(probabilities[0])
            }
        
        return result
    
    def predict_batch(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> List[Dict]:
        """
        Predict labels for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            encodings = self.tokenizer(
                batch_texts,
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            
            input_ids = encodings['input_ids'].to(self.device)
            attention_mask = encodings['attention_mask'].to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
                predicted_indices = torch.argmax(probabilities, dim=1)
            
            # Process results
            for j, text in enumerate(batch_texts):
                pred_idx = predicted_indices[j].item()
                results.append({
                    'text': text,
                    'predicted_label': self.idx_to_label[pred_idx],
                    'confidence': probabilities[j][pred_idx].item()
                })
        
        return results
    
    def predict_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str = 'text_clean',
        output_column: str = 'predicted_label'
    ) -> pd.DataFrame:
        """
        Add predictions to a dataframe.
        
        Args:
            df: Input dataframe
            text_column: Name of text column
            output_column: Name for output column
            
        Returns:
            Dataframe with predictions added
        """
        texts = df[text_column].tolist()
        predictions = self.predict_batch(texts)
        
        df[output_column] = [p['predicted_label'] for p in predictions]
        df[f'{output_column}_confidence'] = [p['confidence'] for p in predictions]
        
        return df


def load_all_models(models_dir: str = 'models/saved_model') -> Dict[str, CommentClassifier]:
    """
    Load all trained models.
    
    Args:
        models_dir: Directory containing saved models
        
    Returns:
        Dictionary mapping task names to classifiers
    """
    classifiers = {}
    
    for task in ['sentiment', 'toxicity', 'intent']:
        model_path = os.path.join(models_dir, f'best_{task}_model')
        if os.path.exists(model_path):
            classifiers[task] = CommentClassifier(model_path)
    
    return classifiers


def classify_comment(
    text: str,
    classifiers: Dict[str, CommentClassifier]
) -> Dict[str, Dict]:
    """
    Classify a comment with all available models.
    
    Args:
        text: Comment text
        classifiers: Dictionary of classifiers
        
    Returns:
        Dictionary with all predictions
    """
    results = {}
    
    for task, classifier in classifiers.items():
        results[task] = classifier.predict(text, return_probabilities=True)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inference on comments")
    parser.add_argument('--model', required=True, help='Path to model directory')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--text-column', default='text_clean', help='Text column name')
    
    args = parser.parse_args()
    
    # Load classifier
    print(f"Loading model from {args.model}...")
    classifier = CommentClassifier(args.model)
    
    # Load data
    print(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    
    # Predict
    print(f"Running inference on {len(df)} comments...")
    df = classifier.predict_dataframe(df, text_column=args.text_column)
    
    # Save
    df.to_csv(args.output, index=False)
    print(f"Saved predictions to {args.output}")
    
    # Print summary
    print("\nPrediction Summary:")
    print(df['predicted_label'].value_counts())
