from flask import Blueprint, jsonify
from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/stats", methods=["GET"])
@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    try:
        data = DashboardService.get_stats()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
