#!/usr/bin/env python

# Author: Ella Norman

from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import LPoint3, LVector3, NodePath
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
from math import sin, cos, pi
import sys
from pandac.PandaModules import *
from direct.showutil.Rope import Rope
from direct.gui.DirectGui import *
from sail import Sail
from math import radians

# Constants that will control the behavior of the game. It is good to
# group constants like this so that they can be changed once without
# having to find everywhere they are used in code
SPRITE_POS = 55     # At default field of view and a depth of 55, the screen
# dimensions is 40x30 units
SCREEN_X = 20       # Screen goes from -20 to 20 on X
SCREEN_Y = 15       # Screen goes from -15 to 15 on Y
TURN_RATE = 360     # Degrees ship can turn in 1 second
ACCELERATION = 10   # Ship acceleration in units/sec/sec
MAX_VEL = 10         # Maximum ship velocity in units/sec
MAX_VEL_SQ = MAX_VEL ** 2  # Square of the ship velocity
DEG_TO_RAD = pi / 180  # translates degrees to radians for sin and cos

# This helps reduce the amount of code used by loading objects, since all of
# the objects are pretty much the same.
def loadObject(tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=1,
               transparency=True):
    # Every object uses the plane model and is parented to the camera
    # so that it faces the screen.
    obj = loader.loadModel("models/plane")
    obj.reparentTo(camera)

    # Set the initial position and scale.
    obj.setPos(pos.getX(), depth, pos.getY())
    obj.setScale(scale)

    # This tells Panda not to worry about the order that things are drawn in
    # (ie. disable Z-testing).  This prevents an effect known as Z-fighting.
    obj.setBin("unsorted", 0)
    obj.setDepthTest(True)

    if transparency:
        # Enable transparency blending.
        obj.setTransparency(TransparencyAttrib.MAlpha)

    if tex:
        # Load and set the requested texture.
        tex = loader.loadTexture("textures/" + tex)
        obj.setTexture(tex, 1)

    return obj



