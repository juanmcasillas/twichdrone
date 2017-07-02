#!/usr/bin/env python

import sys
import pygame
from pygame.locals import (
    Color,
    Rect,
)
import json
import threading
import math
import wsock
import model

model.MODEL = model.DroneModel()
model.MODEL_LOCK = threading.Lock()


class PyGameToolBox:
    def __init__(self, winsize, screen):
        self.fonts = {}

        for i in [8, 12, 14, 18, 36]:
            self.fonts[str(i)] = pygame.font.Font(None, i)

        self.background = pygame.Surface(screen.get_size())
        self.background = self.background.convert()
        self.winsize = winsize
        self.screen = screen

    def RenderText(self, fontsize, text, pos, color=Color("black"),
                   surface=None):
        if not surface:
            surface = self.background

        _text = self.fonts[str(fontsize)].render(text, 1, color)
        textpos = _text.get_rect(centerx=pos[0], centery=pos[1])
        surface.blit(_text, textpos)

    def BGFill(self, color=Color("black")):
        self.background.fill(color)

    def Blit(self): self.screen.blit(self.background, (0, 0))

    def Width(self):
        return self.winsize[0]

    def Height(self):
        return self.winsize[1]

    def rot_center(self, image, rect, angle):
        """rotate an image while keeping its center"""
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = rot_image.get_rect(center=rect.center)
        return rot_image, rot_rect


class JoyWidget:
    def __init__(self, pos, radius, caption):
        self.pos = pos
        self.radius = radius
        self.caption = caption
        self.forward_angle_range = (0, 0)
        self.backward_angle_range = (0, 0)

    def Draw(self, TB, ccolor=Color("orange"), tcolor=Color("black")):
        pygame.draw.circle(TB.background,
                           ccolor,
                           self.pos,
                           self.radius,
                           1)
        TB.RenderText(18,
                      self.caption,
                      (self.pos[0],
                       self.pos[1] - self.radius - 25),
                      tcolor)

        # pygame.gfxdraw.pie(TB.background,
        #                    Color("blue"),
        #                    Rect(self.pos[0]-self.radius,
        #                         self.pos[1]-self.radius,
        #                         self.radius*2,self.radius*2),
        #                    math.radians(self.forward_angle_range[0]),
        #                    math.radians(self.forward_angle_range[1])
        # )
        pygame.gfxdraw.pie(TB.background,
                           self.pos[0],
                           self.pos[1],
                           self.radius, 360 - self.forward_angle_range[1],
                           360 - self.forward_angle_range[0],
                           Color("darkgreen"))
        pygame.gfxdraw.pie(TB.background,
                           self.pos[0],
                           self.pos[1],
                           self.radius,
                           360 - self.backward_angle_range[1],
                           360 - self.backward_angle_range[0],
                           Color("purple"))

    def MouseInside(self, x, y):
        return self.In_Circle(self.pos[0], self.pos[1], self.radius, x, y)

    def In_Circle(self, center_x, center_y, radius, x, y):
        square_dist = (center_x - x) ** 2 + (center_y - y) ** 2
        return square_dist <= radius ** 2

    def UpdateFromInput(self, TB, x, y, lcolor=Color("red")):

        angle = math.degrees(math.atan2(y - self.pos[1], x - self.pos[0]))
        angle = 360.0 - ((angle - 360.0) % 360.0)

        distance = math.sqrt(
            math.pow(x-self.pos[0], 2) + math.pow(y-self.pos[1], 2)
        )

        pygame.draw.line(TB.background,
                         lcolor,
                         (self.pos[0],
                          self.pos[1]),
                         (x, y),
                         3)
        TB.RenderText(18,
                      "DIST: %3.2f ANG: %3.2f deg" % (distance, angle),
                      (self.pos[0],
                       self.pos[1] - self.radius-10),
                      Color("black"))

        data_model = {'kind': 'joystick',
                      'distance': distance,
                      'angle': math.radians(angle)}
        return data_model

    def UpdateFromData(self, TB, data, lcolor=Color("red")):

        x = self.pos[0] + math.cos(data.angle) * data.distance_linear
        y = self.pos[1] - math.sin(data.angle) * data.distance_linear
        pygame.draw.line(TB.background,
                         Color("green"),
                         self.pos,
                         (x, y),
                         5)

        x = self.pos[0] + math.cos(data.angle) * data.distance
        y = self.pos[1] - math.sin(data.angle) * data.distance
        pygame.draw.line(TB.background,
                         lcolor,
                         self.pos,
                         (x, y),
                         3)

        TB.RenderText(18,
                      "DIST: %3.2f ANG: %3.2f deg" % (
                          data.distance,
                          math.degrees(data.angle)),
                      (self.pos[0], self.pos[1] - self.radius-10),
                      Color("black"))
        TB.RenderText(18,
                      "DIST (Linear): %3.2f" % (data.distance_linear),
                      (self.pos[0],
                       self.pos[1] + self.radius+10),
                      Color("black"))

    def SetAngleRanges(self, for_ar, bac_ar):
        self.forward_angle_range = for_ar
        self.backward_angle_range = bac_ar


