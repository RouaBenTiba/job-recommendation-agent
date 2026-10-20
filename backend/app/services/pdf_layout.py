"""Ordre de lecture des blocs de texte d'une page (US-4.2, tâche 2).

Un CV a souvent une colonne latérale (contacts, compétences) et une colonne
principale. Lu de haut en bas, le texte mélange les deux. On détecte les colonnes,
puis on lit chaque colonne en entier. Les titres pleine largeur coupent la page en
sections lues dans l'ordre.
"""

from dataclasses import dataclass

# Un bloc plus large que cette part de la page (titre) coupe la page en sections.
# Plus de 0,75 : la colonne principale d'un CV à colonne latérale reste en dessous.
FULL_WIDTH_RATIO = 0.75
# Un bloc qui déborde d'au moins 6 points de chaque côté d'une gouttière la traverse.
SPAN_MARGIN = 6.0
# Une zone verticale est « vide » si moins de 15 % du texte (en hauteur) la recouvre :
# un titre ou un numéro de page peut déborder sur la gouttière sans la masquer.
EMPTY_COVERAGE_RATIO = 0.15
# Une gouttière (espace entre colonnes) fait au moins 2 % de la largeur de la page.
MIN_GUTTER_RATIO = 0.02
# Deux blocs sont sur la même ligne si leur haut diffère de moins de 4 points.
ROW_TOLERANCE = 4.0
# Si 60 % des blocs de la plus petite colonne ont un voisin de ligne : tableau.
ROW_ALIGNED_RATIO = 0.6
SLOTS = 200


@dataclass(frozen=True)
class Block:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return max(self.y1 - self.y0, 1.0)

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2


def order_blocks(blocks: list[Block], page_width: float) -> list[Block]:
    """Renvoie les blocs dans l'ordre de lecture."""
    usable = sorted((b for b in blocks if b.text.strip()), key=lambda b: (b.y0, b.x0))
    narrow = [b for b in usable if b.width < FULL_WIDTH_RATIO * page_width]
    page_cuts = _find_gutters(narrow, page_width) if len(narrow) >= 2 else []

    def is_separator(block: Block) -> bool:
        if block.width >= FULL_WIDTH_RATIO * page_width:
            return True
        # Un titre centré qui passe au-dessus de deux colonnes les sépare aussi.
        return any(block.x0 < cut - SPAN_MARGIN and block.x1 > cut + SPAN_MARGIN for cut in page_cuts)

    ordered: list[Block] = []
    group: list[Block] = []
    for block in usable:
        if is_separator(block):
            ordered.extend(_order_group(group, page_width))
            group = []
            ordered.append(block)
        else:
            group.append(block)
    ordered.extend(_order_group(group, page_width))
    return ordered


def _top_to_bottom(blocks: list[Block]) -> list[Block]:
    return sorted(blocks, key=lambda b: (b.y0, b.x0))


def _order_group(group: list[Block], page_width: float) -> list[Block]:
    if len(group) < 2:
        return _top_to_bottom(group)
    cuts = _find_gutters(group, page_width)
    if not cuts:
        return _top_to_bottom(group)
    columns = _split_columns(group, cuts)
    if len(columns) < 2:
        return _top_to_bottom(group)
    if _rows_are_aligned(columns):
        # Tableau (date | description) : on lit ligne par ligne.
        return _row_order(group)
    return [block for column in columns for block in column]


def _find_gutters(group: list[Block], page_width: float) -> list[float]:
    """Positions (en x) des espaces verticaux vides entre deux zones de texte."""
    total_height = sum(block.height for block in group)
    slot_width = page_width / SLOTS
    weights = [0.0] * SLOTS
    for block in group:
        first = max(0, int(block.x0 / slot_width))
        last = min(SLOTS - 1, int(block.x1 / slot_width))
        for slot in range(first, last + 1):
            weights[slot] += block.height
    empty = [weight < EMPTY_COVERAGE_RATIO * total_height for weight in weights]
    covered = [index for index, is_empty in enumerate(empty) if not is_empty]
    if not covered:
        return []

    cuts: list[float] = []
    index, end = covered[0], covered[-1]
    while index <= end:
        if not empty[index]:
            index += 1
            continue
        stop = index
        while stop <= end and empty[stop]:
            stop += 1
        if (stop - index) * slot_width >= MIN_GUTTER_RATIO * page_width:
            cuts.append(((index + stop) / 2) * slot_width)
        index = stop
    return cuts


def _split_columns(group: list[Block], cuts: list[float]) -> list[list[Block]]:
    columns: list[list[Block]] = [[] for _ in range(len(cuts) + 1)]
    for block in group:
        columns[sum(1 for cut in cuts if block.center_x > cut)].append(block)
    return [_top_to_bottom(column) for column in columns if column]


def _rows_are_aligned(columns: list[list[Block]]) -> bool:
    """Vrai si les colonnes forment un tableau (blocs alignés ligne à ligne)."""
    smallest = min(columns, key=len)
    if len(smallest) < 2:
        return False
    others = [block for column in columns if column is not smallest for block in column]
    aligned = sum(1 for block in smallest if any(abs(block.y0 - other.y0) <= ROW_TOLERANCE for other in others))
    return aligned / len(smallest) >= ROW_ALIGNED_RATIO


def _row_order(group: list[Block]) -> list[Block]:
    rows: list[list[Block]] = []
    for block in _top_to_bottom(group):
        if rows and abs(block.y0 - rows[-1][0].y0) <= ROW_TOLERANCE:
            rows[-1].append(block)
        else:
            rows.append([block])
    return [block for row in rows for block in sorted(row, key=lambda b: b.x0)]
