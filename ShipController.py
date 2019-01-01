from pandac.PandaModules import *
from math import sin, cos, pi, sqrt
import sys
from sail import Sail
from math import radians

MAX_VEL = 10  # Maximum ship velocity in units/sec
MAX_VEL_SQ = MAX_VEL ** 2  # Square of the ship velocity
DEG_TO_RAD = pi / 180  # translates degrees to radians for sin and cos
SCREEN_X = 20  # Screen goes from -20 to 20 on X
SCREEN_Y = 15  # Screen goes from -15 to 15 on Y
TURN_RATE = 360  # Degrees ship can turn in 1 second
ACCELERATION = 10  # Ship acceleration in units/sec/sec


class ShipController:

    def __init__(self, showbaseMain):
        self.sailBoat = Sail()
        self.showbaseMain = showbaseMain
        self.setupShipSprites()
        self.setupKeys()

    def setupShipSprites(self):
        # Load the ship and set its initial velocity.
        self.ship = self.showbaseMain.loadObject("sailing_ship.png", scale=3)
        self.setVelocity(self.ship, LVector3.zero())

        # creates an empty sin-graph object
        # the sail holder allows the sail to be slightly off set from the middle
        # making it more realistic
        # the actual sail is then parented to the sail holder
        self.sailHolder = NodePath("sailHolder")
        self.sailHolder.reparentTo(self.ship)
        self.sailHolder.setPos(0, 0, 0.2)
        # self.sailHolder.setR(25)

        # Load the sail into holder
        self.sail = self.showbaseMain.loadObject("sail2.png", scale=0.9)
        self.sail.reparentTo(self.sailHolder)
        self.sail.setPos(0, -0.1, -0.3)

        self.rudderHolder = NodePath("rudderHolder")
        self.rudderHolder.reparentTo(self.ship)
        self.rudderHolder.setPos(0, 0, -0.4)

        self.rudder = self.showbaseMain.loadObject("sail2.png", scale=0.4, depth=0)
        self.rudder.reparentTo(self.rudderHolder)
        self.rudder.setPos(0, 0, -0.1)
        # self.rudderHolder.setR(-25)

    def setupKeys(self):
        # A dictionary of what keys are currently being pressed
        # The key events update this list, and our task will query it as input
        self.keys = {"turnLeft": 0, "turnRight": 0,
                    "main_sheet_left": 0, "main_sheet_right": 0}

        self.showbaseMain.accept("escape", sys.exit)  # Escape quits the simulator
        # Other keys events set the appropriate value in our key dictionary
        # these keys control the movement of the sail boat
        self.showbaseMain.accept("arrow_left", self.setKey, ["turnLeft", 1])
        self.showbaseMain.accept("arrow_left-up", self.setKey, ["turnLeft", 0])
        self.showbaseMain.accept("arrow_right", self.setKey, ["turnRight", 1])
        self.showbaseMain.accept("arrow_right-up", self.setKey, ["turnRight", 0])


        # these keys control the movement of the main sheet
        self.showbaseMain.accept("e", self.setKey, ["main_sheet_left", 1])
        self.showbaseMain.accept("e-up", self.setKey, ["main_sheet_left", 0])
        self.showbaseMain.accept("r", self.setKey, ["main_sheet_right", 1])
        self.showbaseMain.accept("r-up", self.setKey, ["main_sheet_right", 0])

    def getDistanceToLine(self, pos, pathPoints):
        smallestDist = 1000000000000

        for pt in pathPoints:
            dist = sqrt(((pt.x - pos.x) ** 2.0) + ((pt.z - pos.z) ** 2.0))
            if dist < smallestDist:
                smallestDist = dist

        return smallestDist

    def nearLastPoint(self, pos, pathPoints):
        lastPt = pathPoints[len(pathPoints) - 1]
        dist = sqrt(abs(((lastPt.x - pos.x) ** 2.0) + ((lastPt.z - pos.z) ** 2.0)))
        return dist

    # As described earlier, this simply sets a key in the self.keys dictionary
    # to the given value.
    def setKey(self, key, val):
        self.keys[key] = val

    def setVelocity(self, obj, val):
        obj.setPythonTag("velocity", val)

    def getVelocity(self, obj):
        return obj.getPythonTag("velocity")

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

    def updateShip(self, dt, pathPoints):
        heading = self.ship.getR()  # Heading is the roll value for this model

        windHeading = self.showbaseMain.wind_direction.getR()
        windStrength = self.showbaseMain.wind_strength['value']
        mainSheetLength = self.showbaseMain.main_sheet_length['value']

        pos = self.ship.getPos()

        dist = self.getDistanceToLine(pos, pathPoints)

        self.showbaseMain.score -= (dist * dist)

        if (abs(self.nearLastPoint(pos, pathPoints)) < 1.5):
            print("****Game finish****" + str(self.nearLastPoint(pos, pathPoints)))
            self.showbaseMain.finished = True

        #print("Last: " + str(self.nearLastPoint(pos)))

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
        # clips vel to maximum value MAX_VEL_SQ
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
            self.showbaseMain.main_sheet_length['value'] = mainSheetLength
        elif self.keys["main_sheet_right"]:
            mainSheetLength += dt * 10
            self.showbaseMain.main_sheet_length['value'] = mainSheetLength

        # Finally, update the position as with any other object
        self.update_pos(self.ship, dt)
