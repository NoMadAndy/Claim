"""Service for managing player heatmap colors"""
import hashlib

# Predefined color palette for heatmaps (vibrant, distinct colors)
COLOR_PALETTE = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#FFA07A",  # Light Salmon
    "#98D8C8",  # Mint
    "#F7DC6F",  # Yellow
    "#BB8FCE",  # Purple
    "#85C1E2",  # Light Blue
    "#F8B88B",  # Peach
    "#76D7C4",  # Turquoise
    "#F6A192",  # Coral
    "#A8E6CF",  # Light Green
    "#FFD3B6",  # Light Orange
    "#FFAAA5",  # Light Red
    "#FF8B94",  # Pink
    "#A8D8EA",  # Light Sky Blue
    "#AA96DA",  # Lavender
    "#FCBAD3",  # Light Pink
    "#A1DE93",  # Light Green
    "#80D0C1",  # Aqua
]


def generate_color_for_user(user_id: int, username: str) -> str:
    """
    Generate a consistent, unique color for a user based on their ID and username.
    The same user always gets the same color.
    
    Args:
        user_id: User's database ID
        username: User's username
    
    Returns:
        Hex color string (e.g., "#FF6B6B")
    """
    # Combine user_id and username for consistent hashing
    hash_input = f"{user_id}_{username}".encode()
    hash_obj = hashlib.md5(hash_input)
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Use hash to select from palette
    color_index = hash_int % len(COLOR_PALETTE)
    return COLOR_PALETTE[color_index]


def get_user_color(user_id: int, username: str, stored_color: str = None) -> str:
    """
    Get the heatmap color for a user.
    If a color is already stored, return it (consistency).
    Otherwise, generate and return a new one.
    
    Args:
        user_id: User's database ID
        username: User's username
        stored_color: Color already stored in database (if any)
    
    Returns:
        Hex color string
    """
    if stored_color:
        return stored_color
    return generate_color_for_user(user_id, username)
