#!/usr/bin/python

import thread
import threading
import wsock
import model
import argparse
import sys
import time
from  ardumotor import ArduMotor
from nanpy import (ArduinoApi, SerialManager)
from goprohero import GoProHero
import logging

class GoProHelper:
    def __init__(self,passwd):
        self.camera = GoProHero(password=passwd,log_level=logging.CRITICAL) #info shows LOTS of things

    def Status(self): 
        s= self.camera.status()  
        if s['raw'] == {}: 
            s = { 'power': 'off', 'batt1': 0}
        return s
        #for i in s.keys(): print "%s: %s" % (i, s[i])
    
    def RecordStart(self): 
        self.camera.command('record', 'on')     
    
    def RecordStop(self): 
        self.camera.command('record', 'off')
        
def LOG(msg):
    s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    msg = "[%s]" + msg
    return msg % s

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show detailed model info", action="count", default=0)
    parser.add_argument("-a", "--address", help="Host Address", default='')
    parser.add_argument("-p", "--port", help="Listen Port", default=8000)
    parser.add_argument("-f", "--frequency", help="FPS to run model", default=60)
    parser.add_argument("-g", "--gopropasswd",help="GoPro Password", default='')
    parser.add_argument("-s", "--serialport",help="arduino serial port", default='')
    args = parser.parse_args()
    
    model.MODEL = model.DroneModel(verbose=args.verbose)
    model.MODEL_LOCK = threading.Lock()
    
    wsock.websocketserver_start(args.address,int(args.port))
 
    print "ControlServer started at %s:%s (verbose:%s) Refresh: %s Hz" % (args.address, args.port, args.verbose, args.frequency)
 
    #TODO: pass as argument
    #driver =ArduMotor() # raspy
    #driver =ArduMotor(port='/dev/cu.wchusbserial1a1130') # mac
    #driver =ArduMotor(port='/dev/cu.wchusbserial620') # macbookpro
    
    driver =ArduMotor(port=args.serialport) # macbookpro
    
    gopro = GoProHelper(args.gopropasswd) 
    gopro_status = gopro.Status()
    print "Gopro Status: Powered: %s [battery: %s %%]" % (gopro_status['power'], gopro_status['batt1'])

    olddata = None
    ml_amp = 0.0
    mr_amp = 0.0
    
    gopro_timer = time.time()
     
    while True:
        target_freq = 1/float(args.frequency)
        sample_start_time = time.time()

        if time.time() - gopro_timer > 10:
            gopro_timer = time.time()
            if gopro_status['power'] == 'off':
                gopro = GoProHelper(args.gopropasswd) 
            gopro_status = gopro.Status()
    

        # begin block 

        ml_amp = (ml_amp + driver.GetCurrent(ArduMotor.MOTOR_LEFT)  )/2.0
        mr_amp = (mr_amp + driver.GetCurrent(ArduMotor.MOTOR_RIGHT) )/2.0
        
        stats = { 'gopro': gopro_status, 'amp_l': ml_amp, 'amp_r': mr_amp }
        
        model.MODEL.set_stats(stats)
        model.MODEL.update()
        data = model.MODEL.getdata()
        
        if olddata and (olddata['data'] != data['data'] or olddata['MR'] != data['MR'] or  olddata['ML'] != data['ML'] or olddata['buttons'] != data['buttons']):

            # manage buttons
            rec_old = olddata['buttons'] and olddata['buttons']['rec']
            rec = None
            if data['buttons'] and 'rec' in data['buttons']:
                rec = data['buttons']['rec']
            
            if data['buttons']:  
                if rec_old:
                    if not rec_old and rec:
                        if args.verbose >1 : print LOG("START_RECORDING")
                        gopro.RecordStart()
                    if rec_old and not rec:
                        if args.verbose >1 : print LOG("STOP_RECORDING")
                        gopro.RecordStop()
                else:
                    if rec:
                        if args.verbose >1 : print LOG("START_RECORDING")
                        gopro.RecordStart()
                    else:
                        if args.verbose >1 : print LOG("STOP_RECORDING")  
                        gopro.RecordStop()
                
            # send data to arduino HERE
               
            driver.DriveMotor(ArduMotor.MOTOR_LEFT, data['ML'].direction , data['ML'].power)
            driver.DriveMotor(ArduMotor.MOTOR_RIGHT, data['MR'].direction , data['MR'].power)
     
            # until here
            
            if args.verbose >= 1:  
                MRD = 'F'
                MLD = 'F'
                if data['MR'].direction == model.MotorModel.BACKWARD: MRD = 'B'
                if data['ML'].direction == model.MotorModel.BACKWARD: MLD = 'B'
           
                print LOG("[CONTROL][OUT][MotorLEFT] [Power: %03d] [Direction: %s[%s] | [MotorRIGHT] [Power: %03d] [Direction: %s[%s]" %\
                    (data['MR'].power, data['MR'].direction, MRD, data['ML'].power, data['ML'].direction, MLD ))
            
        olddata = data
        driver.DriveMotor(ArduMotor.MOTOR_LEFT,brake=True)
        driver.DriveMotor(ArduMotor.MOTOR_RIGHT,brake=True)
    
            
        # time control
        sample_end_time = time.time()
        time_diff = sample_end_time - sample_start_time
        if time_diff < target_freq:
            time.sleep(target_freq - time_diff)
        
        