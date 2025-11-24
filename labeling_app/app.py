"""
Streamlit Labeling Application for YouTube Comments.

This interactive web application allows annotators to label comments
with multiple categories including sentiment, toxicity, emotion, relevance, and intent.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from src.utils import ensure_dir

# Page configuration
st.set_page_config(
    page_title="GTA VI Comment Labeling Tool",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Label schema
LABEL_SCHEMA = {
    'sentiment': ['Positive', 'Neutral', 'Negative', 'Sarcasm'],
    'toxicity': ['Safe', 'Mild Toxic', 'Severe Toxic'],
    'emotion': ['Excited', 'Angry', 'Disappointed', 'Nostalgic', 'Humor/Meme', 'Other'],
    'relevance': ['On-topic', 'Off-topic', 'Spam'],
    'intent': ['Reaction', 'Speculation', 'Criticism', 'Complaint', 'Meme/Joke', 'Question']
}

# Keyboard shortcuts mapping
SHORTCUTS = {
    'sentiment': {'1': 'Positive', '2': 'Neutral', '3': 'Negative', '4': 'Sarcasm'},
    'toxicity': {'5': 'Safe', '6': 'Mild Toxic', '7': 'Severe Toxic'},
}


class LabelingApp:
    """Main labeling application class."""
    
    def __init__(self):
        """Initialize the labeling application."""
        self.data_path = Path("../data")
        self.clean_data_file = self.data_path / "clean_comments_validated.csv"
        self.labeled_data_file = self.data_path / "labeled_comments.csv"
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0
        
        if 'labels' not in st.session_state:
            st.session_state.labels = {}
        
        if 'annotator_id' not in st.session_state:
            st.session_state.annotator_id = ""
        
        if 'filter_mode' not in st.session_state:
            st.session_state.filter_mode = "All"
        
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        if 'labeled_count' not in st.session_state:
            st.session_state.labeled_count = 0
        
        if 'show_guidelines' not in st.session_state:
            st.session_state.show_guidelines = False
    
    def load_data(self) -> pd.DataFrame:
        """Load comments data."""
        if not self.clean_data_file.exists():
            st.error(f"Data file not found: {self.clean_data_file}")
            st.info("Please run the data cleaning pipeline first.")
            st.stop()
        
        df = pd.read_csv(self.clean_data_file)
        
        # Load existing labels if available
        if self.labeled_data_file.exists():
            labeled_df = pd.read_csv(self.labeled_data_file)
            # Merge labels
            df = df.merge(
                labeled_df[['comment_id', 'sentiment', 'toxicity', 'emotion', 'relevance', 'intent', 'annotator_id']],
                on='comment_id',
                how='left',
                suffixes=('', '_labeled')
            )
        
        return df
    
    def save_label(self, comment_id: str, labels: Dict[str, str], annotator_id: str):
        """Save a single label to the labeled dataset."""
        # Create label entry
        label_entry = {
            'comment_id': comment_id,
            'sentiment': labels.get('sentiment', ''),
            'toxicity': labels.get('toxicity', ''),
            'emotion': labels.get('emotion', ''),
            'relevance': labels.get('relevance', ''),
            'intent': labels.get('intent', ''),
            'annotator_id': annotator_id,
            'labeled_at': datetime.now().isoformat()
        }
        
        # Load existing labels or create new dataframe
        if self.labeled_data_file.exists():
            labeled_df = pd.read_csv(self.labeled_data_file)
            # Remove existing label for this comment if any
            labeled_df = labeled_df[labeled_df['comment_id'] != comment_id]
            # Append new label
            labeled_df = pd.concat([labeled_df, pd.DataFrame([label_entry])], ignore_index=True)
        else:
            labeled_df = pd.DataFrame([label_entry])
        
        # Save
        ensure_dir(self.data_path)
        labeled_df.to_csv(self.labeled_data_file, index=False)
        
        st.session_state.labeled_count += 1
    
    def render_header(self):
        """Render application header."""
        st.title("🎮 GTA VI Comment Labeling Tool")
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### Label YouTube comments for LLM training")
        
        with col2:
            if st.button("📖 Show Guidelines"):
                st.session_state.show_guidelines = not st.session_state.show_guidelines
        
        with col3:
            st.metric("Labels Today", st.session_state.labeled_count)
    
    def render_sidebar(self, df: pd.DataFrame):
        """Render sidebar with controls and statistics."""
        st.sidebar.title("⚙️ Controls")
        
        # Annotator ID
        st.sidebar.markdown("### Annotator Info")
        annotator_id = st.sidebar.text_input(
            "Your ID",
            value=st.session_state.annotator_id,
            help="Enter your annotator ID"
        )
        st.session_state.annotator_id = annotator_id
        
        st.sidebar.markdown("---")
        
        # Filter options
        st.sidebar.markdown("### Filters")
        filter_mode = st.sidebar.selectbox(
            "Show",
            ["All", "Unlabeled Only", "Labeled Only", "High Quality Only", "English Only"]
        )
        st.session_state.filter_mode = filter_mode
        
        # Search
        search_query = st.sidebar.text_input(
            "Search",
            value=st.session_state.search_query,
            help="Search in comment text"
        )
        st.session_state.search_query = search_query
        
        st.sidebar.markdown("---")
        
        # Statistics
        st.sidebar.markdown("### 📊 Statistics")
        
        total = len(df)
        labeled = 0
        if self.labeled_data_file.exists():
            labeled_df = pd.read_csv(self.labeled_data_file)
            labeled = len(labeled_df)
        
        unlabeled = total - labeled
        progress = (labeled / total * 100) if total > 0 else 0
        
        st.sidebar.metric("Total Comments", f"{total:,}")
        st.sidebar.metric("Labeled", f"{labeled:,}")
        st.sidebar.metric("Remaining", f"{unlabeled:,}")
        st.sidebar.progress(progress / 100)
        st.sidebar.caption(f"{progress:.1f}% Complete")
        
        st.sidebar.markdown("---")
        
        # Keyboard shortcuts
        st.sidebar.markdown("### ⌨️ Shortcuts")
        st.sidebar.markdown("""
        **Sentiment:**
        - `1` = Positive
        - `2` = Neutral
        - `3` = Negative
        - `4` = Sarcasm
        
        **Toxicity:**
        - `5` = Safe
        - `6` = Mild Toxic
        - `7` = Severe Toxic
        
        **Navigation:**
        - `N` = Next
        - `P` = Previous
        - `S` = Submit
        """)
    
    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filters to dataframe."""
        filtered_df = df.copy()
        
        # Apply filter mode
        if st.session_state.filter_mode == "Unlabeled Only":
            if 'sentiment' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['sentiment'].isna()]
        elif st.session_state.filter_mode == "Labeled Only":
            if 'sentiment' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['sentiment'].notna()]
        elif st.session_state.filter_mode == "High Quality Only":
            if 'is_high_quality' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['is_high_quality'] == True]
        elif st.session_state.filter_mode == "English Only":
            if 'is_english' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['is_english'] == True]
        
        # Apply search
        if st.session_state.search_query:
            query = st.session_state.search_query.lower()
            if 'text_clean' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['text_clean'].str.lower().str.contains(query, na=False)
                ]
        
        return filtered_df
    
    def render_comment_display(self, comment: pd.Series):
        """Render the current comment for labeling."""
        st.markdown("### 💬 Comment")
        
        # Comment text
        st.markdown(f"**Text:**")
        st.info(comment.get('text_clean', comment.get('text', 'N/A')))
        
        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👍 Likes", comment.get('like_count', 0))
        
        with col2:
            st.metric("📝 Words", comment.get('word_count', 0))
        
        with col3:
            st.metric("🔤 Characters", comment.get('cleaned_length', 0))
        
        with col4:
            if 'published_at' in comment:
                date = pd.to_datetime(comment['published_at']).strftime('%Y-%m-%d')
                st.metric("📅 Date", date)
        
        # Quality indicators
        if 'is_english' in comment or 'is_spam' in comment or 'toxicity_score' in comment:
            st.markdown("**Quality Indicators:**")
            cols = st.columns(3)
            
            if 'is_english' in comment:
                with cols[0]:
                    lang_status = "✅ English" if comment['is_english'] else "❌ Non-English"
                    st.caption(lang_status)
            
            if 'is_spam' in comment:
                with cols[1]:
                    spam_status = "⚠️ Spam" if comment['is_spam'] else "✅ Not Spam"
                    st.caption(spam_status)
            
            if 'toxicity_score' in comment:
                with cols[2]:
                    tox_score = comment['toxicity_score']
                    st.caption(f"🔍 Toxicity: {tox_score:.2f}")
    
    def render_labeling_interface(self, comment: pd.Series):
        """Render the labeling interface."""
        st.markdown("---")
        st.markdown("### 🏷️ Labels")
        
        # Create columns for label categories
        col1, col2 = st.columns(2)
        
        labels = {}
        
        with col1:
            # Sentiment
            st.markdown("**Sentiment**")
            labels['sentiment'] = st.selectbox(
                "Sentiment",
                options=[''] + LABEL_SCHEMA['sentiment'],
                key='sentiment_select',
                label_visibility='collapsed'
            )
            
            # Toxicity
            st.markdown("**Toxicity**")
            labels['toxicity'] = st.selectbox(
                "Toxicity",
                options=[''] + LABEL_SCHEMA['toxicity'],
                key='toxicity_select',
                label_visibility='collapsed'
            )
            
            # Emotion
            st.markdown("**Emotion**")
            labels['emotion'] = st.selectbox(
                "Emotion",
                options=[''] + LABEL_SCHEMA['emotion'],
                key='emotion_select',
                label_visibility='collapsed'
            )
        
        with col2:
            # Relevance
            st.markdown("**Relevance**")
            labels['relevance'] = st.selectbox(
                "Relevance",
                options=[''] + LABEL_SCHEMA['relevance'],
                key='relevance_select',
                label_visibility='collapsed'
            )
            
            # Intent
            st.markdown("**Intent Type**")
            labels['intent'] = st.selectbox(
                "Intent",
                options=[''] + LABEL_SCHEMA['intent'],
                key='intent_select',
                label_visibility='collapsed'
            )
        
        return labels
    
    def validate_labels(self, labels: Dict[str, str]) -> tuple[bool, str]:
        """Validate label combinations."""
        # Check all labels are filled
        for category, value in labels.items():
            if not value:
                return False, f"Please select a value for {category}"
        
        # Check for incompatible combinations
        if labels['relevance'] == 'Spam':
            # Spam comments don't need other labels to be meaningful
            pass
        
        if labels['toxicity'] == 'Severe Toxic' and labels['sentiment'] == 'Positive':
            return False, "Severe Toxic comments are rarely Positive. Please review."
        
        return True, ""
    
    def render_navigation(self, df: pd.DataFrame):
        """Render navigation controls."""
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", use_container_width=True):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1
                    st.rerun()
        
        with col2:
            if st.button("➡️ Next", use_container_width=True):
                if st.session_state.current_index < len(df) - 1:
                    st.session_state.current_index += 1
                    st.rerun()
        
        with col3:
            st.caption(f"Comment {st.session_state.current_index + 1} of {len(df)}")
        
        with col4:
            if st.button("🔀 Random", use_container_width=True):
                import random
                st.session_state.current_index = random.randint(0, len(df) - 1)
                st.rerun()
        
        with col5:
            jump_to = st.number_input(
                "Jump to",
                min_value=1,
                max_value=len(df),
                value=st.session_state.current_index + 1,
                label_visibility='collapsed'
            )
            if jump_to - 1 != st.session_state.current_index:
                st.session_state.current_index = jump_to - 1
                st.rerun()
    
    def render_guidelines(self):
        """Render labeling guidelines."""
        if st.session_state.show_guidelines:
            st.markdown("---")
            st.markdown("## 📖 Labeling Guidelines")
            
            with st.expander("Sentiment Categories", expanded=False):
                st.markdown("""
                - **Positive**: Approval, excitement, satisfaction
                - **Neutral**: Factual, balanced, or no clear emotion
                - **Negative**: Disappointment, criticism, dissatisfaction
                - **Sarcasm**: Ironic, mocking, says opposite of what's meant
                """)
            
            with st.expander("Toxicity Levels", expanded=False):
                st.markdown("""
                - **Safe**: Respectful, appropriate language
                - **Mild Toxic**: Mildly rude, casual profanity
                - **Severe Toxic**: Offensive, abusive, hate speech
                """)
            
            with st.expander("Emotion Types", expanded=False):
                st.markdown("""
                - **Excited**: High energy, enthusiasm
                - **Angry**: Frustration, irritation
                - **Disappointed**: Let down, underwhelmed
                - **Nostalgic**: Reminiscing, sentimental
                - **Humor/Meme**: Jokes, comedic content
                - **Other**: Other emotions
                """)
            
            with st.expander("Relevance", expanded=False):
                st.markdown("""
                - **On-topic**: Related to GTA VI or trailer
                - **Off-topic**: Unrelated content
                - **Spam**: Promotional, repetitive, bot-like
                """)
            
            with st.expander("Intent Types", expanded=False):
                st.markdown("""
                - **Reaction**: Immediate emotional response
                - **Speculation**: Theories, predictions
                - **Criticism**: Constructive feedback
                - **Complaint**: Dissatisfaction, grievances
                - **Meme/Joke**: Humorous content
                - **Question**: Asking for information
                """)
    
    def run(self):
        """Run the main application."""
        # Render header
        self.render_header()
        
        # Load data
        df = self.load_data()
        
        # Render sidebar
        self.render_sidebar(df)
        
        # Apply filters
        filtered_df = self.filter_dataframe(df)
        
        if len(filtered_df) == 0:
            st.warning("No comments match the current filters.")
            return
        
        # Ensure current index is valid
        if st.session_state.current_index >= len(filtered_df):
            st.session_state.current_index = 0
        
        # Get current comment
        current_comment = filtered_df.iloc[st.session_state.current_index]
        
        # Render comment
        self.render_comment_display(current_comment)
        
        # Render labeling interface
        labels = self.render_labeling_interface(current_comment)
        
        # Submit button
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("✅ Submit Label", use_container_width=True, type="primary"):
                if not st.session_state.annotator_id:
                    st.error("Please enter your Annotator ID in the sidebar")
                else:
                    # Validate labels
                    is_valid, message = self.validate_labels(labels)
                    
                    if is_valid:
                        # Save label
                        self.save_label(
                            current_comment['comment_id'],
                            labels,
                            st.session_state.annotator_id
                        )
                        st.success("Label saved successfully!")
                        
                        # Move to next comment
                        if st.session_state.current_index < len(filtered_df) - 1:
                            st.session_state.current_index += 1
                        
                        st.rerun()
                    else:
                        st.error(message)
        
        # Navigation
        self.render_navigation(filtered_df)
        
        # Guidelines
        self.render_guidelines()


def main():
    """Main entry point."""
    app = LabelingApp()
    app.run()


if __name__ == "__main__":
    main()
