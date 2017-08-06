# em-facilities
This repository has the main purpose of sharing code recipes used in different EM facilities. It can also points to other places where interesting scripts/programs are hosted. The idea of creating this repository came from an EM Facilities meeting host in Madrid during 27 and 28 of July 2017.

## Scipion related code

### General repository 
The general Scipion repository can be found at: https://github.com/I2PC/scipion. Scipion now implements processing in streaming, which is very useful for processing on-the-fly during data acquisition. 

### Other scripts 
The following repository contains some scripts that are not part of Scipion, but use its API to achieve some tasks: https://github.com/I2PC/scipion-scripts

### Session Wizards
Session wizards are scripts that prepare the setup for the data acquisition and create a pre-set Scipion project to be used in streaming. 

* Session Wizard at CNB: This wizard is hosted within the main Scipion repository and can be found here: https://github.com/I2PC/scipion/blob/release-1.1.facilities-devel/scripts/scipionbox_wizard.py
* Session Wizard at SciLifeLab: This wizards is similar to the CNB one, but also communicates with third-party software (Instruments Booking System and National projects Application Portal). It is hosted in a separated repository: https://github.com/delarosatrevin/scipion-session





