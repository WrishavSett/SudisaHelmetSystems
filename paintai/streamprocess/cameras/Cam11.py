import os
import cv2
import time
import uuid
import json
import ffmpeg
import logging
import threading
import numpy as np
from api_post import API
from test_infer import Infer
import multiprocessing as mp


class TESTFFMPEGC():
    def __init__(self):
        self.camera_config = {
            "dept_name": "Manufacturing",
            "camera": "Cam55",
            "camera_id": int("10"),
            "logdir": "D:/RohitDa/SudisaHelmetSystems/paintai/logs",
            "imgdir": "D:/RohitDa/SudisaHelmetSystems/paintai/imgs",
            "alarm_type": "Warning",
            "rtsp_url": "rtsp://localhost:18554/mystream"
        }

        if not os.path.exists(self.camera_config['imgdir']):
            os.makedirs(self.camera_config['imgdir'])
        if not os.path.exists(self.camera_config['logdir']):
            os.makedirs(self.camera_config['logdir'])

        # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(self.camera_config['camera'])
        self.logger.setLevel(logging.DEBUG)
        time_rotation = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(
                self.camera_config['logdir'],
                self.camera_config['camera'] + '.log'),
            when='W5', backupCount=1)
        logFormat = logging.Formatter(
            '%(asctime)s - %(name)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s')
        time_rotation.setFormatter(logFormat)
        time_rotation.setLevel(logging.DEBUG)
        self.logger.addHandler(time_rotation)

        self.rtsp_url = self.camera_config['rtsp_url']
        self.img_folder = self.camera_config['camera']
        self.inferob = Infer()
        self.api = API()

        time.sleep(15)
        self.logger.info("Delaying 15 seconds for RTSP Stream to stabilize before Capture")
        attempt = 0
        while attempt <= 4:
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                self.logger.error("Failed to open RTSP stream")
                attempt += 1
                time.sleep(15)
            else:
                self.logger.error("Captured RTSP stream")
                break
                # raise Exception("Failed to open RTSP stream")

        if attempt >= 4 and self.cap.isOpened() == False:
            self.logger.error("Didn't receive RTSP Stream")
            raise Exception("Didn't receive RTSP Stream")

        # Capture the video properties
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.logger.info(f"RTSP stream details:\nResolution={self.width}*{self.height}\nFPS={self.fps}")

        if not os.path.exists(os.path.join(self.camera_config['imgdir'], self.img_folder)):
            os.makedirs(os.path.join(self.camera_config['imgdir'], self.img_folder))

    def handle_stream_restart(self):
        self.logger.warning("Attempting restart of RTSP stream")
        try:
            time.sleep(15)
            self.cap.release()
            time.sleep(15)
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                self.logger.error("Failed to restart RTSP stream")
            else:
                # Capture the video properties
                self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                self.logger.info("Successfully restarted RTSP Stream")
                self.logger.info(
                    f"Restarted RTSP stream details:\nResolution={self.width}*{self.height}\nFPS={self.fps}")
        except Exception as e:
            self.logger.error("Failed to restart RTSP stream")
            self.logger.error(e)

    def process_frames(self):
        while True:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame from RTSP stream")
                    self.handle_stream_restart()
                    continue

                # Perform inference and tracking
                dets = self.inferob.detection(frame)
                frames = self.inferob.tracking(frame, dets)
                i = uuid.uuid4()
                fnmae = "frame" + str(i) + '.jpg'
                frame_name = os.path.join(self.camera_config['imgdir'], self.img_folder, fnmae)

                if frames is not None:
                    self.logger.info("Saving Image to Local Storage")
                    cv2.imwrite(frame_name, frames)

                    try:
                        self.api.posting(frame_name, self.camera_config)
                        self.logger.info("Image Successfully Sent to Server")

                    except Exception as e:
                        self.logger.error("Failed to Send Image to Server")
                        self.logger.error(e)

            except Exception as e:
                self.logger.error("Problem with processing frame")
                self.logger.error(e)
                self.handle_stream_restart()

    def run_threads(self):
        self.logger.info("Running threads for RTSP stream")
        frame_thread = threading.Thread(target=self.process_frames, daemon=True)
        frame_thread.start()

        frame_thread.join()


if __name__ == "__main__":
    rtspob = TESTFFMPEGC()
    rtspob.run_threads()
    rtspob.logger.info("===========================================")
