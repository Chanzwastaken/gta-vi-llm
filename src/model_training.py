"""
Model Training Script for Text Classification.

This script trains DistilBERT-based classifiers for sentiment, toxicity, and intent classification.
"""

import sys
import os
import logging
import argparse
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    AdamW,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_config, setup_logging, ensure_dir


class CommentDataset(Dataset):
    """PyTorch Dataset for comment classification."""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        """
        Initialize dataset.
        
        Args:
            texts: List of comment texts
            labels: List of label indices
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class TextClassifier:
    """Text classifier using DistilBERT."""
    
    def __init__(self, config: Dict, task: str, label_map: Dict[str, int]):
        """
        Initialize classifier.
        
        Args:
            config: Configuration dictionary
            task: Task name (sentiment, toxicity, intent)
            label_map: Mapping from label names to indices
        """
        self.config = config
        self.task = task
        self.label_map = label_map
        self.num_labels = len(label_map)
        self.logger = logging.getLogger(__name__)
        
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.info(f"Using device: {self.device}")
        
        # Model and tokenizer
        model_name = config['training']['model_name']
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=self.num_labels
        ).to(self.device)
        
        # Training parameters
        self.batch_size = config['training']['batch_size']
        self.learning_rate = config['training']['learning_rate']
        self.num_epochs = config['training']['num_epochs']
        self.max_length = config['training']['max_length']
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        text_column: str = 'text_clean',
        label_column: str = None
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Prepare data loaders.
        
        Args:
            df: Input dataframe
            text_column: Name of text column
            label_column: Name of label column
            
        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        if label_column is None:
            label_column = self.task
        
        self.logger.info(f"Preparing data for {self.task} classification...")
        
        # Filter out missing labels
        df = df[df[label_column].notna()].copy()
        
        # Convert labels to indices
        df['label_idx'] = df[label_column].map(self.label_map)
        
        # Remove any unmapped labels
        df = df[df['label_idx'].notna()].copy()
        
        self.logger.info(f"Total samples: {len(df)}")
        
        # Split data
        train_ratio = self.config['training']['train_ratio']
        val_ratio = self.config['training']['val_ratio']
        
        train_df, temp_df = train_test_split(df, train_size=train_ratio, random_state=42, stratify=df['label_idx'])
        val_df, test_df = train_test_split(temp_df, train_size=val_ratio/(1-train_ratio), random_state=42, stratify=temp_df['label_idx'])
        
        self.logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        # Create datasets
        train_dataset = CommentDataset(
            train_df[text_column].tolist(),
            train_df['label_idx'].astype(int).tolist(),
            self.tokenizer,
            self.max_length
        )
        
        val_dataset = CommentDataset(
            val_df[text_column].tolist(),
            val_df['label_idx'].astype(int).tolist(),
            self.tokenizer,
            self.max_length
        )
        
        test_dataset = CommentDataset(
            test_df[text_column].tolist(),
            test_df['label_idx'].astype(int).tolist(),
            self.tokenizer,
            self.max_length
        )
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size)
        
        # Compute class weights for imbalanced data
        if self.config['training']['use_class_weights']:
            class_weights = compute_class_weight(
                'balanced',
                classes=np.unique(train_df['label_idx']),
                y=train_df['label_idx']
            )
            self.class_weights = torch.tensor(class_weights, dtype=torch.float).to(self.device)
            self.logger.info(f"Class weights: {self.class_weights}")
        else:
            self.class_weights = None
        
        return train_loader, val_loader, test_loader
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """
        Train the model.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
        """
        self.logger.info(f"Starting training for {self.num_epochs} epochs...")
        
        # Optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate)
        
        total_steps = len(train_loader) * self.num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.config['training']['warmup_steps'],
            num_training_steps=total_steps
        )
        
        # Training loop
        best_val_f1 = 0
        
        for epoch in range(self.num_epochs):
            self.logger.info(f"\nEpoch {epoch + 1}/{self.num_epochs}")
            
            # Training
            self.model.train()
            train_loss = 0
            train_preds = []
            train_labels = []
            
            for batch in tqdm(train_loader, desc="Training"):
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                train_loss += loss.item()
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                preds = torch.argmax(outputs.logits, dim=1)
                train_preds.extend(preds.cpu().numpy())
                train_labels.extend(labels.cpu().numpy())
            
            # Calculate training metrics
            train_acc = accuracy_score(train_labels, train_preds)
            train_f1 = f1_score(train_labels, train_preds, average='weighted')
            avg_train_loss = train_loss / len(train_loader)
            
            # Validation
            val_loss, val_acc, val_f1 = self.evaluate(val_loader)
            
            self.logger.info(f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}, Train F1: {train_f1:.4f}")
            self.logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}")
            
            # Save best model
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                self.save_model(f"best_{self.task}_model")
                self.logger.info(f"Saved best model with F1: {best_val_f1:.4f}")
    
    def evaluate(self, data_loader: DataLoader) -> Tuple[float, float, float]:
        """
        Evaluate the model.
        
        Args:
            data_loader: Data loader
            
        Returns:
            Tuple of (loss, accuracy, f1_score)
        """
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs.loss.item()
                
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_loss = total_loss / len(data_loader)
        accuracy = accuracy_score(all_labels, all_preds)
        f1 = f1_score(all_labels, all_preds, average='weighted')
        
        return avg_loss, accuracy, f1
    
    def test(self, test_loader: DataLoader):
        """
        Test the model and print detailed metrics.
        
        Args:
            test_loader: Test data loader
        """
        self.logger.info("\nEvaluating on test set...")
        
        self.model.eval()
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(test_loader, desc="Testing"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # Calculate metrics
        accuracy = accuracy_score(all_labels, all_preds)
        f1 = f1_score(all_labels, all_preds, average='weighted')
        
        self.logger.info(f"\nTest Accuracy: {accuracy:.4f}")
        self.logger.info(f"Test F1 Score: {f1:.4f}")
        
        # Classification report
        label_names = list(self.label_map.keys())
        report = classification_report(all_labels, all_preds, target_names=label_names)
        self.logger.info(f"\nClassification Report:\n{report}")
        
        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        self.logger.info(f"\nConfusion Matrix:\n{cm}")
        
        return accuracy, f1, report, cm
    
    def save_model(self, model_name: str):
        """Save model and tokenizer."""
        output_dir = os.path.join(self.config['paths']['models'], model_name)
        ensure_dir(output_dir)
        
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        # Save label map
        import json
        with open(os.path.join(output_dir, 'label_map.json'), 'w') as f:
            json.dump(self.label_map, f)
    
    def load_model(self, model_path: str):
        """Load saved model."""
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Train text classification model")
    parser.add_argument('--config', default='config.yaml', help='Config file')
    parser.add_argument('--input', required=True, help='Labeled data CSV')
    parser.add_argument('--task', required=True, choices=['sentiment', 'toxicity', 'intent'], help='Classification task')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Setup logging
    logger = setup_logging(log_level='INFO', log_file=f'logs/training_{args.task}.log')
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Define label maps
    label_maps = {
        'sentiment': {'Positive': 0, 'Neutral': 1, 'Negative': 2, 'Sarcasm': 3},
        'toxicity': {'Safe': 0, 'Mild Toxic': 1, 'Severe Toxic': 2},
        'intent': {'Reaction': 0, 'Speculation': 1, 'Criticism': 2, 'Complaint': 3, 'Meme/Joke': 4, 'Question': 5}
    }
    
    label_map = label_maps[args.task]
    
    # Initialize classifier
    classifier = TextClassifier(config, args.task, label_map)
    
    # Prepare data
    train_loader, val_loader, test_loader = classifier.prepare_data(df)
    
    # Train
    classifier.train(train_loader, val_loader)
    
    # Test
    classifier.test(test_loader)
    
    logger.info("Training complete!")


if __name__ == "__main__":
    main()
