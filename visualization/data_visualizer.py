"""Визуализация данных."""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, Any

from preprocessing.data_preprocessor import load_data_from_db, preprocess_product_data

# Настройка стиля графиков
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except OSError:
    plt.style.use('seaborn-darkgrid')
sns.set_palette("husl")


def ensure_output_dir() -> Path:
    """Создание директории для сохранения графиков."""
    output_dir = Path("reports/visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def plot_price_distribution(df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Построение распределения цен."""
    if 'price' not in df.columns:
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Гистограмма
    axes[0].hist(df['price'].dropna(), bins=50, edgecolor='black', alpha=0.7)
    axes[0].set_title('Распределение цен на товары', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Цена (руб.)', fontsize=12)
    axes[0].set_ylabel('Количество товаров', fontsize=12)
    axes[0].grid(True, alpha=0.3)
    
    # Box plot
    axes[1].boxplot(df['price'].dropna(), vert=True)
    axes[1].set_title('Box Plot цен на товары', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Цена (руб.)', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_category_distribution(df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Построение распределения по категориям."""
    # Извлечение категорий из URL
    if 'product_url' not in df.columns:
        return
    
    categories = df['product_url'].str.extract(r'/catalog/([^/]+)/')[0]
    if categories.isna().all():
        return
    
    category_counts = categories.value_counts().head(15)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    category_counts.plot(kind='barh', ax=ax, color='steelblue')
    ax.set_title('Распределение товаров по категориям', fontsize=14, fontweight='bold')
    ax.set_xlabel('Количество товаров', fontsize=12)
    ax.set_ylabel('Категория', fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_price_by_category(df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Построение распределения цен по категориям."""
    if 'price' not in df.columns or 'product_url' not in df.columns:
        return
    
    categories = df['product_url'].str.extract(r'/catalog/([^/]+)/')[0]
    if categories.isna().all():
        return
    
    df_with_cat = df.copy()
    df_with_cat['category'] = categories
    df_with_cat = df_with_cat[df_with_cat['category'].notna()]
    
    top_categories = df_with_cat['category'].value_counts().head(10).index
    df_with_cat = df_with_cat[df_with_cat['category'].isin(top_categories)]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    df_with_cat.boxplot(column='price', by='category', ax=ax, rot=45)
    ax.set_title('Распределение цен по категориям', fontsize=14, fontweight='bold')
    ax.set_xlabel('Категория', fontsize=12)
    ax.set_ylabel('Цена (руб.)', fontsize=12)
    plt.suptitle('')  # Удаляем автоматический заголовок
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_characteristics_heatmap(df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Построение heatmap характеристик (если есть числовые характеристики)."""
    # Это упрощенная версия, так как характеристики в JSON
    # В реальном проекте можно извлечь числовые характеристики
    
    if 'characteristics' not in df.columns:
        return
    
    # Попытка извлечь числовые характеристики
    char_matrix = []
    char_labels = []
    
    # Упрощенная реализация - в реальности нужно парсить JSON
    # и извлекать числовые значения
    
    if not char_matrix:
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(char_matrix, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax)
    ax.set_title('Heatmap характеристик товаров', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_visualizations(df: Optional[pd.DataFrame] = None, output_dir: Optional[str] = None) -> Dict[str, str]:
    """Создание всех визуализаций."""
    if df is None:
        df = load_data_from_db()
        df = preprocess_product_data(df)
    
    if output_dir is None:
        output_dir = ensure_output_dir()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = {}
    
    # Распределение цен
    price_path = output_dir / "price_distribution.png"
    plot_price_distribution(df, str(price_path))
    saved_files['price_distribution'] = str(price_path)
    
    # Распределение по категориям
    category_path = output_dir / "category_distribution.png"
    plot_category_distribution(df, str(category_path))
    saved_files['category_distribution'] = str(category_path)
    
    # Цены по категориям
    price_by_cat_path = output_dir / "price_by_category.png"
    plot_price_by_category(df, str(price_by_cat_path))
    saved_files['price_by_category'] = str(price_by_cat_path)
    
    return saved_files


def save_all_visualizations(df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
    """Сохранение всех визуализаций."""
    return create_visualizations(df)

