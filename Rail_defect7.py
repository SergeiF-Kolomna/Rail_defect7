import cv2
import numpy as np
import PySimpleGUI as sg
import sys

# -*- coding: utf-8 -*-


point1 = None
point2 = None
frame_start = None
frame_end = None
frame_resizing = False
image = None
image_mini = None
threshold_value = 207
etalon_line = 100
scale_percent = 30 # percent of original size. To compress the image
names = []
dark_spots_dict = {}

def calculate_distance(p1, p2):
    return (p2[0] - p1[0]) #np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def calculate_area(distance, pixel_per_cm):
    return ((etalon_line**2) * distance / (pixel_per_cm*etalon_line)** 2) #(distance / pixel_per_cm) ** 2

def calculate_dimensions(cropped_image, pixel_per_cm):
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dark_spots = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 0:
            dimensions = calculate_area(area, pixel_per_cm)
            if dimensions > 0.1 and dimensions < 5.1:  # Check if area is more than 0,1 sq.cm. and less then 5,1 sq.sm
                (x, y, w, h) = cv2.boundingRect(contour)

                # Draw rectangle around the dark spot
                cv2.rectangle(cropped_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Store the detected dark spot
                dark_spots.append((x, y, w, h, dimensions))

    return cropped_image, dark_spots

def mouse_callback(event, x, y, flags, param):
    global point1, point2, frame_start, frame_end, frame_resizing, image_mini

    if event == cv2.EVENT_LBUTTONDOWN:
        if frame_start is None:
            frame_start = (x, y)
        elif frame_end is None:
            frame_end = (x, y)
            frame_resizing = True

    elif event == cv2.EVENT_MOUSEMOVE:
        if frame_resizing:
            frame_end = (x, y)
            temp_image = image_mini.copy()
            cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
            cv2.imshow("Image", temp_image)

    elif event == cv2.EVENT_LBUTTONUP:
        frame_resizing = False
        temp_image = image_mini.copy()
        cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
        cv2.imshow("Image", temp_image)

        # Set point1 and point2 when frame selection is complete
        if frame_start and frame_end:
            point1 = frame_start
            point2 = frame_end

def on_key(event):
    global point1, point2, image_mini, frame_start, frame_end

    if event == ord('a') and frame_start and frame_end:
        frame_start = (min(frame_start[0], frame_end[0]), min(frame_start[1], frame_end[1]))
        frame_end = (max(frame_start[0], frame_end[0]), max(frame_start[1], frame_end[1]))

        if frame_start[0] == frame_end[0] or frame_start[1] == frame_end[1]:
            print("Invalid frame size. Please try again.")
            return

        cropped_image = image_mini[frame_start[1]:frame_end[1], frame_start[0]:frame_end[0]]

        pixel_per_cm = calculate_distance(point1, point2) / etalon_line
        cropped_image_with_dimensions, dark_spots = calculate_dimensions(cropped_image, pixel_per_cm)

        cv2.imshow("Cropped Image", cropped_image_with_dimensions)

        return dark_spots

def listbox_drawing(lst):
    global window_list

    event, values = window_list.read()
    print(event, values)
    #if event in (sg.WIN_CLOSED, 'Exit'):
    #    break
    
    if event == 'Add':
        names.append(values['-INPUT-'])
        window_list['-LIST-'].update(names)
        msg = "A new item added : {}".format(values['-INPUT-'])
        window_list['-MSG-'].update(msg)
    if event == 'Remove':
        val = lst.get()[0]
        names.remove(val)
        window_list['-LIST-'].update(names)
        msg = "A new item removed : {}".format(val)
        window['-MSG-'].update(msg)
        #window_list.close()

def on_trackbar(val):
    global threshold_value
    threshold_value = val
    cv2.imshow("Image", image_mini)


    
#*Рисуем интерфейс*
#Open file
layout = [
            [sg.Text('File'), sg.InputText(), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
         ]
window = sg.Window('Open file to find defects', layout)
#Window for list was here
lst = sg.Listbox(names, size=(20, 4), font=('Arial Bold', 14), expand_y=True, enable_events=True, key='-LIST-')
layout = [[sg.Input(size=(20, 1), font=('Arial Bold', 14), expand_x=True, key='-INPUT-'),
   sg.Button('Add'),
   sg.Button('Remove'),
   sg.Button('Exit')],
   [lst],
   [sg.Text("", key='-MSG-', font=('Arial Bold', 14), justification='center')]
]
window_list = sg.Window('Listbox Example', layout, size=(600, 200))

while True:
    event, values = window.read()
    if event in (None, 'Exit', 'Cancel'):
        break

    if event == 'Submit':
        image_path = values[0] 

        #image_path = r'C:\Users\Фокин\source\repos\Rail_defect5\image_test2.jpg'
        #image_path = r'E:\AAA\image_test2.jpg'
        #image_path = 'E:\БББ\image_test2.jpg'
        #

        image = cv2.imread(image_path)
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", mouse_callback)
        cv2.createTrackbar("Threshold", "Image", threshold_value, 255, on_trackbar)
        
        #compress image
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        image_mini = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        #
        
        while True:
            cv2.imshow("Image", image_mini)
            key = cv2.waitKey(0)

            if key == ord("q"):
                break

            if (key == ord("a") or key == ord("A") or key == ord("ф") or key == ord("Ф")) and frame_start and frame_end:
                dark_spots = on_key(key)
                if dark_spots:
                    # формируем словарь
                    numbers = list(range(0, len(dark_spots)))
                    dark_spots_dict =dict(zip(numbers, dark_spots))
                    #-=-
                    #event, values = window_list.read()
                    #print(event, values)
                    for i in range(len(dark_spots_dict)):
                        names.append(str(i))
                    window_list.update(names)

                    for dark_spot in dark_spots:
                        temp_image = image_mini.copy()
                        (x, y, w, h, dimensions) = dark_spot
                        cv2.rectangle(temp_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (0, 0, 255), 2)

                        # Add dimensions text to the dark spot
                        width_cm = w / (calculate_distance(point1, point2)/etalon_line)
                        height_cm = h / (calculate_distance(point1, point2)/etalon_line)
                        cv2.putText(temp_image, f"Square: {dimensions:.5f} cm^2", (x + frame_start[0], y + frame_start[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        cv2.putText(temp_image, f"Width: {width_cm:.5f} cm", (x + frame_start[0], y + frame_start[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        cv2.putText(temp_image, f"Height: {height_cm:.5f} cm", (x + frame_start[0], y + frame_start[1] + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                        cv2.imshow("Image", temp_image)
                        cv2.waitKey(0)


cv2.destroyAllWindows()