class SailingSimulator(ShowBase):

    def __init__(self):
        # Initialize the ShowBase class from which we inherit, which will
        # create a window and set up everything we need for rendering into it.
        ShowBase.__init__(self)

        self.sailBoat = Sail()

        # Disable default mouse-based camera control. This is a method on the
        # ShowBase class from which we inherit.
        self.disableMouse()

        # Setting the background to 'water'
        self.setBackgroundColor((0, 0, 0, 1))
        self.bg = loadObject("water.jpg", scale=146, depth=200,
                             transparency=False)

        self.gbuoy = loadObject("Green_buoy.png", scale=4, depth=50)
        self.setVelocity(self.gbuoy, LVector3.zero())
        self.gbuoy.setPos(-7, 50, 7)

        self.rbuoy = loadObject("Red_buoy.png", scale=4, depth=50)
        self.setVelocity(self.rbuoy, LVector3.zero())
        self.rbuoy.setPos(2, 50, -4)

        self.wind_direction = loadObject("arrow.png", scale=2, depth=50)
        #self.setVelocity(self.arrow, LVector3.zero())
        self.wind_direction.setPos(11, 50, 11)
        self.wind_direction.setR(90)


        # Load the ship and set its initial velocity.
        self.ship = loadObject("sailing_ship.png", scale=3)
        self.setVelocity(self.ship, LVector3.zero())
        self.ship.setPos(-16, 50, 0)

        self.sailHolder = NodePath("sailHolder")
        self.sailHolder.reparentTo(self.ship)
        self.sailHolder.setPos(0, 0, 0.2)
        #self.sailHolder.setR(25)

        # Load the sail into holder
        self.sail = loadObject("sail2.png", scale=0.9)
        self.sail.reparentTo(self.sailHolder)
        self.sail.setPos(0, -0.1, -0.3)

        self.rudderHolder = NodePath("rudderHolder")
        self.rudderHolder.reparentTo(self.ship)
        self.rudderHolder.setPos(0, 0, -0.4)

        self.rudder = loadObject("sail2.png", scale=0.4, depth=0)
        self.rudder.reparentTo(self.rudderHolder)
        self.rudder.setPos(0, 0, -0.1)
        #self.rudderHolder.setR(-25)

        #coding in on screen text
        self.wind_strength = DirectSlider(range=(0, 100), value=10, command=self.show_wind_strength,
                                          pos=LPoint3(1, 1, 0.9), scale=0.2)
        self.wind_strength_text = OnscreenText(text=str(int(self.wind_strength['value'])), parent=base.a2dTopLeft,
                                               pos=(2.2, -.06 * 2 - 0.1),
                                               fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1)

        self.main_sheet_length = DirectSlider(range=(0, 100), value=10, command=self.show_main_sheet_length,
                                              pos=LPoint3(.3, 1, 0.9),
                                              scale=0.2)

        self.main_sheet_length_text = OnscreenText(text=str(int(self.main_sheet_length['value'])),
                                                   parent=base.a2dTopLeft,
                                                   pos=(1.5, -.06 * 2 - 0.1),
                                                   fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5),
                                                   scale=.1)

        self.velocityText = OnscreenText(text="Velocity: 0", parent=base.a2dTopLeft,
                                         pos=(0.04, -.06 * 1 - 0.1),
                                         fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1,
                                         mayChange=True)
        self.scoreText = OnscreenText(text="Score: 0", parent=base.a2dTopLeft,
                                      pos=(0.07, -.06 * 3 - 0.1),
                                      fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1,
                                      mayChange=True)


        r = Rope()
        r.setup(4, [(None, (-18, 0, 0)),
                    (None, (-8, 0, -20)),
                    (None, (-15, 0, 15)),
                    (None, (0, 0, 10)),
                    (None, (0, 0, -25)),
                    (None, (10, 0, 10)),
                    (None, (10, 0, 10)),
                    (None, (15, 0, -10))
                    ])
        r.ropeNode.setThickness(10)
        r.setPos(0, 55, 0)
        r.reparentTo(camera)


        # A dictionary of what keys are currently being pressed
        # The key events update this list, and our task will query it as input
        self.keys = {"turnLeft": 0, "turnRight": 0,
                     "accel": 0, "fire": 0, "main_sheet_left": 0, "main_sheet_right": 0}

        self.accept("escape", sys.exit)  # Escape quits
        # Other keys events set the appropriate value in our key dictionary
        self.accept("arrow_left",     self.setKey, ["turnLeft", 1])
        self.accept("arrow_left-up",  self.setKey, ["turnLeft", 0])
        self.accept("arrow_right",    self.setKey, ["turnRight", 1])
        self.accept("arrow_right-up", self.setKey, ["turnRight", 0])
        self.accept("arrow_up",       self.setKey, ["accel", 1])
        self.accept("arrow_up-up",    self.setKey, ["accel", 0])
        self.accept("space",          self.setKey, ["fire", 1])

        self.accept("e",   self.setKey, ["main_sheet_left", 1])
        self.accept("e-up", self.setKey, ["main_sheet_left", 0])
        self.accept("r", self.setKey, ["main_sheet_right", 1])
        self.accept("r-up", self.setKey, ["main_sheet_right", 0])

        # Now we create the task. taskMgr is the task manager that actually
        # calls the function each frame. The add method creates a new task.
        # The first argument is the function to be called, and the second
        # argument is the name for the task.  It returns a task object which
        # is passed to the function each frame.
        self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")
        self.finished=False

    def show_wind_strength(self):
        self.wind_strength_text['text'] = "Wind:" + str(int(self.wind_strength['value']))

    def show_main_sheet_length(self):
        self.main_sheet_length_text['text'] = "Main: " + str(int(self.main_sheet_length['value']))

    def show_score(self):
        self.scoreText['text'] = "Score: " + str(int(self.score))


    # As described earlier, this simply sets a key in the self.keys dictionary
    # to the given value.
    def setKey(self, key, val):
        self.keys[key] = val

    def setVelocity(self, obj, val):
        obj.setPythonTag("velocity", val)

    def getVelocity(self, obj):
        return obj.getPythonTag("velocity")

   # This is our main task function, which does all of the per-frame
    # processing.  It takes in self like all functions in a class, and task,
    # the task object returned by taskMgr.
    def gameLoop(self, task):
        # Get the time elapsed since the next frame.  We need this for our
        # distance and velocity calculations.
        dt = globalClock.getDt()

        # If the ship is not alive, do nothing.  Tasks return Task.cont to
        # signify that the task should continue running. If Task.done were
        # returned instead, the task would be removed and would no longer be
        # called every frame.
        if self.finished:
            return Task.cont

        # update ship position
        self.updateShip(dt)

        # Since every return is Task.cont, the task will
        return Task.cont
        # continue indefinitely

    # Updates the positions of objects
    def update_pos(self, obj, dt):
        vel = self.getVelocity(obj)
        # newpos - SOH this does the maths bit for me
        newPos = obj.getPos() + (vel * dt)

        # Check if the object is out of bounds. If so, wrap it
        radius = .5 * obj.getScale().getX()
        if newPos.getX() - radius > SCREEN_X:
            newPos.setX(-SCREEN_X)
        elif newPos.getX() + radius < -SCREEN_X:
            newPos.setX(SCREEN_X)
        if newPos.getZ() - radius > SCREEN_Y:
            newPos.setZ(-SCREEN_Y)
        elif newPos.getZ() + radius < -SCREEN_Y:
            newPos.setZ(SCREEN_Y)

        obj.setPos(newPos)

    # This updates the ship's position. This is similar to the general update
    # but takes into account turn and thrust

    def updateShip(self, dt):
        heading = self.ship.getR()  # Heading is the roll value for this model

        windHeading = self.wind_direction.getR()
        windStrength = self.wind_strength['value']
        mainSheetLength = self.main_sheet_length['value']

        pos = self.ship.getPos()

        [boatVelocity, sailAngle] = self.sailBoat.update((windStrength + .000001) / 1000.0, radians(windHeading),
                                                         mainSheetLength, radians(heading), pos.x, pos.z)
        self.sailHolder.setR(sailAngle)

        heading_rad = DEG_TO_RAD * heading
        # This builds a new velocity vector and adds it to the current one
        # relative to the camera, the screen in Panda is the XZ plane.
        # Therefore all of our Y values in our velocities are 0 to signify
        # no change in that direction.
        newVel = LVector3(sin(heading_rad), 0, cos(heading_rad)) * boatVelocity * dt
        # newVel += (self.getVelocity(self.ship)*.99)
        if newVel.lengthSquared() > MAX_VEL_SQ:
            newVel.normalize()
            newVel *= MAX_VEL
        self.setVelocity(self.ship, newVel)

       # self.velocityText.setText("Boat Velocity: " + str(round(newVel.lengthSquared(), 2)))
        # Change heading if left or right is being pressed
        if self.keys["turnRight"]:
            heading += dt * TURN_RATE
            self.ship.setR(heading % 360)
        elif self.keys["turnLeft"]:
            heading -= dt * TURN_RATE
            self.ship.setR(heading % 360)

        if self.keys["main_sheet_left"]:
            mainSheetLength -= dt * 10
            self.main_sheet_length['value'] = mainSheetLength
        elif self.keys["main_sheet_right"]:
            mainSheetLength += dt * 10
            self.main_sheet_length['value'] = mainSheetLength


        # Thrust causes acceleration in the direction the ship is currently
        # facing
        if self.keys["accel"]:
            heading_rad = DEG_TO_RAD * heading
            # This builds a new velocity vector and adds it to the current one
            # relative to the camera, the screen in Panda is the XZ plane.
            # Therefore all of our Y values in our velocities are 0 to signify
            # no change in that direction.
            newVel = LVector3(sin(heading_rad), 0, cos(heading_rad)) * ACCELERATION * dt
            newVel += self.getVelocity(self.ship)
            # Clamps the new velocity to the maximum speed. lengthSquared() is
            # used again since it is faster than length()
            if newVel.lengthSquared() > MAX_VEL_SQ:
                newVel.normalize()
                newVel *= MAX_VEL
            self.setVelocity(self.ship, newVel)

        # Finally, update the position as with any other object
        self.update_pos(self.ship, dt)

# We now have everything we need. Make an instance of the class and start
# 3D rendering
sailingSimulator = SailingSimulator()
sailingSimulator.run()
