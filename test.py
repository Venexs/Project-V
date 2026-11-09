import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera 0 FAILED")
else:
    print("Camera 0 OK")

#cap.release()
