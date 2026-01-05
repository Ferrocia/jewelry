"""Скрипт для запуска анализа данных."""

from reports.report_generator import generate_full_report
from quality.data_quality import generate_quality_report
from analytics.data_analyzer import analyze_products


def main():
    """Запуск полного анализа данных."""
    print("🔍 Запуск анализа данных...")
    
    # Оценка качества данных
    print("\n📊 Оценка качества данных...")
    quality_report = generate_quality_report()
    print(quality_report)
    
    # Анализ данных
    print("\n📈 Анализ данных...")
    analysis = analyze_products()
    print("\nКлючевые инсайты:")
    for i, insight in enumerate(analysis.get('insights', []), 1):
        print(f"  {i}. {insight}")
    
    # Генерация полного отчета
    print("\n📝 Генерация отчетов и визуализаций...")
    reports = generate_full_report()
    
    print("\n✅ Анализ завершен!")
    print("\nСгенерированные файлы:")
    for report_type, path in reports.items():
        if isinstance(path, dict):
            print(f"  {report_type}:")
            for key, value in path.items():
                print(f"    - {key}: {value}")
        else:
            print(f"  {report_type}: {path}")


if __name__ == "__main__":
    main()

