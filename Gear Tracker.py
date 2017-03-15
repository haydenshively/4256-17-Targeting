import cv2
import numpy as np
from networktables import NetworkTables
import urllib
import time
import copy
from shivelyCV import SmartContours

#{DEFINE FUNCTIONS}
def slope(pointA, pointB):
    try:
        return (float(pointA[0] - pointB[0])/float(pointA[1] - pointB[1]))
    except ZeroDivisionError:
        return 0
#{SETUP STREAM}
cameraURL = 'http://10.42.56.3/mjpg/video.mjpg'
stream = urllib.urlopen(cameraURL)
found = False
bytes = ''
image_bytes = ''
#{SETUP NETWORKTABLES}
rioURL = '10.42.56.2'#'roborio-4256-frc.local'
NetworkTables.initialize(server = rioURL)
sender = NetworkTables.getTable('edison')
receiver = NetworkTables.getTable('LeapStick')#TODO
#{SET PARAMETERS}
kernel = np.ones((20,5),np.uint8)
aspectRatio = .38
confidenceThresh = 80
uniformityThresh = 80
#{MAIN}
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
        frame = cv2.imdecode(np.fromstring(jpg, dtype = np.uint8), -1)
        #-----------------------------------------------------------------------
        redmask = copy.deepcopy(frame);
        filteredFrame = copy.deepcopy(frame);
        redmask[:,:,0] = redmask[:,:,2]
        redmask[:,:,1] = redmask[:,:,2]
#        filtered = cv2.subtract(frame, redmask)#color filter based on blue LED
        cv2.subtract(frame, redmask, filteredFrame)#color filter based on blue LED

        l = cv2.cvtColor(filteredFrame, cv2.COLOR_BGR2LUV)[:,:,0]
        l[l >= 20] = 255
        l[l < 20] = 0

        closed = cv2.morphologyEx(l, cv2.MORPH_CLOSE, kernel)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

        ret, contours, hierarchy = cv2.findContours(opened, mode = cv2.RETR_LIST, method = cv2.CHAIN_APPROX_SIMPLE)
        contours = SmartContours(contours)
        contours.think(targetAspect = aspectRatio)

        centers = []
        for i in range(0, contours.rectangles.count()):
            if (contours.rectangles.confidence(i) > confidenceThresh and contours.rectangles.uniformity(i) > uniformityThresh):
                cv2.circle(frame, contours.rectangles.center(i), 6, (255, 102, 178), thickness = -1)
                centers.append(contours.rectangles.center(i))
        cv2.putText(frame, str(len(centers)), (0, 0), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 102, 178), bottomLeftOrigin = True)
        sender.putNumber('targets', len(centers))
        if len(centers) is 2:
            cv2.line(frame, centers[0], centers[1], (255, 102, 178), thickness = 4)
            sender.putNumber('gear x', (centers[0][0] + centers[1][0])/2)
            sender.putNumber('gear y', (centers[0][1] + centers[1][1])/2)
        elif len(centers) is 1:
            sender.putNumber('gear x', centers[0][0])
            sender.putNumber('gear y', centers[0][1])
        else:
            sender.putNumber('gear x', 0)
            sender.putNumber('gear y', 0)
            #sender.delete('gear x')
            #sender.delete('gear y')
           
        #-----------------------------------------------------------------------
        #cv2.imshow('l channel', l)
        #cv2.imshow('post morphs', opened)
        cv2.imshow('frame', frame)
        found = False
        ch = 0xFF & cv2.waitKey(1)
        if (ch == 27):
            break

cv2.destroyAllWindows()
