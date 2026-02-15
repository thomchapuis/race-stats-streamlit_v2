SPORT_ICONS = {
    "Trail": "🏔️",
    "Running": "🏃‍♂️",
    "Cyclisme": "🚴‍♂️",
    "Triathlon": "🏊‍♂️🚴‍♂️🏃‍♂️"
}

def sport_icon(sport):
    """Retourne l'icône correspondant au sport ou un drapeau par défaut."""
    return SPORT_ICONS.get(sport, "🏁")
