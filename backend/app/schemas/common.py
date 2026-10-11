def dedupe(values: list[str]) -> list[str]:
    """Supprime les doublons (sans tenir compte de la casse) en gardant l'ordre."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result