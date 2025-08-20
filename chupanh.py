import cv2

cam = cv2.VideoCapture(0)
cv2.namedWindow("Chụp ảnh (nhấn SPACE để chụp, ESC để thoát)")

img_counter = 0

while True:
    ret, frame = cam.read()
    if not ret:
        break
    cv2.imshow("Chụp ảnh", frame)

    k = cv2.waitKey(1)
    if k % 256 == 27:
        break
    elif k % 256 == 32:
        name = input("Nhập tên để lưu (không có .jpg): ")
        img_name = f"faces/{name}.jpg"
        cv2.imwrite(img_name, frame)
        print(f"Đã lưu: {img_name}")
        img_counter += 1

cam.release()
cv2.destroyAllWindows()