class ButtonWidget:
    def __init__(self, pos, width, height, caption):
        self.pos = pos
        self.width = width
        self.height = height
        self.caption = caption

    def Draw(self, TB, ccolor=Color("red"),  tcolor=Color("black")):
        pygame.draw.rect(TB.background,
                         ccolor,
                         Rect(self.pos, (self.width, self.height)))
        TB.RenderText(14,
                      self.caption,
                      (self.pos[0] + self.width/2,
                       self.pos[1] + self.height/2),
                      tcolor)

    def MouseInside(self, x, y):
        r = Rect(self.pos, (self.width, self.height))
        return r.collidepoint((x, y))


class MotorWidget:
    def __init__(self, position, width, height, caption):
        self.pos = position
        self.width = width
        self.height = height
        self.caption = caption

        self.center = (self.pos[0] + (self.width/2),
                       self.pos[1] + self.height/2 + 10)
        self.lmpos = (self.center[0]-100, self.center[1])
        self.rmpos = (self.center[0]+100, self.center[1])

        self.attitude_ind = (60, 10)

        self.lmpower = 0
        self.lmforward = 1

        self.rmpower = 0
        self.rmforward = 1

        self.angular_a = 0.0
        # 1: left, counterclockwise, incremental,
        # -1: right, clockwise, decremental
        self.angular_d = 1
        self.steering_angle = 0.0

        self.linear_a = 0.0

    def Update(self, MR, ML):
        self.rmpower = MR.power
        self.rmforward = 1
        if MR.direction == model.MotorModel.BACKWARD:
            self.rmforward = -1

        self.lmpower = ML.power
        self.lmforward = 1
        if ML.direction == model.MotorModel.BACKWARD:
            self.lmforward = -1

        #
        # calculate speed, and angle of rotation based on motor power.
        # its a pair of forces, so we have to
        #

        MoR = 1.0 * (self.rmpower * self.rmforward)
        MoL = -1.0 * (self.lmpower * self.lmforward)
        Mo = (MoR + MoL)
        # calculate direction of rotation.
        # Mo < 0: left (counter clockwise)
        # Mo >=0: right (clocwise)

        # angular data
        self.angular_a = (math.fabs(Mo) * model.MotorModel.MAXSPEED) / model.MotorModel.MAXPOWER
        self.angular_d = 1  # left
        if Mo < 0:
            self.angular_d = -1  # right
        self.steering_angle = self.angular_d * (self.angular_a * model.DroneModel.MAX_STEERINGANGLE) / model.MotorModel.MAXANGSPEED

        # linear data
        LF = (self.rmpower * self.rmforward) + (self.lmpower * self.lmforward)
        self.linear_a = (LF * model.MotorModel.MAXSPEED) / model.MotorModel.MAXPOWER
        # print "LinearV: %3.2f" %  self.linear_a

    def Draw(self, TB, ccolor=Color("black"),  tcolor=Color("black"), mlcolor=Color("blue"), mrcolor=Color("red")):
        pygame.draw.rect (TB.background, ccolor, Rect(self.pos, (self.width,self.height)),  1)
        TB.RenderText(18, self.caption, (self.pos[0]+self.width/2,self.pos[1]+10), tcolor)

        #motors and body
        pygame.draw.rect (TB.background, mlcolor, Rect((self.lmpos[0]-20, self.lmpos[1]-40), (40,80)),  1)
        pygame.draw.rect (TB.background, mrcolor, Rect((self.rmpos[0]-20, self.lmpos[1]-40), (40,80)),  1)
        pygame.draw.rect (TB.background, ccolor , Rect((self.center[0]-50, self.center[1]-50), (100,100)),  1)

        # axis
        pygame.draw.rect (TB.background, ccolor , Rect((self.lmpos[0]+20, self.center[1]-15), (30,30)),  0)
        pygame.draw.rect (TB.background, ccolor , Rect((self.rmpos[0]-50, self.center[1]-15), (30,30)),  0)

        # attitude indicator. Use code for rotating thing.

        rect_surface = pygame.Surface(self.attitude_ind,pygame.SRCALPHA, 32)
        #rect_surface.fill(ccolor)
        # use a fancy triangle
        pygame.draw.polygon(rect_surface, Color("red3"), ((0, self.attitude_ind[1]), (self.attitude_ind[0]/2, 0),(self.attitude_ind[0], self.attitude_ind[1])), 0)

        oldRect = rect_surface.get_rect(center=(self.center))
        rect_surface, newRect = TB.rot_center(rect_surface,oldRect,(math.degrees(self.steering_angle)))
        TB.background.blit(rect_surface, newRect)


        # vectors
        maxlen = 35 #px
        maxpower = model.MotorModel.MAXPOWER
        s_lmpower = (self.lmpower * maxlen) / maxpower
        s_rmpower = (self.rmpower * maxlen) / maxpower
        lf = 'F'
        lcolor = Color("darkgreen") # forward
        rf = 'F'
        rcolor = Color("darkgreen") # backward

        if self.lmforward < 0:
            lf = 'B'
            lcolor = Color("purple")

        if self.rmforward < 0:
            rf = 'B'
            rcolor = Color("purple")

        lend = (self.lmpos[0],self.lmpos[1]+(s_lmpower*self.lmforward)*-1)
        rend = (self.rmpos[0],self.rmpos[1]+(s_rmpower*self.rmforward)*-1)

        pygame.draw.line(TB.background, lcolor, self.lmpos, lend, 3) # *-1 Y axis are inverted
        pygame.draw.line(TB.background, rcolor, self.rmpos, rend, 3)



        if self.lmpos[1] < lend[1]: # down arrow
            pygame.draw.polygon(TB.background, lcolor, ((lend[0],lend[1]+3), (lend[0]-3,lend[1]-2), (lend[0]+3,lend[1]-2)), 0)
        if self.lmpos[1] > lend[1]: # up  arrow
            pygame.draw.polygon(TB.background, lcolor, ((lend[0],lend[1]-3), (lend[0]-3,lend[1]+2), (lend[0]+3,lend[1]+2)), 0)

        if self.rmpos[1] < rend[1]: # down arrow
            pygame.draw.polygon(TB.background, rcolor, ((rend[0],rend[1]+3), (rend[0]-3,rend[1]-2), (rend[0]+3,rend[1]-2)), 0)
        if self.lmpos[1] > rend[1]: # up  arrow
            pygame.draw.polygon(TB.background, rcolor, ((rend[0],rend[1]-3), (rend[0]-3,rend[1]+2), (rend[0]+3,rend[1]+2)), 0)


        # text
        TB.RenderText(14, "LEFT_M", (self.lmpos[0], self.center[1]-50), tcolor)
        TB.RenderText(14, "RIGHT_M", (self.rmpos[0], self.center[1]-50), tcolor)
        TB.RenderText(14, "Front", (self.center[0], self.center[1]-40), tcolor)

        TB.RenderText(14, "%3.2f %c" % (self.lmpower,lf), (self.lmpos[0]-50, self.center[1]), tcolor)
        TB.RenderText(14, "%3.2f %c" % (self.rmpower,rf), (self.rmpos[0]+50, self.center[1]), tcolor)

        TB.RenderText(14, "v: %3.2f*%d|%3.2fdeg" % (self.angular_a, self.angular_d, math.degrees(self.steering_angle)*self.angular_d), (self.center[0], self.center[1]+40), tcolor)





