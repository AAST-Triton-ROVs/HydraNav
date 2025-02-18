from logging import Logger
from queue import Queue
from rov.admin.daemon import AdminDaemon


class Admin:
    def __init__(self, logging: Logger, ip: str = "0.0.0.0", port: int = 3000):
        self.__admin_queue: Queue[int] = Queue(1)
        self.__logging = logging
        self.__admin_daemon = AdminDaemon(self.__admin_queue, self.__logging, ip, port)
        self.__admin_daemon.start()
        self.__logging.logger.success("Admin daemon started")
        
    def poweroff(self):
        self.__admin_queue.put(0)
        self.__logging.logger.success("Powering off")
    def reboot(self):
        self.__admin_queue.put(1)
        self.__logging.logger.success("Rebooting")
    def restart_mavproxy(self):
        self.__admin_queue.put(2)
        self.__logging.logger.success("Restarting mavproxy service")
    def restart_gripper(self):
        self.__admin_queue.put(3)
        self.__logging.logger.success("Restarting gripper service")
    def restart_telemetry(self):
        self.__admin_queue.put(4)
        self.__logging.logger.success("Restarting telemetry service")
    def restart_admin(self):
        self.__admin_queue.put(10)
        self.__logging.logger.success("Restarting admin service")