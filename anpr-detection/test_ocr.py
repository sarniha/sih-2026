import cv2, re, easyocr

reader = easyocr.Reader(['en'], gpu=False)

def read_plate(plate_img):
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    results = reader.readtext(thresh)
    if not results:
        return None, 0.0

    text = " ".join(r[1] for r in results).upper().strip()
    conf = min(r[2] for r in results)
    return text, conf

def clean_plate(raw_text):
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}', cleaned)
    return match.group(0) if match else cleaned

# --- load and pad the crop ---
img = cv2.imread('models/image.png')
pad = 5
x1, y1, x2, y2 = 182, 475, 266, 501   # your original box
x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
x2, y2 = x2 + pad, y2 + pad

plate_crop = img[y1:y2, x1:x2]
cv2.imwrite('models/plate_crop_padded.png', plate_crop)

raw_text, conf = read_plate(plate_crop)
print("Raw OCR text:", raw_text)
print("Confidence:", conf)
print("Cleaned plate:", clean_plate(raw_text) if raw_text else None)