class ArenaWidget:
    def __init__(self, position, width, height, caption, tdelta):
        self.pos = position
        self.width = width
        self.height = height
        self.caption = caption

        self.center = (self.pos[0]+(self.width/2), self.pos[1]+self.height/2)

        # to see if found inside (box when drone runs)

        self.droneRect = Rect(self.pos[0]+20, self.pos[1]+20, self.width-40, self.height-50)
        self.drone = DroneSprite(self.center,tdelta)

        # scale in meters of the field.
        # max speed: 0.6m/s -> 60cm second
        # 100m / self.width =>


    def Draw(self, TB, motors, tdelta, ccolor=Color("black"),  tcolor=Color("black")):

        # arena
        pygame.draw.rect (TB.background, ccolor, Rect(self.pos, (self.width,self.height)),  1)
        TB.RenderText(18, self.caption, (self.pos[0]+self.width/2,self.pos[1]+10), tcolor)

        # drone arena
        # pygame.draw.rect (TB.background, Color("red"), self.droneRect)

        # drone
        self.drone.UpdateVelocity(motors.linear_a, tdelta)
        self.drone.UpdateAngle(motors.steering_angle)
        self.drone.UpdatePosition(self.droneRect)

        oldRect = self.drone.image.get_rect(center=(self.drone.pos))
        rect_surface, newRect = TB.rot_center(self.drone.image,oldRect,(math.degrees(self.drone.angle))%360 )
        TB.background.blit(rect_surface, newRect)





