# Fichier : analyse.py
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("analyse")

# Dossier de sortie pour les graphiques
os.makedirs("./OUTPUTS", exist_ok=True)


# ============================================================
# NETTOYAGE FINAL
# ============================================================

def nettoyer_donnees_finales(df):
    """Applique les corrections de nettoyage identifiées dans le notebook."""
    df = df.copy()
    df.loc[df['stock_quantity'] < 0, 'stock_quantity'] = 0
    df['stock_status'] = np.where(df['stock_quantity'] == 0, 'outofstock', 'instock')
    if 'post_date' in df.columns:
        df['post_date'] = pd.to_datetime(df['post_date'], errors='coerce')
    df['total_sales'] = df['total_sales'].abs()
    log.info("Nettoyage final appliqué (stocks négatifs, statuts, dates)")
    return df


# ============================================================
# 1. CHIFFRE D'AFFAIRES
# ============================================================

def analyser_ca(df):
    """Calcule le CA par produit et global."""
    log.info("--- ANALYSE DU CHIFFRE D'AFFAIRES ---")
    df = df.copy()
    df['ca_produit'] = df['price'] * df['total_sales']
    ca_total = df['ca_produit'].sum()
    log.info(f"Chiffre d'affaires total : {ca_total:,.2f} €")
    return df, ca_total


# ============================================================
# 2. OUTLIERS (IQR + Z-SCORE)
# ============================================================

def detecter_outliers(df):
    """Détecte les outliers par méthode IQR."""
    log.info("--- OUTLIERS MÉTHODE IQR ---")
    q1 = df['price'].quantile(0.25)
    q3 = df['price'].quantile(0.75)
    iqr = q3 - q1
    seuil_haut = q3 + 1.5 * iqr
    outliers = df[df['price'] > seuil_haut]
    log.info(f"Outliers IQR (prix > {seuil_haut:.2f}€) : {len(outliers)} produits")
    return outliers, seuil_haut


def detecter_outliers_zscore(df, seuil=3):
    """Détecte les outliers par méthode Z-score."""
    log.info("--- OUTLIERS MÉTHODE Z-SCORE ---")
    df = df.copy()
    prix_moy = df['price'].mean()
    ecart_type = df['price'].std()
    df['z_score'] = (df['price'] - prix_moy) / ecart_type

    seuil_z = prix_moy + (seuil * ecart_type)
    outliers_z = df[df['z_score'] > seuil]

    log.info(f"Moyenne prix : {prix_moy:.2f} € | Écart-type : {ecart_type:.2f} €")
    log.info(f"Seuil Z-score={seuil} : {seuil_z:.2f} € → {len(outliers_z)} outliers détectés")

    if 'post_title' in df.columns:
        cols = ['product_id', 'post_title', 'price', 'z_score']
    else:
        cols = ['product_id', 'price', 'z_score']

    log.info("Liste des outliers (Z-score > 3) :")
    for _, row in outliers_z[cols].sort_values('z_score', ascending=False).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    return df, outliers_z, seuil_z


# ============================================================
# 3. ANALYSE DE PARETO (CA + QUANTITÉ)
# ============================================================

def analyser_pareto_ca(df):
    """Analyse de Pareto sur le chiffre d'affaires."""
    log.info("--- PARETO CA ---")
    df_pareto = df[df['ca_produit'] > 0].sort_values('ca_produit', ascending=False).copy()
    ca_total = df_pareto['ca_produit'].sum()
    df_pareto['part_ca'] = df_pareto['ca_produit'] / ca_total
    df_pareto['ca_cumsum'] = df_pareto['part_ca'].cumsum()

    top_80 = df_pareto[df_pareto['ca_cumsum'] <= 0.8]
    nombre_articles_80 = len(top_80) + 1
    proportion = (nombre_articles_80 / len(df)) * 100

    log.info(f"Pareto CA : {nombre_articles_80} articles ({proportion:.2f}%) génèrent 80% du CA")
    return df_pareto, nombre_articles_80, proportion


