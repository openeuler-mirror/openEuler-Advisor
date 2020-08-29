#!/usr/bin/python3
"""
Use queues to implement the producer and consumer model
to solve the database lock introduced by high concurrency issues
"""
import threading
from queue import Queue
from sqlalchemy.exc import SQLAlchemyError
from packageship.libs.dbutils import DBHelper
from packageship.libs.exception import Error, ContentNoneException
from packageship.libs.log import Log


class ProducerConsumer():
    """
        The data written in the database is added to the high
        concurrency queue, and the high concurrency is solved
        by the form of the queue
    """
    _queue = Queue(maxsize=0)
    _instance_lock = threading.Lock()
    _log = Log(__name__)

    def __init__(self):
        self.thread_queue = threading.Thread(target=self.__queue_process)
        if not self.thread_queue.isAlive():
            self.thread_queue.start()

    def start_thread(self):
        """
            Judge a thread, if the thread is terminated, restart
        """
        if not self.thread_queue.isAlive():
            self.thread_queue = threading.Thread(target=self.__queue_process)
            self.thread_queue.start()

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
            Use the singleton pattern to create a thread-safe producer pattern
        """
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = object.__new__(cls)
        return cls._instance

    def __queue_process(self):
        """
            Read the content in the queue and save and update
        """
        while not self._queue.empty():
            _queue_value = self._queue.get()
            try:
                with DBHelper(db_name="lifecycle") as database:
                    database.add(_queue_value)
            except (Error, ContentNoneException, SQLAlchemyError) as error:
                self._log.logger.error(error)

    def put(self, pending_content):
        """
            The content of the operation is added to the queue
        """
        if pending_content:
            self._queue.put(pending_content)
            self.start_thread()
