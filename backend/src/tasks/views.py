from flask import jsonify

from tasks import tasks_bp
from tasks.config import default_queue
from tasks.tasks import bulk_generation_task


@tasks_bp.route("/bulk-generate", methods=["POST"])
def bulk_generate():
    job = default_queue.enqueue(
        bulk_generation_task,
        job_timeout="2h",
        result_ttl=86400,
    )

    return (
        jsonify(
            {
                "status": "enqueued",
                "job_id": job.get_id(),
                "queue_position": len(default_queue),
            }
        ),
        202,
    )
