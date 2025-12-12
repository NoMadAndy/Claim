from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Tuple

from sqlalchemy.orm import Session

from app.models import UserBuff, get_cet_now


@dataclass(frozen=True)
class BuffModifiers:
    xp_multiplier: float = 1.0
    claim_multiplier: float = 1.0
    range_bonus_m: float = 0.0


def cleanup_expired_buffs(db: Session, user_id: int) -> int:
    """Delete expired buffs for a user. Returns number of deleted rows."""
    now = get_cet_now()
    deleted = (
        db.query(UserBuff)
        .filter(UserBuff.user_id == user_id, UserBuff.expires_at <= now)
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
    return int(deleted or 0)


def get_active_modifiers(db: Session, user_id: int) -> BuffModifiers:
    """Compute effective modifiers from all active buffs (expired ones are cleaned up)."""
    cleanup_expired_buffs(db, user_id)

    now = get_cet_now()
    buffs = (
        db.query(UserBuff)
        .filter(UserBuff.user_id == user_id, UserBuff.expires_at > now)
        .all()
    )

    xp_multiplier = 1.0
    claim_multiplier = 1.0
    range_bonus_m = 0.0

    for buff in buffs:
        try:
            xp_multiplier *= float(buff.xp_multiplier or 1.0)
            claim_multiplier *= float(buff.claim_multiplier or 1.0)
            range_bonus_m += float(buff.range_bonus_m or 0.0)
        except Exception:
            continue

    return BuffModifiers(
        xp_multiplier=xp_multiplier,
        claim_multiplier=claim_multiplier,
        range_bonus_m=range_bonus_m,
    )


def create_buff_from_item_effects(
    db: Session,
    *,
    user_id: int,
    xp_boost: float,
    claim_boost: float,
    range_boost: float,
    duration_seconds: int,
) -> UserBuff:
    """Create a new buff row based on item effect fields.

    xp_boost/claim_boost are interpreted as additive boosts (e.g. 0.5 => +50%).
    range_boost is additive meters.
    """
    now = get_cet_now()
    expires_at = now + timedelta(seconds=int(duration_seconds))

    buff = UserBuff(
        user_id=user_id,
        xp_multiplier=1.0 + float(xp_boost or 0.0),
        claim_multiplier=1.0 + float(claim_boost or 0.0),
        range_bonus_m=float(range_boost or 0.0),
        expires_at=expires_at,
    )

    db.add(buff)
    db.commit()
    db.refresh(buff)
    return buff
