import pytest

from app.services.text_cleaning import clean_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Profil \ufb01nancier et \ufb02exible",
            "Profil financier et flexible",
        ),  # ligatures
        ("Python\u00a0:\u00a0SQL", "Python : SQL"),  # espaces insécables
        ("Do\u200bcker", "Docker"),  # espace de largeur nulle
        ("dévelop\u00adpement", "développement"),  # trait d'union conditionnel
        (
            "Ingénieur dévelop-\npement",
            "Ingénieur développement",
        ),  # césure en fin de ligne
        ("Saint-\nEtienne", "Saint-\nEtienne"),  # majuscule : trait d'union conservé
        ("• Python\n●  SQL\n▪ Docker", "- Python\n- SQL\n- Docker"),  # puces
        (
            "\uf095 06 12 34 56 78\n\uf0e0 roua@example.com",
            "06 12 34 56 78\nroua@example.com",
        ),
        ("C O M P É T E N C E S\nPython", "COMPÉTENCES\nPython"),  # lettres espacées
        (
            "Je maitrise R et C et A B",
            "Je maitrise R et C et A B",
        ),  # pas de faux positif
        (
            "Expérience\n1\nPage 2 sur 3\n2/3\nSuite",
            "Expérience\nSuite",
        ),  # numéros de page
        ("2024\nIngénieur", "2024\nIngénieur"),  # une année n'est pas un numéro de page
        ("Python     SQL\t\tDocker   ", "Python SQL Docker"),  # espaces multiples
        ("A\n\n\n\n\nB", "A\n\nB"),  # lignes vides en excès
        ("A\r\nB\rC", "A\nB\nC"),  # fins de ligne Windows et Mac
        ("A\x00B\x07C", "ABC"),  # caractères de contrôle
        (
            "https://github.com/RouaBenTiba",
            "https://github.com/RouaBenTiba",
        ),  # URL intacte
        ("  \n \n", ""),
    ],
)
def test_clean_text(raw: str, expected: str) -> None:
    assert clean_text(raw) == expected


def test_clean_text_is_idempotent() -> None:
    raw = "• Dévelop-\npement\u00a0Python\n\n\n\nPage 1/2\nC O M P É T E N C E S"
    once = clean_text(raw)
    assert clean_text(once) == once
