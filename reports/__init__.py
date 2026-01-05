"""Модуль генерации отчетов."""

from .report_generator import (
    generate_full_report,
    generate_analysis_report,
    generate_quality_report_file,
    generate_summary_report,
)

__all__ = [
    "generate_full_report",
    "generate_analysis_report",
    "generate_quality_report_file",
    "generate_summary_report",
]

