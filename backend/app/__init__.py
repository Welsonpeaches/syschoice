"""Flask application factory."""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import BASE_DIR, Config
from .db import init_db


def create_app(config=Config, serve_frontend=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config)

    CORS(
        app,
        resources={r"/api/*": {"origins": config.CORS_ORIGINS}},
        allow_headers=["Content-Type", "X-Admin-Token"],
        methods=["GET", "POST", "OPTIONS"],
    )

    init_db(config.DB_PATH)

    from .api.admin import admin_bp
    from .api.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    # BASE_DIR points at backend/, so the built SPA lives one level up.
    dist = Path(BASE_DIR).parent / "frontend" / "dist"
    if serve_frontend is None:
        serve_frontend = (dist / "index.html").exists()

    if serve_frontend and (dist / "index.html").exists():
        @app.get("/")
        def index():
            return send_from_directory(dist, "index.html")

        @app.get("/<path:path>")
        def spa(path):
            target = dist / path
            if target.is_file():
                return send_from_directory(dist, path)
            # Unknown paths fall through to the SPA router.
            return send_from_directory(dist, "index.html")
    else:
        @app.get("/")
        def index():
            return jsonify({
                "name": "syschoice-backend",
                "hint": "前端未构建。开发时请运行 frontend 的 npm run dev。",
                "api": "/api/health",
            })

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "接口不存在。"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "服务器内部错误。"}), 500

    return app
