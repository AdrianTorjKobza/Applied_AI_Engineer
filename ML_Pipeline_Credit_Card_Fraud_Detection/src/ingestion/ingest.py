import pandas as pd
from src.utils.config import DATA_PATH


def load_data():
    df = pd.read_csv(DATA_PATH)
    return df