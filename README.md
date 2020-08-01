## Yahboom_fan_hat_service
#### Concept
The goal is to create a solution that runs in the background as a service to provide cooling and default information about the Raspberry Pi, while still allowing for on demand modification of the behavior. The hardware is created by Yahboom described on their website [here](https://www.yahboom.net/study/RGB_Cooling_HAT). The scripts provided by Yahboom are not very straightforward to understand, so this setup is designed to provide a somewhat easier way to interact with the hardware.

#### Implementation
This project is made up of three simple files.

1) Python Object Oriented server script (python3)
2) Systemd Service definition file (systemctl)
3) JSON behavior override file

#### Installation
0) GIT the files

1) Confirm the script works (Ctrl-C to stop)

        python3 fan_service.py

2) Move the script to your service bin folder.

        sudo cp fan_service.py /usr/local/bin/

3) Update the service definition for the location you used then install it.

        sudo cp fan_hat.service /etc/systemd/system && sudo systemctl start fan_hat.service

4) Enable the service to automatically boot

        sudo systemctl enable fan_hat.service

5) Place the behavior file (this will not override yet, see Utilization below)

        mkdir /usr/local/share/RGBHatInterface/
        cp _behavior.json /usr/local/share/RGBHatInterface/

#### Utilization
Once the server is up and running you can start and stop is easily with the `sudo systemctl [start|stop|status] fan_hat.service` commands. While the service is running it will check for the behavior.json file. If the file exists it will override the default behavior.

###### Default Behavior
The RGB Fan boots to show the CPU utilization, Temperature, Hostname, and IP address on the OLED screen. It then continuously checks the temperature and updates the fan speed and LED actions. As the temperature increases it moves from BLUE -> CYAN -> YELLOW -> RED with the 'breathing effect' speeding up each step. The fan speed increases with each step starting at 0% and going to 100%. The service is also designed to stop gracefully by responding to `SIGINT`, `SIGTERM`, and Keyboard Interupts with the intent of being fully off as the computer shuts down.

###### Override Behavior
The JSON file (behavior.json) describes how to override each of the functions of the fan HAT. When the file is present, all other behaviors are suspended except for what is described in the file. Uncomment and changes the values to meet your needs. To make the file 'present' or active, simply rename the '_behavior.json' to 'behavior.json' in the target directory. Changing the name (e.g. back to _behavior.json) will return the service to the default behavior.

#### Copyright and Disclaimer
This is a hobby project that I felt was worth sharing with others. I'm not doing this with the intent to generate any compensation, and may not make regular updates. As such:

MIT License

Copyright (c) [2020] [Jon Haun]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
