#!/usr/bin/env python

# Author: Ella Norman

from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import LPoint3, LVector3, NodePath
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
from math import sin, cos, pi
from random import randint, choice, random
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
import sys

# Constants that will control the behavior of the game. It is good to
# group constants like this so that they can be changed once without
# having to find everywhere they are used in code
SPRITE_POS = 55     # At default field of view and a depth of 55, the screen
# dimensions is 40x30 units
SCREEN_X = 20       # Screen goes from -20 to 20 on X
SCREEN_Y = 15       # Screen goes from -15 to 15 on Y
TURN_RATE = 360     # Degrees ship can turn in 1 second
ACCELERATION = 10   # Ship acceleration in units/sec/sec
MAX_VEL = 6         # Maximum ship velocity in units/sec
MAX_VEL_SQ = MAX_VEL ** 2  # Square of the ship velocity
DEG_TO_RAD = pi / 180  # translates degrees to radians for sin and cos
BULLET_LIFE = 2     # How long bullets stay on screen before removed
BULLET_REPEAT = .2  # How often bullets can be fired
BULLET_SPEED = 10   # Speed bullets move
AST_INIT_VEL = 1    # Velocity of the largest asteroids
AST_INIT_SCALE = 3  # Initial asteroid scale
AST_VEL_SCALE = 2.2  # How much asteroid speed multiplies when broken up
AST_SIZE_SCALE = .6  # How much asteroid scale changes when broken up
AST_MIN_SCALE = 1.1  # If and asteroid is smaller than this and is hit,
# it disapears instead of splitting up


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
    obj.setDepthTest(False)

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

        # Disable default mouse-based camera control. This is a method on the
        # ShowBase class from which we inherit.
        self.disableMouse()

        # Load the background starfield.
        self.setBackgroundColor((0, 0, 0, 1))
        self.bg = loadObject("water.jpg", scale=146, depth=200,
                             transparency=False)

        # Load the ship and set its initial velocity.
        self.ship = loadObject("sailing_ship.png", scale=3)
        self.setVelocity(self.ship, LVector3.zero())

        self.sailHolder = NodePath("sailHolder")
        self.sailHolder.reparentTo(self.ship)
        self.sailHolder.setPos(0, 0, 0.2)
        self.sailHolder.setR(25)

        # Load the sail into holder
        self.sail = loadObject("sail2.png", scale=1, depth=50)
        #self.setVelocity(self.sail, LVector3.zero())
        self.sail.reparentTo(self.sailHolder)
        self.sail.setPos(0, 0, -0.3)

        self.rudderHolder = NodePath("rudderHolder")
        self.rudderHolder.reparentTo(self.ship)
        self.rudderHolder.setPos(0, 0, -0.4)

        self.rudder = loadObject("sail2.png", scale=.4)
        self.rudder.reparentTo(self.rudderHolder)
        self.rudder.setPos(0, 0, -0.1)
        self.rudderHolder.setR(-25)

        # A dictionary of what keys are currently being pressed
        # The key events update this list, and our task will query it as input
        self.keys = {"turnLeft": 0, "turnRight": 0,
                     "accel": 0, "fire": 0}

        self.accept("escape", sys.exit)  # Escape quits
        # Other keys events set the appropriate value in our key dictionary
        self.accept("arrow_left",     self.setKey, ["turnLeft", 1])
        self.accept("arrow_left-up",  self.setKey, ["turnLeft", 0])
        self.accept("arrow_right",    self.setKey, ["turnRight", 1])
        self.accept("arrow_right-up", self.setKey, ["turnRight", 0])
        self.accept("arrow_up",       self.setKey, ["accel", 1])
        self.accept("arrow_up-up",    self.setKey, ["accel", 0])
        self.accept("space",          self.setKey, ["fire", 1])

        # Now we create the task. taskMgr is the task manager that actually
        # calls the function each frame. The add method creates a new task.
        # The first argument is the function to be called, and the second
        # argument is the name for the task.  It returns a task object which
        # is passed to the function each frame.
        self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")
        self.finished=False

    # As described earlier, this simply sets a key in the self.keys dictionary
    # to the given value.
    def setKey(self, key, val):
        self.keys[key] = val

    def setVelocity(self, obj, val):
        obj.setPythonTag("velocity", val)

    def getVelocity(self, obj):
        return obj.getPythonTag("velocity")

    def setExpires(self, obj, val):
        obj.setPythonTag("expires", val)

    def getExpires(self, obj):
        return obj.getPythonTag("expires")

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
        # Change heading if left or right is being pressed
        if self.keys["turnRight"]:
            heading += dt * TURN_RATE
            self.ship.setR(heading % 360)
        elif self.keys["turnLeft"]:
            heading -= dt * TURN_RATE
            self.ship.setR(heading % 360)

        # Thrust causes acceleration in the direction the ship is currently
        # facing
        if self.keys["accel"]:
            heading_rad = DEG_TO_RAD * heading
            # This builds a new velocity vector and adds it to the current one
            # relative to the camera, the screen in Panda is the XZ plane.
            # Therefore all of our Y values in our velocities are 0 to signify
            # no change in that direction.
            newVel = \
                LVector3(sin(heading_rad), 0, cos(heading_rad)) * ACCELERATION * dt
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
