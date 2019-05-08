from collections import deque
import numpy as np
import cv2
import time
from timeit import default_timer as timer
import warnings
import matplotlib.pyplot as plt
import math
import serial
from math import tan
from math import pi

#   Initialize the serial port
#   --------
ser = serial.Serial('COM3', 57600, timeout=0, parity=serial.PARITY_NONE, rtscts=1)
#   --------

warnings.simplefilter('ignore', np.RankWarning)
# warnings.filterwarnings('error')
# np.seterr(all='raise')


#   Set the threshold for color black in HSV space`
blackLower = np.array([0, 0, 0])
blackUpper = np.array([180, 255, 46])


#   Initialize the length for tracking coordinates
my_buffer = 64
ptsYZL = deque(maxlen=my_buffer)  # comes from laptop camera (bad coords)
ptsXZJ = deque(maxlen=my_buffer)  # comes from Josh camera (bad coords)


ptsRealX = deque(maxlen=my_buffer)
ptsRealY = deque(maxlen=my_buffer)
ptsRealZ = deque(maxlen=my_buffer)

#   Turn on the camera
camera1 = cv2.VideoCapture(1)  # Josh's Camera <-- will be looking at the ball, the ball will be crossing the frame
camera2 = cv2.VideoCapture(0)  # Laptop's Camera <-- will be in front of the camera, the ball will be in the frame

#   Wait for 2 seconds
time.sleep(2)

#   Make the camera data Arrays

# ---------------------------
time_lst = np.array([0])
timeTilPrediction = 0
movement = np.array([0])
other_camera = np.array([0])
# ---------------------------

# Initialize the read data from the PSoC (I hope)
# TODO: transfer the algorithm from the other file
# ---------------------------

# ---------------------------

# Make the function to give the data to the PSOC
# TODO: get the working function from the other file
# ---------------------------

# ---------------------------


# need to make a function that takes the data from the deque and returns an array
# ---------------------------
def toLst(dequeArray):
    returnLst = []
    for integer, _ in enumerate(range(my_buffer)):
        returnLst.append(dequeArray[integer])
    return returnLst
# ---------------------------

# Define camera constants (NOTE: make sure that the robot is a distance 2A from the laptop camera)
# NOTE: these are in decimeters. Why? because that is what I chose
# ---------------------------
A = 10
B = 10
C = 10
# ---------------------------

