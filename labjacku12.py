# Copyright 2008 Jim Bridgewater

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# 06/19/2008 Jim Bridgewater
# Removed the print statement from check_connection.

# 06/04/2008 Jim Bridgewater
# Changed to conform to the PEP8 python style guide.

# 05/06/2008 Jim Bridgewater
# Adapted this from the SPEX1681 interface to be an interface module
# for the LabJack U12.  I'm working on the interface to a stepper
# motor and am only defining the functions necessary for that
# interface.

# 04/28/2008 Jim Bridgewater
# Creating this module to encapsulate the functions required to 
# control the SPEX1681 monochromator.  Also added a timeout to stop
# the program if Recalibration takes longer than 2 minutes because
# this typically indicates that the SPEX1681 is not turned on.

# 04/21/2008 Jim Bridgewater
# Added code to make sure the labjack is plugged in and defined functions
# (SetDirection, ChangeWavelength, CheckUpperLimit, CheckLowerLimit) to 
# make the 1681 less cumbersome to control.  

# 04/14/2008 Jim Bridgewater
# This program uses digital outputs on the Labjack U12 to control
# the SPEX 1681 monochromator.  The 1681 has a maximum speed of 500
# steps per second (500 Hz).  The upper wavelength limit is about 1198 nm 
# according to the instrument's dial.  On the lower end the dial rolls 
# past 0 to about 9921 nm.  The instrument moves very nearly 1 nm for 
# every 50 pulses on the step input signal.

#################################################################
# the functions defined in this module are:
#################################################################
# check_connection():
# read_IO():
# set_IO_to_output(direction, data = 0):
# write_to_IO(data, bitmask = 0xf):
# read_DIO():
# set_DIO_to_output(direction, data = 0):
# write_to_DIO(data, bitmask = 0xffff):
# pulse_DIO(DIOs, pulses, f = 500):

#################################################################
# import modules and create handles for labjack functions
#################################################################

import sys
from errors import Error

# ctypes is a module that allows Python to call DLL routines (like 
# the labjack drivers) written in C
from ctypes import windll, c_long, c_float, byref 

# Load the labjack driver 'ljackuw.dll' 
ljackuw = windll.ljackuw
# Load the desired functions (see LabJack_U12_Users_Guide.PDF for
# a list of functions and descriptions of what they do)
GetFirmwareVersion = ljackuw.GetFirmwareVersion
DigitalIO = ljackuw.DigitalIO  
PulseOut = ljackuw.PulseOut 


#################################################################
# define functions to make using the LabJack U12 easier
#################################################################

# define parameters required by all functions
idnum = c_long(-1)        # first labjack found
demo = c_long(0)        # not using demo mode

# define parameters that need to be stored in global variables
trisD = c_long(0)              # all D lines inputs to start
trisIO = c_long(0)               # all IO lines inputs to start
stateD = c_long(0)        # initial state is low
stateIO = c_long(0)        # initial state is low


# This function checks the communication link with the LabJack U12 
# by requesting its firmware version.  It returns zero if no LabJack
# is detected and one if a LabJack is detected.
def check_connection():
  if GetFirmwareVersion(byref(idnum)) > 512:
    return 0
  else:
    return 1


# This function reads the four IO lines on the LabJack's screw 
# terminals. 
def read_IO():
  global stateIO
  updateDigital = c_long(0)         # don't update output states
  outputD = c_long(0)         # placeholder for return value
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: ReadIO Error Code = " + str(error_code))
  return stateIO.value


# This function sets the direction of the four IO lines on the 
# LabJack's screw terminals.  A bit position containing a 1 sets
# the corresponding IO to be an output.  The default data value
# for outputs is 0, but this can be changed by specifying a value
# for the optional data input.
def set_IO_to_output(direction, data = 0):
  global trisIO, stateIO
  # set desired IOs to outputs
  trisIO = c_long(direction | trisIO.value) 
  # set initial IO state
  stateIO = c_long(data | stateIO.value)
  # update output states
  updateDigital = c_long(1)         
    # placeholder for return value
  outputD = c_long(0)
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: SetIOtoOutput Error Code = " + str(error_code))


# This function can be used to write output values to any of the four 
# IO lines on the LabJack's screw terminals.  The optional bitmask 
# argument allows the user to write values to a subset of these signals.
def write_to_IO(data, bitmask = 0xf):
  global stateIO
  # set desired IO lines
  stateIO = c_long(stateIO.value | (data & bitmask))
  # clear desired IO lines
  stateIO = c_long(stateIO.value & (data | ~bitmask))
  updateDigital = c_long(1)       # update output states
  outputD = c_long(0)             # placeholder for return value
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: WritetoIO Error Code = " + str(error_code))


# This function reads the 16 DIO lines on the LabJack's DB25 connector. 
def read_DIO():
  global stateD
  updateDigital = c_long(0)         # don't update output states
  outputD = c_long(0)         # placeholder for return value
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: ReadDIO Error Code = " + str(error_code))
  return stateD.value


# This function enables the user to set any of the 16 digital IO
# lines on the LabJack's DB25 connector to output mode.  Setting
# a bit position in the direction input sets the corresponding IO 
# to be an output.  The default data value for outputs is 0, but 
# this can be changed by specifying a value for the optional data input.
def set_DIO_to_output(direction, data = 0):
  global trisD, stateD
  trisD = c_long(direction | trisD.value)  # set desired DIOs to outputs
  stateD = c_long(data | stateD.value)  # set initial state
  updateDigital = c_long(1)           # update output states
  outputD = c_long(0)                 # placeholder for return value
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: SetDIOtoOutput Error Code = " + str(error_code))


# This function can be used to write output values to any of the 16 
# digital IO lines on the LabJack's DB25 connector.  The optional bitmask 
# argument allows the user to write values to a subset of these signals.
def write_to_DIO(data, bitmask = 0xffff):
  global stateD
   # set desired IO lines
  stateD = c_long(stateD.value | (data & bitmask))
  # clear desired IO lines
  stateD = c_long(stateD.value & (data | ~bitmask))
  updateDigital = c_long(1)             # update output states
  outputD = c_long(0)                   # placeholder for return value
  error_code = DigitalIO(byref(idnum), demo, byref(trisD), trisIO, \
  byref(stateD), byref(stateIO), updateDigital, byref(outputD))
  if error_code != 0:
    raise Error("LabJack: WritetoDIO Error Code = " + str(error_code))


# This function pulses a DIO line the specified number of times at roughly
# the specified frequency.  Only DIOs 0-7 can be pulsed.
def pulse_DIO(DIOs, pulses, f):
  max_pulses = (1<<15) - 1
  if pulses != 0:
    B = 25000/f
    lowFirst = c_long(0)            # high, then low
    bitSelect = c_long(DIOs)
    timeB1 = c_long(B)        # timing parameters for f steps/second
    timeC1 = c_long(1)        
    timeB2 = c_long(B)      
    timeC2 = c_long(1)
    while pulses > 0:
      if pulses > max_pulses:
        numPulses = c_long(max_pulses)
        pulses = pulses - max_pulses
        error_code = PulseOut(byref(idnum), demo, lowFirst, bitSelect, \
        numPulses, timeB1, timeC1, timeB2, timeC2)
        if error_code != 0:
          raise Error("LabJack: PulseDIO Error Code = " + str(error_code))
      else:
        numPulses = c_long(pulses)
        pulses = 0
        error_code = PulseOut(byref(idnum), demo, lowFirst, bitSelect, \
        numPulses, timeB1, timeC1, timeB2, timeC2)
        if error_code != 0:
          raise Error("LabJack: PulseDIO Error Code = " + str(error_code))

