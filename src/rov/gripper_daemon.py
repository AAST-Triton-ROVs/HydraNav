from queue import Queue
import time 
import struct
from threading import Thread
from logger import logging
import socket
from Scripts.GCS.src.rov.enums import GripperCommands





RASP_IP = "192.168.1.100"
PORT = 2500

class Gripper:
    def __init__(self, logging: logging):
        self.__gripper_queue: Queue[GripperCommands] = Queue(1)
        self.__logging = logging
        self.__gripper_daemon = GripperDaemon(self.__gripper_queue, self.__logging, RASP_IP, PORT)
        self.__gripper_daemon.start()
        self.__logging.logger.success("Gripper daemon started")

    def reset(self):
        self.__gripper_queue.put(GripperCommands.RESET)
        self.__logging.logger.success("Gripper reset")
    def open_gripper(self):
        self.__gripper_queue.put(GripperCommands.OPEN)
        self.__logging.logger.success("Gripper open")
    def close_gripper(self):
        self.__gripper_queue.put(GripperCommands.CLOSE)
        self.__logging.logger.success("Gripper close")
    def pitch_up(self):
        self.__gripper_queue.put(GripperCommands.PITCH_UP)
        self.__logging.logger.success("Gripper pitch up")
    def pitch_down(self):
        self.__gripper_queue.put(GripperCommands.PITCH_DOWN)
        self.__logging.logger.success("Gripper pitch down")
    def roll_right(self):
        self.__gripper_queue.put(GripperCommands.ROLL_RIGHT)
        self.__logging.logger.success("Gripper roll right")
    def roll_left(self):
        self.__gripper_queue.put(GripperCommands.ROLL_LEFT)
        self.__logging.logger.success("Gripper roll left")


class GripperDaemon(Thread):
    def __init__(self, gripper_queue: Queue[GripperCommands], logging: logging, ip: str, port: int):
        super().__init__(daemon=True)
        self.gripper_queue = gripper_queue
        self.logging = logging
        self.ip = ip
        self.port = port

while True:
    def run(self):
        gripper_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        gripper_socket.bind(self.ip, self.port)
        while True:
            try:
                gripper_socket.connect((RASP_IP, PORT))
                self.logging.logger.success("Connected to gripper")
                break
            except:
                print("Connection failed...retrying")
                time.sleep(1)
        while True:
            if not self.gripper_queue.empty():
                command = self.gripper_queue.get()
                data = struct.pack("i", command.value)
                gripper_socket.sendall(data)
                self.logging.logger.success("Gripper command sent")