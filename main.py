# Sailing Simulator - A level coursework
# Author: Ella Norman

# ShowBase class loads most of the other Panda3D modules
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
# importing maths for physics engine
from pandac.PandaModules import *
from direct.gui.DirectGui import *
from panda3d.core import TextNode

import sqlite3
from ShipController import ShipController
from Scene import Scene

# Constants that will control the behavior of the game. It is good to
# group constants like this so that they can be changed once without
# having to find everywhere they are used in code

SPRITE_POS = 55  # At default field of view and a depth of 55, the screen

# start of class
class SailingSimulator(ShowBase):
    # __init__ is an object constructor
    def __init__(self):  # self is a special variable which refers to the class of the object
        # Initialize the ShowBase class from which we inherit, which will
        # create a window and sets up everything I need for rendering into it.
        ShowBase.__init__(self)

        self.shipController = ShipController(self)

        self.highScoreTextRow = [10]
        self.scene = Scene(self)

        # Disable default mouse-based camera control. This is a method on the
        # ShowBase class from which we inherit.
        self.disableMouse()

        self.scene.setup()

        # This 'sprite' shows the direction of the wind to the user
        self.wind_direction = self.loadObject("arrow.png", scale=2, depth=50)

        self.wind_direction.setPos(11, 50, 11)
        self.wind_direction.setR(90)

        # coding in on screen text
        self.wind_strength = DirectSlider(range=(0, 100), value=12, command=self.show_wind_strength,
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

        self.scoreText = OnscreenText(text="Score: 0", parent=base.a2dTopLeft,
                                      pos=(0.1, -.5 * 1.3 - 1.3),
                                      fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1,
                                      mayChange=True)


        # Created the task. taskMgr is the task manager that actually
        # calls the function each frame. The add method creates a new task.
        # The first argument is the function to be called, and the second
        # argument is the name for the task.  It returns a task object which
        # is passed to the function each frame.
        self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")
        self.finished = True

        self.startButton = DirectButton(text=("Start Game"), scale=0.09, command=self.startGame)

        self.showHighscoreTable()

        self.restartGame()

    def restartGame(self):
        self.score = 10000
        self.main_sheet_length['value'] = 10
        self.shipController.ship.setPos(-16, 50, 0)
        self.shipController.ship.setR(170)

    def finishGame(self):
        self.insertNewscore("Name", self.score)
        self.showHighscoreTable()

    def showHighscoreTable(self):
        highscoreList = self.getHighscores()

        self.highscoreTextHeading = OnscreenText(text="Highscores", parent=base.a2dTopLeft,
                                                 pos=(0.10, -.1),
                                                 fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1,
                                                 mayChange=True)
        self.highScoreTextRow = []
        for f in range(len(highscoreList)):
            self.highScoreTextRow.append(
                OnscreenText(text=highscoreList[f][0] + " " + str(int(highscoreList[f][1])), parent=base.a2dTopLeft,
                             pos=(0.10, -.2 - (f * .08)),
                             fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.1,
                             mayChange=True))

    def show_score(self):
        self.scoreText['text'] = "Score: " + str(int(self.score))

    def startGame(self):
        self.restartGame()
        self.finished = False
        self.startButton.hide()

    def show_wind_strength(self):
        self.wind_strength_text['text'] = "Wind:" + str(int(self.wind_strength['value']))

    def show_main_sheet_length(self):
        self.main_sheet_length_text['text'] = "Main: " + str(int(self.main_sheet_length['value']))

    def show_score(self):
        self.scoreText['text'] = "Score: " + str(int(self.score))



    # This is my main task function, which does all of the per-frame
    # processing.  It takes in self like all functions in a class, and task,
    # the task object returned by taskMgr.
    def gameLoop(self, task):
        # Get the time elapsed since the next frame.  I need this for our
        # distance and velocity calculations.
        dt = globalClock.getDt()
        # If the ship is not alive, do nothing.  Tasks return Task.cont to
        # signify that the task should continue running. If Task.done were
        # returned instead, the task would be removed and would no longer be
        # called every frame.
        if self.finished:
            self.startButton.show()
            return Task.cont
        # update ship position
        self.shipController.updateShip(dt, self.scene.curvePoints)
        self.show_score()
        # Since every return is Task.cont, the task will
        return Task.cont
        # continue indefinitely


    def insertNewscore(self, name, score):
        # Insert user 1
        cursor.execute('''INSERT INTO users(name,score) VALUES(?,?)''', (name, score))
        print("New user score inserted")
        db.commit()
        self.keepTop5ScoresOnly()

    def keepTop5ScoresOnly(self):
        res = cursor.execute('''SELECT * FROM users order by score desc limit 5''')
        results = res.fetchall()
        if len(results) > 5:
            lowestScore = results[len(results) - 1][2]
            print (lowestScore)
            cursor.execute('''DELETE FROM users WHERE score < ?''', (lowestScore,))

    def getHighscores(self):
        cursor = db.cursor()
        res = cursor.execute('''SELECT * FROM users order by score desc limit 5 ''')
        highscores = res.fetchall()
        return highscores


    # This helps reduce the amount of code used by loading objects, since all of
    # the objects are pretty much the same.
    def loadObject(self, tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=1,
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

db = sqlite3.connect('data.db')


try:
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE users(name TEXT, score NUMBER)''')
    db.commit()
    print("Table created")
except:
    print("Table already created")

# We now have everything we need. Make an instance of the class and start
# 3D rendering
sailingSimulator = SailingSimulator()
sailingSimulator.run()
