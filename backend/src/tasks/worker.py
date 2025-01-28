from rq import Worker

from tasks.config import default_queue, redis_conn

if __name__ == "__main__":
    worker = Worker([default_queue], connection=redis_conn)
    worker.work()
