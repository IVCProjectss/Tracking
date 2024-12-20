import cv2
import numpy as np

class ObjectTracking:
    def __init__(self):
        self.track_window = None
        self.roi_hist = None
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        self.roi_selected = False

    def initialize_camera(self):
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            print("Erro ao inicializar a câmera.")
            exit()
        return cam

    def initialize_tracking(self, frame):
        print("Press 'r' to select ROI.")
        roi = cv2.selectROI("Select ROI", frame, fromCenter=False)
        x, y, w, h = roi
        self.track_window = (x, y, w, h)

        # Convert the ROI to HSV and compute the histogram
        roi_frame = frame[y:y + h, x:x + w]
        hsv_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_roi, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
        self.roi_hist = cv2.calcHist([hsv_roi], [0], mask, [16], [0, 180])
        cv2.normalize(self.roi_hist, self.roi_hist, 0, 255, cv2.NORM_MINMAX)
        self.roi_selected = True  # Mark that ROI has been selected

    def track_object(self, frame):
        # Convert the frame to HSV and calculate the back projection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        dst = cv2.calcBackProject([hsv], [0], self.roi_hist, [0, 180], 1)

        # Apply the back projection mask
        dst &= cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))

        # Apply CamShift to track the object
        ret, self.track_window = cv2.CamShift(dst, self.track_window, self.term_crit)
        pts = cv2.boxPoints(ret)
        pts = np.int0(pts)
        x_center = int(ret[0][0])

        # Draw the tracking box on the frame
        annotated_frame = cv2.polylines(frame, [pts], True, 255, 2)

        return annotated_frame, x_center