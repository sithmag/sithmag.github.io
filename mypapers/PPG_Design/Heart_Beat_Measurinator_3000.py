# GUI
"""
Calls a series of pySimpleGUI demonstration functions and collects
output for use in GUI lab.
Author: Sithma
Date: 6/9/23
"""
import PySimpleGUI as sg
import numpy as np
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import tkinter as TK
import matplotlib as plt
import datetime
import serial
import time
import sys
import csv
import re

# label the port and define conditions for the serial port
portName="/dev/tty.ESP32sithma-ESP32SPP"
serialPort = serial.Serial(
        port=portName,
        baudrate=115200,
        bytesize=8,
        timeout=2,
        stopbits=serial.STOPBITS_ONE
    )
serialPort.close()
# open the serial port - if it fails, print error message
try:
    serialPort.open()
except:
    print("Port open failed: " + portName)
    for e in sys.exc_info():
        print("  ",e)




HeartRate = 0
def interpretData():
    '''
    Function to read and intepret data from the microcontroller
    Outputs: 
    PulseData = a list of pulse readings from the sensor being received from the microncontroller
    HeartRate = a float representing averaged heart rate value being calculated using Arduino over the 50 pulse readings recorded
    no_data_check = a boolean variable recording whether or not data is being received
    sequence = packet number received from ESP
    button = status of button - 0 = not pressed, 1 = pressed
    '''
    
    
    # initialise important variables for later
    HeartRate = 0
    PulseData = []
    sequence = 0
    button = 0

    if serialPort.isOpen():
        if serialPort.in_waiting > 0:
            serial_string = serialPort.readline().decode("ASCII").strip()
            unpacked_data = serial_string.split(",")
            data_points = []

            if unpacked_data[0] == "No data":
                PulseData = [0] * 50
                HeartRate = 0
                no_data_check = False
                sequence = 0
                
            else:
                no_data_check = True
                for i in range(0, 53):
                    input_string = unpacked_data[i]
                    print(input_string)
                    numeric_string = re.sub(r'[^0-9.]', '', input_string)  # Remove non-numeric characters
                    if 0 <= i < 50:
                        try:
                            value = int(numeric_string)  # Convert the cleaned string to an integer
                        except ValueError:
                            value = 0
                        data_points.append(value)
                        
                    if i == 50: 
                        
                        HeartRate = float(numeric_string)
                    if i == 51:
                        sequence = int(numeric_string)
                    if i == 52:
                        button = int(numeric_string)
                PulseData = data_points
        else:
            PulseData = False
            no_data_check = False
    else:
        PulseData = False
        no_data_check = False
    return PulseData, HeartRate, no_data_check, sequence, button

def saveDataCSV(csv_data, csv_HR_value, file_name='SensorReadings.csv'):
    ''' Takes in csv lists generated from reading data and outputs a file to the computer containing these lists'''
    header = ['Sensor Reading', 'Heart Rate (BPM)']
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(len(csv_data)):
            row = [csv_data[i], csv_HR_value[i]]
            writer.writerow(row)


def HR_Alarm(window, HeartRate, lower, upper):
    '''Creates the alarms for if the heart rate exceeds or falls below maximum and minimum allowable values'''
    time = datetime.datetime.now()
    if 0 < HeartRate < lower:
        window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")}: Heart Rate too low! \n', append=True)
        window["HR alarm"].update(f'Heart Rate too low! \n')
    elif HeartRate > upper:
        window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")}: Heart Rate too high! \n', append=True)
        window["HR alarm"].update(f'Heart Rate too high! \n')
    else:
        window["HR alarm"].update(f'')

def Packets(sequence, last_number, window):
    '''Checks that all the packets have been delivered in order'''
    if sequence != 0:
        if last_number == sequence:
            window["System Log"].update(f"Packet =  {sequence} \n", append = True)
            last_number += 1
        else:
            window["System Log"].update(f"Packets received out of order \n", append = True)
            last_number = sequence
            last_number += 1
    else:
        last_number = 0
        window["System Log"].update(f"Packet = {sequence} \n", append = True)
        last_number += 1
    return sequence, last_number

def system_log():
    '''Creates layout for system log'''
    system_log_layout = [sg.Multiline(size = (75, 15), key = "System Log", autoscroll = True, enable_events = TRUE), sg.Button("Save", key = "Save",  enable_events=TRUE), sg.Button("Exit", enable_events=TRUE)]
    return [system_log_layout]

