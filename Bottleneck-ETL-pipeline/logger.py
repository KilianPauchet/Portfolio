# Fichier : logger.py
import logging
import os
from datetime import datetime

def get_logger(nom):
    """Configure et retourne un logger avec sortie console + fichier."""
    
    # Crée le dossier logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Nom du fichier de log avec la date du jour
    date_du_jour = datetime.now().strftime("%Y-%m-%d")
    fichier_log = f"logs/pipeline_{date_du_jour}.log"
    
    # Configuration du logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(fichier_log, encoding="utf-8"),  # → fichier
            logging.StreamHandler()                               # → terminal
        ]
    )
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    return logging.getLogger(nom)