def analyser_pareto_quantite(df):
    """Analyse de Pareto sur les quantités vendues."""
    log.info("--- PARETO QUANTITÉS ---")
    df_pareto = df[df['total_sales'] > 0].sort_values('total_sales', ascending=False).copy()
    total_ventes = df_pareto['total_sales'].sum()
    df_pareto['part_ventes'] = df_pareto['total_sales'] / total_ventes
    df_pareto['ventes_cumsum'] = df_pareto['part_ventes'].cumsum()

    top_80 = df_pareto[df_pareto['ventes_cumsum'] <= 0.8]
    nombre_articles_80 = len(top_80) + 1
    proportion = (nombre_articles_80 / len(df)) * 100

    log.info(f"Pareto QTÉ : {nombre_articles_80} articles ({proportion:.2f}%) représentent 80% des ventes")

    cols = ['product_id', 'post_title', 'price', 'total_sales'] if 'post_title' in df.columns else ['product_id', 'price', 'total_sales']
    log.info("Top 20 des produits par Quantité Vendue :")
    for _, row in df_pareto[cols].head(20).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    return df_pareto, nombre_articles_80, proportion


# ============================================================
# 4. ANALYSE DES MARGES
# ============================================================

def analyser_marges(df):
    """Calcule et analyse les taux de marge par produit."""
    log.info("--- ANALYSE DES MARGES ---")

    if 'purchase_price' not in df.columns:
        log.warning("Colonne 'purchase_price' absente — analyse des marges ignorée")
        return df

    df = df.copy()
    # ← Conversion forcée en numérique pour éviter les erreurs de type
    df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['taux_marge'] = ((df['price'] - df['purchase_price']) / df['price']) * 100

    marge_moy = df['taux_marge'].mean()
    log.info(f"Taux de marge moyen : {marge_moy:.2f}%")

    cols = ['post_title', 'price', 'purchase_price', 'taux_marge'] if 'post_title' in df.columns else ['product_id', 'price', 'purchase_price', 'taux_marge']

    log.info("Top 20 des produits les PLUS rentables :")
    for _, row in df[cols].sort_values('taux_marge', ascending=False).head(20).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    log.info("Top 20 des produits les MOINS rentables :")
    for _, row in df[cols].sort_values('taux_marge', ascending=True).head(20).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    return df


# ============================================================
# 5. ANALYSE DES STOCKS (COUVERTURE EN MOIS)
# ============================================================

def analyser_stocks(df):
    """Calcule la couverture de stock en mois pour chaque produit."""
    log.info("--- ANALYSE DES STOCKS ---")
    df = df.copy()

    if 'post_date' not in df.columns:
        log.warning("Colonne 'post_date' absente — période calculée sur 12 mois par défaut")
        nb_mois = 12
    else:
        date_min = df['post_date'].min()
        date_max = df['post_date'].max()
        nb_mois = (date_max - date_min).days / 30.44
        log.info(f"Période analysée : {nb_mois:.1f} mois")

    df['ventes_mensuelles'] = df['total_sales'] / nb_mois
    df['mois_de_stock'] = df.apply(
        lambda x: x['stock_quantity'] / x['ventes_mensuelles'] if x['ventes_mensuelles'] > 0 else np.inf,
        axis=1
    )
    df['mois_de_stock'] = df['mois_de_stock'].replace([np.inf, -np.inf], -1)

    df_actifs = df[df['total_sales'] > 0].copy()
    cols = ['post_title', 'stock_quantity', 'total_sales', 'ventes_mensuelles', 'mois_de_stock'] if 'post_title' in df.columns else ['product_id', 'stock_quantity', 'total_sales', 'mois_de_stock']

    log.info("Top 5 des produits avec le plus de stock dormant (hors ventes nulles) :")
    for _, row in df_actifs[cols].sort_values('mois_de_stock', ascending=False).head(5).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    log.info("Top 20 des produits avec le plus gros stock dormant :")
    for _, row in df_actifs[cols].sort_values('mois_de_stock', ascending=False).head(20).iterrows():
        log.info("  " + " | ".join(f"{col}: {row[col]}" for col in cols))

    return df, nb_mois


