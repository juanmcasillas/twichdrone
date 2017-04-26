import time
import datetime

import math
import json
import copy
from nonlinearinterp import NonLinearInterpolator

class MotorModel:
        FORWARD = 1
        BACKWARD = 0
        MAXPOWER = 255 
        MAXSPEED = 0.6 # in m/s. Power<->Speed is LINEAR relation
        MAXANGSPEED = ((MAXPOWER*2) *  MAXSPEED) / MAXPOWER
        
        def __init__(self,mlabel):
            self.mlabel = mlabel
            self.direction = MotorModel.FORWARD
            self.power = 0.0
            
            
        def update(self, power, direction):
            self.power = power
            self.direction = direction
        
        def __eq__(self, other):
            
            if self.mlabel == other.mlabel and \
               self.power == other.power and \
               self.direction == other.direction:
                    return True
            return False
        
        def __ne__(self, other): 
            return not self.__eq__(other)
        
        def __str__(self):
            s ="[ %s, %d, %d]" % (self.label, self.power, self.direction)
            return s
        
            
class InputData:
    def __init__(self, distance=0.0, angle=0.0, maxdistance=75, x=None, y=None):
        "maxdistance is set in the CLIENT (nipplejs)"
        self.distance_linear = distance
        self.distance = distance
        self.angle = angle                  # in radians
        self.maxdistance = maxdistance
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        if  self.distance_linear == other.distance_linear and \
            self.distance == other.distance and \
            self.angle == other.angle and \
            self.maxdistance == other.maxdistance and \
            self.x == other.x and \
            self.y == other.y:
                return True
        return False
    
    def __ne__(self, other): 
        return not self.__eq__(other)
         
    def __str__(self):
        s = "[%3.2f, %3.2f, %3.2f, %3.2f, %s %s]" % (self.distance_linear, self.distance, self.angle, self.maxdistance, self.x, self.y)
        return s

