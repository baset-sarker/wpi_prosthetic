# importing OpenCV library
from cv2 import cv2
import os  

import datetime



if not os.path.exists('images'):
    os.makedirs('images')


cap = cv2.VideoCapture(0)


while(cap.isOpened()):
    ret, frame = cap.read()

    cv2.imshow('frame',frame)

    date_string = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    cv2.imwrite("images/"+date_string+".jpg", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
  


cap.release()
cv2.destroyAllWindows()
  

