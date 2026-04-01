import pytest
from number_to_letters import amount_to_letters

def test_integer_amounts():
    assert amount_to_letters(0) == "Zéro dirham"
    assert amount_to_letters(1) == "Un dirham"
    assert amount_to_letters(2) == "Deux dirhams"
    assert amount_to_letters(20) == "Vingt dirhams"
    assert amount_to_letters(80) == "Quatre-vingts dirhams"
    assert amount_to_letters(81) == "Quatre-vingt-un dirhams"
    assert amount_to_letters(100) == "Cent dirhams"
    assert amount_to_letters(200) == "Deux cents dirhams"
    assert amount_to_letters(1000) == "Mille dirhams"
    assert amount_to_letters(2000) == "Deux mille dirhams"
    assert amount_to_letters(1000000) == "Un million dirhams"
    assert amount_to_letters(2000000) == "Deux millions dirhams"

def test_decimal_amounts():
    assert amount_to_letters(10.50) == "Dix dirhams et cinquante centimes"
    assert amount_to_letters(100.01) == "Cent dirhams et un centime"
    assert amount_to_letters(0.25) == "Zéro dirham et vingt-cinq centimes"
    assert amount_to_letters(2.99) == "Deux dirhams et quatre-vingt-dix-neuf centimes"

def test_edge_cases():
    assert amount_to_letters(-10) == "Montant négatif invalide"
    assert amount_to_letters("invalid") == ""
    assert amount_to_letters(None) == ""
