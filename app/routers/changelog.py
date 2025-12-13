from fastapi import APIRouter, HTTPException
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api", tags=["changelog"])


def is_meaningful_entry(entry: Dict[str, Any]) -> bool:
    """
    Determine if a changelog entry is meaningful (not just .pyc or merge conflicts).
    
    Returns True if:
    - Entry has highlights (feature release)
    - Entry modifies non-.pyc files
    - Entry modifies multiple files
    """
    # Check if it's a feature release with highlights
    if entry.get("highlights"):
        return True
    
    # Check modified files
    files = entry.get("files", [])
    if not files:
        return False
    
    # Filter out .pyc files
    non_pyc_files = [f for f in files if not f.endswith(".pyc")]
    
    # Meaningful if has non-.pyc files
    if non_pyc_files:
        return True
    
    return False


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
        # Format can be:
        # "2025-12-10 22:22:32" or
        # "2025-12-09 Feature Release: Loot Spots & Logging"
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
                entry["highlights"].append(line[2:].strip())
            elif in_files and line.startswith("- "):
                file_path = line[2:].strip().strip('`')
                entry["files"].append(file_path)
            elif line and not in_files:
                description_parts.append(line)
        
        # Join description parts
        if description_parts:
            entry["description"] = " ".join(description_parts)
        
        # Only add meaningful entries
        if is_meaningful_entry(entry):
            entries.append(entry)
    
    return entries


@router.get("/changelog")
async def get_changelog() -> List[Dict[str, Any]]:
    """
    Parse CHANGELOG.md and return structured changelog entries.
    
    Returns the last 15 meaningful entries (excluding .pyc only changes and merge conflicts).
    """
    try:
        changelog_path = Path(__file__).parent.parent.parent / "CHANGELOG.md"
        
        if not changelog_path.exists():
            raise HTTPException(status_code=404, detail="Changelog not found")
        
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse changelog entries
        entries = parse_changelog(content)
        
        # Return last 15 meaningful entries
        return entries[:15]
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Changelog file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading changelog: {str(e)}")
