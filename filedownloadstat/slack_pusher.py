#!/usr/bin/env python3
"""
Slack Pusher - Pushes consolidated report to Slack

This module contains functionality to push the consolidated summary report
to Slack. HTML files are uploaded as file attachments, TSV files are sent as text.
"""

import json
import sys
import logging
import requests
from pathlib import Path
from typing import Optional

from exceptions import (
    SlackPushError,
    ValidationError
)
from interfaces import ISlackPusher

logger = logging.getLogger(__name__)


class SlackPusher(ISlackPusher):
    """Class for pushing reports to Slack."""
    
    def __init__(self, webhook_url: str, bot_token: Optional[str] = None, channel: Optional[str] = None) -> None:
        """Initialize the Slack pusher.
        
        Args:
            webhook_url: Slack webhook URL (required)
            bot_token: Optional Slack bot token (for file uploads)
            channel: Optional Slack channel ID (required if bot_token is provided)
        """
        if not webhook_url:
            raise ValidationError("webhook_url must be provided", field="webhook_url")
        if bot_token and not channel:
            raise ValidationError("channel must be provided when bot_token is set", field="channel")
        
        self.webhook_url: str = webhook_url
        self.bot_token: Optional[str] = bot_token
        self.channel: Optional[str] = channel
    
    def _upload_file_to_slack(self, file_path: str, title: str) -> bool:
        """Upload a file to Slack using the Web API.
        
        Args:
            file_path: Path to the file to upload
            title: Title for the message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'text/html')}
                data = {
                    'channels': self.channel,
                    'title': title,
                    'initial_comment': f"*{title}*"
                }
                headers = {'Authorization': f'Bearer {self.bot_token}'}
                
                response = requests.post(
                    'https://slack.com/api/files.upload',
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
                
                result = response.json()
                if result.get('ok'):
                    logger.info("Successfully uploaded file to Slack", extra={"file": file_path, "title": title})
                    return True
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error("Failed to upload file to Slack", extra={"file": file_path, "error": error_msg})
                    return False
        except Exception as e:
            logger.error("Error uploading file to Slack", extra={"file": file_path, "error": str(e)}, exc_info=True)
            return False
    
    def push_report(self, report_file: str, title: Optional[str] = None) -> bool:
        """Push consolidated report to Slack.
        
        Args:
            report_file: Path to the report file (TSV or HTML)
            title: Optional title for the message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            report_path = Path(report_file)
            if not report_path.exists():
                raise FileNotFoundError(f"Report file not found: {report_file}")
            
            message_title = title or "PRIDE Protein Pipeline - Consolidated Report"
            
            # For HTML files, upload as file attachment
            if report_file.endswith('.html'):
                if self.bot_token and self.channel:
                    return self._upload_file_to_slack(report_file, message_title)
                else:
                    error = SlackPushError(
                        "bot_token and channel are required for HTML file uploads",
                        report_file=report_file
                    )
                    logger.error("bot_token and channel required for HTML files", extra={"report_file": report_file})
                    return False
            else:
                # For TSV files, send as code block via webhook
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                formatted_content = f"```\n{report_content}\n```"
                full_message = f"*{message_title}*\n\n{formatted_content}"
                
                payload = {
                    "text": full_message
                }
                
                response = requests.post(self.webhook_url, json=payload, timeout=30)
                if response.status_code == 200:
                    logger.info("Successfully pushed report to Slack", extra={"report_file": report_file, "title": message_title})
                    return True
                else:
                    error = SlackPushError(
                        f"Failed to push to Slack: HTTP {response.status_code}",
                        report_file=report_file,
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    logger.error("Failed to push to Slack", extra={"report_file": report_file, "status_code": response.status_code, "response": response.text})
                    return False
                
        except FileNotFoundError as e:
            error = SlackPushError(
                f"Report file not found: {report_file}",
                report_file=report_file
            )
            logger.error("Report file not found", extra={"report_file": report_file})
            return False
        except requests.RequestException as e:
            error = SlackPushError(
                f"Network error pushing to Slack: {str(e)}",
                report_file=report_file,
                original_error=str(e)
            )
            logger.error("Network error pushing to Slack", extra={"report_file": report_file, "error": str(e)}, exc_info=True)
            return False
        except Exception as e:
            error = SlackPushError(
                f"Unexpected error pushing to Slack: {str(e)}",
                report_file=report_file,
                original_error=str(e)
            )
            logger.error("Error pushing to Slack", extra={"report_file": report_file, "error": str(e)}, exc_info=True)
            return False


def push_to_slack(report_file: str, webhook_url: str, title: Optional[str] = None, 
                  bot_token: Optional[str] = None, channel: Optional[str] = None) -> bool:
    """Convenience function to push report to Slack.
    
    Args:
        report_file: Path to the report file (TSV or HTML)
        webhook_url: Slack webhook URL
        title: Optional title for the message
        bot_token: Optional Slack bot token (for HTML file uploads)
        channel: Optional Slack channel ID (required if bot_token is provided)
    
    Returns:
        True if successful, False otherwise
    """
    pusher = SlackPusher(webhook_url, bot_token=bot_token, channel=channel)
    return pusher.push_report(report_file, title)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Push consolidated report to Slack")
    parser.add_argument('--input-file', required=True, help='Path to report file (TSV or HTML)')
    parser.add_argument('--webhook-url', required=True, help='Slack webhook URL')
    parser.add_argument('--title', help='Title for the Slack message (optional)')
    parser.add_argument('--bot-token', help='Slack bot token (optional, for HTML file uploads)')
    parser.add_argument('--channel', help='Slack channel ID (required if --bot-token is provided)')
    
    args = parser.parse_args()
    
    success = push_to_slack(args.input_file, args.webhook_url, args.title, 
                           bot_token=args.bot_token, channel=args.channel)
    
    sys.exit(0 if success else 1)