# ============================================================
# 6. GRAPHIQUES
# ============================================================

def generer_visuels(df, outliers, seuil_haut, df_pareto_ca=None, df_pareto_qtv=None,
                    nombre_articles_80_ca=None, nombre_articles_80_qty=None,
                    proportion_ca=None, proportion_qty=None, nb_mois=12):
    """Génère tous les graphiques d'analyse."""

    # --- Graphique 1 : Dispersion Prix vs Ventes (IQR) ---
    plt.figure(figsize=(12, 6))
    plt.scatter(df['price'], df['total_sales'], alpha=0.5, label='Produits standards')
    plt.scatter(outliers['price'], outliers['total_sales'], color='red', label='Outliers')
    plt.axvline(seuil_haut, color='orange', linestyle='--', label='Seuil Outlier IQR')
    plt.title("Dispersion des ventes par prix")
    plt.xlabel("Prix (€)")
    plt.ylabel("Nombre de ventes")
    plt.legend()
    plt.savefig('./OUTPUTS/analyse_prix_outliers.png', dpi=150, bbox_inches='tight')
    plt.close()
    log.info("Graphique 'analyse_prix_outliers.png' sauvegardé")

    # --- Graphique 2 : Boxplot des prix ---
    plt.figure(figsize=(10, 4))
    plt.boxplot(df['price'].dropna(), vert=False, patch_artist=True,
                boxprops=dict(facecolor='lightblue'))
    plt.title("Répartition des prix (Boîte à moustaches)")
    plt.xlabel("Prix (€)")
    plt.savefig('./OUTPUTS/boxplot_prix.png', dpi=150, bbox_inches='tight')
    plt.close()
    log.info("Graphique 'boxplot_prix.png' sauvegardé")

    # --- Graphique 3 : Pareto CA ---
    if df_pareto_ca is not None and nombre_articles_80_ca is not None:
        df_plot = df_pareto_ca.reset_index(drop=True)
        df_plot['index_prod'] = df_plot.index
        fig, ax1 = plt.subplots(figsize=(12, 6))
        df_plot['index_prod'] = df_plot['index_prod'].astype(float)
        ax1.bar(df_plot['index_prod'], df_plot['ca_produit'], color='steelblue')
        ax1.set_title('Analyse de Pareto : Concentration du CA', fontsize=16)
        ax1.set_xlabel('Produits (du plus grand CA au plus petit)', fontsize=12)
        ax1.set_ylabel('CA par produit (€)', fontsize=12)
        ax1.set_xticks([])
        ax2 = ax1.twinx()
        ax2.plot(df_plot['index_prod'], df_plot['ca_cumsum'], color='red', linewidth=2)
        ax2.set_ylabel('Pourcentage cumulé du CA', fontsize=12)
        ax2.set_ylim(0, 1.05)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        ax2.axhline(y=0.8, color='green', linestyle='--', label='Seuil 80%')
        if nombre_articles_80_ca:
            ax2.axvline(x=nombre_articles_80_ca, color='orange', linestyle='--',
                        label=f'{proportion_ca:.1f}% des produits')
        plt.legend(loc='center right')
        plt.savefig('./OUTPUTS/pareto_ca.png', dpi=150, bbox_inches='tight')
        plt.close()
        log.info("Graphique 'pareto_ca.png' sauvegardé")

    # --- Graphique 4 : Pareto Quantités ---
    if df_pareto_qtv is not None and nombre_articles_80_qty is not None:
        df_plot = df_pareto_qtv.reset_index(drop=True)
        df_plot['index_prod'] = df_plot.index
        fig, ax1 = plt.subplots(figsize=(12, 6))
        df_plot['index_prod'] = df_plot['index_prod'].astype(float)
        sns.barplot(x='index_prod', y='total_sales', data=df_plot, ax=ax1, color='skyblue')
        ax1.set_title('Analyse de Pareto : Concentration des Ventes', fontsize=16)
        ax1.set_xlabel('Produits (du plus vendu au moins vendu)', fontsize=12)
        ax1.set_ylabel('Quantité totale de ventes', fontsize=12)
        ax1.set_xticks([])
        ax2 = ax1.twinx()
        ax2.plot(df_plot['index_prod'], df_plot['ventes_cumsum'], color='red', linewidth=2)
        ax2.set_ylabel('Pourcentage cumulé des ventes', fontsize=12)
        ax2.set_ylim(0, 1.05)
        ax2.axhline(y=0.8, color='green', linestyle='--', label='Seuil 80%')
        ax2.axvline(x=nombre_articles_80_qty, color='orange', linestyle='--',
                    label=f'{proportion_qty:.1f}% des produits')
        plt.legend(loc='center right')
        plt.savefig('./OUTPUTS/pareto_ventes.png', dpi=150, bbox_inches='tight')
        plt.close()
        log.info("Graphique 'pareto_ventes.png' sauvegardé")

    # --- Graphique 5 : Top 5 stock dormant ---
    if 'mois_de_stock' in df.columns:
        df_actifs = df[(df['total_sales'] > 0) & (df['mois_de_stock'] != -1)].copy()
        top5 = df_actifs[['post_title', 'mois_de_stock']].sort_values('mois_de_stock', ascending=False).head(5) if 'post_title' in df.columns else df_actifs[['product_id', 'mois_de_stock']].head(5)
        fig, ax = plt.subplots(figsize=(10, 5))
        col_label = 'post_title' if 'post_title' in top5.columns else 'product_id'
        top5[col_label] = top5[col_label].astype(str)
        ax.barh(top5[col_label], top5['mois_de_stock'], color='salmon')
        ax.set_title("Top 5 des produits avec le plus de stock dormant (en mois)")
        ax.set_xlabel("Mois de couverture")
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig('./OUTPUTS/top5_stock_dormant.png', dpi=150, bbox_inches='tight')
        plt.close()
        log.info("Graphique 'top5_stock_dormant.png' sauvegardé")


