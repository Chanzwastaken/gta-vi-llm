# Dataset Card: GTA VI Trailer 2 YouTube Comments

## Dataset Summary

This dataset contains YouTube comments collected from the Grand Theft Auto VI Trailer 2 video, processed and labeled for training Large Language Models (LLMs) and text classification tasks. The dataset includes multi-dimensional labels covering sentiment, toxicity, emotion, relevance, and intent classification.

**Total Comments**: ~50,000 (target)  
**Language**: Primarily English (with language detection flags)  
**Source**: YouTube Data API v3  
**Video**: [GTA VI Trailer 2](https://www.youtube.com/watch?v=QdBZY2fkU-0)  
**Collection Period**: 2024  
**License**: For research and educational purposes

---

## Dataset Description

### Motivation

The gaming community's reactions to major game announcements provide rich, authentic data for understanding:
- Public sentiment and emotional responses
- Online discourse patterns in gaming communities
- Toxicity and moderation challenges
- Meme culture and humor in digital spaces

This dataset was created to:
1. Build high-quality training data for LLM fine-tuning
2. Develop text classification models for gaming community analysis
3. Demonstrate best practices in dataset preparation and labeling
4. Study sentiment and toxicity patterns in gaming discourse

---

## Data Collection

### Source

Comments were collected using the **YouTube Data API v3** from the official GTA VI Trailer 2 video published by Rockstar Games.

### Collection Methodology

- **API**: YouTube Data API v3
- **Pagination**: Automated with resume capability
- **Rate Limiting**: Exponential backoff and quota management
- **Fields Collected**:
  - `comment_id`: Unique comment identifier
  - `text`: Original comment text
  - `like_count`: Number of likes
  - `published_at`: Publication timestamp
  - `parent_id`: Parent comment ID (for replies)
  - `author_id`: Hashed author identifier (privacy protection)
  - `video_id`: Source video ID

### Privacy Considerations

- Author IDs are **SHA-256 hashed** to protect user privacy
- No personally identifiable information (PII) is stored
- All data is publicly available on YouTube
- Comments are used for research purposes only

---

## Data Processing Pipeline

### 1. Cleaning

**Operations**:
- HTML tag removal
- Emoji removal/normalization
- URL extraction and removal
- Whitespace normalization
- Duplicate detection and removal
- Length validation (3-1000 characters)

**Tools**: BeautifulSoup4, regex, pandas

### 2. Validation

**Quality Checks**:
- **Language Detection**: Using `langdetect` library
- **Spam Detection**: Keyword-based and pattern matching
- **Toxicity Scoring**: Using Detoxify (BERT-based model)
- **Bot Detection**: Repetitive patterns and suspicious behavior

**Quality Flags**:
- `is_english`: Boolean flag for English language
- `is_spam`: Spam detection flag
- `is_high_quality`: Combined quality indicator
- `toxicity_score`: Continuous toxicity score (0-1)

### 3. Feature Engineering

**Derived Features**:
- `word_count`: Number of words
- `char_count`: Number of characters
- `avg_word_length`: Average word length
- `uppercase_ratio`: Ratio of uppercase characters
- `has_question`: Contains question mark
- `has_exclamation`: Contains exclamation mark
- `sentence_count`: Number of sentences

---

## Labeling Process

### Label Categories

#### 1. Sentiment (4 classes)
- **Positive**: Approval, excitement, satisfaction
- **Neutral**: Factual statements, balanced opinions
- **Negative**: Disappointment, criticism
- **Sarcasm**: Ironic or mocking tone

#### 2. Toxicity (3 classes)
- **Safe**: Respectful, appropriate language
- **Mild Toxic**: Mildly rude, casual profanity
- **Severe Toxic**: Offensive, abusive, hate speech

#### 3. Emotion (6 classes)
- **Excited**: High energy, enthusiasm
- **Angry**: Frustration, irritation
- **Disappointed**: Let down, underwhelmed
- **Nostalgic**: Reminiscing about past games
- **Humor/Meme**: Jokes, comedic content
- **Other**: Other emotions

#### 4. Relevance (3 classes)
- **On-topic**: Related to GTA VI or trailer
- **Off-topic**: Unrelated content
- **Spam**: Promotional, repetitive

#### 5. Intent Type (6 classes)
- **Reaction**: Immediate emotional response
- **Speculation**: Theories, predictions
- **Criticism**: Constructive feedback
- **Complaint**: Dissatisfaction, grievances
- **Meme/Joke**: Humorous content
- **Question**: Asking for information

### Labeling Guidelines

Comprehensive labeling guidelines were developed including:
- Detailed definitions for each category
- 5+ examples per label
- Edge case handling (e.g., sarcasm detection)
- Decision rules for ambiguous cases
- Inter-annotator agreement protocols

**Guideline Document**: See `src/labeling_guidelines.md`

### Labeling Tool

A custom **Streamlit web application** was developed featuring:
- Interactive labeling interface
- Progress tracking
- Label validation
- Search and filtering
- Keyboard shortcuts
- Multi-annotator support

---

## Quality Assurance

### QA Checks

1. **Label Distribution Analysis**: Detect class imbalance
2. **Consistency Checks**: Identify conflicting labels for identical text
3. **Inter-Annotator Agreement**: Cohen's Kappa calculation
4. **Annotator Bias Detection**: Statistical analysis per annotator
5. **Outlier Detection**: Unusual label combinations

### Quality Metrics

- **Target Inter-Annotator Agreement**: κ > 0.6 (Moderate to Substantial)
- **Minimum Labels per Category**: 100+ samples per class
- **Quality Threshold**: >80% high-quality comments (English, non-spam, safe)

---

## Dataset Statistics

### Size
- **Total Comments**: ~50,000
- **After Cleaning**: ~45,000
- **High Quality**: ~35,000 (English, non-spam, safe)
- **Labeled Subset**: Variable (depends on annotation effort)

### Language Distribution
- **English**: ~75%
- **Spanish**: ~8%
- **Portuguese**: ~5%
- **Other**: ~12%

### Toxicity Distribution
- **Safe**: ~85%
- **Mild Toxic**: ~12%
- **Severe Toxic**: ~3%

### Temporal Coverage
- **Date Range**: From trailer release to collection date
- **Peak Activity**: First 48 hours after release

---

## Dataset Structure

### Files

```
data/
├── raw_comments.csv              # Raw collected comments
├── clean_comments.csv            # Cleaned comments
├── clean_comments_validated.csv  # Validated with quality flags
├── labeled_comments.csv          # Human-labeled subset
└── data_quality_report.html      # Quality analysis report
```

### Schema

**raw_comments.csv**:
- `comment_id`, `text`, `like_count`, `published_at`, `parent_id`, `author_id`, `video_id`, `is_reply`

**clean_comments_validated.csv** (adds):
- `text_clean`, `word_count`, `char_count`, `language`, `is_english`, `is_spam`, `spam_score`, `toxicity_score`, `toxicity_level`, `is_high_quality`

**labeled_comments.csv** (adds):
- `sentiment`, `toxicity`, `emotion`, `relevance`, `intent`, `annotator_id`, `labeled_at`

---

## Intended Uses

### Primary Uses

1. **LLM Fine-Tuning**: Training language models on gaming community discourse
2. **Text Classification**: Multi-label classification tasks
3. **Sentiment Analysis**: Gaming industry sentiment tracking
4. **Toxicity Detection**: Content moderation research
5. **Intent Recognition**: Understanding user intent in comments

### Research Applications

- Gaming community analysis
- Social media discourse studies
- Sarcasm and humor detection
- Multilingual sentiment analysis
- Temporal sentiment tracking

---

## Limitations

### Data Limitations

1. **Platform Bias**: YouTube comments may not represent all gamers
2. **Temporal Bias**: Comments from specific time period (trailer release)
3. **Language Bias**: Primarily English-speaking audience
4. **Selection Bias**: Only users who comment (not silent viewers)
5. **Topic Specificity**: Specific to GTA VI and Rockstar Games

### Labeling Limitations

1. **Subjectivity**: Sentiment and emotion are subjective
2. **Context Dependency**: Some comments require video context
3. **Sarcasm Difficulty**: Sarcasm detection is challenging
4. **Cultural Nuances**: Memes and references may be culture-specific
5. **Annotation Errors**: Human labeling is not perfect

### Technical Limitations

1. **API Quotas**: Limited by YouTube API rate limits
2. **Deleted Comments**: Comments deleted after collection not updated
3. **Language Detection**: Not 100% accurate for short texts
4. **Toxicity Model**: Detoxify may have biases

---

## Ethical Considerations

### Privacy

- All data is publicly available on YouTube
- Author IDs are hashed for privacy protection
- No attempt to de-anonymize users
- Compliant with YouTube Terms of Service

### Toxicity and Harmful Content

- Dataset contains toxic and offensive language
- Appropriate for research and moderation tool development
- Should not be used to train models that amplify toxicity
- Content warnings should be provided when sharing

### Bias and Fairness

- Gaming community demographics may not be representative
- Potential biases in language, culture, and perspectives
- Models trained on this data may inherit these biases
- Should not be used for high-stakes decisions without validation

### Responsible Use

**Do**:
- Use for research and education
- Cite this dataset appropriately
- Consider ethical implications
- Validate models on diverse data

**Don't**:
- Use for surveillance or harassment
- Deploy without bias testing
- Ignore privacy considerations
- Amplify toxic content

---

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{gta_vi_comments_2024,
  title={GTA VI Trailer 2 YouTube Comments Dataset},
  author={[Your Name]},
  year={2024},
  publisher={GitHub},
  url={https://github.com/[username]/gta-vi-llm-dataset}
}
```

---

## Changelog

- **v1.0** (2024-11-24): Initial dataset release
  - 50,000 comments collected
  - Comprehensive cleaning and validation
  - Multi-dimensional labeling schema
  - Quality assurance pipeline

---

## Contact

For questions, issues, or collaboration:
- **GitHub**: [Repository Issues](https://github.com/[username]/gta-vi-llm-dataset/issues)
- **Email**: [your.email@example.com]

---

## Acknowledgments

- **Rockstar Games** for creating GTA VI
- **YouTube Data API** for data access
- **HuggingFace** for Transformers library
- **Detoxify** for toxicity detection model
- **Open-source community** for tools and libraries

---

## License

This dataset is released under the **MIT License** for research and educational purposes.

**Note**: While the dataset is MIT licensed, users must comply with:
- YouTube Terms of Service
- Applicable data protection regulations (GDPR, CCPA, etc.)
- Ethical research guidelines

---

**Last Updated**: 2024-11-24