def HR():
    ''' Creates layout for heart rate graph '''
    heart_rate_layout = [
        [sg.Text('Graph of Heart Rate', font = ("Times New Roman", 20))],
        [sg.Canvas(key = "Heart Canvas")],
    ]
    return heart_rate_layout

def pulse_reading():
    ''' Creates layout for pulse waveform graph'''
    pulse_reading_layout = [
        [sg.Text('Graph of Pulse Reading', font = ("Times New Roman", 20))],
        [sg.Canvas(key = "Pulse Canvas")],
    ]
    return pulse_reading_layout

def sliders():
    ''' Creates layout for sliders'''
    sliders_layout = [
        [sg.Column([[sg.Text("Lower Threshold", key = 'Lower Threshold')], [sg.Slider(orientation='horizontal', range=(0,80), key="Lower HR", enable_events=True)]])],
        [sg.Column([[sg.Text("Upper Threshold", key = 'Upper Threshold')], [sg.Slider(orientation='horizontal', range=(80,160), key="Upper HR", enable_events=True)]])]
    ]
    return sliders_layout

def display_HR():
    '''Creates frame to display current heart rate'''
    HR_Display = [
        [sg.Frame(title = '', layout = [[sg.Text(f'Current Heart Rate: {HeartRate} BPM', font = ("Times New Roman", 26) , key = 'Current HR', size = (25, 2))]])], 
        [sg.Frame(title = '', layout = [[sg.Text(f'', font = ("Times New Roman", 26), text_color= "red", key = 'HR alarm', size = (25, 2))]])]
        ]
    return HR_Display

def addPlot(canvasElement):
    '''
    Takes in canvas element and generates a plot on the canvas with set physical dimensions
    '''
    fig = Figure(figsize=(5, 4))
    canvas = canvasElement.TKCanvas
    figAgg = FigureCanvasTkAgg(fig, canvas)
    ax = fig.add_subplot(1,1,1)
    figAgg.draw()
    figAgg.get_tk_widget().pack(side = "top", fill = "both", expand = 1)
    return ax, figAgg
  
    
    
def create_graph(ax1, ax2, figAgg1, figAgg2, PulseData, HeartRate, pulse_time, HR_time, HR_data, x, y, pulsedatapointcounter, HRdatapointcounter, counter1, counter2, pulse, moving_average):
    ''' 
     Creates plot in given window
    '''
    
    ax1.cla()  
    ax2.cla() 
    ax1.set_title("Pulse")    
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax2.set_title("Heart Rate")    
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("HR (BPM)")
    
    
    if  pulsedatapointcounter < counter1:
        for i in range (pulsedatapointcounter, pulsedatapointcounter + 50):
            pulse[i] = int(PulseData[i%50])
    else:
        for i in PulseData:
            pulse = np.append(pulse, int(i))
        
    if HRdatapointcounter < counter2:
        HR_data[HRdatapointcounter] = HeartRate
    else:
        HR_data = np.append(HR_data, HeartRate)
        for i in range (0,4):
            moving_average[i] = np.mean(HR_data[HRdatapointcounter - counter2:HRdatapointcounter])
    
    if len(HR_data) <= counter2:
        ax1.plot(pulse_time, pulse)
        ax2.plot(HR_time, HR_data, label = "HR (BPM)")
        
    else:
        ax1.plot(pulse_time, pulse[pulsedatapointcounter - 200:pulsedatapointcounter])
        ax2.plot(HR_time, HR_data[HRdatapointcounter - 4:HRdatapointcounter], label = "Current HR")
        ax2.plot(HR_time, moving_average, label="Moving Average")
        
    HRdatapointcounter += 1
    pulsedatapointcounter += 50
    
    if HRdatapointcounter >= 4:
        x += 1
        y += 1
    ax2.legend()
    
    figAgg1.draw()
    figAgg2.draw()
    figAgg1.flush_events()
    figAgg2.flush_events()


    return HR_data, HRdatapointcounter, pulsedatapointcounter, pulse, x, y
   
    


    