# import cv2
# import time
# import logging
# import numpy as np
# import os
# import threading
# import uuid
# import ffmpeg
# import json
# import multiprocessing as mp
# from test_infer import Infer
# from api_post import API
# class TESTFFMPEGC():
#     def __init__(self):
#
#         self.camera_config = {
#             "dept_name": "Manufacturing",
#             "camera": "Cam11",
#             "camera_id": int("13"),
#             "logdir":"D:\RohitDa\SudisaHelmetSystems\paintai\logs",
#             "imgdir":"D:\RohitDa\SudisaHelmetSystems\paintai\imgs",
#             "alarm_type": "Warning",
#             "rtsp_url" : "rtsp://localhost:18554/mystream"
#         }
#         if not os.path.exists(self.camera_config['imgdir']):
#             os.makedirs(self.camera_config['imgdir'])
#
#         if not os.path.exists(self.camera_config['logdir']):
#             os.makedirs(self.camera_config['logdir'])
#         # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s')
#         self.logger = logging.getLogger(self.camera_config['camera'])
#         self.logger.setLevel(logging.DEBUG)
#         time_rotation = logging.handlers.TimedRotatingFileHandler(filename=os.path.join(self.camera_config['logdir'],self.camera_config['camera']+'.log'),\
#                                                                 when='W5',backupCount=1)
#         logFormat = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s - %(funcName)s - %(levelname)s - %(message)s')
#         time_rotation.setFormatter(logFormat)
#         time_rotation.setLevel(logging.DEBUG)
#         self.logger.addHandler(time_rotation)
#         #filename=os.path.join(self.camera_config['logdir'],self.camera_config['camera']+'.log')
#         #self.camera_config = camera_config
#         self.rtsp_url = self.camera_config['rtsp_url']
#         self.img_folder = self.camera_config['camera']
#
#         self.inferob = Infer()
#         self.api = API()
#         self.args = {
#         "rtsp_transport": "tcp",
#         "fflags": "nobuffer",
#         "flags": "low_delay"}
#         try:
#             self.logger.info("Begin Probing RTSP Stream for camera :- {}".format(self.rtsp_url))
#             self.logger.info("Begin Probing RTSP Stream with url :- {}".format(self.img_folder))
#             probe = ffmpeg.probe(self.rtsp_url,**self.args)
#             cap_info = next(x for x in probe['streams'] if x['codec_type'] == 'video')
#             self.logger.info("fps: {}".format(cap_info['r_frame_rate']))
#             self.width = cap_info['width']
#             self.height = cap_info['height']
#             # self.logger.info(str(self.width),str(self.height))
#             up, down = str(cap_info['r_frame_rate']).split('/')
#             fps = eval(up) / eval(down)
#             self.logger.info("fps: {}".format(fps))
#         except Exception as e:
#             self.logger.error("Failed to Probe RTSP Stream")
#             self.logger.error(e)
#             raise e
#
#         if not os.path.exists(os.path.join(self.camera_config['imgdir'], self.img_folder)):
#             os.makedirs(os.path.join(self.camera_config['imgdir'], self.img_folder))
#
#     def enqueue_frame_buffer(self):
#         self.process1 = (
#             ffmpeg
#             .input(self.rtsp_url, **self.args)
#             .output('pipe:', format='rawvideo', pix_fmt='bgr24')
#             .overwrite_output()
#             .run_async(pipe_stdout=True)
#         )
#
#         while True:
#             try:
#                 in_bytes = self.process1.stdout.read(self.width * self.height * 3)
#                 if not in_bytes:
#                     self.logger.info("Some Issue with reading from STDOUT")
#                     time.sleep(20)
#                     self.process1.terminate()
#                     time.sleep(10)
#                     self.process1 = (
#                         ffmpeg
#                         .input(self.rtsp_url, **self.args)
#                         .output('pipe:', format='rawvideo', pix_fmt='bgr24')
#                         .overwrite_output()
#                         .run_async(pipe_stdout=True)
#                     )
#                     continue
#
#                 Frame = (
#                     np
#                     .frombuffer(in_bytes, np.uint8)
#                     .reshape([self.height, self.width, 3])
#                 )
#                 if Frame is not None:
#                     dets = self.inferob.detection(Frame)
#                     frames = self.inferob.tracking(Frame,dets)
#                     i = uuid.uuid4()
#                     fnmae = "frame" + str(i) + '.jpg'
#                     frame_name = os.path.join(self.camera_config['imgdir'], self.img_folder, fnmae)
#
#                     if(frames is not None):
#                         self.logger.info("Saving Image to Local Storage")
#                         cv2.imwrite(frame_name,frames)
#                         try:
#                             self.api.posting(frame_name,self.camera_config)
#                             self.logger.info("Image Successfully Sent to Server")
#                         except Exception as e:
#                             self.logger.error("Failed to Send Image to Server")
#                             self.logger.error(e)
#
#
#             except Exception as e:
#                 self.logger.error("Problem with Processing")
#                 self.logger.error(e)
#
#     def run_threads(self):
#         self.logger.info("running threads")
#         self.enqueue_frame_buffer()
#
# if __name__ == "__main__":
#
#     rtspob = TESTFFMPEGC()
#     rtspob.run_threads()
#
#     self.logger.info("=========================================")
