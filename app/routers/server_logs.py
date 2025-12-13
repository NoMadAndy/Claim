from fastapi import APIRouter, HTTPException
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["server-logs"])


def get_log_file_path() -> Path:
    """
    Get the server log file path with robust resolution.
    
    Tries multiple methods in order:
    1. Environment variable SERVER_LOG_PATH
    2. Relative to app directory (app/../logs/client-debug.log)
    3. Relative to current working directory
    
    Returns:
        Path object pointing to the log file
        
    Raises:
        FileNotFoundError: If log file cannot be found
    """
    # Method 1: Check environment variable
    env_path = os.environ.get("SERVER_LOG_PATH")
    if env_path:
        try:
            path = Path(env_path).resolve()
            if path.exists() and path.is_file():
                logger.info(f"Using SERVER_LOG_PATH from environment: {path}")
                return path
            else:
                logger.warning(f"SERVER_LOG_PATH from environment does not exist: {path}")
        except (ValueError, OSError) as e:
            logger.warning(f"Invalid SERVER_LOG_PATH from environment: {env_path}, error: {e}")
    
    # Method 2: Relative to this file (standard location)
    # Structure: app/routers/server_logs.py -> .parent -> app/routers -> .parent -> app -> .parent -> root
    try:
        repo_root = Path(__file__).resolve().parents[2]  # Go up 2 levels from server_logs.py
        log_path = repo_root / "logs" / "client-debug.log"
        if log_path.exists():
            logger.debug(f"Found log file at: {log_path}")
            return log_path
    except (AttributeError, OSError, RuntimeError, IndexError) as e:
        logger.warning(f"Failed to resolve path relative to __file__: {e}")
    
    # Method 3: Relative to current working directory
    cwd_path = Path.cwd() / "logs" / "client-debug.log"
    if cwd_path.exists():
        logger.info(f"Found log file in current working directory: {cwd_path}")
        return cwd_path
    
    # If we get here, file not found (this is acceptable - logs may not exist yet)
    env_path_str = env_path if env_path else "None"
    logger.info(f"Log file not found. Tried: env_path={env_path_str}, __file__ relative, cwd={cwd_path}")
    raise FileNotFoundError("Log file not found in any expected location")


def read_tail_lines(file_path: Path, max_lines: int = 200, max_bytes: int = 100000) -> str:
    """
    Read the last N lines from a file safely.
    
    Args:
        file_path: Path to the log file
        max_lines: Maximum number of lines to return
        max_bytes: Maximum bytes to read from end of file
        
    Returns:
        String containing the last N lines
    """
    try:
        # Get file size
        file_size = file_path.stat().st_size
        
        # If file is empty, return empty string
        if file_size == 0:
            return ""
        
        # Limit how much we read from the end
        read_size = min(file_size, max_bytes)
        
        with open(file_path, 'rb') as f:
            # Seek to the position
            f.seek(max(0, file_size - read_size))
            
            # Read and decode
            content = f.read(read_size).decode('utf-8', errors='replace')
            
            # Split into lines and take last N
            lines = content.splitlines()
            
            # If we didn't start at the beginning, the first line might be partial
            if file_size > read_size and lines:
                lines = lines[1:]  # Skip potentially partial first line
            
            # Return last max_lines
            tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            return '\n'.join(tail_lines)
            
    except PermissionError as e:
        logger.error(f"Permission denied reading log file: {e}")
        raise
    except (IOError, OSError, UnicodeDecodeError) as e:
        logger.error(f"Error reading log file: {e}", exc_info=True)
        raise


@router.get("/server-logs")
async def get_server_logs() -> Dict[str, Any]:
    """
    Get recent server log lines from client-debug.log.
    
    Returns the last 200 lines of the log file (or fewer if file is smaller).
    If the log file doesn't exist yet, returns empty logs.
    
    Returns:
        Dictionary with:
        - logs: string containing log lines
        - line_count: number of lines returned
        - file_exists: whether the log file exists
        
    Status codes:
        - 200: Success (can have empty logs if file doesn't exist yet)
        - 500: Error reading log file
    """
    try:
        # Try to get log file path
        try:
            log_path = get_log_file_path()
            file_exists = True
        except FileNotFoundError:
            # Log file doesn't exist yet - this is normal on first startup
            logger.info("Log file doesn't exist yet")
            return {
                "logs": "",
                "line_count": 0,
                "file_exists": False,
                "message": "Log file not created yet. Make some client logs to see them here."
            }
        
        # Read log lines
        try:
            log_content = read_tail_lines(log_path, max_lines=200, max_bytes=100000)
            line_count = len(log_content.splitlines()) if log_content else 0
            
            logger.debug(f"Read {line_count} lines from log file")
            
            return {
                "logs": log_content,
                "line_count": line_count,
                "file_exists": file_exists
            }
            
        except PermissionError as e:
            logger.error(f"Permission denied reading log file: {e}")
            raise HTTPException(status_code=500, detail="Permission denied reading log file")
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading log file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error reading log file")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in get_server_logs: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error reading logs")
