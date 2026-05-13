# -*- coding: utf-8 -*-

dico = {
    # Majuscules
    "Α": "A",
    "Β": "B",
    "Γ": "G",
    "Δ": "D",
    "Ε": "E",
    "Ζ": "Z",
    "Η": "U",
    "Θ": "H",
    "Ι": "I",
    "Κ": "K",
    "Λ": "L",
    "Μ": "M",
    "Ν": "N",
    "Ξ": "X",
    "Ο": "O",
    "Π": "P",
    "Ρ": "R",
    "Σ": "S",
    "Τ": "T",
    "Υ": "Y",
    "Φ": "F",
    "Χ": "Q",
    "Ψ": "C",
    "Ω": "W",

    # Minuscules
    "α": "a",
    "β": "b",
    "γ": "g",
    "δ": "d",
    "ε": "e",
    "ζ": "z",
    "η": "u",
    "θ": "H",
    "ι": "i",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "x",
    "ο": "o",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "~",
    "τ": "t",
    "υ": "y",
    "φ": "f",
    "χ": "q",
    "ψ": "c",
    "ω": "w",
}

import unicodedata


def enlever_accents(texte):
    texte_normalise = unicodedata.normalize("NFD", texte)

    return "".join(
        c for c in texte_normalise
        if unicodedata.category(c) != "Mn"
    )

def grec_vers_font(texte):
    texte = enlever_accents(texte)
    resultat = ""

    for caractere in texte:
        resultat += dico.get(caractere, caractere)

    return resultat