#!/usr/bin/python3
"""
Use queues to implement the producer and consumer model
to solve the database lock introduced by high concurrency issues
"""
import threading
import time
from queue import Queue
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError
from packageship.libs.exception import Error, ContentNoneException
from packageship.libs.log import LOGGER
from packageship.libs.conf import configuration


class ProducerConsumer():
    """
        The data written in the database is added to the high
        concurrency queue, and the high concurrency is solved
        by the form of the queue
    """
    _queue = Queue(maxsize=configuration.QUEUE_MAXSIZE)
    _instance_lock = threading.Lock()

    def __init__(self):
        self.thread_queue = threading.Thread(target=self.__queue_process)
        self._instance_lock.acquire()
        if not self.thread_queue.isAlive():
            self.thread_queue = threading.Thread(target=self.__queue_process)
            self.thread_queue.start()
        self._instance_lock.release()

    def start_thread(self):
        """
            Judge a thread, if the thread is terminated, restart
        """
        self._instance_lock.acquire()
        if not self.thread_queue.isAlive():
            self.thread_queue = threading.Thread(target=self.__queue_process)
            self.thread_queue.start()
        self._instance_lock.release()

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
            _queue_value, method = self._queue.get()
            try:
                method(_queue_value)
            except OperationalError as error:
                LOGGER.warning(error)
                time.sleep(0.2)
                self._queue.put((_queue_value, method))
            except (Error, ContentNoneException, SQLAlchemyError) as error:
                LOGGER.error(error)

    def put(self, pending_content):
        """
            The content of the operation is added to the queue
        """
        if pending_content:
            self._queue.put(pending_content)
            self.start_thread()