class DroneModel:
    FORWARD_ANGLE_RANGE  =  ( 90-60, 90+60) # goes forward
    BACKWARD_ANGLE_RANGE = (270-60,270+60) # goes backward (reverse)
    NEAR_ZERO = 0.0001
    MAX_DISTANCE = 75
    MAX_STEERINGANGLE = math.radians(45) # if you set the same than 90-40 ... there is no gap.
    
    # non linear interpolator "curve" for joystick input"
    
    # 20%, 30%, 30%, 20% -> 10%, 40%, 40%, 10%
    
    #DISTANCECURVE = [ [(0,23),(0,7)], [(23,37),(7,37)], [(37,55),(37,55)], [(55,75),(55,75)] ]
    # map the distance with the distance (joystick dead end)
    #DISTANCECURVE = [ [(0,20),(0,10)], [(20,60),(10,50)], [(60,70),(50,60)], [(70,76),(60,75)] ]
    DISTANCECURVE = [ [(0,15),(0,7)], [(15,30),(7,18)], [(30,45),(18,31)], [(45,65),(31,49)], [(65,76),(49,76)] ]
    
    
    # 20%, 30%, 30%, 20% -> 10%, 40%, 40%, 10%
    # 27/03/2017: this curve is TOO fast. Change it to something more smooth
    #JOYCURVE = [ [(0,55),(0,25)], [(55,128),(25,127)], [(128,200),(127,229)], [(200,255),(229,255)] ]
    # maps the output curve to this curve
    #POWERCURVE = [ [(0,80),(0,40)], [(80,210),(40,180)], [(210,240),(180,190)], [(240,256),(190,200)] ]
    POWERCURVE = [ [(0,40),(0,15)], [(40,80),(15,40)], [(80,120),(40,70)], [(120,200),(70,140)], [(200,240),(140,190)], [(240,256),(190,210)] ]
    
    def __init__(self, verbose=0):
        
        self.MR = MotorModel("R")
        self.ML = MotorModel("L")
        self.data = InputData()
        self.allowed_messages = { 'joystick', 'button', 'status' }
        
        self.buttons = {}
        self.interpolator = NonLinearInterpolator()
        
        self.verbose = verbose
        self.start_time = time.time()
        self.stats = None

    def HandleData(self, data, wsock=None):
        "receive a JSON string, and process it. Do some sanity checks."
        
        # {u'y': u'up', u'distance': 30.675723300355934, u'kind': u'joystick', u'angle': 1.902855794337782, u'x': u'left'}
        # {u'y': 0, u'distance': 0, u'kind': u'joystick', u'angle': 0, u'x': 0}
        # {u'kind': u'button', u'id': u'rec', u'pressed': u'true'}
        # {u'kind': u'status' }
        
        if data == None or data == "": return
        
        try:
            data = json.loads(data)
        except Exception, e:
            s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print "[MODEL][HandleData] Exception %s " % e
            return
        
        if data.has_key("kind") and data["kind"].lower() in self.allowed_messages:
            
            if data["kind"].lower() == "joystick" and "distance" in data.keys() and "angle" in data.keys():
                #joystick input
                self.UpdateJoyData(data)
                
                
            if data["kind"].lower() == "button" and "id" in data.keys() and "pressed" in data.keys():
                #button pressed (work as boolean switch
                self.UpdateButtonData(data)
                
                
                
            if data["kind"] == "status":
                self.HandleMessageStatus(data,wsock)
                                
        
    
    def UpdateJoyData(self, data):
        
        dint = self.interpolator.NLinterp(data["distance"],DroneModel.DISTANCECURVE)
        
        with MODEL_LOCK:
            self.data.distance_linear = data["distance"]
            self.data.distance  = dint
            self.data.angle = data["angle"]         # in radians
         
       
            if self.verbose > 1:
                s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print "[MODEL][%s][ IN][joy] [distance: L:%09.5f|NL:%09.5f] [angle: %09.5fd]" % (s,self.data.distance_linear,self.data.distance,math.degrees(self.data.angle))
            
            # optional
            if "x" in data.keys() and "y" in data.keys():
                self.data.x = data["x"]
                self.data.y = data["y"]

    def UpdateButtonData(self, data):
        with MODEL_LOCK:
            if data["id"] not in self.buttons.keys():
                self.buttons[data["id"]] = False
            
            # toggle
            if data["pressed"].lower() == "true":
                self.buttons[data["id"]] = not self.buttons[data["id"]] 
            
            if self.verbose > 1:
                s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print "[MODEL][%s][ IN][button] [Name: %s] [Pressed: %s]" % (s,data["id"],self.buttons[data["id"]])

    def HandleMessageStatus(self, data, wsock):
        #print "sending message to client (dummy)"
        
        time_delta = time.time() - self.start_time
        m, s = divmod(time_delta, 60)
        h, m = divmod(m, 60)
        time_delta_s = "Running time: %02d:%02d:%02d" % (h, m, s)
        
        
        gopro = 'Gopro: Not Found/OFF'
        if self.stats['gopro']['power'].lower() == 'on':
            
            recording = 'off'
            if 'record' in self.stats['gopro'].keys():
                recording = self.stats['gopro']['record']
            
            gopro = "Powered [battery: %s%%] Recording: %s" % (self.stats['gopro']['batt1'],recording)
     
        if self.stats['amp_l'] == None or self.stats['amp_r'] == None:
            motor_a = "Left Current: N/A | Right Current: N/A [Arduino Off?]"
        else:
            motor_a = "Left Current_avg: %3.2fA | Right Current_avg: %3.2fA" % (self.stats['amp_l'],self.stats['amp_r'])
            
        msg = "%s</br>%s</br>%s</br>" % (time_delta_s, gopro, motor_a)
        
        wsock.sendMessage(unicode(msg,'utf-8'))
        #tornado 
        #wsock.write_message(unicode("hola","utf-8"))
        
    
    
    
    
    
    def InForwardAngle(self, angle):    
        # in radians
        ang_d = math.degrees(angle)
        if  ang_d >= self.FORWARD_ANGLE_RANGE[0] and ang_d <=  self.FORWARD_ANGLE_RANGE[1]:
            return True
        return False

    def InBackwardAngle(self, angle):    
        # in radians
        ang_d = math.degrees(angle)
        if  ang_d >= self.BACKWARD_ANGLE_RANGE[0] and ang_d <=  self.BACKWARD_ANGLE_RANGE[1]:
            return True
        return False
    
    def set_stats(self, stats):
        self.stats = stats
        
    def update(self) :
        "calculate everything needed to work propertly"
        
        data = self.getdata()['data']
        Fx = data.distance * math.cos(data.angle) 
        Fy = data.distance * math.sin(data.angle)
   
     
        # include partial angle component
        #
        # If Fx -> O, D -> full aligned.
        # Else, asign the partial component to the force, to create somekind of moment.
        # # calculate first the % of the force, then modify it
        #
        percent_x = 0.0
        cx = 0.0
        if data.distance != 0.0:
            cx = math.fabs(Fx)*100.0/data.distance
            #cx = (data.distance*percent_x)/100.0
            #print "Distance: %3.2f, Fx: %3.2f, Percent: %3.2f %%, Cx: %3.2f" % (data.distance, math.fabs(Fx), percent_x, cx)
        
        # generic power (non balanced)
        
        MPower = self.interpolator.interpolate(data.distance,0,data.maxdistance,0,MotorModel.MAXPOWER)

        # get directions
        forward = True
        right = True
        FullForward = False
        FullBackward = False
        
        if Fy <0:  forward = False
        if Fx <0:  right = False
        
        if self.InForwardAngle(data.angle):
            FullForward = True
            cr = cx
            cl = -cx
            if right:
                cr = -cx
                cl = cx
                
            MRPower = MPower + (MPower * cr /100.0)
            MLPower = MPower + (MPower * cl /100.0)    
            
            
        elif self.InBackwardAngle(data.angle):
            FullBackward = True
            cr = cx
            cl = -cx     
            if right:
                cr = -cx
                cl = +cx

            MRPower = MPower + (MPower * cr /100.0)
            MLPower = MPower + (MPower * cl /100.0)    
        else:
            
            MRPower = MLPower = MPower
            
        if MRPower > MotorModel.MAXPOWER: MRPower = MotorModel.MAXPOWER
        if MLPower > MotorModel.MAXPOWER: MLPower = MotorModel.MAXPOWER

        MRPower = self.interpolator.NLinterp(MRPower,DroneModel.POWERCURVE)
        MLPower = self.interpolator.NLinterp(MLPower,DroneModel.POWERCURVE)
        
        MRPower = int(MRPower)
        MLPower = int(MLPower)
        
        with MODEL_LOCK:
      
            if FullForward:
                self.MR.update(MRPower,MotorModel.FORWARD)
                self.ML.update(MLPower,MotorModel.FORWARD)
                return
            
            if FullBackward:
                self.MR.update(MRPower,MotorModel.BACKWARD)
                self.ML.update(MLPower,MotorModel.BACKWARD)
                return
            
            if forward and not right or\
               not forward and not right: 
                self.MR.update(MRPower,MotorModel.FORWARD)
                self.ML.update(MLPower,MotorModel.BACKWARD)
    
            if forward and right or\
                not forward and right: 
                self.MR.update(MRPower,MotorModel.BACKWARD)
                self.ML.update(MLPower,MotorModel.FORWARD)        


                
                
            

    
    def getdata(self):
        with MODEL_LOCK:
            return { 'data': copy.copy(self.data), 'MR': copy.copy(self.MR), 'ML': copy.copy(self.ML), 'buttons': copy.copy(self.buttons) }
            
    def printdata(self):
        print self.data
    
    def getbuttons_str(self):
        s = ''
        with MODEL_LOCK:
            for i in self.buttons.keys():
                s += '[%s->%s]' % (i, self.buttons[i])
        
        return s
        
    # tools
    
