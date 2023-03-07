import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from time import sleep
from cv_bridge import CvBridge
import sys
from PyQt5 import QtWidgets, uic
from threading import Thread, Event
from queue import Queue
from PyQt5.QtGui import QPixmap, QImage

UI_FILE_PATH = "/PATH/TO/UI_FILE"

class ROS(QtWidgets.QMainWindow):
    def __init__(self):
        super(ROS, self).__init__()
        uic.loadUi(UI_FILE_PATH, self)
        self.img_queue = Queue()
        self.threadEvent = Event()
        self.stopEvent = Event()
        self.threadEvent.clear()
        self.stopEvent.set()
        self.stopFlag = False
        self.btnStart.clicked.connect(self.setEvent)
        self.btnStop.clicked.connect(self.clearEvent)
        Thread(target=self.runRos, args=()).start()
        Thread(target=self.startStream, args=()).start()
        self.show()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
                self, 'Quit?',
                'Are you sure you want to quit?',
                QtWidgets.QMessageBox.Yes , QtWidgets.QMessageBox.No
            )
        if reply == QtWidgets.QMessageBox.Yes:
            self.stopEvent.clear()
            event.accept()
        else:
            event.ignore()

    def setEvent(self) -> None:
        self.threadEvent.set()
    
    def clearEvent(self) -> None:
        self.threadEvent.clear()

    def runRos(self) -> None:
        rclpy.init(args=None)
        self.stream_subs = StreamSubscriber(img_queue=self.img_queue)
        while self.stopEvent.is_set():
            rclpy.spin_once(self.stream_subs, timeout_sec=1)
        else:
            self.stream_subs.destroy_node()
            rclpy.shutdown()
    
    def startStream(self) -> None:
        while self.stopEvent.is_set():
            if self.threadEvent.is_set():    
                self.frame = self.img_queue.get()
                self.img_h, self.img_w, self.img_c = self.frame.shape
                self.bytesPerLine = self.img_c * self.img_w
                self.q_image = QImage(self.frame.data, self.img_w, self.img_h,self.bytesPerLine, QImage.Format_BGR888)
                self.imgStreamObj.setPixmap(QPixmap.fromImage(self.q_image))
            else:
                self.imgStreamObj.clear()
                self.threadEvent.wait(1)

class StreamSubscriber(Node):
    def __init__(self, img_queue):
        super().__init__("stream_subscriber")
        self.frame = None
        self.img_queue = img_queue
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(CompressedImage, "stream", self.stream_callback, 10)        
        
    def stream_callback(self, msg):
        self.frame = self.bridge.compressed_imgmsg_to_cv2(msg)
        self.img_queue.put(self.frame)


def main_gui():
    app = QtWidgets.QApplication(sys.argv)
    window = ROS()
    sys.exit(app.exec_())