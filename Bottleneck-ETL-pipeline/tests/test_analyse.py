import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest
from analyse import nettoyer_donnees_finales, analyser_ca, detecter_outliers

@pytest.fixture
def df_analyse():
    return pd.DataFrame({
        'product_id': [1, 2, 3, 4],
        'price': [10.0, 20.0, 500.0, 15.0],
        'total_sales': [5, 10, 2, 0],
        'stock_quantity': [-5, 10, 3, 0],
        'stock_status': ['instock', 'instock', 'instock', 'instock']
    })

def test_stocks_negatifs_remis_a_zero(df_analyse):
    df_clean = nettoyer_donnees_finales(df_analyse)
    assert df_clean['stock_quantity'].min() >= 0

def test_statut_stock_synchronise(df_analyse):
    df_clean = nettoyer_donnees_finales(df_analyse)
    produits_zero = df_clean[df_clean['stock_quantity'] == 0]
    assert (produits_zero['stock_status'] == 'outofstock').all()

def test_ca_calcul_correct(df_analyse):
    df_clean = nettoyer_donnees_finales(df_analyse)
    df_ca, ca_total = analyser_ca(df_clean)
    # CA attendu : (10*5) + (20*10) + (500*2) + (15*0) = 1250
    assert ca_total == 1250.0

def test_detecter_outliers_trouve_haut_de_gamme(df_analyse):
    df_clean = nettoyer_donnees_finales(df_analyse)
    df_ca, _ = analyser_ca(df_clean)
    outliers, seuil = detecter_outliers(df_ca)
    assert 500.0 in outliers['price'].values