class DroneSprite(pygame.sprite.Sprite):

    def __init__(self, orig_pos, tdelta):
        pygame.sprite.Sprite.__init__(self) #call Sprite intializer
        self.image, self.rect = self.load_image('drone.png', 0)
        self.orig_pos = orig_pos

        self.Reset(tdelta)

    def Reset(self, tdelta):
        self.angle = 0
        self.v = 0.0
        self.t  = tdelta
        self.pos = self.orig_pos
        self.MoveTo()

    #def sign(self, x): return 1 if x >= 0.0 else -1

    def UpdateVelocity(self, a, t):

        # if tdelta remains constant, it works.
        tdelta = 80

        if a == 0.0 and self.v > 0.0:
            self.v -= 0.01
            if self.v > -0.01 and self.v < 0.01:
                self.v = 0.0
            self.t = tdelta
            return
        if a == 0.0 and self.v < 0.0:
            self.v += 0.01
            if self.v > -0.01 and self.v < 0.01:
                self.v = 0.0
            self.t = tdelta
            return


        self.v = a*(tdelta/1000.0)
        self.t = tdelta


    def UpdatePosition(self, parentRect):
        #
        # move the drone to the new position, based on ANGLE and SPEED
        #

        ARENA_SCALE = 1.5 #(1px -> 1cm)

        D = (self.v * ARENA_SCALE)*self.t
        x = D*math.cos(self.angle+math.radians(90))
        y = -1*D*math.sin(self.angle+math.radians(90))

        #print D,x,y

        newpos = (self.pos[0]+x, self.pos[1]+y)
        oldpos = self.pos

        self.rect.center = newpos
        self.pos = newpos

        if not parentRect.contains(self.rect):
             self.rect.center = oldpos
             self.pos = oldpos




    def UpdateAngle(self, angle):
        # inserted a new constant to manage the angle (not too fast)
        self.angle = (self.angle + angle/10.0) % (2*math.pi)


    def MoveTo(self, pos=None):
        if pos == None:
            pos = self.pos
        self.rect.center = pos

    def load_image(self, name, colorkey=None):

        try:
            image = pygame.image.load(name)
            image.convert_alpha()
        except pygame.error, message:
            print 'Cannot load image:', name
            raise SystemExit, message
        #image = image.convert()

        #if colorkey is not None:
        #    if colorkey is -1:
        #        colorkey = image.get_at((0,0))
        #    image.set_colorkey(colorkey, RLEACCEL)
        return image, image.get_rect()




