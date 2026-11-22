from math import sin ,cos ,pi
from libs .vector import Vec3
from libs .misc import *
from libs .camera import Camera
from libs .gun import Gun
from libs .sound import *
from libs .timer import *
class Player :
    def __init__ (self ,terrain ):
        self .sScale =1 /terrain .scale
        self .tScale =GAME_FPS
        self .height =2.9 *self .sScale
        self .walkSpeed =3.6 *self .sScale /self .tScale
        self .runSpeed =5.5 *self .sScale /self .tScale
        self .swimSpeed =3 *self .sScale /self .tScale
        self .currentSpeed =0
        self .running =False
        self .gravity =9.8 *self .sScale /(self .tScale **2 )
        self .stoppingInertia =12 *self .sScale /(self .tScale **2 )
        self .jumpPower =2.4 *self .sScale /self .tScale
        self .alive =True
        self .health =100.0
        self .lives =3
        self .sphereR =2.9 *self .sScale
        self .firstMovement =True
        self .jump =False
        self .inAir =False
        self .upSpeed =0
        self .beingAttacked =False
        self .left ,self .forward ,self .right ,self .backward =False ,False ,False ,False
        self .gameOver =False
        self .camera =Camera ()
        self .terrain =terrain
        self .triggering =False
        self .shootingDir =0
        self .gun =Gun (200 )
        self .lastEightChars =["a"for _ in range (8 )]
        self .sounds ={}
        self .loadSounds ()
        self .kills =0
        self .camera .cam_pos =Vec3 (terrain .width //2 ,0 ,terrain .height //2 )
        self .motionTimer =Timer ()
        self .lastMoving ={"forward":False ,"backward":False ,"left":False ,"right":False }
    def getPos (self ):
        return self .camera .cam_pos
    def getLegPos (self ):
        t =self .camera .cam_pos .copy ()
        t .y -=self .height
        return t
    def loadSounds (self ):
        self .sounds ["walk"]=SoundSeries ("assets/sounds/player/WALK",13 ,0.6 )
        self .sounds ["run"]=SoundSeries ("assets/sounds/player/run",8 ,0.6 )
        self .sounds ["jumpInit"]=Sound ("assets/sounds/player/jumpinit.ogg",0.6 )
        self .sounds ["jumpLand"]=Sound ("assets/sounds/player/jumpland.ogg",0.6 )
        self .sounds ["damage"]=SoundSeries ("assets/sounds/player/damage",6 ,0.6 )
        self .sounds ["swim"]=Sound ("assets/sounds/player/swim-01.ogg",0.6 )
    def moveForward (self ,velocity ):
        self .camera .cam_pos .x +=self .camera .cam_fr .x *velocity
        self .camera .cam_pos .z +=self .camera .cam_fr .z *velocity
    def moveBackward (self ,velocity ):
        self .camera .cam_pos .x -=cos (radians (self .camera .jaw ))*cos (radians (self .camera .pitch ))*velocity
        self .camera .cam_pos .z -=sin (radians (self .camera .jaw ))*cos (radians (self .camera .pitch ))*velocity
    def moveLeft (self ,velocity ):
        self .camera .cam_pos -=self .camera .cam_ri *velocity *0.7
    def moveRight (self ,velocity ):
        self .camera .cam_pos +=self .camera .cam_ri *velocity *0.7
    def move_up (self ,velocity ):
        self .camera .cam_pos +=self .camera .cam_up *velocity
    def handle_motion (self ):
        if self .forward or self .left or self .right or self .backward :
            if not self .inWater ():
                if self .running :
                    self .currentSpeed =self .runSpeed
                else :
                    self .currentSpeed =self .walkSpeed
            else :
                self .currentSpeed =self .swimSpeed
            for i in self .lastMoving .keys ():
                self .lastMoving [i ]=self .__dict__ [i ]
        elif self .currentSpeed >0 :
            self .currentSpeed -=self .stoppingInertia
        else :
            self .currentSpeed =0
        if self .forward or self .lastMoving ["forward"]:
            self .moveForward (self .currentSpeed )
        if self .backward or self .lastMoving ["backward"]:
            self .moveBackward (0.8 *self .currentSpeed )
        if self .left or self .lastMoving ["left"]:
            self .moveLeft (0.6 *self .currentSpeed )
        if self .right or self .lastMoving ["right"]:
            self .moveRight (0.6 *self .currentSpeed )
        if not self .inAir :
            if not self .inWater ():
                if self .forward or self .backward :
                    if self .running :
                        stepSpeed =3.2
                        t =stepSpeed *self .motionTimer .getTime ('run')*pi /1000
                        self .moveRight (.01 *self .sScale *cos (t ))
                        self .move_up (.008 *self .sScale *sin (2 *t ))
                    else :
                        stepSpeed =1.62
                        t =stepSpeed *self .motionTimer .getTime ('walk')*pi /1000
                        self .moveRight (.007 *self .sScale *cos (t ))
                        self .camera .cam_pos .y +=.02 *self .sScale *sin (2 *t )
                else :
                    stepSpeed =1.62
                    t =stepSpeed *self .motionTimer .getTime ('standing')*pi /1000
                    self .camera .cam_pos .y +=.005 *self .sScale *sin (0.5 *t )
            else :
                stepSpeed =1.4
                if self .forward or self .backward :
                    t =stepSpeed *self .motionTimer .getTime ('swim')*pi /1000
                    self .moveRight (.003 *self .sScale *cos (t ))
                    self .camera .cam_pos .x +=self .camera .cam_fr .x *.008 *self .sScale *sin (1.7 *t )
                    self .camera .cam_pos .z +=self .camera .cam_fr .z *.008 *self .sScale *sin (1.7 *t )
                else :
                    t =stepSpeed *glutGet (GLUT_ELAPSED_TIME )*pi /1000
                    self .camera .cam_pos .y +=.03 *self .sScale *sin (0.7 *t )
        else :
            self .motionTimer .setTag ("")
    def playSounds (self ):
        if self .forward or self .backward or self .left or self .right :
            if self .inWater ():
                self .sounds ["swim"].play ()
            elif not self .inAir :
                self .sounds ["swim"].stop ()
                if self .running :
                    self .sounds ["run"].play ()
                else :
                    self .sounds ["walk"].play ()
        elif self .currentSpeed ==0 :
            self .sounds ["run"].stop ()
            self .sounds ["walk"].stop ()
            self .sounds ["swim"].stop ()
    def inWater (self ):
        return self .getLegPos ().y <=self .terrain .getSeaLevel ()
    def dead (self ):
        ...
    def loop (self ):
        if self .health <=0 :
            self .alive =False
        if self .triggering :
            self .gun .shoot (self .camera .cam_fr )
            self .triggering =False
        self .playSounds ()
        posY =self .terrain .heightPlus (self .getPos ().tuple (),self .height )
        if self .jump :
            self .jump =False
            self .sounds ["walk"].stop ()
            self .sounds ["run"].stop ()
            self .gun .animation ["hide"].animate ()
            if not self .inAir and not self .inWater ():
                self .sounds ["jumpInit"].play ()
                self .upSpeed =self .jumpPower
                self .inAir =True
            elif self .inWater ():
                self .sounds ["jumpInit"].play ()
        if self .upSpeed !=0 :
            if self .getPos ().y +self .upSpeed >posY :
                self .camera .cam_pos .y +=self .upSpeed
                self .upSpeed -=self .gravity
            else :
                self .sounds ["jumpLand"].play ()
                if abs (self .upSpeed )>=0.2 *self .sScale :
                    self .sounds ["damage"].play ()
                self .upSpeed =0
                self .camera .cam_pos .y =posY
                self .gun .animation ["show"].animate ()
        else :
            self .camera .cam_pos .y =posY
        if self .camera .cam_pos .y <=posY :
            self .inAir =False
            self .upSpeed =0
        self .handle_motion ()
        if self .health <100 :
            self .health +=0.09
        elif self .health !=inf :
            self .health =100
        self .onScreenStuff ()
        self .gun .reload ()
    def inTerr (self ):
        return self .terrain .checkIfInRange (self .camera .cam_pos .tuple ())
    def spotLight (self ):
        glDisable (GL_LIGHTING )
        glMatrixMode (GL_MODELVIEW )
        glPushMatrix ()
        glPushAttrib (GL_CURRENT_BIT )
        glLoadIdentity ()
        glLightfv (GL_LIGHT1 ,GL_DIFFUSE ,(1 ,1 ,1 ))
        glLightfv (GL_LIGHT1 ,GL_SPECULAR ,(1 ,1 ,1 ))
        glLightf (GL_LIGHT1 ,GL_CONSTANT_ATTENUATION ,0.1 )
        glLightf (GL_LIGHT1 ,GL_LINEAR_ATTENUATION ,0.03 )
        glLightf (GL_LIGHT1 ,GL_QUADRATIC_ATTENUATION ,0.03 )
        glLightfv (GL_LIGHT1 ,GL_SPOT_DIRECTION ,[0 ,0 ,-1 ])
        glLightf (GL_LIGHT1 ,GL_SPOT_CUTOFF ,45.0 )
        glLightf (GL_LIGHT1 ,GL_SPOT_EXPONENT ,64.0 )
        glLightfv (GL_LIGHT1 ,GL_POSITION ,(0 ,0.1 ,0 ,1.0 ))
        glPopAttrib ()
        glMatrixMode (GL_MODELVIEW )
        glPopMatrix ()
    def onScreenStuff (self ):
        glPushMatrix ()
        glLoadIdentity ()
        if self .gun .recoiling :
            currTime =glutGet (GLUT_ELAPSED_TIME )
            if currTime -self .gun .recoilStartTime <self .gun .recoilStrength :
                glTranslate (0 ,0 ,0.05 )
            else :
                self .gun .recoiling =False
        if self .inWater ():
            glScale (0 ,0 ,0 )
        if not self .inWater ():
            if self .running :
                t =2.7 *glutGet (GLUT_ELAPSED_TIME )*pi /900
            elif self .currentSpeed !=0 :
                t =1.6 *glutGet (GLUT_ELAPSED_TIME )*pi /900
            else :
                t =0.6 *glutGet (GLUT_ELAPSED_TIME )*pi /900
            glRotate (2.7 ,0 ,1 ,0 )
            glTranslate (0.27 +.006 *self .sScale *sin (t ),-0.33 +.006 *self .sScale *sin (2 *t ),-0.2 )
            glScale (1 ,1 ,1 )
        if self .gun .animation ["reload"].isPlaying ():
            glCallList (self .gun .animation ["reload"].getNextFrame ())
        elif self .inAir :
            glCallList (self .gun .animation ["hide"].getNextFrame ())
        else :
            glCallList (self .gun .animation ["shoot"].getNextFrame ())
        glPopMatrix ()