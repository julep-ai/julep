# Standard library imports
import sys
import json
import re
import logging
from pathlib import Path
import os
import time
from typing import List, Dict, Any

# Third-party imports
from julep import Client
import yaml

# Configure logging with timestamp, level, and message format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants and configurations
HTML_TAGS_PATTERN = re.compile(r"(<[^>]+>)")  # Regex pattern to match HTML tags
REQUIRED_ENV_VARS = ['AGENT_UUID', 'TASK_UUID', 'JULEP_API_KEY']  # List of required environment variables

def load_template(filename: str) -> str:
    """Load template content from file"""
    return Path(f'./scripts/templates/{filename}').read_text(encoding='utf-8')

def run_task(pr_data: str) -> str:
    """
    Execute the changelog generation task using Julep API.
    
    Args:
        pr_data (str): Formatted PR data to process
        
    Returns:
        str: Generated changelog content
        
    Raises:
        ValueError: If required environment variables are missing
        Exception: If task execution fails
    """
    # Validate env vars with list comprehension
    if missing_vars := [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    client = Client(api_key=os.environ['JULEP_API_KEY'], environment="dev")
    
    # Use context manager for file operations
    with Path('./scripts/templates/changelog.yaml').open(encoding='utf-8') as f:
        task_description = yaml.safe_load(f)
    
    # Create or update the AI agent
    agent = client.agents.create_or_update(
        agent_id=os.environ['AGENT_UUID'],
        name="Changelog Generator",
        about="An AI assistant that can generate a changelog from a list of PRs.",
        model="gpt-4o",
    )

    # Create or update the task configuration
    task = client.tasks.create_or_update(
        task_id=os.environ['TASK_UUID'],
        agent_id=os.environ['AGENT_UUID'],
        **task_description
    )

    # Create a new execution instance
    execution = client.executions.create(
        task_id=os.environ['TASK_UUID'],
        input={"pr_data": str(pr_data)}
    )

    # Wait for task completion using context manager for proper resource cleanup
    with client:
        while (result := client.executions.get(execution.id)).status not in ['succeeded', 'failed']:
            time.sleep(3)
        
        if result.status != "succeeded":
            raise Exception(result.error)
        return result.output

def preserve_and_update_changelog(new_changelog: str, source: str = './CHANGELOG.md') -> None:
    """
    Save the generated changelog while preserving HTML content.
    
    Args:
        new_changelog (str): The new changelog content to save
        source (str): Path to the changelog file (default: 'CHANGELOG.md')
    """
    path = Path(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load templates at runtime
    html_content = load_template('header.html')
    author_list = load_template('authors.md')
    
    content = f"{html_content}\n\n{new_changelog}\n\n{author_list}"
    path.write_text(content, encoding='utf-8')

def is_html_tag(segment: str) -> bool:
    """
    Check if a given string segment is an HTML tag.
    
    Args:
        segment (str): String to check
        
    Returns:
        bool: True if segment is an HTML tag, False otherwise
    """
    return re.fullmatch(HTML_TAGS_PATTERN, segment) is not None

def process_body(body: str) -> str:
    """
    Process PR body text by removing HTML tags and special markers.
    
    Args:
        body (str): PR description body text
        
    Returns:
        str: Cleaned and processed body text
    """
    if not body:
        return ""
    
    # Remove HTML tags and clean up the text
    segments = [seg for seg in re.split(HTML_TAGS_PATTERN, body) if not is_html_tag(seg)]
    processed_body = "".join(segments)
    return processed_body.replace(">", "").replace("[!IMPORTANT]", "").strip()

def process_pr_data(pr_data: str) -> str:
    """
    Generate changelog entries from PR data.
    
    Args:
        pr_data (str): JSON string containing PR information
        
    Returns:
        str: Formatted changelog entries
    """
    prs: List[Dict[str, Any]] = json.loads(pr_data)
    
    # Use list comprehension with f-strings
    entries = [
        f"""- PR #{pr['number']}: {pr['title']}
            Author: {pr['author']}
            Body:
            {process_body(pr.get('body', ''))}
        """
        for pr in prs
    ]
    return "\n".join(entries)

def main(pr_data: str) -> None:
    """
    Main function to orchestrate changelog generation process.
    
    Args:
        pr_data (str): JSON string containing PR information
        
    Raises:
        Exception: If any step in the process fails
    """
    try:
        logging.info("Processing PR data...")
        processed_pr_data = process_pr_data(pr_data)
        
        logging.info("Running task...")
        final_changelog = run_task(processed_pr_data)
        
        logging.info("Saving changelog...")
        preserve_and_update_changelog(final_changelog)

        logging.info("Successfully saved changelog to CHANGELOG.md")

        # delete the pr_data.json file
        os.remove('pr_data.json')
        logging.info("Deleted pr_data.json file")
    except Exception as e:
        logging.error(f"Failed to generate changelog: {str(e)}")
        raise

# Script entry point
if __name__ == "__main__":
    try:
        # Read PR data from JSON file
        with open('pr_data.json', 'r') as file:
            pr_data = file.read()
        main(pr_data)
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        sys.exit(1)