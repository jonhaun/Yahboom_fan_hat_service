"""
fan_service.py

Program to run as a service and control the Yahboom RGB Fan Hat for the RPI

MIT License

Copyright (c) [2020] [Jon Haun]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import time
import os
import re
import signal
import smbus
import json
from os import path

import Adafruit_GPIO.I2C as I2C
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

class RGBFanManager:
    
    # Registers
    HAT_ADDR = 0x0d
    EFFECT_REG = 0x04
    SPEED_REG = 0x05
    COLOR_REG = 0x06
    OFF_REG = 0x07
    FAN_REG = 0x08
    
    # Other Constants
    MAX_LED = 3
    WRITE_SLEEP = 0.25
    BEHAVIOR_FILE = "/usr/local/share/RGBHatInterface/behavior.json"
    DEFAULT_MESSAGE = "Hostname: " + subprocess.check_output('hostname', shell = True).decode('utf-8')
    
    # speed steps (0x00 = 0%, 0x01 = 100%)
    SPEED_STEP = [0x00, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x01]
    
    def __init__(self, high, med, low, debug=False):
        self.DEBUG = debug
        self.HIGH = high
        self.MED = med
        self.LOW = low
        
        # Setup for graceful exit
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        self.stop = False
        
        # Initialize Management Variables
        self.bus = smbus.SMBus(1)
        self.fan_state = 2
        self.count = 0
        
        # Turn everything off
        self.setFanSpeed(0)
        self.lightsOut()
        
        # Initialize the display
        self.initializeDisplay()
        
        # initialize message
        self.message = self.DEFAULT_MESSAGE
        
    def initializeDisplay(self):
        # Raspberry Pi pin configuration:
        self.RST = None     # on the PiOLED this pin isnt used
    
        # 128x32 display with hardware I2C:
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=self.RST)
        
        # Initialize library.
        self.disp.begin()
        
        # Clear display.
        self.disp.clear()
        self.disp.display()
        
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        
        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)
        
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height-self.padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0
        
        # Load default font.
        # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
        # Some other nice fonts to try: http://www.dafont.com/bitmap.php
        #font = ImageFont.truetype('8bitM.ttf', 8)
        self.font = ImageFont.load_default()

    def lightsOut(self):
        self.bus.write_byte_data(self.HAT_ADDR, self.OFF_REG, 0x00)
        time.sleep(self.WRITE_SLEEP)
    
    def setRGB(self, num, r, g, b):
        if num >= self.MAX_LED:
            self.bus.write_byte_data(self.HAT_ADDR, 0x00, 0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x01, r&0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x02, g&0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x03, b&0xff)
        elif num >= 0:
            self.bus.write_byte_data(self.HAT_ADDR, 0x00, num&0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x01, r&0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x02, g&0xff)
            self.bus.write_byte_data(self.HAT_ADDR, 0x03, b&0xff)
        time.sleep(self.WRITE_SLEEP)
        
    def setFanSpeed(self, step):
        step = max( min( len(self.SPEED_STEP)-1, step), 0)
        speed = self.SPEED_STEP[step]
        self.bus.write_byte_data(self.HAT_ADDR, self.FAN_REG, speed&0xff)
        time.sleep(self.WRITE_SLEEP)
    
    def setRGBEffect(self, effect):
        self.bus.write_byte_data(self.HAT_ADDR, self.EFFECT_REG, effect&0xff)
        time.sleep(self.WRITE_SLEEP)
    
    def setRGBColor(self, color):
        if color >= 0 and color <= 6:
            self.bus.write_byte_data(self.HAT_ADDR, self.COLOR_REG, color&0xff)
            time.sleep(self.WRITE_SLEEP)
    
    def setRGBSpeed(self, speed):
        if speed >= 1 and speed <= 3:
            self.bus.write_byte_data(self.HAT_ADDR, self.SPEED_REG, speed&0xff)
            time.sleep(self.WRITE_SLEEP)
    
    def getCPULoadRate(self):
        f1 = os.popen("cat /proc/stat", 'r')
        stat1 = f1.readline()
        count = 10
        data_1 = []
        for i  in range (count):
            data_1.append(int(stat1.split(' ')[i+2]))
        total_1 = data_1[0]+data_1[1]+data_1[2]+data_1[3]+data_1[4]+data_1[5]+data_1[6]+data_1[7]+data_1[8]+data_1[9]
        idle_1 = data_1[3]
    
        time.sleep(1)
    
        f2 = os.popen("cat /proc/stat", 'r')
        stat2 = f2.readline()
        data_2 = []
        for i  in range (count):
            data_2.append(int(stat2.split(' ')[i+2]))
        total_2 = data_2[0]+data_2[1]+data_2[2]+data_2[3]+data_2[4]+data_2[5]+data_2[6]+data_2[7]+data_2[8]+data_2[9]
        idle_2 = data_2[3]
    
        total = int(total_2-total_1)
        idle = int(idle_2-idle_1)
        usage = int(total-idle)
        usageRate =int(float(usage * 100/ total))
        return "CPU:"+str(usageRate)+"%"
    
    def getTemp(self):
        cmd = os.popen('vcgencmd measure_temp').readline()
        return float(cmd.replace("temp=","").replace("'C\n",""))
    
    def displayStatusMsg(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
    
        # Get the status information
        CPU = self.getCPULoadRate()
        CPU_temp = self.getTemp()
        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell = True).decode('utf-8')
    
        # Write lines of text.
        self.draw.text((self.x, self.top), str(CPU), font=self.font, fill=255)
        self.draw.text((self.x+56, self.top), "Temp: " + str(CPU_temp), font=self.font, fill=255)
        self.draw.text((self.x, self.top+12), self.message,  font=self.font, fill=255)
        self.draw.text((self.x, self.top+24), "IP:" + IP,  font=self.font, fill=255)
    
        # Display image.
        self.disp.image(self.image)
        self.disp.display()
        time.sleep(.1)
        
    def modBehavior(self):
        return path.exists(self.BEHAVIOR_FILE)
    
    def readBehavior(self):
        with open(self.BEHAVIOR_FILE) as f:
          return json.load(f)
    
    def storeBehavior(self, data):
        with open(self.BEHAVIOR_FILE, 'w') as json_file:
            json.dump(data, json_file, indent=4, sort_keys=True)
    
    def displayBehavior(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        self.draw.text((self.x, self.top), self.message, font=self.font, fill=255)
        
        # Display image.
        self.disp.image(self.image)
        self.disp.display()
        time.sleep(.1)
    
    def manageBehavior(self):
        data = self.readBehavior()
        
        self.message = data['message'] if 'message' in data else self.DEFAULT_MESSAGE
        self.displayBehavior()
        
        if 'fan' in data: self.setFanSpeed(data['fan'])
        
        if 'RGB' in data:
            for i in range(len(data['RGB'])):
                self.setRGB(i, data['RGB'][i][0], data['RGB'][i][1], data['RGB'][i][2] )
        
    def run(self):
        
        try:
            step = 0.5
            state = 0
            mod_flag = 0
            while not self.stop:
                try:
                    if m.modBehavior():
                        m.manageBehavior()
                        step = 2.0
                        state = 0
                    else:
                        if state == 0:
                            self.setFanSpeed(0)
                            self.setRGBColor(2)
                            self.setRGBEffect(1)
                            self.setRGBSpeed(1)
                            self.message = self.DEFAULT_MESSAGE
                            
                        m.displayStatusMsg()
                        temp = m.getTemp()
                        
                        if temp >= self.HIGH:
                            if state != 1:
                                m.setFanSpeed(10) # Max
                                m.setRGBColor(0) # Red
                                m.setRGBSpeed(3) # Fastest
                                step = 2.0
                            state = 1
                        elif temp >= self.MED:
                            if state != 2:
                                m.setFanSpeed(8)
                                m.setRGBColor(3) # Yellow
                                m.setRGBSpeed(2) # Medium
                                step = 1.5
                            state = 2
                        elif temp >= self.LOW:
                            if state != 3:
                                m.setFanSpeed(4)
                                m.setRGBColor(5) # Cyan
                                m.setRGBSpeed(1) # Slow
                                step = 1.0
                            state = 3
                        else:
                            if state != 4:
                                m.setFanSpeed(0) # Off
                                m.setRGBColor(2) # Blue
                                m.setRGBSpeed(1) # Slow
                                step = 0.5
                            state = 4
                            
                    time.sleep(step)
                except IOError:
                    pass # don't let a failed write stop the service
        except KeyboardInterupt:
            pass

    def shutdown(self, signum, frame):
        self.stop = True
        
if __name__ == '__main__':
    
    m = RGBFanManager(high=59, med=48, low=37)
    m.run()

    # shutdown gracefully
    m.initializeDisplay()
    m.setFanSpeed(0)
    m.lightsOut()
