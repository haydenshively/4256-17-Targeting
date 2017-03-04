#http://docs.opencv.org/trunk/dd/d49/tutorial_py_contour_features.html
#http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_filtering/py_filtering.html
#http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html
#http://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html?highlight=findcontours#findcontours

import cv2
import numpy as np
from networktables import NetworkTables
import urllib
import time

cameraURL = 'http://10.42.56.3/mjpg/video.mjpg'#'http://192.168.0.146:4747/mjpegfeed?340x280'
stream = urllib.urlopen(cameraURL)
rioURL = 'roborio-4256-frc.local'
NetworkTables.initialize(server = rioURL)
table = NetworkTables.getTable('axis')
bytes = ''
image_bytes = ''
kernel = np.ones((5,5),np.uint8)
found = False
frames = 0
start = int(time.time()*1000)

while (True):
    bytes = stream.read(1024)
    a = bytes.find('\xff\xd8')
    if (a is not -1 and image_bytes is ''):#hit an image header and need to start new jpg
        b = bytes[a:].find('\xff\xd9')
        if (b is not -1):
            jpg = bytes[a:b+2]
            image_bytes = ''
            found = True
        else:
            image_bytes += bytes[a:]
    elif (a is -1 and image_bytes is not ''):#working through an intermediate section
        b = bytes.find('\xff\xd9')
        if (b is not -1):
            jpg = image_bytes + bytes[:b+2]
            image_bytes = ''
            found = True
        else:
            image_bytes += bytes
    elif (a is not -1 and image_bytes is not ''):#hit an image header and need to complete old jpg
        b = bytes.find('\xff\xd9')
        jpg = image_bytes + bytes[:b+2]
        image_bytes = bytes[a:]
        found = True
    if (found):
        frames += 1
        print(frames*1000/(int(time.time()*1000) - start))
        frame = cv2.imdecode(np.fromstring(jpg, dtype = np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('raw', frame)
        #-----------------------------------------------------------------------
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        v = hsv[:,:,2]
        v[v >= 130] = 255
        v[v < 130] = 0
        hsv[:,:,2] = v

        #morphology: http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html
        closed = cv2.morphologyEx(v, cv2.MORPH_CLOSE, kernel)
        ret, contours, hierarchy = cv2.findContours(closed, mode = cv2.RETR_EXTERNAL, method = cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            #hull = cv2.convexHull(contour, clockwise = False, returnPoints = False)
            #epsilon = 0.1*cv2.arcLength(contour, True)
            #approx = cv2.approxPolyDP(contour, epsilon, True)
            hull = cv2.convexHull(contour)
            cv2.drawContours(hsv, contour, -1, (60,100,100), -1)
            print(cv2.isContourConvex(contour))

        #cv2.drawContours(hsv, contours, -1, (60,100,100), -1)
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        #-----------------------------------------------------------------------
        cv2.imshow("frame", frame)
        found = False
        ch = 0xFF & cv2.waitKey(1)
        if ch == 27:
            break

cv2.destroyAllWindows()
