import cv2
import numpy as np

def slope(pointA, pointB):
    try:
        return (float(pointA[0] - pointB[0])/float(pointA[1] - pointB[1]))
    except ZeroDivisionError:
        return 0
def validateAngle(angle):
    if angle < 0:
        return 360 - (abs(angle)%360) if 360 - (abs(angle)%360) < 360 else 0;
    else:
        return angle%360 if angle%360 < 360 else 0

class SmartContours(object):
    def __init__(self, contours):
        self.contours = contours
    def think(self, targetAspect):
        self.rectangles = AccessRects()
        for contour in self.contours:
            rectangle = cv2.minAreaRect(contour)
            center, size, angle = rectangle
            angle = validateAngle(angle)
            shape = np.int0(cv2.boxPoints(rectangle))
            if ((45 < angle < 135) or (225 < angle < 315)):
                aspectRatio = size[1]/size[0]
            else:
                aspectRatio = size[0]/size[1]
            confidence = 100 - 100*abs(targetAspect - aspectRatio)/targetAspect
            uniformity = 100*cv2.contourArea(contour)/(size[0]*size[1])
            self.rectangles.new(shape, center, confidence, uniformity)

class AccessRects(object):
    def __init__(self):
        self._arr = []
    def new(self, shape, center, confidence, uniformity):
        self._arr.append((shape, center, confidence, uniformity))
    def shape(self, i):
        return self._arr[i][0]
    def center(self, i):#tuple: x,y
        return int(self._arr[i][1][0]), int(self._arr[i][1][1])
    def confidence(self, i):
        return self._arr[i][2]
    def uniformity(self, i):
        return self._arr[i][3]
    def count(self):
        return len(self._arr)
