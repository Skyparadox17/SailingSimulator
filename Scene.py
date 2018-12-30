from direct.showutil.Rope import Rope


class Scene:

    def __init__(self, showbaseMain):
        self.showbaseMain = showbaseMain

    def setup(self):
        # Setting the background to 'water'
        # .self refers back to class(linking it) ensuring it's not just global
        self.showbaseMain.setBackgroundColor((0, 0, 0, 1))
        self.bg = self.showbaseMain.loadObject("water.jpg", scale=146, depth=200, transparency=False)

        # creating & positioning the green buoy
        self.gbuoy = self.showbaseMain.loadObject("Green_buoy.png", scale=4, depth=50)
        self.gbuoy.setPos(-7, 50, 7)

        # Second green buoy
        self.sgbuoy = self.showbaseMain.loadObject("Green_buoy.png", scale=4, depth=50)
        self.sgbuoy.setPos(9, 50, 3)

        # creating & positioning the red buoy
        self.rbuoy = self.showbaseMain.loadObject("Red_buoy.png", scale=4, depth=50)
        self.rbuoy.setPos(2.5, 50, -6)

        # Importing land
        self.sland = self.showbaseMain.loadObject("land.png", scale=16, depth=50)
        self.sland.setPos(3, 50, 9)
        self.sland.setR(180)

        self.land = self.showbaseMain.loadObject("land.png", scale=16, depth=50)
        self.land.setPos(-5, 50, -9)

        self.Finflag = self.showbaseMain.loadObject("Finflag.png", scale=4, depth=50)
        self.Finflag.setPos(15, 50, -10)

        # the 'rope' is the white line that is the
        # sailing course the user must follow
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

        self.curve = r.ropeNode.getCurve()
        self.curvePoints = r.getPoints(50)
        print(self.curvePoints)
