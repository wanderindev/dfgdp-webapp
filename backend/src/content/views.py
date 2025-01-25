from flask import request, jsonify, current_app, send_from_directory
from content.models import Media

from content import content_bp


@content_bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded files"""
    uploads_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(uploads_dir, filename)


@content_bp.route("/api/media/upload", methods=["POST"])
def upload_media():
    """Handle media file uploads"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        media = Media.create_from_upload(
            file=file, title=file.filename, alt_text=file.filename
        )

        if not media:
            return jsonify({"error": "Failed to create media entry"}), 500

        return jsonify(
            {
                "id": media.id,
                "filename": media.filename,
                "filePath": media.file_path,
                "publicUrl": media.public_url,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": str(e)}), 500
