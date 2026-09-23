from __future__ import annotations

import base64
import uuid
from datetime import datetime

from sentinelai.platform.errors import ValidationError


def encode_cursor(recorded_at: datetime, id: uuid.UUID) -> str:
    """Opaque keyset cursor: the sort key of the last row returned. Clients
    treat it as a token, never construct or parse it themselves."""
    raw = f"{recorded_at.isoformat()}|{id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """A cursor is opaque to clients but still attacker/typo-controlled
    input — validate it like any other input rather than let a malformed
    one surface as an unhandled 500."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        recorded_at_str, id_str = raw.split("|", 1)
        return datetime.fromisoformat(recorded_at_str), uuid.UUID(id_str)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValidationError("invalid pagination cursor") from exc
