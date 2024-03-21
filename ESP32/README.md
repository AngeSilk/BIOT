# Termostato_Micropython_ESP32

## Update v0.9

 - Two **asynchronous functions** were defined to work in parallel:
	+ The first function measures the sensor every second and activates the relay if the thermostat mode is in automatic. 
	+ The second function publishes the data at certain intervals (periode).

 - A new function named **read_db()** was incorporated to fetch the stored information from the database and update the utilized parameters.
 - The information is published under the topic Device ID
 -  Two additional classes have been included:
	> **Variables()**, responsible for handling variables
	> **Parameters()**, which manages parameters.