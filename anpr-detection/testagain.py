import cv2
cap = cv2.VideoCapture("models/test_clip.mp4")
print(cap.get(cv2.CAP_PROP_FPS))