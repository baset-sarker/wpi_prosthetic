# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import time
time.sleep(2)
import cv2
from ST_VL6180X import VL6180X
from ADXL345 import adxl_default,getAxes


from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference
from periphery import GPIO


import serial
#Seiral on  pins 29/31 (9600 baud) to arduino 29->Rx, 31->Tx
ser = serial.Serial('/dev/ttyS1',
                    baudrate=9600,
					parity=serial.PARITY_NONE,
					stopbits=serial.STOPBITS_ONE)



#hand state  can be OPEN_HAND,CLOSE_HAND,GRUB_OBJECT
#initialization
hand_state = 'CLOSE_HAND'
button = GPIO("/dev/gpiochip0", 39, "in")  # pin 40
pin_38_out_led   = GPIO("/dev/gpiochip0", 38, "out")  # pin 38
#button2 = GPIO("/dev/gpiochip0", 13, "in")  # pin 36

#####################################
########### Modify here #############
# this are the main function to send 
# command to open and close hand
#####################################
def open_hand_command():
    pin_38_out_led.write(True)
    ser.write(serial.to_bytes([0x4C,0x12,0x01,0x00,0x03,0x40,0xFB,0x02,0x7a,0x4C,0x4C]))
    
def close_hand_command():
    pin_38_out_led.write(False)
    ser.write(serial.to_bytes([0x4C,0x12,0x01,0x00,0x03,0x40,0xFB,0x02,0x7a,0x4C,0x4C]))
# Modification end



#initial state set close hand
pin_38_out_led.write(False)
close_hand_command()  #close hand
#end simulation


#Initialize and report Sensor 0
sensor0_i2cid = 0x29
sensor0 = VL6180X(sensor0_i2cid)
sensor0.get_identification()
if sensor0.idModel != 0xB4:
    print("Not Valid Sensor, Id reported as ",hex(sensor0.idModel))
else:
    print("Valid Sensor, ID reported as ",hex(sensor0.idModel))


#bus = sensor0.default_settings()
#adxl default setting
#adxl_default(bus)

          
def check_and_open_hand():
    global bus,hand_state
    
    while(True):
        button_value = button.read()
        print("Object grubed, Press button to release","button value",button_value)
        if button_value == False: # if connected to 
            hand_state = "OPEN_HAND"
            open_hand_command()  
            time.sleep(3)
            break



# this function change the state of hand 
def check_and_change_state(detection_percent,bbox_ratio):
    global hand_state
    # get distance 
    distance0 = sensor0.get_distance()
    print("Distance: ",distance0)

    #OPEN_HAND,CLOSE_HAND,GRUB_OBJECT
    if hand_state == "CLOSE_HAND":
        if detection_percent > 85 and bbox_ratio > 20 and distance0 < 150 :
            hand_state = "OPEN_HAND"
            open_hand_command()
            time.sleep(3)

    elif hand_state == "OPEN_HAND":
        if detection_percent > 85 and bbox_ratio > 50 and (distance0 > 40 and distance0 < 70):
            hand_state = "GRUB_OBJECT"
            close_hand_command()
            time.sleep(3) 
            check_and_open_hand()

        elif bbox_ratio < 20 and distance0 > 100:
            hand_state = "CLOSE_HAND"
            close_hand_command()
            time.sleep(3)
            

def calculate_framerate(frame_rate_calc,t1,freq):
    print('FPS: {0:.2f}'.format(frame_rate_calc))
    # Calculate framerate
    t2 = cv2.getTickCount()
    time1 = (t2-t1)/freq
    frame_rate_calc= 1/time1
    return frame_rate_calc


def main():
    global hand_state
    default_model = 'model/efficientdet-lite-pchallange2022_edgetpu.tflite'
    default_labels = 'model/pchallange2022-labels.txt'
    threshold = 0.1 
    top_k = 3 
    
    interpreter = make_interpreter(default_model)
    interpreter.allocate_tensors()
    labels = read_label_file(default_labels)
    inference_size = input_size(interpreter)

    cap = cv2.VideoCapture(0)

    # Initialize frame rate calculation
    frame_rate_calc = 1
    freq = cv2.getTickFrequency()



    while cap.isOpened():
    
        #pin_38_out_led.write(True) 
        if hand_state == "OPEN_HAND" or hand_state == 'CLOSE_HAND':
   
            t1 = cv2.getTickCount()
            ret, cv2_im = cap.read()
            if not ret:
                #pin_38_out_led.write(False)
                break
        
            cv2_im = cv2.resize(cv2_im,inference_size)
            cv2_im = cv2.rotate(cv2_im, cv2.ROTATE_90_COUNTERCLOCKWISE)
            cv2_im_rgb = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
            run_inference(interpreter, cv2_im_rgb.tobytes())
            objs = get_objects(interpreter, threshold)[:top_k]

            cv2_im,percent,bbox_ratio = append_objs_to_img(cv2_im, inference_size, objs, labels)
            check_and_change_state(percent,bbox_ratio)
  
            frame_rate_calc = calculate_framerate(frame_rate_calc,t1,freq)
            cv2.imshow('Vision Enable Hand', cv2_im)
        else:
            #pin_38_out_led.write(False) 
            check_and_open_hand()

        
        print("#Hand State= ",hand_state) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    pin_38_out_led.write(False) 
    cap.release()
    cv2.destroyAllWindows()

    #close pin
    pin_38_out_led.close()
    ser.close()
    button.close()


def append_objs_to_img(cv2_im, inference_size, objs, labels):
    height, width, channels = cv2_im.shape
    scale_x, scale_y = width / inference_size[0], height / inference_size[1]
    percent = 0
    bbox_ratio = 0
    b_area = 0

    for obj in objs:

        #box area  and ratio calculation
        bbox = obj.bbox.scale(scale_x, scale_y)
        x0, y0 = int(bbox.xmin), int(bbox.ymin)
        x1, y1 = int(bbox.xmax), int(bbox.ymax)

        b_area = (x1-x0) * (y1-y0)
        img_area = height * width

        bbox_ratio = (b_area/img_area)*100
        #print("img_area: ",img_area,"\nbox_area: ",b_area,"\nBox Ratio: ",bbox_ratio)
        print("Box Ratio: ",bbox_ratio)
    

        percent = int(100 * obj.score)
        label = '{}% {}'.format(percent, labels.get(obj.id, obj.id))
        print("Percent",percent)
        
        if percent > 85:
            cv2_im = cv2.rectangle(cv2_im, (x0, y0), (x1, y1), (0, 255, 0), 2)
            cv2_im = cv2.putText(cv2_im, label, (x0, y0+30),
                             cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)

            return cv2_im,percent,bbox_ratio

    percent = 0
    bbox_ratio = 0
    b_area = 0

    return cv2_im,percent,bbox_ratio



if __name__ == '__main__':
    main()
