"""Nettoyage et normalisation du texte extrait d'un CV (US-4.2, tâche 4)."""

import re
import unicodedata

# Caractères invisibles : largeur nulle, joiners, BOM, trait d'union conditionnel.
INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"))
# Caractères de contrôle, sauf le retour à la ligne et la tabulation.
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Zone d'usage privé : icônes des polices de modèles de CV (téléphone, courrier...).
PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")
# Puces de toutes sortes au début d'une ligne.
BULLET = re.compile(r"^[ \t]*[•●○◦▪■□▫‣⁃∙·➢➤➔►▶✓✔✗➜*]+[ \t]*", re.MULTILINE)
# Mot coupé par un trait d'union en fin de ligne : « dévelop-\npement ».
HYPHEN_BREAK = re.compile(r"(?<=[^\W\d_])-[ \t]*\n[ \t]*(?=[a-zà-ÿ])")
# Lettres espacées d'un titre de section : « C O M P É T E N C E S ».
SPACED_LETTERS = re.compile(r"(?<![^\W\d_])(?:[^\W\d_] ){3,}[^\W\d_](?![^\W\d_])")
# Numéro de page seul : « 2 », « Page 2 », « 2/3 », « Page 2 sur 3 ».
PAGE_NUMBER = re.compile(r"^\s*(?:page\s*)?\d{1,2}(?:\s*(?:/|sur|of)\s*\d{1,2})?\s*$", re.IGNORECASE)
MULTI_SPACES = re.compile(r"[ \t]{2,}")
MANY_NEWLINES = re.compile(r"\n{3,}")


def clean_text(raw: str) -> str:
    """Renvoie un texte propre, prêt à être envoyé au LLM."""
    # NFKC : ligatures « ﬁ » → « fi », espaces insécables → espaces normaux.
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(INVISIBLE)
    text = CONTROL.sub("", text)
    text = PRIVATE_USE.sub("", text)
    text = HYPHEN_BREAK.sub("", text)
    text = BULLET.sub("- ", text)
    text = SPACED_LETTERS.sub(lambda match: match.group(0).replace(" ", ""), text)

    lines = []
    for line in text.split("\n"):
        line = MULTI_SPACES.sub(" ", line.replace("\t", " ")).strip()
        if PAGE_NUMBER.match(line):
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = MANY_NEWLINES.sub("\n\n", text)
    return text.strip()
