from redis import Redis
from rq import Worker, Queue

redis_conn = Redis(host='localhost', port=6379, db=0)

queue = Queue(connection=redis_conn)

worker = Worker([queue], connection=redis_conn)
worker.work()
