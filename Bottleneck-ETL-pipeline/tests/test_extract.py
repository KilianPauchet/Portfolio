import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from extract import load_data

def test_chargement_fichier_valide(tmp_path):
    """Vérifie qu'un CSV valide est bien chargé."""
    fichier = tmp_path / "test.csv"
    fichier.write_text("product_id,price\n1,10.5\n2,20.0", encoding="utf-8")

    df = load_data(str(fichier))

    assert df is not None
    assert len(df) == 2
    assert "product_id" in df.columns

def test_chargement_fichier_inexistant():
    """Vérifie qu'un fichier inexistant retourne None."""
    df = load_data("fichier_qui_nexiste_pas.csv")
    assert df is None