#   Detect color black
while True:
    #   --------
    before = timer()
    #   --------
    #   Read the frames
    _, frame = camera1.read()
    _, frame2 = camera2.read()

    #   Change the frames to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)

    #   Build a mask based on threshold
    mask = cv2.inRange(hsv, blackLower, blackUpper)
    mask2 = cv2.inRange(hsv2, blackLower, blackUpper)

    #   Erosion
    mask = cv2.erode(mask, None, iterations=2)
    mask2 = cv2.erode(mask2, None, iterations=2)

    #   Dilation, remove the noise by erosion and dilation
    mask = cv2.dilate(mask, None, iterations=2)
    mask2 = cv2.dilate(mask2, None, iterations=2)

    #   Detect the contour
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    contours2 = cv2.findContours(mask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    #   Initialize the centroid
    center = None
    center2 = None

    #   If there is a contour
    if len(contours) > 0:  # Josh's camera for ball crossing the frame

        #   Find the contour with the largest area
        c = max(contours, key=cv2.contourArea)

        #   Determine the circle of the largest contour
        ((y, z1), radius) = cv2.minEnclosingCircle(c)

        #   Calculate the moment of the contour
        M = cv2.moments(c)

        #   Calculate the centroid
        center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))

        #   Plot only when the radius is greater than 0
        if radius > 0:
            cv2.circle(frame, (int(y), int(z1)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            # print('y coordinate: %s, z1 coordinate: %s'%(y, z1))

            #  Add the centroid to the left of the list
            ptsYZL.appendleft(center)


    if len(contours2) > 0:
        #   Find the contour with the largest area
        c2 = max(contours2, key=cv2.contourArea)

        #   Determine the circle of the largest contour
        ((x, z2), radius2) = cv2.minEnclosingCircle(c2)

        #   Calculate the moment of the contour
        M2 = cv2.moments(c2)

        #   Calculate the centroid
        center2 = (int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"]))

        #   Plot only when the radius is greater than 0
        if radius2 > 0:
            cv2.circle(frame2, (int(x), int(z2)), int(radius2), (0, 255, 255), 2)
            cv2.circle(frame2, center2, 5, (0, 0, 255), -1)
            #   print('y coordinate: %s, z1 coordinate: %s'%(y, z2))

            #   Add the centroid to the left of the list
            ptsXZJ.appendleft(center2)

    #   Covert pixel coordinates (x,y,z1,z2) to real world coordinates (X,Y,Z)
    # since we are adding to the front of the list, we are always taking the most recent coords
    # this works:
    x_convert = ptsXZJ[0][0] # take most recent recorded X coord from Josh Camera
    y_convert = ptsYZL[0][0] # the most recent recorded Y coord from Laptop camera
    z1_convert = ptsYZL[0][1] # the most recorded Z coord from the laptop camera
    X_real = (tan(pi/2 - 0.7084 + 2.2111e-3*x_convert)*A + B) / (1 - tan(0.6145 - 1.9203e-3*y_convert)*tan(pi/2 - 0.7084 + 2.2111e-3*x_convert))
    Y_real = tan(0.6145 - 1.9203e-3*y_convert)*X_real + A
    Z_real = tan(0.3779-1.5744e-3*z1_convert)*X_real + C
    Real_world_coordinate = (X_real, Y_real, Z_real)
    # ptsXYZ.appendleft(Real_world_coordinate)

    ptsRealX.appendleft(Real_world_coordinate[0])
    ptsRealY.appendleft(Real_world_coordinate[1])
    ptsRealZ.appendleft(Real_world_coordinate[2])

    cv2.imshow('YZ', frame)
    cv2.imshow('XZ', frame2)
    after = timer()
    tme = after - before
    time_lst = np.append(time_lst, [tme])
    timeTilPrediction += tme
    #   print(ptsXY, len(ptsXY))
    # moveX_array = np.array([0])
    # moveY_array = np.array([0])
    # moveX = 0
    # moveY = 0

    # Prediction Starts
    if timeTilPrediction > .25:
        timeTilPrediction = 0  # Once this part of code is executed, we will start the time again from zero

        # the following code will take our 64 coords points and put them into a python list
        # we will then use this list to make a numpy A array for our linear least squares
        realXCoords = toLst(ptsRealX)
        realYCoords = toLst(ptsRealY)
        realZCoords = toLst(ptsRealZ)

        x = np.array(realXCoords)
        y = np.array(realYCoords)
        A = np.vstack([x, np.ones(len(x))]).T # this is our linear least squares matrix
        m, b = np.linalg.lstsq(A, y, rcond=None)[0] # a tuple to satisfy the equation y = mx + b

        # assuming our (zero, zero) is on the same line as our laptop camera
        """
                                    [Robot]        
            ⌄     |~~~~~~~~~~~~~~~~~~~{X}~~~~~~~~~~~~~~~~~~~~~
                  |                  /
                  |                 / 
            A     |                /
                  |               /   
            ^     |              /
        [Josh's]  |             /
        camera]   |            /
            ⌄     |           /
                  |          /
            A     |         /
                  |        /
                  |_______/__________________________________
            ^      [-    B     -][laptop camera][-    B     -]
            _
          / ⌄ \          
         |>{C}<|
          \ ^ /          
        The above is what the following line of code predicts:       
        """
        predictedX = (2 * A - b) / m

        # from above we already have y
        # we now need z
        z = np.array(realZCoords)
        function = np.polyfit(y, z, 2)
        polynomial = np.poly1d(function)
        predictedZ = polynomial(2 * A)


        # This is the Laptop Prediction Logic
        # if len(ptsYZ1) > 6:
        #     timeTilPrediction = 0
        #     #   We want to predict .25 seconds ahead
        #     with warnings.catch_warnings():
        #         warnings.filterwarnings('error')
        #         try:
        #             x = np.array(y_camera_0)
        #             y = np.array(z1_camera_0)
        #             x1 = np.concatenate(x)
        #             y1 = np.concatenate(y)
        #             z1 = np.polyfit(x1, y1, 2)
        #             polyPredict1 = np.poly1d(z1)
        #             # polyPredict = np.polyder(polyPredict)
        #             # print(z)
        #             moveY = polyPredict1(640)
        #             moveY_array = np.append(moveY_array, moveY)
        #             if moveY > 480 or moveY < 0:
        #                 continue
        #             movement = np.append(movement, [moveY])
        #             print('Last Y is', moveY)
        #         except Warning:
        #             moveY = 0
        #
        # #   Camera needs to have root prediction, which it does have
        # if len(ptsXZ2) > 6:
        #     with warnings.catch_warnings():
        #         warnings.filterwarnings('error')
        #         try:
        #             Y = np.array(x_camera_1)
        #             Z = np.array(z2_camera_1)
        #             Y1 = np.concatenate(Y)
        #             Z1 = np.concatenate(Z)
        #             z2 = np.polyfit(Y1, Z1, 2)
        #             polyPredict2 = np.poly1d(z2)
        #             delta = z2[1] * z2[1] - 4 * z2[0] * (z2[2] - moveY)
        #             if delta > 0:
        #                 if Z[0] > Z[1]:
        #                     moveX = (-z2[1] + math.sqrt(delta)) / (2 * z2[0])
        #                     moveX_array = np.append(moveX_array, moveX)
        #                     print('Depth 1 is', moveX)
        #                 else:
        #                     moveX = (-z2[1] - math.sqrt(delta)) / (2 * z2[0])
        #                     moveX_array = np.append(moveX_array, moveX)
        #                     print('Depth 2 is', moveX)
        #             else:
        #                 print('No root')
        #             other_camera = np.append(other_camera, [max(Z[0], Z[1])])
        #         except Warning:
        #             Depth1 = 0
        #             Depth2 = 0
        # y2 = np.array([ptsYZ1[0][0], ptsYZ1[1][0], ptsYZ1[2][0], ptsYZ1[3][0]])
        # z2 = np.array([ptsYZ1[0][1], ptsYZ1[1][1], ptsYZ1[2][1], ptsYZ1[3][1]])
        # x2 = np.polyfit(x2, y2, 2)
        # polyPredict = np.poly1d(x2)
        # polyPredict = np.polyder(polyPredict)
        # moveZ = polyPredict(.25)

    # print("These are the coordinates. X position is: ", moveX, "\n", "Y Position is: ", moveY)
    # sentData = ser.write([moveX, moveY])
    # print(sentData)
    # # send one array of data at a time, will block until the number of bytes is read
    # # Ethan thinks the while loop will not continue until after the number of bytes is read
    # # but Ethan could be wrong
    # # Ethan is wrong.
    # byteArray = ser.read(16)
    # print(byteArray)

    # Exit when press the esc button
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

#   Release the camera
camera1.release()
#   Destroy the windows
cv2.destroyAllWindows()
print(1/np.mean(time_lst))

plt.plot(movement, 'r-', label='ptsYZ1')
plt.plot(other_camera, 'k--', label='ptsXZ2')
plt.show()

plt.plot(moveX_array, moveY_array, 'r--', label='raw coordinates')
plt.show()
