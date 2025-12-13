from fastapi import APIRouter, HTTPException
import re
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["changelog"])


def is_meaningful_entry(entry: Dict[str, Any]) -> bool:
    """Filter out build commits and merge conflicts"""
    
    # Skip git merge conflicts
    if any(marker in entry.get('title', '') for marker in ['<<<<<<<', '=======', '>>>>>>>']):
        return False
    
    # Prioritize feature releases with highlights
    if entry.get('highlights'):
        return True
    
    # Skip entries with no files (after .pyc filtering)
    files = entry.get('files', [])
    if not files:
        return False
    
    # Skip if only .pyc files changed
    only_pyc = all('.pyc' in f or '__pycache__' in f for f in files)
    if only_pyc:
        return False
    
    return True


def parse_changelog(content: str) -> List[Dict[str, Any]]:
    """
    Parse CHANGELOG.md content into structured entries.
    
    Returns list of entries with:
    - date: The date/timestamp
    - title: Entry title (from header)
    - description: Summary of changes
    - highlights: List of key points (if available)
    - files: List of modified files
    """
    entries = []
    
    # Split by ## headers
    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    
    for section in sections[1:]:  # Skip first empty section
        if not section.strip():
            continue
        
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        # First line is the date/title
        header = lines[0].strip()
        
        # Skip merge conflict markers
        if any(marker in header for marker in ['<<<<<<<', '=======', '>>>>>>>']):
            continue
        
        entry = {
            "date": "",
            "title": "",
            "description": "",
            "highlights": [],
            "files": []
        }
        
        # Parse date and title from header
        # Supported formats:
        #   - "2025-12-10 22:22:32"
        #   - "2025-12-09 Feature Release: Loot Spots & Logging"
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)\s*(.*)', header)
        if date_match:
            entry["date"] = date_match.group(1).strip()
            title_part = date_match.group(2).strip()
            entry["title"] = title_part if title_part else "Update"
        else:
            entry["title"] = header
        
        # Parse content
        in_highlights = False
        in_files = False
        description_parts = []
        
        for line in lines[1:]:
            line = line.strip()
            
            # Skip merge conflict markers
            if any(marker in line for marker in ['<<<<<<<', '=======', '>>>>>>>']):
                continue
            
            if line.startswith("**Highlights:**"):
                in_highlights = True
                in_files = False
                continue
            elif line.startswith("**Modified:**") or line.startswith("**Wichtige Dateien:**"):
                in_files = True
                in_highlights = False
                continue
            elif line.startswith("**Files:**"):
                # Parse file count info
                description_parts.append(line.replace("**Files:**", "").strip())
                continue
            elif line.startswith("**"):
                in_highlights = False
                in_files = False
                continue
            
            if in_highlights and line.startswith("- "):
                highlight = line[2:].strip()
                # Skip file paths that are mistakenly in highlights section
                if highlight and not highlight.startswith('`'):
                    entry["highlights"].append(highlight)
            elif in_files and line.startswith("- "):
                # Handle multiple file formats:
                # - `file.py`
                # - `file1.py`, `file2.py`, Backend: `file3.py`
                line_content = line[2:].strip()
                
                # Extract all files wrapped in backticks
                file_matches = re.findall(r'`([^`]+)`', line_content)
                if file_matches:
                    entry["files"].extend(file_matches)
                else:
                    # Fallback: treat whole line as single file (strip backticks)
                    file_path = line_content.strip('`')
                    if file_path:
                        entry["files"].append(file_path)
            elif line and not in_files:
                description_parts.append(line)
        
        # Join description parts
        if description_parts:
            entry["description"] = " ".join(description_parts)
        
        # Filter out .pyc files from the file list
        entry["files"] = [f for f in entry["files"] if '.pyc' not in f and '__pycache__' not in f]
        
        # Only add meaningful entries
        if is_meaningful_entry(entry):
            entries.append(entry)
    
    return entries


def get_changelog_path() -> Path:
    """
    Get the changelog path with robust resolution for different deployment scenarios.
    
    Tries multiple methods:
    1. Environment variable CHANGELOG_PATH
    2. Relative to this file (Path(__file__).parent.parent.parent)
    3. Relative to current working directory
    """
    # Method 1: Check environment variable
    env_path = os.environ.get("CHANGELOG_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            logger.info(f"Using CHANGELOG_PATH from environment: {path}")
            return path
        else:
            logger.warning(f"CHANGELOG_PATH from environment does not exist: {path}")
    
    # Method 2: Relative to this file (standard location)
    try:
        file_path = Path(__file__).resolve().parent.parent.parent / "CHANGELOG.md"
        if file_path.exists():
            logger.debug(f"Found changelog at: {file_path}")
            return file_path
    except (AttributeError, OSError, RuntimeError) as e:
        logger.warning(f"Failed to resolve path relative to __file__: {e}")
    
    # Method 3: Relative to current working directory
    cwd_path = Path.cwd() / "CHANGELOG.md"
    if cwd_path.exists():
        logger.info(f"Found changelog in current working directory: {cwd_path}")
        return cwd_path
    
    # If we get here, file not found
    env_path_str = env_path if env_path else "None"
    logger.error(f"CHANGELOG.md not found. Tried: env_path={env_path_str}, __file__ relative, cwd={cwd_path}")
    raise FileNotFoundError("CHANGELOG.md not found in any expected location")


@router.get("/changelog")
async def get_changelog() -> List[Dict[str, Any]]:
    """
    Parse CHANGELOG.md and return structured changelog entries.
    
    Returns the last 15 meaningful entries (excluding .pyc only changes and merge conflicts).
    
    Returns:
    - 200: List of changelog entries (can be empty if no meaningful entries)
    - 404: CHANGELOG.md file not found
    - 500: Error parsing changelog
    """
    try:
        # Get changelog path with robust resolution
        changelog_path = get_changelog_path()
        logger.info(f"Reading changelog from: {changelog_path}")
        
        # Read file content
        try:
            with open(changelog_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except PermissionError as e:
            logger.error(f"Permission denied reading changelog: {e}")
            raise HTTPException(status_code=500, detail="Permission denied reading changelog")
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading changelog file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error reading changelog file")
        
        # Parse changelog entries
        try:
            entries = parse_changelog(content)
            logger.debug(f"Parsed {len(entries)} meaningful entries from changelog")
        except (ValueError, AttributeError, KeyError, IndexError) as e:
            # parse_changelog may raise these on malformed content
            logger.error(f"Error parsing changelog content: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error parsing changelog content")
        
        # Return last 15 meaningful entries (or empty array if none)
        result = entries[:15]
        
        if not result:
            logger.info("No meaningful entries found in changelog after filtering")
        
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Changelog file not found: {e}")
        raise HTTPException(status_code=404, detail="CHANGELOG.md not found")
    except HTTPException:
        # Re-raise HTTP exceptions from inner try blocks without wrapping them
        # This preserves the original status code and error message
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in get_changelog: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing changelog")
