# Fichier : extract.py
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("extract")

def load_data(filepath):
    log.info(f"Chargement des données depuis {filepath}...")
    if not os.path.exists(filepath):
        log.error(f"Fichier introuvable : {filepath}")
        return None
    combinaisons = [
        {'encoding': 'utf-8', 'sep': ','},
        {'encoding': 'utf-8', 'sep': ';'},
        {'encoding': 'iso-8859-1', 'sep': ','},
        {'encoding': 'iso-8859-1', 'sep': ';'}
    ]
    
    for config in combinaisons:
        try:
            df = pd.read_csv(filepath, encoding=config['encoding'], sep=config['sep'])
            if df.shape[1] <= 1 and config['sep'] == ',':
                continue
            log.info(f"Succès ({config['encoding']}, séparateur '{config['sep']}')")
            return df
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    
    log.error(f"Impossible de lire le fichier {filepath}")
    return None