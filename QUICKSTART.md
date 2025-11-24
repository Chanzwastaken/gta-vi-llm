# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup

```bash
# Clone repository
git clone https://github.com/[username]/gta-vi-llm-dataset.git
cd gta-vi-llm-dataset

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your YouTube API key
```

### 2. Collect Data (Test Mode)

```bash
python src/data_collection.py --test-mode
```

This collects 100 comments for testing.

### 3. Clean Data

```bash
python src/data_cleaning.py
```

### 4. Validate Data

```bash
python src/data_validation.py
```

### 5. Generate Quality Report

```bash
python src/report_generator.py \
  --input data/clean_comments_validated.csv \
  --output data/data_quality_report.html
```

Open `data/data_quality_report.html` in your browser!

### 6. Label Comments

```bash
cd labeling_app
streamlit run app.py
```

### 7. View Results

Open the generated HTML reports in your browser:
- `data/data_quality_report.html`
- `data/qa_report.html` (after labeling)

---

## 📋 Command Cheat Sheet

### Data Pipeline

```bash
# Full data collection (requires API key)
python src/data_collection.py --max-comments 50000

# Clean data
python src/data_cleaning.py

# Validate data
python src/data_validation.py

# Generate quality report
python src/report_generator.py --input data/clean_comments_validated.csv --output data/data_quality_report.html
```

### Labeling

```bash
# Launch labeling tool
cd labeling_app
streamlit run app.py

# Run QA analysis
python src/qa_analysis.py --input data/labeled_comments.csv --output data/qa_report.html
```

### Model Training

```bash
# Train sentiment classifier
python src/model_training.py --input data/labeled_comments.csv --task sentiment

# Train toxicity detector
python src/model_training.py --input data/labeled_comments.csv --task toxicity

# Train intent classifier
python src/model_training.py --input data/labeled_comments.csv --task intent
```

### Notebooks

```bash
# Launch Jupyter
jupyter notebook

# Open notebooks/01_EDA.ipynb
```

---

## 🔧 Troubleshooting

### YouTube API Issues

**Problem**: "Invalid or missing YouTube API key"

**Solution**:
1. Get API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Add key to `.env` file: `YOUTUBE_API_KEY=your_key_here`

### Quota Exceeded

**Problem**: "Quota exceeded" error

**Solution**:
- Wait 24 hours for quota reset
- Use `--test-mode` for testing
- Request quota increase from Google

### Module Not Found

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
pip install -r requirements.txt
```

### GPU Not Detected

**Problem**: PyTorch not using GPU

**Solution**:
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📚 Next Steps

1. **Read the full [README.md](README.md)**
2. **Review [labeling_guidelines.md](src/labeling_guidelines.md)**
3. **Check [DATASET_CARD.md](DATASET_CARD.md)**
4. **Explore the notebooks**
5. **Train your first model**

---

## 💡 Tips

- Start with `--test-mode` to verify setup
- Review quality reports before labeling
- Use keyboard shortcuts in labeling tool
- Monitor GPU usage during training
- Save models frequently

---

## 🆘 Need Help?

- **Documentation**: See [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/[username]/gta-vi-llm-dataset/issues)
- **Guidelines**: [labeling_guidelines.md](src/labeling_guidelines.md)

---

**Happy Dataset Building! 🎉**
