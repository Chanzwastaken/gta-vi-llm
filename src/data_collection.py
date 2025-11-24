"""
YouTube Data Collection Script for GTA VI Trailer 2 Comments.

This script uses the YouTube Data API v3 to collect comments from
the GTA VI Trailer 2 video, including replies, metadata, and author information.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import (
    load_config, load_env_vars, setup_logging, hash_string,
    ensure_dir, ProgressTracker, save_progress, load_progress,
    validate_api_key
)


class YouTubeCommentCollector:
    """Collect comments from YouTube videos using the YouTube Data API v3."""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        """
        Initialize the YouTube comment collector.
        
        Args:
            api_key: YouTube Data API v3 key
            config: Configuration dictionary
        """
        self.api_key = api_key
        self.config = config
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.logger = logging.getLogger(__name__)
        
        # Collection settings
        self.video_id = config['video']['video_id']
        self.max_comments = config['collection']['max_comments']
        self.comments_per_request = config['collection']['comments_per_request']
        self.max_retries = config['collection']['max_retries']
        self.retry_delay = config['collection']['retry_delay']
        
        # Storage
        self.comments = []
        self.collected_ids = set()
    
    def collect_comments(
        self,
        resume: bool = True,
        progress_file: str = "data/collection_progress.json"
    ) -> pd.DataFrame:
        """
        Collect comments from the video.
        
        Args:
            resume: Whether to resume from previous progress
            progress_file: Path to progress file
            
        Returns:
            DataFrame containing collected comments
        """
        self.logger.info(f"Starting comment collection for video: {self.video_id}")
        self.logger.info(f"Target: {self.max_comments} comments")
        
        # Load previous progress if resuming
        next_page_token = None
        if resume:
            progress = load_progress(progress_file)
            if progress:
                self.comments = progress.get('comments', [])
                self.collected_ids = set(c['comment_id'] for c in self.comments)
                next_page_token = progress.get('next_page_token')
                self.logger.info(f"Resuming from {len(self.comments)} comments")
        
        # Collect comment threads
        with ProgressTracker(self.max_comments, "Collecting comments") as pbar:
            pbar.update(len(self.comments))
            
            while len(self.comments) < self.max_comments:
                try:
                    # Fetch comment threads
                    response = self._fetch_comment_threads(next_page_token)
                    
                    if not response:
                        self.logger.warning("No response received, stopping collection")
                        break
                    
                    # Process comment threads
                    for item in response.get('items', []):
                        if len(self.comments) >= self.max_comments:
                            break
                        
                        # Extract top-level comment
                        top_comment = self._extract_comment(item['snippet']['topLevelComment'])
                        if top_comment and top_comment['comment_id'] not in self.collected_ids:
                            self.comments.append(top_comment)
                            self.collected_ids.add(top_comment['comment_id'])
                            pbar.update(1)
                        
                        # Extract replies if present
                        if item['snippet']['totalReplyCount'] > 0:
                            replies = self._fetch_replies(item['id'])
                            for reply in replies:
                                if len(self.comments) >= self.max_comments:
                                    break
                                if reply['comment_id'] not in self.collected_ids:
                                    self.comments.append(reply)
                                    self.collected_ids.add(reply['comment_id'])
                                    pbar.update(1)
                    
                    # Get next page token
                    next_page_token = response.get('nextPageToken')
                    
                    # Save progress
                    save_progress({
                        'comments': self.comments,
                        'next_page_token': next_page_token,
                        'timestamp': datetime.now().isoformat()
                    }, progress_file)
                    
                    # Check if there are more pages
                    if not next_page_token:
                        self.logger.info("No more comments available")
                        break
                    
                    # Rate limiting - small delay between requests
                    time.sleep(0.5)
                
                except HttpError as e:
                    self.logger.error(f"HTTP error occurred: {e}")
                    if e.resp.status == 403:
                        self.logger.error("Quota exceeded or API key invalid")
                        break
                    time.sleep(self.retry_delay)
                
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    time.sleep(self.retry_delay)
        
        self.logger.info(f"Collection complete: {len(self.comments)} comments collected")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.comments)
        return df
    
    def _fetch_comment_threads(self, page_token: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch comment threads from YouTube API.
        
        Args:
            page_token: Page token for pagination
            
        Returns:
            API response dictionary
        """
        for attempt in range(self.max_retries):
            try:
                request = self.youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=self.video_id,
                    maxResults=self.comments_per_request,
                    pageToken=page_token,
                    textFormat='plainText',
                    order='relevance'  # Can be 'time' or 'relevance'
                )
                response = request.execute()
                return response
            
            except HttpError as e:
                if e.resp.status == 403:
                    raise  # Don't retry quota errors
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _fetch_replies(self, parent_id: str) -> List[Dict[str, Any]]:
        """
        Fetch replies to a comment.
        
        Args:
            parent_id: Parent comment ID
            
        Returns:
            List of reply comment dictionaries
        """
        replies = []
        
        try:
            request = self.youtube.comments().list(
                part='snippet',
                parentId=parent_id,
                maxResults=100,
                textFormat='plainText'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                reply = self._extract_comment(item, parent_id=parent_id)
                if reply:
                    replies.append(reply)
        
        except Exception as e:
            self.logger.warning(f"Failed to fetch replies for {parent_id}: {e}")
        
        return replies
    
    def _extract_comment(
        self,
        comment_data: Dict[str, Any],
        parent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract relevant fields from comment data.
        
        Args:
            comment_data: Raw comment data from API
            parent_id: Parent comment ID if this is a reply
            
        Returns:
            Processed comment dictionary
        """
        try:
            snippet = comment_data['snippet']
            
            return {
                'comment_id': comment_data['id'],
                'text': snippet['textDisplay'],
                'like_count': snippet.get('likeCount', 0),
                'published_at': snippet['publishedAt'],
                'updated_at': snippet.get('updatedAt', snippet['publishedAt']),
                'parent_id': parent_id if parent_id else '',
                'author_id': hash_string(snippet['authorChannelId']['value'] if 'authorChannelId' in snippet else snippet.get('authorDisplayName', 'unknown')),
                'video_id': self.video_id,
                'is_reply': bool(parent_id)
            }
        
        except Exception as e:
            self.logger.warning(f"Failed to extract comment: {e}")
            return None
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save comments to CSV file.
        
        Args:
            df: DataFrame containing comments
            output_path: Output file path
        """
        ensure_dir(os.path.dirname(output_path))
        df.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"Saved {len(df)} comments to {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Collect YouTube comments for GTA VI Trailer 2"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file path (overrides config)'
    )
    parser.add_argument(
        '--max-comments',
        type=int,
        default=None,
        help='Maximum number of comments to collect (overrides config)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from previous progress'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Test mode: collect only 100 comments'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    load_env_vars()
    
    # Setup logging
    log_config = config.get('logging', {})
    logger = setup_logging(
        log_level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/data_collection.log')
    )
    
    # Get API key
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not validate_api_key(api_key):
        logger.error("Invalid or missing YouTube API key")
        logger.error("Please set YOUTUBE_API_KEY in your .env file")
        sys.exit(1)
    
    # Override config with command line arguments
    if args.max_comments:
        config['collection']['max_comments'] = args.max_comments
    
    if args.test_mode:
        config['collection']['max_comments'] = 100
        logger.info("Test mode: collecting only 100 comments")
    
    output_path = args.output or config['paths']['raw_data']
    
    # Collect comments
    try:
        collector = YouTubeCommentCollector(api_key, config)
        df = collector.collect_comments(resume=args.resume)
        
        # Save to CSV
        collector.save_to_csv(df, output_path)
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total comments collected: {len(df)}")
        logger.info(f"Top-level comments: {len(df[df['parent_id'] == ''])}")
        logger.info(f"Replies: {len(df[df['parent_id'] != ''])}")
        logger.info(f"Date range: {df['published_at'].min()} to {df['published_at'].max()}")
        logger.info(f"Output file: {output_path}")
        logger.info("="*50)
    
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