if __name__ == "__main__":

    wsock.websocketserver_start('',8000)

    ltime = 0
    pygame.init()
    clock = pygame.time.Clock()

    winsize = (800,800)
    screen = pygame.display.set_mode(winsize)
    TB = PyGameToolBox(winsize,screen)

    pygame.display.set_caption('TwichDrone Sim')

    modeljoy = JoyWidget( (100,110), 75, "MODEL JOYSTICK" )
    emujoy = JoyWidget( (700,110), 75, "SIM JOYSTICK" )
    recbutton = ButtonWidget( (760,170), 30,30, "REC" )

    motors = MotorWidget( (200,50), TB.Width()-400, 150,  "Drone Motors (Power Range: 0-255)")
    arena = ArenaWidget( (10,210), TB.Width()-20, TB.Height()-220, "Drone Simulator (Max Speed Motor: 0.6 m/s) [Click in Drone to RESET POS]", ltime)


    modeljoy.SetAngleRanges(model.DroneModel.FORWARD_ANGLE_RANGE, model.DroneModel.BACKWARD_ANGLE_RANGE)
    emujoy.SetAngleRanges(model.DroneModel.FORWARD_ANGLE_RANGE, model.DroneModel.BACKWARD_ANGLE_RANGE)

    while 1:
        clock.tick(60)
        TB.BGFill(Color("grey"))
        TB.RenderText(36,"TwichDrone Sim",(TB.Width()/2, 12), Color("black"))

        recbutton.Draw(TB)
        emujoy.Draw(TB)
        motors.Draw(TB)
        arena.Draw(TB, motors, ltime)

        # get the angle from the center position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if emujoy.MouseInside(mouse_x,mouse_y):

            data_model = emujoy.UpdateFromInput(TB, mouse_x, mouse_y)
            if pygame.mouse.get_pressed()[0]:
                model.MODEL.HandleData(json.dumps(data_model))

        #
        # get data from model
        #

        model.MODEL.update()
        data = model.MODEL.getdata()

        modeljoy.UpdateFromData(TB, data['data'])
        motors.Update(data['MR'], data['ML'])


        modeljoy.Draw(TB)
        TB.RenderText(18,"[MODEL] Buttons: %s" % (model.MODEL.getbuttons_str()), (TB.Width()/2,30), Color("black"))

        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                    sys.exit(0)
            if event.type == pygame.MOUSEBUTTONUP:
                    data_model = { 'kind': 'joystick', 'distance': 0.0, 'angle': 0.0 }
                    model.MODEL.HandleData(json.dumps(data_model))

            # click on REC button
            if event.type == pygame.MOUSEBUTTONUP and recbutton.MouseInside(mouse_x, mouse_y):
                    data_model = { 'kind': 'button', 'id': 'rec', 'pressed': 'true'}
                    model.MODEL.HandleData(json.dumps(data_model))

            # click on Drone (reset)
            if event.type == pygame.MOUSEBUTTONUP and arena.drone.rect.collidepoint(mouse_x, mouse_y):
                    print "resetting drone"
                    arena.drone.Reset(ltime)


        TB.Blit()
        pygame.display.flip()
        ltime +=1
