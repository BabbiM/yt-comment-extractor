import os
import csv
import uuid
from .extractor import extract_comments
from .video_list import get_videos_from_channel
import pandas as pd

EXTRACTED_DIR = "server/data/extracted"

def extract_channel_comments(channel_url, num_videos):
    print(f"Scraping channel: {channel_url} for {num_videos} videos")

    # Get video metadata
    videos = get_videos_from_channel(channel_url, num_videos)
    print(f"Found {len(videos)} videos")

    if not os.path.exists(EXTRACTED_DIR):
        os.makedirs(EXTRACTED_DIR)

    analytics = {}
    total_extracted = 0
    last_csv_path = None

    for i, video in enumerate(videos, 1):
        video_url = video.get("url")
        print(f"Scraping ({i}/{len(videos)}): {video}")

        if not video_url:
            print("Missing video URL, skipping.")
            continue

        try:
            print(f"Starting to extract comments from: {video_url}")
            # CHANGED THIS LINE - Now properly unpacking the tuple
            total_comments, comments = extract_comments(video_url)
            print(f"Successfully extracted {total_comments} comments from {video_url}")

            if total_comments == 0:
                print(f"No comments found for {video_url}")
                continue

            filename = video_url.split("v=")[-1].split("&")[0] + ".csv"  # Cleaner filename
            csv_path = os.path.join(EXTRACTED_DIR, filename)
            
            # SAFER DataFrame conversion
            try:
                comments_df = pd.DataFrame(comments)
                comments_df.to_csv(csv_path, index=False)
                last_csv_path = csv_path
            except Exception as df_error:
                print(f"DataFrame conversion failed, using manual CSV export: {df_error}")
                export_comments_manually(comments, csv_path)
                last_csv_path = csv_path

            analytics[video_url] = {
                "title": video.get("title", "Untitled"),
                "total_comments": total_comments,
                "csv_path": csv_path,
            }
            total_extracted += total_comments

        except Exception as e:
            print(f"Error extracting comments from {video_url}: {e}")

    if total_extracted == 0:
        raise Exception("No comments extracted from any videos.")

    return analytics, last_csv_path

def export_comments_manually(comments, csv_path):
    """Fallback CSV export without pandas"""
    fieldnames = [
        'comment_id', 'text', 'likes', 'author',
        'author_id', 'timestamp', 'time_text', 'is_pinned'
    ]
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comments)