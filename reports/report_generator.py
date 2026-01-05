"""Генерация отчетов."""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd

from analytics.data_analyzer import analyze_products
from quality.data_quality import assess_data_quality, generate_quality_report
from visualization.data_visualizer import create_visualizations
from preprocessing.data_preprocessor import load_data_from_db, preprocess_product_data


def ensure_reports_dir() -> Path:
    """Создание директории для отчетов."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def generate_analysis_report(output_path: Optional[str] = None) -> str:
    """Генерация отчета по анализу данных."""
    if output_path is None:
        reports_dir = ensure_reports_dir()
        output_path = reports_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    analysis = analyze_products()
    
    report = []
    report.append("=" * 80)
    report.append("ОТЧЕТ ПО АНАЛИЗУ ДАННЫХ")
    report.append("=" * 80)
    report.append(f"\nДата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n" + "-" * 80)
    report.append("ОБЩАЯ СТАТИСТИКА")
    report.append("-" * 80)
    
    stats = analysis.get('statistics', {})
    report.append(f"Всего товаров: {stats.get('total_products', 0)}")
    
    if 'price' in stats:
        price_stats = stats['price']
        report.append(f"\nСтатистика по ценам:")
        report.append(f"  Средняя цена: {price_stats.get('mean', 0):,.0f} руб.")
        report.append(f"  Медианная цена: {price_stats.get('median', 0):,.0f} руб.")
        report.append(f"  Минимальная цена: {price_stats.get('min', 0):,.0f} руб.")
        report.append(f"  Максимальная цена: {price_stats.get('max', 0):,.0f} руб.")
        report.append(f"  Стандартное отклонение: {price_stats.get('std', 0):,.0f} руб.")
    
    report.append("\n" + "-" * 80)
    report.append("АНАЛИЗ ЦЕН")
    report.append("-" * 80)
    
    price_anal = analysis.get('price_analysis', {})
    if price_anal:
        report.append(f"Средняя цена: {price_anal.get('avg_price', 0):,.0f} руб.")
        report.append(f"Медианная цена: {price_anal.get('median_price', 0):,.0f} руб.")
        
        price_ranges = price_anal.get('price_ranges', {})
        report.append("\nРаспределение по ценовым диапазонам:")
        for range_name, count in price_ranges.items():
            report.append(f"  {range_name}: {count} товаров")
    
    report.append("\n" + "-" * 80)
    report.append("АНАЛИЗ КАТЕГОРИЙ")
    report.append("-" * 80)
    
    category_anal = analysis.get('category_analysis', {})
    if category_anal.get('categories_from_url'):
        report.append("\nТоп категории:")
        categories = category_anal['categories_from_url']
        for i, (cat, count) in enumerate(list(categories.items())[:10], 1):
            report.append(f"  {i}. {cat}: {count} товаров")
    
    report.append("\n" + "-" * 80)
    report.append("КЛЮЧЕВЫЕ ИНСАЙТЫ")
    report.append("-" * 80)
    
    insights = analysis.get('insights', [])
    for i, insight in enumerate(insights, 1):
        report.append(f"{i}. {insight}")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return str(output_path)


def generate_quality_report_file(output_path: Optional[str] = None) -> str:
    """Генерация файла отчета о качестве данных."""
    if output_path is None:
        reports_dir = ensure_reports_dir()
        output_path = reports_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    report_text = generate_quality_report()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return str(output_path)


def generate_summary_report(output_path: Optional[str] = None) -> str:
    """Генерация краткого сводного отчета."""
    if output_path is None:
        reports_dir = ensure_reports_dir()
        output_path = reports_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    df = load_data_from_db()
    
    report = []
    report.append("=" * 80)
    report.append("СВОДНЫЙ ОТЧЕТ")
    report.append("=" * 80)
    report.append(f"\nДата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    report.append("\n" + "-" * 80)
    report.append("ОСНОВНЫЕ МЕТРИКИ")
    report.append("-" * 80)
    report.append(f"Всего товаров в базе: {len(df)}")
    
    if 'price' in df.columns:
        report.append(f"Средняя цена: {df['price'].mean():,.0f} руб.")
        report.append(f"Медианная цена: {df['price'].median():,.0f} руб.")
    
    if 'shop' in df.columns:
        report.append(f"Количество магазинов: {df['shop'].nunique()}")
    
    # Оценка качества
    quality_metrics = assess_data_quality(df)
    report.append(f"\nОценка качества данных: {quality_metrics.get('overall_quality_score', 0)}/100")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return str(output_path)


def generate_full_report(output_dir: Optional[str] = None) -> Dict[str, str]:
    """Генерация полного отчета со всеми разделами и визуализациями."""
    if output_dir is None:
        output_dir = ensure_reports_dir()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Загрузка и предобработка данных
    df = load_data_from_db()
    df = preprocess_product_data(df)
    
    # Генерация отчетов
    reports = {}
    
    # Отчет по анализу
    analysis_report_path = output_dir / f"analysis_report_{timestamp}.txt"
    reports['analysis'] = generate_analysis_report(str(analysis_report_path))
    
    # Отчет о качестве
    quality_report_path = output_dir / f"quality_report_{timestamp}.txt"
    reports['quality'] = generate_quality_report_file(str(quality_report_path))
    
    # Сводный отчет
    summary_report_path = output_dir / f"summary_report_{timestamp}.txt"
    reports['summary'] = generate_summary_report(str(summary_report_path))
    
    # Визуализации
    viz_dir = output_dir / "visualizations"
    viz_files = create_visualizations(df, str(viz_dir))
    reports['visualizations'] = viz_files
    
    return reports

