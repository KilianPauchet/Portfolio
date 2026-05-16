# Fichier : database.py
from sqlalchemy import create_engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("database")

def upload_to_mysql(df, table_name, user, password, host, database):
    try:
        engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        log.info(f"Données envoyées avec succès dans la table '{table_name}'")
    except Exception as e:
        log.error(f"Erreur lors de l'envoi vers MySQL : {e}")