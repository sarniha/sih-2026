import cv2

video_path = "models/test_clip.mp4"
cap = cv2.VideoCapture(video_path)

print("Opened:", cap.isOpened())
print("Frame count (reported):", cap.get(cv2.CAP_PROP_FRAME_COUNT))
print("FPS:", cap.get(cv2.CAP_PROP_FPS))
print("Width x Height:", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "x", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

ret, frame = cap.read()
print("First frame read success:", ret)
if ret:
    print("Frame shape:", frame.shape)

cap.release()