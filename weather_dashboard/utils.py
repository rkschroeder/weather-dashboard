def degrees_to_compass(degrees: float) -> str:
    arrows = ["↑", "↗", "↗", "→", "→", "→", "↘", "↓", "↓", "↙", "↙", "←", "←", "←", "↖", "↑"]
    return arrows[round(degrees / 22.5) % 16]


def format_relative_time(timestamp: str) -> str:
    """Formats a SQLite `datetime('now')`-style UTC string (e.g. '2024-01-01 10:00:00')
    as a short relative label like '5m ago', for the Recent Cities sidebar list."""
    if not timestamp:
        return ""
    from datetime import datetime, timezone

    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return ""

    seconds = max((datetime.now(timezone.utc) - dt).total_seconds(), 0)
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago"
    days = int(hours // 24)
    return f"{days}d ago"