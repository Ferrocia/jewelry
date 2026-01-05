"""Предобработка данных для анализа."""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

from src.storage import init_db


def load_data_from_db() -> pd.DataFrame:
    """Загрузка данных из базы данных в DataFrame."""
    conn, cur = init_db()
    try:
        query = """
            SELECT 
                id,
                shop,
                product_url,
                title,
                price,
                description,
                characteristics,
                created_at
            FROM products
            ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        cur.close()
        conn.close()


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Нормализация данных (приведение к единому формату)."""
    df = df.copy()
    
    # Нормализация текстовых полей
    if 'title' in df.columns:
        df['title'] = df['title'].astype(str).str.strip()
    
    if 'description' in df.columns:
        df['description'] = df['description'].astype(str).str.strip()
        df['description'] = df['description'].replace('None', np.nan)
    
    # Нормализация цены
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    return df


def standardize_data(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Стандартизация числовых данных (z-score normalization)."""
    df = df.copy()
    scaler = StandardScaler()
    
    for col in columns:
        if col in df.columns and df[col].dtype in ['int64', 'float64']:
            df[col] = scaler.fit_transform(df[[col]])
    
    return df


def encode_categorical(df: pd.DataFrame, columns: List[str]) -> Dict[str, LabelEncoder]:
    """Кодирование категориальных данных."""
    df = df.copy()
    encoders = {}
    
    for col in columns:
        if col in df.columns:
            encoder = LabelEncoder()
            df[col] = encoder.fit_transform(df[col].astype(str))
            encoders[col] = encoder
    
    return df, encoders


def handle_missing_values(df: pd.DataFrame, strategy: str = 'mean') -> pd.DataFrame:
    """Обработка пропущенных значений."""
    df = df.copy()
    
    # Для числовых колонок
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        imputer = SimpleImputer(strategy=strategy)
        df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
    
    # Для текстовых колонок - заполняем пустой строкой
    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].fillna('')
    
    return df


def handle_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
    """
    Обработка выбросов в данных.
    
    Methods:
        'iqr' - использует межквартильный размах
        'zscore' - использует z-score (|z| > 3)
    """
    df = df.copy()
    
    if column not in df.columns or df[column].dtype not in ['int64', 'float64']:
        return df
    
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    elif method == 'zscore':
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        df = df[z_scores < 3]
    
    return df


def extract_characteristics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Извлечение признаков из JSON характеристик."""
    df = df.copy()
    
    if 'characteristics' not in df.columns:
        return df
    
    # Попытка извлечь общие характеристики
    common_keys = set()
    for char_str in df['characteristics'].dropna():
        try:
            char_dict = json.loads(char_str) if isinstance(char_str, str) else char_str
            if isinstance(char_dict, dict):
                common_keys.update(char_dict.keys())
        except:
            pass
    
    # Создание колонок для каждой характеристики
    for key in common_keys:
        df[f'char_{key}'] = df['characteristics'].apply(
            lambda x: _extract_char_value(x, key)
        )
    
    return df


def _extract_char_value(char_str: Any, key: str) -> Optional[str]:
    """Извлечение значения характеристики по ключу."""
    try:
        char_dict = json.loads(char_str) if isinstance(char_str, str) else char_str
        if isinstance(char_dict, dict):
            return char_dict.get(key)
    except:
        pass
    return None


def preprocess_product_data(
    df: Optional[pd.DataFrame] = None,
    handle_missing: bool = True,
    handle_outliers_price: bool = True,
    extract_features: bool = True
) -> pd.DataFrame:
    """Комплексная предобработка данных продуктов."""
    if df is None:
        df = load_data_from_db()
    
    # Нормализация
    df = normalize_data(df)
    
    # Обработка пропущенных значений
    if handle_missing:
        df = handle_missing_values(df)
    
    # Обработка выбросов в цене
    if handle_outliers_price and 'price' in df.columns:
        df = handle_outliers(df, 'price', method='iqr')
    
    # Извлечение признаков из характеристик
    if extract_features:
        df = extract_characteristics_features(df)
    
    return df

