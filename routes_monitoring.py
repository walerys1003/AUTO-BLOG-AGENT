"""
Trasy dla monitorowania metrycznych aspektów działania systemu.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from utils.monitoring.content_metrics import ContentMetricsTracker

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/', methods=['GET'])
def metrics_dashboard():
    """Główny panel monitorowania"""
    return redirect(url_for('monitoring.show_metrics'))

@monitoring_bp.route('/metrics', methods=['GET'])
def show_metrics():
    """Wyświetla panel monitorowania z metrykami generowania treści"""
    days = request.args.get('days', 7, type=int)
    avg_metrics = ContentMetricsTracker.calculate_average_metrics(days=days)
    recent_metrics = ContentMetricsTracker.get_recent_metrics(limit=20)
    
    # Upewnij się, że metryki mają prawidłowy format dla lepszej czytelności
    for metric in recent_metrics:
        # Zaokrąglij wartości numeryczne do 2 miejsc po przecinku
        if "duration_seconds" in metric:
            metric["duration_seconds"] = round(metric["duration_seconds"], 2)
    
    return render_template(
        'monitoring/metrics.html',
        avg_metrics=avg_metrics,
        recent_metrics=recent_metrics,
        days=days
    )

@monitoring_bp.route('/api/metrics', methods=['GET'])
def api_metrics():
    """API do pobierania metryk generowania treści w formacie JSON"""
    days = request.args.get('days', 7, type=int)
    avg_metrics = ContentMetricsTracker.calculate_average_metrics(days=days)
    recent_metrics = ContentMetricsTracker.get_recent_metrics(limit=20)
    
    return jsonify({
        "avg_metrics": avg_metrics,
        "recent_metrics": recent_metrics
    })

@monitoring_bp.route('/api/metrics/dashboard', methods=['GET'])
def api_metrics_dashboard():
    """API do pobierania danych metryk do dashboardu"""
    days = request.args.get('days', 30, type=int)
    
    # Pobierz wszystkie metryki z określonego okresu
    metrics = ContentMetricsTracker.get_recent_metrics(limit=100)
    
    # Przygotuj dane do wykresu
    metrics_by_date = {}
    for metric in metrics:
        date = metric.get("timestamp_start", "").split("T")[0]  # Format: YYYY-MM-DD
        if date:
            if date not in metrics_by_date:
                metrics_by_date[date] = {
                    "date": date,
                    "successful": 0,
                    "failed": 0,
                    "avg_duration": 0,
                    "total_duration": 0,
                    "total_words": 0,
                    "content_count": 0
                }
            
            if metric.get("success", False):
                metrics_by_date[date]["successful"] += 1
                metrics_by_date[date]["total_duration"] += metric.get("duration_seconds", 0)
                metrics_by_date[date]["total_words"] += metric.get("content_length_words", 0)
                metrics_by_date[date]["content_count"] += 1
            else:
                metrics_by_date[date]["failed"] += 1
    
    # Oblicz średnie
    for date, data in metrics_by_date.items():
        if data["content_count"] > 0:
            data["avg_duration"] = round(data["total_duration"] / data["content_count"], 2)
            data["avg_words"] = round(data["total_words"] / data["content_count"], 0)
    
    # Posortuj według daty
    metrics_timeline = sorted(list(metrics_by_date.values()), key=lambda x: x["date"])
    
    return jsonify({
        "timeline": metrics_timeline,
        "summary": ContentMetricsTracker.calculate_average_metrics(days=days)
    })