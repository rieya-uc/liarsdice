from Player import Player
import wx, asyncore, os
from ctypes import *
import os.path

NUM_PLY = 4

class Layout(wx.Frame):
    def __init__(self, clientHelper, ID, names, player):
        ''' Liar's Dice GUI

        Argments:
        clientHelper -- instance of clientHelper
        ID -- player's ID
        names -- list of all players' names. names[ID] is this player's name
        player -- instance of Player belonging to this client

        '''
        wx.Frame.__init__(self, None, title="Layout")
        
        #as asyncore and wxPython block each other out, use a timer instead
        #of asyncore.loop(), and call asyncore.poll() repeatedly
        self.timer = wx.Timer(self, wx.NewId())
        wx.EVT_TIMER(self, self.timer.GetId(), self.SocketPoller)
        self.timer.Start(10, wx.TIMER_CONTINUOUS) 
        
        bgColour = "#10818C"
        dcColour = "#12B225"
       
        self.ID = ID
        self.ch = clientHelper
        self.player = player
        self.names = names
        self.heldDice = [5]*NUM_PLY  # Keeps track of how many dice each 
                                     # player has (but not what the dice are)
        self.firstTurn = True
        
        self.bidBtn = None
        self.liarBtn = None
        self.spotOnBtn = None
        self.curBidFace = 1
        self.bidFaceImg = None
        self.bidFaceUpBtn = None
        self.bidFaceDownBtn = None
        self.bidFaceImg = None
        self.curBidNum = 1
        self.bidNumTxt = None
        self.bidNumUpBtn = None
        self.bidNumDownBtn = None
        self.minBidNum = 0          
        self.minBidFace = 0  
        self.diceAreaPanel = None
        self.rollBtn = None
        self.opAreaPanel = None
        self.chatMessages = None
        self.yourMessages = None
        self.gameMessages = None
        self.messages = []  
        self.tickCounter = 0
        
        #font init, taken from the python wxpython wiki
        gdi32 = WinDLL("gdi32.dll")
        fonts = [font for font in os.listdir("fonts") if font.endswith("ttf")]
        for font in fonts:
            gdi32.AddFontResourceA(os.path.join("fonts",font))
        font = wx.Font(16, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)
        
        #set up the game area
        self.SetBackgroundColour(bgColour)
        gameAreaPanel = wx.Panel(self)
        gameAreaPanel.SetMinSize((830, 330))
        gameAreaSizer = wx.BoxSizer(wx.VERTICAL)

        #this shows messages from the game to the user
        self.gameMessages = wx.TextCtrl(self, 
                style=wx.TE_READONLY | wx.NO_BORDER)
        self.gameMessages.SetBackgroundColour("#044046")
        self.gameMessages.SetForegroundColour("WHITE")
       
        font.SetPointSize(24)
        font.SetFaceName("Comfortaa")
        self.gameMessages.SetFont(font)
        
        gameAreaSizer.Add(self.gameMessages, proportion=0, 
                flag=wx.ALIGN_RIGHT|wx.EXPAND)
        
        #game area 1 - opponents' dice area
        self.opAreaPanel = wx.Panel(gameAreaPanel, -1, 
                size=(382,198), pos=(15,75))
        self.opAreaPanel.SetForegroundColour("WHITE")
        self.displayOpDice()
                    
        #game area 2 - bid display and buttons
        image = wx.Image("Images/Background/BlueBorder.png", 
                wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        movesArea = wx.Panel(gameAreaPanel, -1, pos=(415,30), 
                size=(image.GetWidth(), image.GetHeight()))
        blueBorder = wx.StaticBitmap(movesArea, -1, image, 
                pos=(0,0), size=(image.GetWidth(), image.GetHeight()))
        
        font.SetPointSize(26)
        font.SetFaceName("Kristen ITC")
        text = wx.StaticText(movesArea, -1, "Current bid", pos=(30,20))
        text.SetFont(font)
        
        self.bidNumTxt = wx.TextCtrl(movesArea, value=str(self.curBidNum), 
                size=(43,43), pos=(130,105), style=wx.TE_READONLY)
        self.bidNumTxt.SetBackgroundColour(bgColour)
        font.SetPointSize(28)
        self.bidNumTxt.SetFont(font)
        
        text = wx.StaticText(movesArea, -1, "x", pos=(202,113))
        font.SetPointSize(24)
        text.SetFont(font)
        
        image = self.getDiceBitmap(self.curBidFace, 38, 38)
        self.bidFaceImg = wx.StaticBitmap(movesArea, -1, image, pos=(258,110))
        
        #buttons
        self.bidNumUpBtn = self.initButton("BidUp", (102,73), 
                blueBorder, bgColour)
        
        self.bidNumDownBtn = self.initButton("BidDown", (102,153), 
                blueBorder, bgColour)
        self.bidNumDownBtn.Disable()
        
        self.bidFaceUpBtn = self.initButton("BidUp", (235, 73),
                blueBorder, bgColour)

        self.bidFaceDownBtn = self.initButton("BidDown", (235, 153),
                blueBorder, bgColour)
        self.bidFaceDownBtn.Disable()
        
        self.bidBtn = self.initButton("Bid", (30,200), 
                blueBorder, bgColour, True)
        self.bidBtn.Disable()
        
        self.liarBtn = self.initButton("Liar", (150,200), 
                blueBorder, bgColour, True)
        self.liarBtn.Disable()
        
        self.spotOnBtn = self.initButton("SpotOn", (270,200), 
                blueBorder, bgColour, True)
        self.spotOnBtn.Disable()
       
        self.rollBtn = wx.Button(self, -1, pos=(650,390), size=(100,100), 
                label=("Roll Dice"))
        self.rollBtn.Hide()
        
        gameAreaSizer.Add(gameAreaPanel)        
        
        #set up your dice area

        diceAreaSizer = wx.BoxSizer(wx.VERTICAL)
       
        self.diceAreaPanel = wx.Panel(self, size=(800,150))
        self.diceAreaPanel.SetBackgroundColour(dcColour)
        self.diceAreaPanel.SetForegroundColour("WHITE")
        self.diceAreaPanel.SetMinSize((800,140))
        
        diceAreaSizer.Add(self.diceAreaPanel, flag=wx.ALIGN_BOTTOM|wx.EXPAND)
        self.displayYourDice()
       
        #set up chat area
        sendBtn = wx.Button(parent=self, label="Send", size=(100, 40))
        self.chatMessages = wx.TextCtrl(self, 
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                size=(790, 90))
        self.yourMessages = wx.TextCtrl(parent=self, style=wx.TE_MULTILINE | 
                wx.TE_WORDWRAP | wx.TE_PROCESS_ENTER, size=(700, 40))
   
        chatSizer = wx.BoxSizer(wx.VERTICAL)
        chatHSizer = wx.BoxSizer(wx.HORIZONTAL)

        chatHSizer.Add(self.yourMessages,  proportion=1, 
                flag=wx.LEFT|wx.EXPAND)
        chatHSizer.Add(sendBtn, flag=wx.RIGHT)

        chatSizer.Add(self.chatMessages, proportion=2, 
                flag=wx.TOP|wx.EXPAND)
        chatSizer.Add(chatHSizer, flag=wx.BOTTOM | wx.EXPAND)

        #layout all the elements
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(gameAreaSizer, proportion=0, flag=wx.ALIGN_BOTTOM)
        vSizer.Add(diceAreaSizer, proportion=0, flag=wx.EXPAND)
        vSizer.Add(chatSizer, proportion=1, 
                flag=wx.ALIGN_BOTTOM|wx.TOP|wx.EXPAND)
       
        self.SetSizerAndFit(vSizer)
        self.Show()

        #bind all buttons to methods
        sendBtn.Bind(wx.EVT_BUTTON, self.OnSendBtn)
        self.bidBtn.Bind(wx.EVT_BUTTON, self.OnBidBtn)
        self.liarBtn.Bind(wx.EVT_BUTTON, self.OnLiarBtn)
        self.spotOnBtn.Bind(wx.EVT_BUTTON, self.OnSpotOnBtn)
        self.bidNumUpBtn.Bind(wx.EVT_BUTTON, self.OnBidNumUp)
        self.bidNumDownBtn.Bind(wx.EVT_BUTTON, self.OnBidNumDown)
        self.bidFaceUpBtn.Bind(wx.EVT_BUTTON, self.OnBidFaceUp)
        self.bidFaceDownBtn.Bind(wx.EVT_BUTTON, self.OnBidFaceDown)
        self.rollBtn.Bind(wx.EVT_BUTTON, self.OnRollBtn)
        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)
        
    def initButton(self, filename, pos, background, colour, pressed=False):
        ''' Creates, sets up and returns button. '''
        image = wx.Image("Images/Buttons/" + filename + ".png",
                wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        btn = wx.BitmapButton(background, -1, image, pos=pos, 
                size=(image.GetWidth(), image.GetHeight()),
                    style=wx.NO_BORDER)
        btn.SetBackgroundColour(colour)
        btn.SetBitmapDisabled(wx.Image("Images/Buttons/" + filename
            + "_Disabled.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        
        if pressed:
            btn.SetBitmapSelected(wx.Image(
                "Images/Buttons/" + filename + "_Pressed.png", 
            wx.BITMAP_TYPE_ANY).ConvertToBitmap()) 
        
        return btn

    def SocketPoller(self, event):
        ''' Polls asyncore socket for data. '''
        asyncore.poll() 

    def OnTick(self, event):
        ''' Changes the ticker message every 100 ticks. '''
        if len(self.messages) > 0 and self.tickCounter >=100:
            # Get next message from self.messages list and display.
            # Reset counter.
            self.tickCounter = 0
            self.displayedMessage += 1
            if self.displayedMessage >= len(self.messages):
                self.displayedMessage = 0
            self.gameMessages.SetLabel(self.messages[self.displayedMessage])
        else:
            self.tickCounter += 1
        event.Skip()
    
    def setGameMessage(self,text):
        ''' Displays messages in the ticker and in chat. '''
        self.messages = []
        self.messages.append(text)
        self.tickCounter = 0
        self.displayedMessage = 0
        self.gameMessages.SetLabel(text)
        self.chatMessages.SetDefaultStyle(wx.TextAttr("RED"))
        self.chatMessages.AppendText(text + "\n")
        self.chatMessages.ScrollLines(-1)

    def appendGameMessage(self, text):
        ''' Appends messages to the ticker list and to chat. '''
        self.messages.append(text)
        self.chatMessages.SetDefaultStyle(wx.TextAttr("RED"))
        self.chatMessages.AppendText(text + "\n")      
        self.chatMessages.ScrollLines(-1)

    def newRound(self):
        ''' Resets everything ready for a new round. '''
        self.firstTurn = True
        self.updateBid(1, 1)
        self.minBidFace = 0
        self.minBidNum = 0
        self.curBidFace = 1
        self.curBidNum = 1
        self.displayOpDice()
    
    def OnRollBtn(self, event):
        ''' Sends roll event message to clienthelper and show new dice. '''
        self.ch.rollDice()
        self.displayYourDice()
        self.rollBtn.Hide()
        
    def displayYourDice(self):
        ''' Draws your dice in dice panel. '''
        panel = self.diceAreaPanel
        panel.DestroyChildren()
        
        font = wx.Font(16, wx.NORMAL, wx.NORMAL, wx.NORMAL, 
                False, 'Kristen ITC')
        font.SetPointSize(26)
        text = wx.StaticText(panel, -1, "Your Dice", 
                style=wx.LEFT, pos=(20, 10))
        text.SetFont(font)

        if self.heldDice[self.ID] == 0:
            text = wx.StaticText(panel, -1, "You have no dice!", 
                    style=wx.CENTER, pos=(50, 30))

        dice = self.ch.getDice()
        for i in range(self.heldDice[self.ID]):
            image = self.getDiceBitmap(dice[i])
            wx.StaticBitmap(panel, -1, image, 
                    pos=(175 + (10+image.GetWidth())*i, 60), 
                    size=(image.GetWidth(), image.GetHeight()))
    
    def displayOpDice(self):
        ''' Draws your opponents' revealed dice. '''
        panel = self.opAreaPanel
        panel.ClearBackground()
        opDiceLength = 40
        
        font = wx.Font(16, wx.NORMAL, wx.NORMAL, 
                wx.NORMAL, False, 'Kristen ITC')
        image = wx.Image("Images/Background/GreenBorder.png",
                wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        wx.StaticBitmap(self.opAreaPanel, -1, image, pos=(0,0), 
                size=(image.GetWidth(), image.GetHeight()))
        
        sp = 0          #vertical spacing between dice
        for i in range(NUM_PLY):
            if i != self.ID:
                text = wx.StaticText(panel, -1, self.names[i], 
                        pos=(30, 35+(50*sp)))
                text.SetFont(font)

                for j in range(self.heldDice[i]):
                    face = 0        #i.e. blank face
                    image = self.getDiceBitmap(face, opDiceLength, 
                            opDiceLength)
                    
                    wx.StaticBitmap(panel, -1, image, 
                            pos=(125+(opDiceLength+5)*j,
                                 29+((10+opDiceLength)*sp)),
                            size=(opDiceLength, opDiceLength))
                sp += 1
        self.Refresh()
        
    def revealDice(self, diceList):
        ''' Reveal opponenents' dice. '''
        self.disableAllButtons()
        panel = self.opAreaPanel
        
        # Clear opps' dice panel - need to re-layout its background
        panel.DestroyChildren()
        opDiceLength = 40
        font = wx.Font(16, wx.NORMAL, wx.NORMAL, wx.NORMAL, 
                False, 'Kristen ITC')
        image = wx.Image("Images/Background/GreenBorder.png", 
                wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        wx.StaticBitmap(self.opAreaPanel, -1, image, pos=(0,0), 
                size=(image.GetWidth(), image.GetHeight()))
        
        sp = 0          #vertical spacing between dice
        for i in range(NUM_PLY):
            if i != self.ID:
                text = wx.StaticText(panel, -1, self.names[i], 
                        pos=(30, 35+(50*sp)))
                text.SetFont(font)

                dlist = diceList[i]
                for j in range(len(dlist)):
                    face = dlist[j]
                    image = self.getDiceBitmap(face, opDiceLength, 
                            opDiceLength)
                    wx.StaticBitmap(panel, -1, image, 
                            pos=(125+(opDiceLength+5)*j, 
                                29+((10+opDiceLength)*sp)), 
                            size=(opDiceLength, opDiceLength))
                sp += 1
        
        if self.heldDice[self.ID] != 0:        
            self.rollBtn.Show()

        panel.Refresh()             
                    
    def yourTurn(self):
        ''' Enables relevent layout elements so you can take your turn. '''
        self.bidFaceImg.Enable()
        self.bidFaceImg.Enable()
        self.bidNumUpBtn.Enable()
       
        if not self.firstTurn:        
            self.minBidNum = self.curBidNum
            self.minBidFace = self.curBidFace
            self.liarBtn.Enable()
            self.spotOnBtn.Enable()
        else:
            self.bidBtn.Enable()
            self.firstTurn = False
            
        if self.curBidFace < 6:
            self.bidFaceUpBtn.Enable()          
        
    def oppTurn(self, ID):
        ''' Disables relevent layout elements as it's not your turn. '''
        self.disableAllButtons()
        self.firstTurn = False
        self.minBidNum = self.curBidNum
        self.minBidFace = self.curBidFace
        
    def disableAllButtons(self):
        ''' These buttons are disabled until it's your turn. '''
        self.bidBtn.Disable()
        self.liarBtn.Disable()
        self.spotOnBtn.Disable()
        self.bidFaceImg.Disable()
        self.bidFaceUpBtn.Disable()
        self.bidFaceDownBtn.Disable()
        self.bidFaceImg.Disable()
        self.bidNumUpBtn.Disable()
        self.bidNumDownBtn.Disable()
        
    def removeDice(self, ID):
        ''' Removes one die from the specified player. '''
        if self.heldDice[ID] > 0:
            self.heldDice[ID] -= 1
                
    def getDiceBitmap(self, face, width=None, height=None):
        ''' Returns the correct image for the specified dice face. ''' 
        file = "Images/Dice/Dice-" + str(face) + ".png"
        bitmap = wx.Image(file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        image = wx.ImageFromBitmap(bitmap)
       
        if width == None:
            w = bitmap.GetWidth()
        else: w = width
        if height == None:
            h = bitmap.GetHeight()
        else: h = height
        
        image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
        result = wx.BitmapFromImage(image)
       
        return result
    
    def chat(self, ID, line):
        ''' Displays chat message. '''
        insert = self.chatMessages.GetInsertionPoint()
        print ("insert", insert)
        self.chatMessages.SetDefaultStyle(wx.TextAttr("BLACK"))
        self.chatMessages.AppendText(self.names[int(ID)] + ": " + line + "\n")
        self.chatMessages.ScrollLines(-1)
    
    def endGame(self):
        ''' Ends the game by disallowing any more moves to be made. '''
        self.disableAllButtons()
        self.rollBtn.Disable()
        
    def OnSendBtn(self, event):
        ''' Sends chat event message to clienthelper and calls chat(). '''
        line = self.yourMessages.GetValue()
        self.yourMessages.Clear()
        self.yourMessages.SetFocus();
        self.ch.onChat(line)
      
    def OnLiarBtn(self, event):
        ''' Sends liar event message to clienthelper. '''
        self.ch.onLiar()
    
    def OnSpotOnBtn(self, event):
        ''' Sends spot on event message to clienthelper. '''
        self.ch.onSpotOn(self.minBidNum, self.minBidFace)
        
    def updateBid(self, num, face):
        ''' When player makes a bid, update the gui to reflect this. '''
        if self.curBidNum != num:
            self.curBidNum = num
            self.bidNumTxt.SetValue(str(num))
        if self.curBidFace != face:
            self.curBidFace = face
            self.bidFaceImg.SetBitmap(self.getDiceBitmap(face, 38, 38))

    def checkBidButtons(self, btn, bid, edge):
        ''' When bid made, check buttons and enable\disable as needed. '''
        
        #Can't bid lower than 'edge', e.g. 1
        if bid == edge or bid == 1:
            btn.Disable()
        elif not btn.IsEnabled():
            btn.Enable()
            
        #If your bid is equal to the previous bid, disable bid button
        #Bid must be higher than the previous one
        if (self.curBidNum == self.minBidNum and 
            self.curBidFace == self.minBidFace):
            self.bidBtn.Disable()
        else:
            self.bidBtn.Enable()
                            
    def OnBidBtn(self, event):
        ''' Sends bid event message to clienthelper. '''
        self.ch.onBid(self.curBidNum, self.curBidFace)
    
    def OnBidNumUp(self, event):
        ''' Update gui to reflect current bid. '''
        self.updateBid(self.curBidNum+1, self.curBidFace)
        self.checkBidButtons(self.bidNumDownBtn, self.curBidNum, self.minBidNum)
    
    def OnBidNumDown(self, event):
        ''' Update gui to reflect current bid. '''
        self.updateBid(self.curBidNum-1, self.curBidFace)
        self.checkBidButtons(self.bidNumDownBtn, self.curBidNum, self.minBidNum)
    
    def OnBidFaceUp(self, event):
        ''' Update gui to reflect current bid. '''
        self.updateBid(self.curBidNum, self.curBidFace+1)
        self.bidFaceDownBtn.Enable()
        self.checkBidButtons(self.bidFaceUpBtn, self.curBidFace, 6)
                  
    def OnBidFaceDown(self, event):
        ''' Update gui to reflect current bid. '''
        self.updateBid(self.curBidNum, self.curBidFace-1)
        self.bidFaceUpBtn.Enable()
        self.checkBidButtons(self.bidFaceDownBtn, self.curBidFace, self.minBidFace)      

if __name__=="__main__":
    from ClientHelper import ClientHelper
    app = wx.App(False)
    l = Layout(ClientHelper(None), 0, ["p0","p1"], Player())
    l.firstTurn = False
    l.yourTurn()
    app.MainLoop()
