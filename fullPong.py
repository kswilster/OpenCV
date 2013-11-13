from Tkinter import *
import cv2
import numpy as np

#(almost) classic Pong game, implement open cv features so you can play with a friend

class Pong():
                
    def __init__(self, master=None):        
        width   = 640
        height  = 480
        background  ='black'
        margin  = 20
        pWidth  = 10
        pHeight = 40
        bRadius = 10
        global canvas, root, elements, cvData
        
        root = Tk()
        root.title('Pong')
        root.bind_all('<Escape>', self.end)
        canvas = Canvas(root, bg=background, height=height, width=width)
        canvas.pack()
        
        canvas.data = { }
        canvas.data["width"] = width
        canvas.data["height"] = height
        
        cvData = { }
        self.cam = cv2.VideoCapture(0)
        self.readCam()
        cvData["width"]    = width
        cvData["height"]   = height
        cvData["minBrightness"] = 80
        cv2.namedWindow('knobs')
        cv2.resizeWindow('knobs', 600, 200)
        
        elements = { }
        elements["ball"] = Ball(width/2, height/2, -5, 2, 4, 'white')
        elements["paddle1"] = Paddle(margin, height/2, pWidth, pHeight, 'green')
        elements["paddle2"] = Paddle(width-margin, height/2, pWidth, pHeight, 'red')
        #elements["cont1"] = Controller(elements["paddle1"])
        elements["cont2"] = Controller(elements["paddle2"])
        elements["cont1"] = CVController(elements["paddle1"], self.cam, 'P1')
        #elements["cont2"] = CVController(elements["paddle2"], self.cam, 'P2')
        elements["score1"] = Score(width/2-60, 60)
        elements["score2"] = Score(width/2+60, 60)
        
        root.mainloop()
        
    def readCam(self):
        ret, cvData["img"] = self.cam.read()
        canvas.after(80, self.readCam)
    
    def end(self, dummy=None):
        root.destroy()
        cv2.destroyAllWindows()
    
#mouse-based controller
class Controller:
    def __init__(self, paddle):
        self.paddle = paddle
        self.updatePos()
        
    def updatePos(self):
        x,y = root.winfo_pointerxy()
        self.paddle.setY(y)
        self.paddle.render()
        #check mouse position every 2 ms
        canvas.after(2, self.updatePos)

#openCV-based controller        
class CVController:
    def __init__(self, paddle, cam, name):
        self.paddle = paddle
        self.cam    = cam
        self.name   = name
        #TODO: Set the default hue to a value that works for your marker
        self.hue    = 100
        self.hueWidth   = 4
        self.minContourArea = 0
        cv2.namedWindow(name)
        cv2.createTrackbar(name+'hue', 'knobs', self.hue, 179, self.update)
        cv2.createTrackbar(name+'minContourArea', 'knobs', 
                            self.minContourArea, 20000, self.update)
        self.update()
        self.updatePos()
        
    def update(self, dummy=None):
        self.hue = cv2.getTrackbarPos(self.name+'hue','knobs')
        self.minContourArea = cv2.getTrackbarPos(self.name+'minContourArea', 'knobs')
        
    def updatePos(self):
        width = cvData["width"]
        height = cvData["height"]
        minBrightness = cvData["minBrightness"]
        img = cvData["img"]
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hue = self.hue
        hueWidth = self.hueWidth
        minContourArea = self.minContourArea
        thresholded = cv2.inRange(hsv, np.array((hue-hueWidth/2.0, float(minBrightness),float(minBrightness))), np.array((hue+hueWidth/2.0, 255.,255.)))
        
        blobs_draw = np.zeros((height,width,3), np.uint8)
        contour, hier = cv2.findContours(thresholded,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        i=0
        for cnt in contour:
            #Contours must be somewhat big
            if (cv2.contourArea(cnt) < minContourArea):
                np.delete(contour,i,0)
            else:
                cv2.drawContours(blobs_draw,[cnt],0,255-i*20,-1)
                i = i+1
                
                #Find center of contour using boundingRect (slightly faster?)
                x,y,w,h = cv2.boundingRect(cnt)
                
                center_x = x + w/2
                center_y = y + h/2
                self.paddle.setY(center_y)
                self.paddle.render()
                cv2.circle(blobs_draw, (center_x, center_y), 3, (0, 0, 255), -1)
                break
                
        cv2.imshow(self.name,blobs_draw)
        canvas.after(80, self.updatePos)
        
class Paddle:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.velocity = 0
        self.width = width
        self.height = height
        self.color = color
        self.bounceCount = 0
        self.bounce()
        
    def render(self):
        try:
            canvas.delete(self.elem)
        except:
            pass
        x0 = self.x - self.width
        x1 = self.x + self.width
        y0 = self.y - self.height
        y1 = self.y + self.height
        self.elem = canvas.create_rectangle(x0, y0, x1, y1, fill=self.color)
    
    #check if a position is within the paddle
    def collides(self, x, y):
        minX = self.x - self.width/2
        maxX = self.x + self.width/2
        minY = self.y - self.height/2
        maxY = self.y + self.height/2
        
        if ((x>minX) and (x<maxX) and (y>minY) & (y<maxY)):
            return True
        return False
        
    def bounce(self):
        if (self.bounceCount > 0):
            self.bounceCount = self.bounceCount - 1
        else:
            ball = elements["ball"]
            bx0 = ball.x - ball.radius
            bx1 = ball.x + ball.radius
            by  = ball.y
            if (self.collides(bx0, by) or self.collides(bx1, by)):
                #TODO change dy based on some factor
                ball.dx = -ball.dx
                self.bounceCount = 20
        canvas.after(2, self.bounce)
    
    #should only modify position using this methods
    #so we can track velocity for putting spin on the ball
    def setY(self, y):
        old_y = self.y
        self.y = y
        self.velocity = (self.y - old_y)

class Ball:
    def __init__(self, x, y, dx, dy, radius, color):
        self.x  = x
        self.y  = y
        self.dx = dx
        self.dy = dy
        self.radius = radius
        self.color  = color
        self.doMove()
        
    def render(self):
        try:
            canvas.delete(self.elem)
        except:
            pass
        x0 = self.x - self.radius
        x1 = self.x + self.radius
        y0 = self.y - self.radius
        y1 = self.y + self.radius
        self.elem = canvas.create_oval(x0, y0, x1, y1, fill=self.color)
        
    def doMove(self):
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        minY = 0
        maxY = canvas.data["height"]
        minX = 0
        maxX = canvas.data["width"]
        
        if ((self.y <= minY) or (self.y >= maxY)):
            self.dy = -self.dy
        if (self.x >= maxX):
            self.x = maxX / 2
            self.y = maxY / 2
            score = elements["score1"]
            score.value = score.value + 1
            score.render()
        if (self.x <= minX):
            self.x = maxX / 2
            self.y = maxY / 2
            score = elements["score2"]
            score.value = score.value + 1
            score.render()
        self.render()
        canvas.after(20, self.doMove)

class Score:
    def __init__(self, x, y):
        self.value = 0
        self.color = 'white'
        self.x = x
        self.y = y
        self.render()
        
    def render(self):
        try:
            canvas.delete(self.elem)
        except:
            pass
        self.elem = canvas.create_text(self.x, self.y,
                                       text=self.value, fill=self.color)
        
if __name__ == '__main__':
    app = Pong()