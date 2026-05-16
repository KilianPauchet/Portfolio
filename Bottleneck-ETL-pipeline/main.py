# Fichier : main.py
import sys
import os
from dotenv import load_dotenv
import argparse

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import get_logger
from extract import load_data
from transform import clean_erp, clean_web, merge_data
from analyse import (
    nettoyer_donnees_finales, analyser_ca,
    detecter_outliers, detecter_outliers_zscore,
    analyser_pareto_ca, analyser_pareto_quantite,
    analyser_marges, analyser_stocks,
    generer_visuels, afficher_recommandations
)
from database import upload_to_mysql

log = get_logger("main")

def main():
    parser = argparse.ArgumentParser(description="Pipeline d'analyse Bottleneck")
    parser.add_argument("--erp", default="./DATA/erp.csv")
    parser.add_argument("--web", default="./DATA/web.csv")
    parser.add_argument("--liaison", default="./DATA/liaison.csv")
    args = parser.parse_args()

    log.info("=== DÉBUT DU PIPELINE ===")

    # 1. EXTRACTION
    df_erp_raw = load_data(args.erp)
    df_web_raw = load_data(args.web)
    df_liaison_raw = load_data(args.liaison)

    if df_erp_raw is None or df_web_raw is None or df_liaison_raw is None:
        log.error("Arrêt : fichiers sources manquants")
        return

    # 2. TRANSFORMATION
    df_erp_clean = clean_erp(df_erp_raw)
    df_web_clean = clean_web(df_web_raw)

    if df_erp_clean is None or df_web_clean is None:
        log.error("Arrêt : données sources non conformes")
        return

    df_merged = merge_data(df_erp_clean, df_web_clean, df_liaison_raw)
    if df_merged is None:
        return
    
    # 3. NETTOYAGE FINAL
    df = nettoyer_donnees_finales(df_merged)

    # 4. ANALYSES
    df, ca_total         = analyser_ca(df)
    outliers, seuil      = detecter_outliers(df)
    df, outliers_z, _    = detecter_outliers_zscore(df)
    df_pareto_ca, n80_ca, pct_ca   = analyser_pareto_ca(df)
    df_pareto_qty, n80_qty, pct_qty = analyser_pareto_quantite(df)
    df                   = analyser_marges(df)
    df, nb_mois          = analyser_stocks(df)

    # 5. GRAPHIQUES
    generer_visuels(
        df=df,
        outliers=outliers,
        seuil_haut=seuil,
        df_pareto_ca=df_pareto_ca,
        df_pareto_qtv=df_pareto_qty,
        nombre_articles_80_ca=n80_ca,
        nombre_articles_80_qty=n80_qty,
        proportion_ca=pct_ca,
        proportion_qty=pct_qty,
        nb_mois=nb_mois
    )

    # 6. BILAN
    afficher_recommandations(df, ca_total, outliers)

    # 7. EXPORT
    df.to_csv("./DATA/dataset_final_propre.csv", index=False)
    log.info("Dataset exporté → ./DATA/dataset_final_propre.csv")

    # 8. BASE DE DONNÉES
    upload_to_mysql(
        df=df,
        table_name="analyse_bottleneck",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME")
    )

    log.info("=== PIPELINE TERMINÉ AVEC SUCCÈS ===")

if __name__ == "__main__":
    main()