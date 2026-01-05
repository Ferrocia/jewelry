"""Оценка качества данных."""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime

from preprocessing.data_preprocessor import load_data_from_db


def check_completeness(df: pd.DataFrame) -> Dict[str, float]:
    """Проверка полноты данных (отсутствие пропусков)."""
    completeness = {}
    total_rows = len(df)
    
    for col in df.columns:
        non_null_count = df[col].notna().sum()
        completeness[col] = (non_null_count / total_rows) * 100 if total_rows > 0 else 0
    
    return completeness


def check_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """Проверка согласованности данных."""
    consistency_issues = {}
    
    # Проверка типов данных
    type_consistency = {}
    for col in df.columns:
        expected_type = df[col].dtype
        type_consistency[col] = str(expected_type)
    
    # Проверка дубликатов
    duplicates = df.duplicated().sum()
    
    # Проверка URL на уникальность (если есть)
    if 'product_url' in df.columns:
        url_duplicates = df['product_url'].duplicated().sum()
    else:
        url_duplicates = 0
    
    consistency_issues['type_consistency'] = type_consistency
    consistency_issues['total_duplicates'] = duplicates
    consistency_issues['url_duplicates'] = url_duplicates
    
    return consistency_issues


def check_accuracy(df: pd.DataFrame) -> Dict[str, Any]:
    """Проверка точности данных."""
    accuracy_issues = {}
    
    # Проверка цен (должны быть положительными)
    if 'price' in df.columns:
        negative_prices = (df['price'] < 0).sum()
        zero_prices = (df['price'] == 0).sum()
        accuracy_issues['negative_prices'] = negative_prices
        accuracy_issues['zero_prices'] = zero_prices
    
    # Проверка URL (должны быть валидными)
    if 'product_url' in df.columns:
        invalid_urls = df['product_url'].str.startswith('http', na=False).sum()
        total_urls = df['product_url'].notna().sum()
        accuracy_issues['valid_urls'] = invalid_urls
        accuracy_issues['invalid_urls'] = total_urls - invalid_urls
    
    # Проверка длины названий
    if 'title' in df.columns:
        empty_titles = (df['title'].astype(str).str.strip() == '').sum()
        accuracy_issues['empty_titles'] = empty_titles
    
    return accuracy_issues


def check_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Проверка валидности данных (соответствие ожидаемым форматам)."""
    validity_issues = {}
    
    # Проверка формата цен
    if 'price' in df.columns:
        numeric_prices = pd.to_numeric(df['price'], errors='coerce').notna().sum()
        total_prices = df['price'].notna().sum()
        validity_issues['numeric_prices'] = numeric_prices
        validity_issues['non_numeric_prices'] = total_prices - numeric_prices
    
    # Проверка формата дат (если есть)
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'created' in col.lower()]
    for col in date_cols:
        try:
            pd.to_datetime(df[col], errors='coerce')
            valid_dates = pd.to_datetime(df[col], errors='coerce').notna().sum()
            validity_issues[f'valid_{col}'] = valid_dates
        except:
            pass
    
    return validity_issues


def calculate_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Расчет метрик качества данных."""
    metrics = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'completeness': check_completeness(df),
        'consistency': check_consistency(df),
        'accuracy': check_accuracy(df),
        'validity': check_validity(df),
    }
    
    # Общий score качества (0-100)
    completeness_scores = list(metrics['completeness'].values())
    avg_completeness = np.mean(completeness_scores) if completeness_scores else 0
    
    consistency_score = 100 if metrics['consistency']['total_duplicates'] == 0 else 80
    
    accuracy_issues = sum([
        metrics['accuracy'].get('negative_prices', 0),
        metrics['accuracy'].get('zero_prices', 0),
        metrics['accuracy'].get('empty_titles', 0),
    ])
    accuracy_score = max(0, 100 - (accuracy_issues / len(df) * 100)) if len(df) > 0 else 0
    
    overall_score = (avg_completeness + consistency_score + accuracy_score) / 3
    metrics['overall_quality_score'] = round(overall_score, 2)
    
    return metrics


def assess_data_quality(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Комплексная оценка качества данных."""
    if df is None:
        df = load_data_from_db()
    
    metrics = calculate_quality_metrics(df)
    return metrics


def generate_quality_report(df: Optional[pd.DataFrame] = None) -> str:
    """Генерация текстового отчета о качестве данных."""
    if df is None:
        df = load_data_from_db()
    
    metrics = assess_data_quality(df)
    
    report = []
    report.append("=" * 60)
    report.append("ОТЧЕТ О КАЧЕСТВЕ ДАННЫХ")
    report.append("=" * 60)
    report.append(f"\nДата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\nОбщее количество записей: {metrics['total_records']}")
    report.append(f"Общее количество колонок: {metrics['total_columns']}")
    report.append(f"\nОБЩАЯ ОЦЕНКА КАЧЕСТВА: {metrics['overall_quality_score']}/100")
    
    report.append("\n" + "-" * 60)
    report.append("ПОЛНОТА ДАННЫХ (Completeness)")
    report.append("-" * 60)
    for col, score in metrics['completeness'].items():
        status = "✓" if score >= 90 else "⚠" if score >= 70 else "✗"
        report.append(f"{status} {col}: {score:.2f}%")
    
    report.append("\n" + "-" * 60)
    report.append("СОГЛАСОВАННОСТЬ ДАННЫХ (Consistency)")
    report.append("-" * 60)
    report.append(f"Дубликаты записей: {metrics['consistency']['total_duplicates']}")
    report.append(f"Дубликаты URL: {metrics['consistency'].get('url_duplicates', 0)}")
    
    report.append("\n" + "-" * 60)
    report.append("ТОЧНОСТЬ ДАННЫХ (Accuracy)")
    report.append("-" * 60)
    accuracy = metrics['accuracy']
    report.append(f"Отрицательные цены: {accuracy.get('negative_prices', 0)}")
    report.append(f"Нулевые цены: {accuracy.get('zero_prices', 0)}")
    report.append(f"Пустые названия: {accuracy.get('empty_titles', 0)}")
    
    report.append("\n" + "-" * 60)
    report.append("ВАЛИДНОСТЬ ДАННЫХ (Validity)")
    report.append("-" * 60)
    validity = metrics['validity']
    for key, value in validity.items():
        report.append(f"{key}: {value}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)

