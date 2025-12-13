from __future__ import annotations

import math
from typing import Tuple

from sqlalchemy.orm import Session

from app.models import GameSetting


DEFAULT_LEVEL_XP_BASE = 100
DEFAULT_LEVEL_XP_INCREMENT = 10


def _get_int_setting(db: Session, setting_name: str, default_value: int) -> int:
    setting = db.query(GameSetting).filter(
        GameSetting.setting_name == setting_name
    ).first()
    if not setting:
        return int(default_value)
    try:
        return int(setting.setting_value)
    except (TypeError, ValueError):
        return int(default_value)


def get_level_curve_params(db: Session) -> Tuple[int, int]:
    """Returns (base, increment) for the level curve.

    base: XP needed for the first level-up (Level 1 -> 2)
    increment: additional XP added per next level-up (linear increase)
    """
    base = _get_int_setting(db, "level_xp_base", DEFAULT_LEVEL_XP_BASE)
    inc = _get_int_setting(db, "level_xp_increment", DEFAULT_LEVEL_XP_INCREMENT)
    if base < 1:
        base = DEFAULT_LEVEL_XP_BASE
    if inc < 0:
        inc = 0
    return base, inc


def xp_required_for_level(level: int, base: int, inc: int) -> int:
    """Total XP required to reach the given level (Level 1 requires 0 XP)."""
    if level <= 1:
        return 0
    n = level - 1
    # Sum_{k=0..n-1} (base + inc*k) = n*base + inc*n*(n-1)/2
    return int(n * base + (inc * n * (n - 1)) // 2)


def level_from_xp(xp: int, base: int, inc: int) -> int:
    """Compute level from total XP using the configured curve."""
    try:
        xp_i = int(xp)
    except Exception:
        xp_i = 0
    if xp_i < 0:
        xp_i = 0

    if inc <= 0:
        return (xp_i // max(1, base)) + 1

    # Solve: inc*n^2 + (2*base - inc)*n - 2*xp = 0, where n = level-1
    a = float(inc)
    b = float(2 * base - inc)
    c = float(-2 * xp_i)
    disc = b * b - 4.0 * a * c
    if disc < 0:
        disc = 0.0
    n = int(math.floor((-b + math.sqrt(disc)) / (2.0 * a)))
    if n < 0:
        n = 0

    level = n + 1
    # Correct for any rounding edge-cases
    while xp_required_for_level(level + 1, base, inc) <= xp_i:
        level += 1
    while level > 1 and xp_required_for_level(level, base, inc) > xp_i:
        level -= 1
    return level


def xp_to_next_level(db: Session, xp: int, current_level: int) -> int:
    base, inc = get_level_curve_params(db)
    next_threshold = xp_required_for_level(max(1, int(current_level)) + 1, base, inc)
    try:
        xp_i = int(xp)
    except Exception:
        xp_i = 0
    remaining = next_threshold - xp_i
    if remaining < 0:
        return 0
    return int(remaining)
