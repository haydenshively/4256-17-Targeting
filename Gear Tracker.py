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
kernel = np.ones((30,10),np.uint8)
found = False

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
        frame = cv2.imdecode(np.fromstring(jpg, dtype = np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('raw', frame)
        #-----------------------------------------------------------------------
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        v = hsv[:,:,2]
        v[v >= 130] = 255
        v[v < 130] = 0
        hsv[:,:,2] = v
        
        opened = cv2.morphologyEx(v, cv2.MORPH_OPEN, kernel)
        ret, contours, hierarchy = cv2.findContours(opened, mode = cv2.RETR_EXTERNAL, method = cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            contourRectangle = np.int0(cv2.boxPoints(cv2.minAreaRect(contour)))
            avg = np.mean(contourRectangle, 0)
            ratio = abs((contourRectangle[0][1] - avg[1])/(contourRectangle[0][0] - avg[0]))
            print(abs(ratio))
            cv2.drawContours(hsv, [contourRectangle], 0, (120,255,255), 2)

        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        #-----------------------------------------------------------------------
        cv2.imshow("frame", frame)
        found = False
        ch = 0xFF & cv2.waitKey(1)
        if ch == 27:
            break

cv2.destroyAllWindows()
