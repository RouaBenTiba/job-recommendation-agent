from app.services.pdf_layout import Block, order_blocks

PAGE_WIDTH = 595.0


def order(blocks: list[Block]) -> list[str]:
    return [block.text for block in order_blocks(blocks, PAGE_WIDTH)]


def test_single_column_is_read_top_to_bottom() -> None:
    blocks = [
        Block(50, 200, 500, 230, "C"),
        Block(50, 100, 540, 130, "A"),
        Block(50, 150, 540, 180, "B"),
    ]
    assert order(blocks) == ["A", "B", "C"]


def test_sidebar_is_read_before_the_main_column() -> None:
    blocks = [
        Block(30, 30, 565, 70, "NOM"),
        Block(30, 100, 170, 140, "CONTACT"),
        Block(30, 260, 170, 320, "COMPETENCES"),
        Block(200, 110, 560, 170, "EXPERIENCE"),
        Block(200, 300, 560, 360, "FORMATION"),
    ]
    assert order(blocks) == ["NOM", "CONTACT", "COMPETENCES", "EXPERIENCE", "FORMATION"]


def test_two_equal_columns_are_read_one_after_the_other() -> None:
    blocks = [
        Block(40, 100, 280, 300, "L1"),
        Block(40, 330, 280, 600, "L2"),
        Block(320, 120, 555, 310, "R1"),
        Block(320, 340, 555, 600, "R2"),
    ]
    assert order(blocks) == ["L1", "L2", "R1", "R2"]


def test_three_columns() -> None:
    blocks = [
        Block(30, 100, 180, 300, "A1"),
        Block(30, 330, 180, 600, "A2"),
        Block(220, 120, 370, 310, "B1"),
        Block(220, 345, 370, 600, "B2"),
        Block(410, 105, 565, 320, "C1"),
        Block(410, 350, 565, 600, "C2"),
    ]
    assert order(blocks) == ["A1", "A2", "B1", "B2", "C1", "C2"]


def test_row_aligned_layout_is_read_line_by_line() -> None:
    # Dates à gauche, descriptions à droite : on lit « date puis description ».
    blocks = [
        Block(40, 100, 120, 112, "2022-2024"),
        Block(150, 100, 550, 160, "Acme"),
        Block(40, 200, 120, 212, "2020-2022"),
        Block(150, 200, 550, 260, "Beta"),
        Block(40, 300, 120, 312, "2018-2020"),
        Block(150, 300, 550, 360, "Gamma"),
    ]
    assert order(blocks) == [
        "2022-2024",
        "Acme",
        "2020-2022",
        "Beta",
        "2018-2020",
        "Gamma",
    ]


def test_centered_title_above_two_columns_comes_first() -> None:
    blocks = [
        Block(150, 30, 450, 60, "NOM"),
        Block(30, 100, 270, 400, "LEFT-1"),
        Block(30, 430, 270, 700, "LEFT-2"),
        Block(320, 110, 565, 380, "RIGHT-1"),
        Block(320, 410, 565, 700, "RIGHT-2"),
    ]
    assert order(blocks) == ["NOM", "LEFT-1", "LEFT-2", "RIGHT-1", "RIGHT-2"]


def test_small_page_number_does_not_hide_the_columns() -> None:
    blocks = [
        Block(30, 100, 170, 400, "SIDE-1"),
        Block(30, 430, 170, 700, "SIDE-2"),
        Block(200, 110, 560, 380, "MAIN-1"),
        Block(200, 410, 560, 700, "MAIN-2"),
        Block(285, 800, 315, 812, "1/2"),
    ]
    assert order(blocks) == ["SIDE-1", "SIDE-2", "MAIN-1", "MAIN-2", "1/2"]


def test_empty_blocks_are_ignored() -> None:
    assert order([Block(0, 0, 10, 10, "   "), Block(0, 20, 10, 30, "A")]) == ["A"]
    assert order([]) == []
