"""Convert datetimes to the naive UTC format required by Odoo Climate Monitor API."""

from datetime import datetime, timezone

ODOO_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def to_odoo_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime(ODOO_DATETIME_FMT)


def parse_device_timestamp(value: object) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    text = str(value).strip()
    if not text:
        raise ValueError("empty timestamp")

    if "T" in text or text.endswith("Z"):
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    dt = datetime.strptime(text, ODOO_DATETIME_FMT)
    return dt.replace(tzinfo=timezone.utc)
