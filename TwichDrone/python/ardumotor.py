import sys
    
from nanpy import (ArduinoApi, SerialManager)
from time import sleep

class MotorPINS:
    def __init__(self, label, channel, direction, power, brake, current, default):
        self.label = label
        self.channel = channel
        self.direction = direction
        self.power = power
        self.brake = brake
        self.current = current
        self.default = default

    def setup(self, arduino):
        arduino.pinMode(self.direction,arduino.OUTPUT);   
        arduino.pinMode(self.brake,    arduino.OUTPUT);   

class ArduMotor:
    
    FORWARD  = 1
    BACKWARD = 0
    
    # map this acordly
    
    MOTOR_LEFT = "LEFT"
    MOTOR_RIGHT = "RIGHT"
    
    DEFAULT_LEFT  = BACKWARD    # if motor is reversed, fixed it here
    DEFAULT_RIGHT = BACKWARD
        
    def __init__(self, port=None, verbose=0):

        self.verbose = verbose
        
        try:        
            if port:
                self.connection = SerialManager(device=port)
            else:
                self.connection = SerialManager()
            self.arduino = ArduinoApi(connection=self.connection)
        
        except Exception, e:
            print "Problem starting arduino interface: %s [skipping arduino interface]" % e
            self.arduino = None
    
        self.motor_left  = MotorPINS("LEFT", 'B', 13,11,8, 1,ArduMotor.DEFAULT_LEFT)      #channel B
        self.motor_right = MotorPINS("RIGHT",  'A',  12,3,9, 0,ArduMotor.DEFAULT_RIGHT)     #channel A 
        
        self.motors = { ArduMotor.MOTOR_LEFT: self.motor_left, ArduMotor.MOTOR_RIGHT: self.motor_right }
    
    def Setup(self):
        if not self.arduino:
            return
        self.motor_left.setup(self.arduino)
        self.motor_right.setup(self.arduino)
    
    def GetCurrent(self, motor):
        if not self.arduino:
            return 0.0
        VOLT_PER_AMP = 1.65
        m = self.motors[motor]
       
        currentRaw   = self.arduino.analogRead(m.current)
        currentVolts = currentRaw *(5.0/1024.0)
        currentAmps = currentVolts/VOLT_PER_AMP
    
        #print "Sensing %s:%s: %3.2f" % (m.label, m.channel, currentAmps)
        return currentAmps

    
    
    def DriveMotor(self, motor, direction=None, power=None, brake=False):
        if not self.arduino:
            return
        
        m = self.motors[motor]
        
        if brake:
             self.arduino.digitalWrite(m.brake, self.arduino.HIGH);   
             return
        
        # sanity check
        
        if direction==None or power==None:
            return
        
        if power < 0:   power = 0
        if power > 255: power = 255
        
        ar_dir = self.arduino.HIGH # forward
        if direction == ArduMotor.BACKWARD:
            ar_dir = self.arduino.LOW # backward
      
        if m.default != ArduMotor.FORWARD:
            # if mounted reversal, change direction here.
            if ar_dir == self.arduino.HIGH: 
                ar_dir = self.arduino.LOW
            else:
                ar_dir = self.arduino.HIGH

        #print "Driving motor: %s:%s to %s: [power: %s] (brake: %s) " % (m.label, m.channel, ar_dir, power, brake)
        
            
        self.arduino.digitalWrite(m.direction, ar_dir);  
        self.arduino.digitalWrite(m.brake, self.arduino.LOW);    
        self.arduino.analogWrite(m.power, power);    
        
    
    def TestMotor(self,motor):
        if not self.arduino:
            return
        
        if motor not in self.motors.keys():
            return ("Error, unknown motor %s" % motor)
        
        for i in [0, 10, 50, 100, 200, 255]:
            #print "Motor: %s Speed %s (Forward)" % (motor,i)
            self.DriveMotor(motor, ArduMotor.FORWARD, i)
            sleep(0.5)
        
        self.DriveMotor(motor,brake=True)
        
       
        for i in [255, 200, 100, 50, 10, 0]:
            #print "Motor: %s Speed %s (Backward)" % (motor,i)
            self.DriveMotor(motor, ArduMotor.BACKWARD, i)
            sleep(0.5)
        
        self.DriveMotor(motor,brake=True)
        
        


if __name__ == "__main__":
    
    # mac with CH341x (Clone)

    #driver =ArduMotor() # raspy
    #driver =ArduMotor(port='/dev/cu.wchusbserial1a1130') # mac
    driver =ArduMotor(port='/dev/cu.wchusbserial620') # macbookpro
    
    driver.Setup()
    
    driver.TestMotor(driver.MOTOR_RIGHT)
    sleep(1)
    driver.TestMotor(driver.MOTOR_LEFT)
    
    
    
