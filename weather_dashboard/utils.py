def degrees_to_compass(degrees: float) -> str:
    directions = [
        ("N", "↓"), ("NNE", "↙"), ("NE", "↙"), ("ENE", "←"),
        ("E", "←"), ("ESE", "←"), ("SE", "↖"), ("SSE", "↑"),
        ("S", "↑"), ("SSW", "↗"), ("SW", "↗"), ("WSW", "→"),
        ("W", "→"), ("WNW", "→"), ("NW", "↘"), ("NNW", "↓"),
    ]
    label, arrow = directions[round(degrees / 22.5) % 16]
    return f"{arrow} {label}"