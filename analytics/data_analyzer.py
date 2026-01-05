"""Анализ данных продуктов."""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from collections import Counter

from preprocessing.data_preprocessor import load_data_from_db, preprocess_product_data


def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Расчет базовой статистики по данным."""
    stats = {
        'total_products': len(df),
    }
    
    if 'price' in df.columns:
        price_stats = df['price'].describe().to_dict()
        stats['price'] = {
            'mean': float(price_stats.get('mean', 0)),
            'median': float(price_stats.get('50%', 0)),
            'std': float(price_stats.get('std', 0)),
            'min': float(price_stats.get('min', 0)),
            'max': float(price_stats.get('max', 0)),
            'q25': float(price_stats.get('25%', 0)),
            'q75': float(price_stats.get('75%', 0)),
        }
    
    if 'shop' in df.columns:
        stats['shops_count'] = df['shop'].nunique()
        stats['products_per_shop'] = df['shop'].value_counts().to_dict()
    
    return stats


def price_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ цен на товары."""
    if 'price' not in df.columns:
        return {}
    
    analysis = {
        'price_distribution': {
            'low': df[df['price'] <= df['price'].quantile(0.33)]['price'].count(),
            'medium': df[(df['price'] > df['price'].quantile(0.33)) & 
                        (df['price'] <= df['price'].quantile(0.67))]['price'].count(),
            'high': df[df['price'] > df['price'].quantile(0.67)]['price'].count(),
        },
        'price_ranges': {
            'under_10000': (df['price'] < 10000).sum(),
            '10000_50000': ((df['price'] >= 10000) & (df['price'] < 50000)).sum(),
            '50000_100000': ((df['price'] >= 50000) & (df['price'] < 100000)).sum(),
            'over_100000': (df['price'] >= 100000).sum(),
        },
        'avg_price': float(df['price'].mean()),
        'median_price': float(df['price'].median()),
    }
    
    return analysis


def category_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ категорий товаров (на основе URL или названий)."""
    analysis = {}
    
    # Попытка извлечь категорию из URL
    if 'product_url' in df.columns:
        categories = df['product_url'].str.extract(r'/catalog/([^/]+)/')[0]
        if categories.notna().any():
            category_counts = categories.value_counts().to_dict()
            analysis['categories_from_url'] = category_counts
    
    # Анализ по магазинам
    if 'shop' in df.columns:
        shop_counts = df['shop'].value_counts().to_dict()
        analysis['products_by_shop'] = shop_counts
    
    return analysis


def characteristics_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализ характеристик товаров."""
    analysis = {}
    
    if 'characteristics' not in df.columns:
        return analysis
    
    # Собираем все характеристики
    all_chars = {}
    for char_str in df['characteristics'].dropna():
        try:
            char_dict = json.loads(char_str) if isinstance(char_str, str) else char_str
            if isinstance(char_dict, dict):
                for key, value in char_dict.items():
                    if key not in all_chars:
                        all_chars[key] = []
                    all_chars[key].append(str(value))
        except:
            pass
    
    # Анализ наиболее частых значений
    analysis['most_common_characteristics'] = {}
    for key, values in all_chars.items():
        counter = Counter(values)
        analysis['most_common_characteristics'][key] = dict(counter.most_common(10))
    
    # Статистика по характеристикам
    analysis['characteristics_coverage'] = {}
    total_products = len(df)
    for key in all_chars.keys():
        count = sum(1 for char_str in df['characteristics'].dropna() 
                   if _has_characteristic(char_str, key))
        analysis['characteristics_coverage'][key] = {
            'count': count,
            'percentage': (count / total_products * 100) if total_products > 0 else 0
        }
    
    return analysis


def _has_characteristic(char_str: Any, key: str) -> bool:
    """Проверка наличия характеристики."""
    try:
        char_dict = json.loads(char_str) if isinstance(char_str, str) else char_str
        if isinstance(char_dict, dict):
            return key in char_dict
    except:
        pass
    return False


def generate_insights(df: pd.DataFrame) -> List[str]:
    """Генерация инсайтов на основе анализа данных."""
    insights = []
    
    stats = calculate_statistics(df)
    price_anal = price_analysis(df)
    category_anal = category_analysis(df)
    
    # Инсайты о ценах
    if price_anal:
        avg_price = price_anal.get('avg_price', 0)
        median_price = price_anal.get('median_price', 0)
        insights.append(f"Средняя цена товара: {avg_price:,.0f} руб.")
        insights.append(f"Медианная цена товара: {median_price:,.0f} руб.")
        
        price_ranges = price_anal.get('price_ranges', {})
        max_range = max(price_ranges.items(), key=lambda x: x[1])
        insights.append(f"Наибольшее количество товаров в диапазоне: {max_range[0]} ({max_range[1]} товаров)")
    
    # Инсайты о категориях
    if category_anal.get('categories_from_url'):
        categories = category_anal['categories_from_url']
        top_category = max(categories.items(), key=lambda x: x[1])
        insights.append(f"Наиболее представленная категория: {top_category[0]} ({top_category[1]} товаров)")
    
    # Инсайты об общем количестве
    insights.append(f"Всего проанализировано товаров: {stats.get('total_products', 0)}")
    
    return insights


def analyze_products(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Комплексный анализ продуктов."""
    if df is None:
        df = load_data_from_db()
        df = preprocess_product_data(df)
    
    analysis = {
        'statistics': calculate_statistics(df),
        'price_analysis': price_analysis(df),
        'category_analysis': category_analysis(df),
        'characteristics_analysis': characteristics_analysis(df),
        'insights': generate_insights(df),
    }
    
    return analysis

