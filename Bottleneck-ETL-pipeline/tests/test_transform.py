import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest
from transform import clean_erp, clean_web, merge_data

@pytest.fixture
def df_erp_valide():
    return pd.DataFrame({
        'product_id': [1, 2, 3],
        'price': [10.5, 20.0, 30.0],
        'stock_quantity': [100, 0, 50]
    })

@pytest.fixture
def df_web_valide():
    return pd.DataFrame({
        'sku': ['SKU001', 'SKU002', 'SKU003'],
        'total_sales': [5, 10, 0]
    })

@pytest.fixture
def df_liaison_valide():
    return pd.DataFrame({
        'product_id': [1, 2, 3],
        'id_web': ['SKU001', 'SKU002', 'SKU003']
    })

def test_clean_erp_supprime_doublons(df_erp_valide):
    df_avec_doublon = pd.concat([df_erp_valide, df_erp_valide.iloc[[0]]])
    df_clean = clean_erp(df_avec_doublon)
    assert len(df_clean) == 3

def test_clean_erp_colonnes_manquantes():
    df_incomplet = pd.DataFrame({'product_id': [1], 'price': [10.0]})
    resultat = clean_erp(df_incomplet)
    assert resultat is None

def test_clean_erp_prix_non_numerique():
    """Vérifie que les prix non numériques sont convertis en NaN."""
    df = pd.DataFrame({
        'product_id': [1, 2, 3],
        'price': ['abc', 20.0, 30.0],  # ← dtype string dès la création
        'stock_quantity': [100, 0, 50]
    })
    df_clean = clean_erp(df)
    assert pd.isna(df_clean.loc[0, 'price'])

def test_clean_web_supprime_sku_vides(df_web_valide):
    df_web_valide.loc[0, 'sku'] = None
    df_clean = clean_web(df_web_valide)
    assert len(df_clean) == 2

def test_clean_web_ventes_nulles_a_zero(df_web_valide):
    df_web_valide.loc[0, 'total_sales'] = None
    df_clean = clean_web(df_web_valide)
    assert df_clean.loc[0, 'total_sales'] == 0

def test_merge_data_taille_correcte(df_erp_valide, df_web_valide, df_liaison_valide):
    df_erp_clean = clean_erp(df_erp_valide)
    df_web_clean = clean_web(df_web_valide)
    df_merged = merge_data(df_erp_clean, df_web_clean, df_liaison_valide)
    assert df_merged is not None
    assert len(df_merged) == 3