def create_window():
    ''' 
    Creates entire GUI window, compiling existing functions that output layouts into one formatted output
    '''
    # Define lower and upper thresholds to be 
    lower = 0
    upper = 0
    # Create window with title and theme etc.
    sg.theme("BluePurple")
    layout  = [
        [sg.Text('Heartbeat Measurinator 3000', font =("Times New Roman", 40), justification='center')],
        [
            [sg.Column(pulse_reading(), key = 'Pulse Graph'),
             sg.Column(HR(), key = 'Heart Rate Graph', justification='center'), ]
        ],
        [
            [sg.Column(sliders()),
            sg.Column(system_log()),
            sg.Column(display_HR())]
        ]
    ]
    # label sliders and create window with title
    slider_keys = ["Lower HR", "Upper HR"]
    window = sg.Window("Canvas Window", layout, finalize = True, size=(1200, 800), resizable=True)
    window.set_title("Pulse Monitor System")
    # Draw pulse rate graph
    canvasElement1 = window["Pulse Canvas"]
    ax1, figAgg1 = addPlot(canvasElement1)
    figAgg1.draw()

    # draw Heart Rate graph
    canvasElement2 = window["Heart Canvas"]
    ax2, figAgg2 = addPlot(canvasElement2)
    figAgg2.draw()

    # initialise time for printing to log
    time = datetime.datetime.now()
    # initialise packet variables to track packet order and no data counter.
    no_data_counter = 0
    last_number = 0
    # initialise csv lists
    csv_data = []
    csv_HR_value = []
    # time vectors initialised for graphs
    x = 0
    y = 0

    # graphing vectors initialised in correct space
    HR_data = np.zeros(4)
    pulse = np.zeros(200)
    moving_average = np.zeros(4)
    
    counter1 = 200
    counter2 = 4
    pulsedatapointcounter = 0
    HRdatapointcounter = 0

    while True:
        # Take in occurrences of window
        event, values = window.read(timeout=0)
        # close window if required
        if event in [sg.WIN_CLOSED, "Exit"]:
            window.close()
            break
        # set baseline threshold values based off slider movement (referenced via slider keys)
        lower = 50
        upper = 100
        # redefine thresholds if sliders interacted with
        lower = values["Lower HR"]
        upper = values["Upper HR"]
        # read data from microcontroller using data class
        data, HeartRate, no_data_check, sequence, button = interpretData()
        # update csv lists
        csv_data.append(data)
        csv_HR_value.append(HeartRate)
        # update Heart Rate display
        window["Current HR"].update(f'Current Heart Rate: {HeartRate} BPM')
        
        # Update window if heart rate is too high or low, or if packets are received out of sequence
        HR_Alarm(window, HeartRate, lower, upper)
        sequence, last_number = Packets(sequence, last_number, window)
        # warn if data is not being registered after 5 repeats
        if data == 0:
            if no_data_check == False:
                no_data_counter += 1
                last_number = 0
                if no_data_counter >= 5:
                    window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")}: No data detected\n', append = True)
            else:
                no_data_counter = 0
        # time vectors update
        pulse_time = np.linspace(x, x + 4, 200)
        HR_time = np.linspace(y, y + 4, 4)
        # create plots
        HR_data1, HRdatapointcounter1, pulsedatapointcounter1, pulse1, x1, y1 = create_graph(ax1, ax2, figAgg1, figAgg2, data, HeartRate, pulse_time, HR_time, HR_data, x, y, pulsedatapointcounter, HRdatapointcounter, counter1, counter2, pulse, moving_average)
        # redefine variables for iteration
        HR_data = HR_data1
        HRdatapointcounter = HRdatapointcounter1
        pulsedatapointcounter = pulsedatapointcounter1
        pulse = pulse1
        x = x1
        y = y1
        # save CSV if button pressed in GUI or on board
        if button == 1:
            saveDataCSV(csv_data, csv_HR_value)
            window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")}: Data saved as SensorReadings.csv\n', append = True)
        if event == "Save":
            saveDataCSV(csv_data, csv_HR_value)
            window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")}: Data saved as SensorReadings.csv\n', append = True)
        # print slider movements into system log
        for slider_key in slider_keys:
            if event == slider_key:
                slider_value = values[slider_key]
                time = datetime.datetime.now()
                window["System Log"].update(f'{time.strftime("%a %b %d %H:%M:%S %Y")} {slider_key} moved to {slider_value} \n', append = True)
        
        
        
    window.close()

create_window()
