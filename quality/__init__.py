"""Модуль оценки качества данных."""

from .data_quality import (
    assess_data_quality,
    calculate_quality_metrics,
    check_completeness,
    check_consistency,
    check_accuracy,
    check_validity,
    generate_quality_report,
)

__all__ = [
    "assess_data_quality",
    "calculate_quality_metrics",
    "check_completeness",
    "check_consistency",
    "check_accuracy",
    "check_validity",
    "generate_quality_report",
]