# ============================================================
# 7. BILAN ET RECOMMANDATIONS
# ============================================================

def afficher_recommandations(df, ca_total, outliers):
    """Affiche le bilan et les recommandations stratégiques."""
    nb_produits = len(df)
    produits_sans_ventes = len(df[df['total_sales'] == 0])

    log.info("=" * 55)
    log.info("        BILAN ET RECOMMANDATIONS BUSINESS")
    log.info("=" * 55)

    log.info(f"PERFORMANCE : CA global : {ca_total:,.2f} €")
    log.info(f"PERFORMANCE : {produits_sans_ventes} produits ({produits_sans_ventes/nb_produits:.1%}) n'ont fait AUCUNE vente")

    log.info(f"ANALYSE DES PRIX : {len(outliers)} produits haut de gamme détectés (IQR)")
    log.info(f"ANALYSE DES PRIX : Prix maximum : {df['price'].max()} €")

    if 'taux_marge' in df.columns:
        marge_moy = df['taux_marge'].mean()
        produits_marge_neg = len(df[df['taux_marge'] < 0])
        log.info(f"MARGES : Taux de marge moyen : {marge_moy:.2f}%")
        if produits_marge_neg > 0:
            log.warning(f"MARGES : ⚠️  {produits_marge_neg} produit(s) vendus à perte !")

    if 'mois_de_stock' in df.columns:
        df_actifs = df[(df['total_sales'] > 0) & (df['mois_de_stock'] != -1)]
        if len(df_actifs) > 0:
            stock_moyen = df_actifs['mois_de_stock'].median()
            log.info(f"STOCKS : Couverture médiane : {stock_moyen:.1f} mois")

    log.info("RECOMMANDATION 1 [Audit Stock] : Vérifier les produits sans ventes pour libérer de la trésorerie.")
    log.info("RECOMMANDATION 2 [Stratégie Prix] : Les outliers semblent correspondre à une gamme Prestige. Ne pas baisser les prix, mais renforcer leur marketing ciblé.")
    if 'taux_marge' in df.columns and len(df[df['taux_marge'] < 0]) > 0:
        log.warning("RECOMMANDATION 3 [Urgence Marge] : Corriger immédiatement les produits vendus à perte.")
    log.info("=" * 55)