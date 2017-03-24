import cv2
import numpy as np
from networktables import NetworkTables
import urllib
import time
from shivelyCV import SmartContours

#{DEFINE FUNCTIONS}
def slope(pointA, pointB):
    try:
        return (float(pointA[0] - pointB[0])/float(pointA[1] - pointB[1]))
    except ZeroDivisionError:
        return 0
def sendToNT(barPos):
    rockefeller.putNumber('auto mode', barPos)
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
rockefeller = NetworkTables.getTable('rockefeller')
leapstick = NetworkTables.getTable('LeapStick')
#{SET PARAMETERS}
gesture = 'clockwise'
kernel = np.ones((20,5),np.uint8)
aspectRatio = .38
confidenceThresh = 80
uniformityThresh = 80
#{SETUP WINDOWS}
cv2.namedWindow('peg finder')
cv2.createTrackbar('auto mode', 'peg finder', 1, 2, sendToNT)
inAuto = True
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
    if found:
        frame = cv2.imdecode(np.fromstring(jpg, dtype = np.uint8), -1)
        gesture = leapstick.getString('n Circle gesture', 'none') if leapstick.getString('n Circle gesture', 'none') != 'none' else gesture#LeapMotion controls
        if (gesture == 'clockwise'):#AUTONOMOUS ALGORITHM
            if not inAuto:
                cv2.destroyWindow('driver helper')
                cv2.namedWindow('peg finder')
                cv2.moveWindow('peg finder', 0, 0)
                cv2.createTrackbar('auto mode', 'peg finder', 1, 2, sendToNT)
                inAuto = True
            redmask = frame.copy()
            redmask[:,:,0] = redmask[:,:,2]
            redmask[:,:,1] = redmask[:,:,2]
            filtered = cv2.subtract(frame, redmask)#color filter based on blue LED

            l = cv2.cvtColor(filtered, cv2.COLOR_BGR2LUV)[:,:,0]
            l[l >= 20] = 255
            l[l < 20] = 0

            opened = cv2.morphologyEx(l, cv2.MORPH_OPEN, kernel)
            frame = cv2.cvtColor(l, cv2.COLOR_GRAY2BGR)
            #cv2.imshow('post morphs', opened)#cv2.findContours() changes 'opened', so we need to show it here

            ret, contours, hierarchy = cv2.findContours(opened, mode = cv2.RETR_LIST, method = cv2.CHAIN_APPROX_SIMPLE)
            contours = SmartContours(contours)
            contours.think(targetAspect = aspectRatio)

            centers = []
            for i in range(0, contours.rectangles.count()):
                if (contours.rectangles.confidence(i) > confidenceThresh and contours.rectangles.uniformity(i) > uniformityThresh):
                    cv2.circle(frame, contours.rectangles.center(i), 6, (102, 102, 255), thickness = -1)
                    centers.append(contours.rectangles.center(i))
            #cv2.putText(frame, str(len(centers)), (0, 0), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 102, 178), bottomLeftOrigin = True)
            sender.putNumber('targets', len(centers))
            if len(centers) is 2:
                cv2.line(frame, centers[0], centers[1], (102, 102, 255), thickness = 4)
                sender.putNumber('peg x', (centers[0][0] + centers[1][0])/2)
                sender.putNumber('peg y', (centers[0][1] + centers[1][1])/2)
            elif len(centers) is 1:
                sender.putNumber('peg x', centers[0][0])
                sender.putNumber('peg y', centers[0][1])
            else:
                sender.putNumber('peg x', 0)
                sender.putNumber('peg y', 0)
            #-----------------------------------------------------------------------
            cv2.imshow('peg finder', cv2.pyrUp(cv2.pyrUp(frame)))
        else:#TELEOP ALGORITHM
            if inAuto:
                cv2.destroyWindow('peg finder')
                cv2.namedWindow('driver helper')
                cv2.moveWindow('driver helper', 0, 0)
                inAuto = False
            h, w, d = frame.shape
            cropped = frame[h/2:h,:,:]

            bgmask = cropped.copy()
            bgmask[:,:,1] = bgmask[:,:,1]/5#take out 1/5th of green
            bgmask[:,:,2] = bgmask[:,:,0] + bgmask[:,:,1]#remove blue and green noise from red channel
            filtered = cv2.subtract(cropped, bgmask)

            filtered[filtered[:,:,2] < 10] = (0,0,0)#red thresholding
            filtered = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
            filtered[filtered >= 20] = 255

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            frame[:,:,2] = cv2.equalizeHist(frame[:,:,2])/3#brighten image for drivers
            cropped = frame[h/2:h,:,:]#must identify cropped again because cv2 functions ruin reference to frame
            cropped[:,:,2] = np.maximum(cropped[:,:,2], filtered)#highlight gears
            frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

            if rockefeller.getBoolean('lift down', True):
                cv2.rectangle(frame, (10, h/3), (h/3, 10), (0, 255, 0), -1)
            else:
                cv2.rectangle(frame, (10, h/3), (h/3, 10), (0, 0, 255), -1)
            if rockefeller.getBoolean('clamp open', True):
                cv2.rectangle(frame, (w - h/3 - 10, h/3), (w - 10, 10), (0, 255, 0), -1)
            else:
                cv2.rectangle(frame, (w - h/3 - 10, h/3), (w - 10, 10), (0, 0, 255), -1)
            #-----------------------------------------------------------------------
            cv2.imshow('driver helper', cv2.pyrUp(cv2.pyrUp(frame)))

        found = False
        ch = 0xFF & cv2.waitKey(1)
        if (ch == 27):
            break

cv2.destroyAllWindows()
