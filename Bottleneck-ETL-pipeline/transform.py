# Fichier : transform.py
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("transform")

def verifier_colonnes(df, colonnes_requises, nom_fichier):
    manquantes = [col for col in colonnes_requises if col not in df.columns]
    if manquantes:
        log.error(f"Colonnes manquantes {manquantes} dans {nom_fichier}")
        return False
    return True

def clean_erp(df_erp):
    log.info("Nettoyage des données ERP...")
    if not verifier_colonnes(df_erp, ['product_id', 'price', 'stock_quantity'], "ERP.CSV"):
        return None
    df = df_erp.copy()
    df = df.drop_duplicates(subset=['product_id'])

    # ← Remplacement des virgules par des points avant conversion
    df['price'] = df['price'].astype(str).str.replace(',', '.', regex=False)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    df['purchase_price'] = df['purchase_price'].astype(str).str.replace(',', '.', regex=False)
    df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce')

    # ← Renommage pour éviter le conflit avec la colonne price du fichier web
    df = df.rename(columns={'price': 'price_erp', 'purchase_price': 'purchase_price_erp'})

    log.info(f"ERP nettoyé : {len(df)} lignes conservées")
    return df

def clean_web(df_web):
    log.info("Nettoyage des données Web...")
    if not verifier_colonnes(df_web, ['sku', 'total_sales'], "WEB.CSV"):
        return None
    df = df_web.copy()
    df = df.dropna(subset=['sku'])
    df = df.drop_duplicates(subset=['sku'])
    df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce').fillna(0)
    log.info(f"Web nettoyé : {len(df)} lignes conservées")
    return df

def merge_data(df_erp, df_web, df_liaison):
    log.info("Fusion des trois sources de données...")
    if not verifier_colonnes(df_liaison, ['product_id', 'id_web'], "LIAISON.CSV"):
        return None

    df_inter = pd.merge(df_erp, df_liaison, on='product_id', how='inner')
    df_final = pd.merge(df_inter, df_web, left_on='id_web', right_on='sku', how='inner')

    # ← Récupération du prix ERP quand le prix web est absent
    if 'price_erp' in df_final.columns:
        # ← 'price' n'existe pas dans web, on crée directement depuis price_erp
        df_final['price'] = df_final['price_erp']
        df_final['purchase_price'] = df_final['purchase_price_erp']
        df_final = df_final.drop(columns=['price_erp', 'purchase_price_erp'])

    log.info(f"Fusion terminée : {df_final.shape[0]} lignes, {df_final.shape[1]} colonnes")
    return df_final