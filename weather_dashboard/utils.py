def degrees_to_compass(degrees: float) -> str:
    arrows = ["↑", "↗", "↗", "→", "→", "→", "↘", "↓", "↓", "↙", "↙", "←", "←", "←", "↖", "↑"]
    return arrows[round(degrees / 22.5) % 16]