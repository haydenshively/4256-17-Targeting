import cv2
import numpy as np

def slope(pointA, pointB):
    try:
        return (float(pointA[0] - pointB[0])/float(pointA[1] - pointB[1]))
    except ZeroDivisionError:
        return 0

class SmartContours(object):
    def __init__(self, contours):
        self.contours = contours
    def think(self, targetAspect, approxTightness):
        self.rectangles = AccessRects()
        for contour in self.contours:
            epsilon = (1 - approxTightness)*cv2.arcLength(contour, True)
            shape = cv2.approxPolyDP(contour, epsilon, True)
            if (len(shape) == 4):
                avgPoint = np.mean(shape, axis = 0)[0]
                m, mabs = 0, 0
                for point in shape:
                    m += slope(avgPoint, point[0])
                    mabs += abs(slope(avgPoint, point[0]))
                aspectRatio = mabs/4
                confidence = 100 - 100*abs(targetAspect - aspectRatio)/targetAspect
                uniformity = 100 - 100*abs(m/4)
                self.rectangles.new(shape[:,0], avgPoint, confidence, uniformity)
    def center(self):
        avgPoint = np.mean(self.rectangles._arr, axis = 0)[1]
        return int(avgPoint[0]), int(avgPoint[1])

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
