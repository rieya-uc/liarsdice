from GUI import Layout
from Player import Player
import wx

class ClientHelper:
    def __init__(self, client):
        ''' Interprets messages between the client, gui and server.

        Provides a common interface between the client, gui and server. 
        When the client or gui sends a message to the client, it first 
        gets formatted by the clienthelper, before being passed on.
        When the client receives a message from the server, the client 
        sends it to clienthelper, which works out what to do with it.

        '''
        self.layout = None          
        self.client = client
        self.player = Player()
        self.name = None            
        self.names = []             
           
    def onChat(self, line):
        ''' Sends a chat message to the server. '''
        self.client.broadcast("CHAT", line)
    
    def onBid(self, num, face):
        ''' Sends a bid to the server. '''
        self.client.broadcast("BID", (str(num) + " " + str(face)))
        
    def onLiar(self):
        ''' Sends a liar message to the server. '''
        self.client.broadcast("LIAR", (str(self.layout.minBidNum) + 
                              " " + str(self.layout.minBidFace)))
        
    def onSpotOn(self, num, face):
        ''' Sends a spot on message to the server. '''
        self.client.broadcast("SPOTON", (str(self.layout.minBidNum) + 
                              " " + str(self.layout.minBidFace)))
    
    def getDice(self):
        ''' Returns the dice that the player holds. '''
        return self.player.dice
    
    def sendDice(self):
        ''' Sends dice info to the server.  '''
        dice = self.player.dice
        self.client.broadcast("REQUEST_DICE", str(dice))
    
    def removeDice(self, ID):
        ''' Removes a dice from the player with the specified ID. '''
        if ID == self.client.ID:
            self.player.removeDice()
            if self.player.numDice == 0:
                self.client.broadcast("NO_DICE")
                
        self.layout.removeDice(ID)
        
    def updateBid(self, line):
        ''' On receiving a bid message from the server, updates the gui. '''
        t = line.split()
        self.layout.updateBid(int(t[0]),int(t[1]))
        
    def rollDice(self):
        ''' Rolls dice and signals to the server this has happened. '''
        self.player.rollDice()
        self.client.broadcast("ROLL_DICE")

    def startGame(self, names):
        ''' Creates layout and starts the wx loop.  '''
        tokens = names.split(" ")
        self.player = Player(self.name)
        
        app = wx.App(False)
        self.layout = Layout(self, self.client.ID, tokens, self.player)

        # i.e. if you're the first player; assuming here that the 
        # first player will always be the first person to connect.
        if self.client.ID == 0:
            self.layout.setGameMessage(self.name + ", it's your turn")
            self.layout.yourTurn()
        else:
            self.layout.setGameMessage("It's " + self.layout.names[0] +
                                       "'s turn.")
            self.layout.oppTurn(0)
        
        app.MainLoop()
        
    def interpretMessage(self, line):
        ''' Interprets messages received from the client.
        
        When client receives a message, it is sent to clienthelper, which
        tokenizes it, and works out what the server/client is requesting.
        
        '''
        tokens = line.split(" ", 2)
        
        for i in range(tokens.__len__()):
            tokens[i] = tokens[i].strip()
        
        senderID = tokens[0]    # ID of the sending client or server
        command = tokens[1]     # What the sender is asking this client to do
        info = tokens[2]        # Any other arguments client may need
        
        #print "com: ", command
        
        if tokens.__len__() != 3:
            self.client.send(" INCORRENT_MESSAGE_FORMAT " + line)  
        elif command == "CHAT":
            self.layout.chat(senderID, info)
        #elif command == "UPDATE_PLAYER":
         #   pass
        elif command == "NAME_REGISTERED":
            if info.strip()=="True":
                print "Welcome", self.name
                print "Waiting for more players..."
            else:
                print "Sorry, that name is taken, please try a different name"
                self.client.register()
        elif command == "START_GAME":        
            self.client.broadcast("REQUEST_ID")
            self.client.broadcast("REQUEST_NAMES")
        elif command == "REQUEST_ID":
            self.client.ID = int(info)
        elif command == "REQUEST_NAMES":
            self.startGame(info)
        elif command == "LIAR":
            ID = int(senderID)
            pp = int(info)
            if ID == self.client.ID:
                self.layout.setGameMessage("You've called " + 
                        self.layout.names[pp] + " a liar")
            elif pp == self.client.ID:
                self.layout.setGameMessage(self.layout.names[ID] 
                        + " has called you a liar!")
            else:
                self.layout.setGameMessage(self.layout.names[ID] + 
                        " has called " + self.layout.names[pp] + " a liar")
        elif command == "SPOTON":
            ID = int(senderID)
            t = info.split()
            num = t[0]
            face = t[1]
            if num == "1": end = ""
            else: end = "s"
            if ID == self.client.ID:
                self.layout.setGameMessage("You've called spot on with " 
                        + num + " " + face + end)
            else:
                self.layout.setGameMessage(self.layout.names[ID] + 
                        " has called spot on with " + num + " " + face + end)
        elif command == "YOUR_TURN":
            self.layout.setGameMessage(self.name + ", it's your turn")
            self.layout.yourTurn()
        elif command == "OPP_TURN":
            self.layout.setGameMessage("It's " + self.layout.names[int(info)] 
                        + "'s turn.")
            self.layout.oppTurn(int(info))
        elif command == "BID" :
            self.updateBid(info)
        elif command == "REQUEST_DICE":
            dice = str(self.player.dice)
            owned = str(self.player.numDice)
            self.client.broadcast("REQUEST_DICE", owned + " " + dice)    
        elif command == "REMOVE_DICE":
            ID = int(info)
            if ID == self.client.ID:
                self.layout.appendGameMessage("Oh no, you lose a die!")
            else:
                self.layout.appendGameMessage(self.layout.names[ID] 
                        + " loses a die")
            self.removeDice(ID)
        elif command == "REVEAL_DICE":
            diceList = []
            list = []
            for c in info:
                if c.isdigit():
                    list.append(int(c))
                elif c == "]":
                    diceList.append(list)
                    list = []
            self.layout.revealDice(diceList)
        elif command == "NEW_ROUND":
            self.layout.newRound()
        elif command == "NO_DICE":
            ID = int(senderID)
            if ID == self.client.ID:
                self.layout.appendGameMessage(
                        "You have no dice left! You're out of the game")
            else:
                self.layout.appendGameMessage(self.layout.names[ID] 
                        + " is out of the game")
        elif command == "ENDOFGAME":
            ID = int(info)
            if ID == self.client.ID:
                self.layout.appendGameMessage("Well done, you win!")
            else:
                self.layout.appendGameMessage(self.layout.names[ID] 
                        + " wins the game!")
            self.layout.endGame()
        else:
            print("This shouldn't be happening!!! " + line)
