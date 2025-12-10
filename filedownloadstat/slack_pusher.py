#!/usr/bin/env python3
"""
Slack Pusher - Pushes consolidated report to Slack

This module contains functionality to push the consolidated summary report
to Slack via webhook URL.
"""

import json
import sys
import requests
from pathlib import Path
from typing import Optional


class SlackPusher:
    """Class for pushing reports to Slack."""
    
    def __init__(self, webhook_url: str):
        """Initialize the Slack pusher.
        
        Args:
            webhook_url: Slack webhook URL
        """
        if not webhook_url:
            raise ValueError("webhook_url must be provided")
        self.webhook_url = webhook_url
    
    def push_report(self, report_file: str, title: Optional[str] = None) -> bool:
        """Push consolidated report to Slack.
        
        Args:
            report_file: Path to the report file (TSV or HTML)
            title: Optional title for the message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the file
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # Create Slack message
            message_title = title or "PRIDE Protein Pipeline - Consolidated Report"
            
            # For HTML files, send as plain text (Slack will display it)
            # For TSV files, format as code block for better readability
            if report_file.endswith('.html'):
                # For HTML, we can send it as plain text or extract a summary
                # Sending as plain text for now - Slack will render basic HTML
                formatted_content = report_content
            else:
                # Format the report as a code block for better readability
                formatted_content = f"```\n{report_content}\n```"
            
            # Combine title and content
            full_message = f"*{message_title}*\n\n{formatted_content}"
            
            # Create payload for Slack webhook
            payload = {
                "text": full_message
            }
            
            # Send to Slack webhook
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Successfully pushed report to Slack via webhook")
                return True
            else:
                print(f"❌ Failed to push to Slack: {response.status_code} {response.text}", file=sys.stderr)
                return False
                
        except FileNotFoundError:
            print(f"Error: {report_file} not found", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error pushing to Slack: {e}", file=sys.stderr)
            return False


def push_to_slack(report_file: str, webhook_url: str, title: Optional[str] = None) -> bool:
    """Convenience function to push report to Slack.
    
    Args:
        report_file: Path to the report file (TSV or HTML)
        webhook_url: Slack webhook URL
        title: Optional title for the message
    
    Returns:
        True if successful, False otherwise
    """
    pusher = SlackPusher(webhook_url)
    return pusher.push_report(report_file, title)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Push consolidated report to Slack")
    parser.add_argument('--input-file', required=True, help='Path to report file (TSV or HTML)')
    parser.add_argument('--webhook-url', required=True, help='Slack webhook URL')
    parser.add_argument('--title', help='Title for the Slack message (optional)')
    
    args = parser.parse_args()
    
    success = push_to_slack(args.input_file, args.webhook_url, args.title)
    
    sys.exit(0 if success else 1)

