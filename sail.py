from math import sin, cos, sqrt, pow, pi, atan2, degrees

# Ported from https://github.com/rahil-p/SailSim/blob/master/js/sailbot.js
HALF_PI = pi*0.5
TWO_PI = pi*2
PI = pi

def placeRound(measure, nDigits = 2):
    rounded = round(measure * pow(10, nDigits)) / pow(10, nDigits)
    return rounded

def angleMod(someAngle, makePos=1):

    someAngle %= (TWO_PI)

    if (makePos==1):
        while (someAngle < 0):
            someAngle += TWO_PI

    return someAngle

class Sail():

    def __init__(self):
        # hull size
        self.boatWidth = 12 # 1px~ = 1.5 ft(8ft)
        self.boatLength = 36 # 1px~ = 1.5ft(24ft)
        self.mainLength = 36 #(2/3 * self.boatLength) - 4 # (20 ft)
        # todo: make this const
        self.mainSheetLimit = self.mainLength * sqrt(2)
        self.sealvlAirDens = .0765
        self.mainArea = pow(self.mainLength, 2) / 2

        self.boatAngle = 0
        self.boatVelocity = 0
        self.boatAccel = 0
        self.mainAngle = 0

    def getFluidCoefs(self, mainAttack2):

        #  based on a degree 2 polynomial regression of estimated data from http://bit.ly/2Jh4mT0
        dragCoef = max(.16,-.45361 * pow(mainAttack2, 2) + 1.64225 * mainAttack2 - .27701)

        #  based on a degree 2 polynomial regression of estimated data from http://bit.ly/2Jh4mT0
        liftCoef = .5626 * pow(mainAttack2, 3) - 3.1881 * pow(mainAttack2, 2) + 4.4150 * mainAttack2 - .6614

        return [dragCoef, liftCoef]

    def getTorque(self, mainArea, windPressure, dragCoef, mainAttack):

      force = mainArea * windPressure * dragCoef * sin(mainAttack)
      torque = force * self.mainLength

      return torque

    def getWindPower(self, appVelocity):

        windPower = .5 * self.mainArea * self.sealvlAirDens * pow(appVelocity, 3)

        return windPower

    def getWindPressure(self, appVelocity):
        #  given .00256 assumption

        windPressure = .00256 * pow(appVelocity, 2)

        return windPressure

    def getAngularVelocity(self, mainLength, mainArea, windPressure, dragCoef, mainAttack,
                              sealvlAirDens, appVelocity):

        torque = self.getTorque(mainArea, windPressure, dragCoef, mainAttack)

        windPower = self.getWindPower(sealvlAirDens)

        angularVelocity = torque / windPower

        return angularVelocity


    def proposeAngle(self, mainAngle, appAngle, angularVelocity):

        if (mainAngle > appAngle):
          mainAngle = angleMod(mainAngle - self.boatAngle - PI) #resets the angle relative to the boat
          mainAngle -= angularVelocity
        elif (mainAngle < appAngle):
          mainAngle = angleMod(mainAngle - self.boatAngle - PI) #resets the angle relative to the boat
          mainAngle += angularVelocity

        return mainAngle


    def limitMainsail(self, mainSheetLength, mainAngle):

        limit = (mainSheetLength / self.mainSheetLimit) * HALF_PI

        flag = True

        if (mainAngle > limit and mainAngle < PI):
            mainAngle = limit
            flag = False
        elif (mainAngle > PI and mainAngle < TWO_PI - limit):
            mainAngle = TWO_PI - limit
            flag = False

        return [mainAngle, flag]

    def clamp(self, n, smallest, largest):
        if n < smallest: return smallest
        if n > largest: return largest
        return n

    def limitMainsail2(self, mainSheetLength, mainAngle):

        limit = (mainSheetLength / self.mainSheetLimit) * HALF_PI

        return [self.clamp(mainAngle, -limit, limit), not abs(mainAngle) > limit]

    def getForces(self, flag, appAngle, boatAngle, dragCoef, liftCoef,
                        mainArea, sealvlAirDens,appVelocity):

        appAngle = angleMod(appAngle + PI, makePos=0)
        boatAttack = max(appAngle, boatAngle) - min(appAngle, boatAngle)

        if (boatAttack > PI):
            boatAttack = TWO_PI - boatAttack

        boatAttack = angleMod(boatAttack)

        if (flag != False):
            dragForce = 0
            liftForce = 0
            forwardForce = 0
            lateralForce = 0
        else:
            dragForce = .5 * mainArea * dragCoef * sealvlAirDens * pow(appVelocity, 2)
            liftForce = .5 * mainArea * liftCoef * sealvlAirDens * pow(appVelocity, 2)

            forwardForce = liftForce * sin(boatAttack) - dragForce * cos(boatAttack)
            lateralForce = liftForce * cos(boatAttack) - dragForce * sin(boatAttack)

        return [dragForce, liftForce, forwardForce, lateralForce, boatAttack]

    def rotateMainsail(self, appAngle, appVelocity, boatAngle, mainAngle, mainLength, mainSheetLength):

        # if x greater than 180, then it is 180-(x-180) = 360-x

        # gets the actual angle(vs.respective to boatAngle)
        mainAngle = angleMod(boatAngle + mainAngle + PI, makePos=0)
        mainAttack = max(mainAngle, appAngle) - min(mainAngle, appAngle)
        mainAttack2 = TWO_PI - mainAttack if (mainAttack > PI) else mainAttack
        self.mainArea = pow(self.mainLength, 2) / 2

        windPressure = self.getWindPressure(appVelocity)
        [dragCoef, liftCoef] = self.getFluidCoefs(mainAttack2)

        angularVelocity = self.getAngularVelocity(mainLength, self.mainArea, windPressure, dragCoef, mainAttack,
                                               self.sealvlAirDens, appVelocity)
        mainAngle = self.proposeAngle(mainAngle, appAngle, angularVelocity)

        [mainAngle, flag] = self.limitMainsail(mainSheetLength, mainAngle)

        return [mainAngle, mainAttack2, flag,
                dragCoef, liftCoef,
                self.mainArea, self.sealvlAirDens,
                angularVelocity]

    # determining the apparent wind's velocity and angle function
    def getAppVector(self, boatVelocity, boatAngle, wVelocity, wAngle):

        # using boatVelocity multiplier of 5(implication of the adhoc adjustment in the text object above)
        appVelocity = sqrt(pow(5 * boatVelocity * sin(boatAngle + PI) +
                           wVelocity * sin(wAngle), 2) +
                       pow(5 * boatVelocity * cos(boatAngle + PI) +
                           wVelocity * cos(wAngle), 2))

        appAngle = atan2(5 * boatVelocity * sin(boatAngle + PI) +
                     wVelocity * sin(wAngle),
                     5 * boatVelocity * cos(boatAngle + PI) +
                     wVelocity * cos(wAngle))
        appAngle = angleMod(appAngle)

        return [appVelocity, appAngle]


    # moves the boat based on its angle and velocity (conversion limits the velocities for reasonable visibility)
    def moveBoat(self, x, y, boatVelocity, boatAngle, conversion=3):

      x += boatVelocity * sin(boatAngle) * conversion
      y -= boatVelocity * cos(boatAngle) * conversion

      return [x,y]

    def update(self,windVelocity, windAngle, mainSheetLength, boatAngle,x, y):

        self.x = x
        self.y = y

        #[self.x, self.y] = self.moveBoat(self.x, self.y, self.boatVelocity, self.boatAngle)
        self.boatAngle = boatAngle

        [appVelocity, appAngle] = self.getAppVector(self.boatVelocity, boatAngle, windVelocity, windAngle)

        [self.mainAngle, self.mainAttack2, self.flag,
         dragCoef, liftCoef,
         self.mainArea, sealvlAirDens,
         self.angularVelocity] = self.rotateMainsail(appAngle, appVelocity,
                                                boatAngle,
                                                self.mainAngle, self.mainLength,
                                                mainSheetLength)

        [self.dragForce, self.liftForce,
         self.forwardForce, self.lateralForce,
         self.boatAttack] = self.getForces(self.flag, appAngle, self.boatAngle,
                                      dragCoef, liftCoef,
                                      self.mainArea, self.sealvlAirDens,
                                      appVelocity)

        self.boatAccel = self.forwardForce / 2000 # assumed mass given J24(similar dimensions)
        self.boatVelocity += self.boatAccel / 60 # 60 pixels per sec(calibrates time)

        self.resistanceForce = 300 * self.boatVelocity # a makeshift attempt at correcting for resistance
        self.resistanceAccel = self.resistanceForce / 2000
        self.boatVelocity -= self.resistanceAccel / 60

        self.boatVelocity = max(-.03, self.boatVelocity) # ad hoc adjustment

        return [self.boatVelocity*10000000, round(degrees(self.mainAngle),2)]