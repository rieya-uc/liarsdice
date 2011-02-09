from Client import Client
from asyncore import dispatcher
from asynchat import async_chat
import socket, asyncore, wx, time, thread

NUM_PLY = 4
    
class Server(dispatcher):
    def __init__(self, host, port, game):
        print("Server started")
        dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        #self.bind((host, port))
        self.bind(("0.0.0.0",port))
        self.listen(5)

        self.sessions = []
        self.numPlayers = 0     
        self.names = []    
        self.game = game
        self.playerOut = [False] * NUM_PLY
        
        self.dice = [None] * NUM_PLY
        self.ready = [False] * NUM_PLY
        self.currentPlayer = 0
        
        client = Client(host, port)
        
    def handle_accept(self):
        ''' Accepts client connections and creates its session. '''
        if self.sessions.__len__() < NUM_PLY :
            sock, addr = self.accept()
            self.sessions.append(Session(self, sock))
        
    def broadcastChatMessage(self, line):
        ''' Sends a chat message received from a client to all clients '''
        for session in self.sessions:
            session.send(line + "\r\n")

    def broadcastServerMessage(self, command, additionalInfo="NONE"):
        ''' Sends a message from the server to client. 
            
            Arguments:
            command -- The type of message
            additionalInfo -- Further data the client may need.

        '''
        for session in self.sessions:
            session.sendServerMessage(command, additionalInfo)
    
    def broadcastClientMessage(self, senderID, command, 
                               additionalInfo="NONE"):
        ''' Sends a client command from one client to all others.
        
            Arguments:
            senderID -- ID of the client who's sending
            command -- Command 'tag' of the message being sent
            additionalInfo -- Any additional arguments the client may need.

        '''
        for session in self.sessions:
            session.sendClientMessage(senderID, command, additionalInfo)
            
    def addName(self, name):
        ''' Part of the registration process. Adds a player's name. '''
        nameAvailable = True

        for n in self.names:
            if name == n:
                nameAvailable = False
                break
            
        if nameAvailable == True:
            self.names.append(name)         
            if len(self.names) == NUM_PLY:
                self.broadcastServerMessage("START_GAME", 0)
          
        return nameAvailable
    
    def nextPlayer(self):
        ''' Returns ID of the next player. '''
        while True:
            self.currentPlayer +=1
            if self.currentPlayer >= NUM_PLY:
                self.currentPlayer = 0
                
            if not self.playerOut[self.currentPlayer]:
                break
            
        return self.currentPlayer
    
    def previousPlayer(self):
        ''' Returns ID of the previous player. '''
        pp = self.currentPlayer
        while True:
            pp -= 1
            if pp < 0:
                pp = NUM_PLY-1
            if not self.playerOut[pp]:
                break
        
        #print "cp:", self.currentPlayer, "pp:", pp
        return pp
    
    def playerTurn(self, clientID):
        ''' Sends a message to all clients saying who's turn it it. '''
        for i in range(NUM_PLY):
            if clientID == i:
                self.sessions[i].sendServerMessage("YOUR_TURN")
            else:
                self.sessions[i].sendServerMessage("OPP_TURN", clientID)
    
    def requestID(self, session):
        ''' Part of registration process. Assigns client with an ID. '''
        ID = -1
        
        for i in range(len(self.sessions)):
            if self.sessions[i] == session:
                ID = i
                break
                
        return str(ID)
     
    def bid(self, senderID, num, face):
        ''' Bid has been made, inform clients and move to next player. '''
        self.broadcastClientMessage(senderID, "BID", (num + " " + face))
        self.playerTurn(self.nextPlayer())
    
    def getAllDice(self):
        ''' Request dice info from clients. '''
        self.dice = [None] * NUM_PLY
        self.broadcastServerMessage("REQUEST_DICE")
        while None in self.dice:
            time.sleep(0.01)

    def newRound(self):
        ''' Wait for all players to roll their dice, then start new round. '''
        self.ready = [False] * NUM_PLY
        
        for i in range(NUM_PLY):
            if self.playerOut[i] == True:
                self.ready[i] = True
                
        while False in self.ready:
            time.sleep(0.01)
            
        self.broadcastServerMessage("NEW_ROUND")
        self.playerTurn(self.nextPlayer())
        
    def liar(self, face, numBid):
        ''' Liar move performed, end round and inform loser and clients. '''
        self.getAllDice()
        self.broadcastServerMessage("REVEAL_DICE", self.dice)
    
        pp = self.previousPlayer()
        if self.dice[pp].count(face) < numBid:
            loser = pp
        else:
            loser = self.currentPlayer
        self.broadcastServerMessage("REMOVE_DICE", loser)
        
        # Start preparing for next round.
        thread.start_new_thread(self.newRound, ())
        
    def spotOn(self, ID, numBid, face):
        ''' Spot on move performed, end round, inform loswer and clients. '''
        self.getAllDice()
        self.broadcastServerMessage("REVEAL_DICE", self.dice)
        
        count = 0
        for d in self.dice:
            count += d.count(face)
        
        if count != numBid:
            self.broadcastServerMessage("REMOVE_DICE", ID)
        else:
            for i in range(NUM_PLY):
                if i != ID:
                    self.broadcastServerMessage("REMOVE_DICE", i)
            
        # Start preparing for new round
        thread.start_new_thread(self.newRound, ())
        
    def removePlayer(self, ID):
        ''' Player is out of the game, set to out. '''
        self.playerOut[ID] = True
    
    def checkForWinner(self):
        ''' Checks if there's only one player left in the game. '''
        if self.playerOut.count(False) == 1:
            self.broadcastServerMessage("ENDOFGAME", 
                    self.playerOut.index(False))
            
class Session(async_chat):
    def __init__(self, server, sock):
        ''' Individual client's link to the server. '''
        async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n")
        self.data = []
        self.name = None

    def collect_incoming_data(self, data):
        ''' Appends received messages to self.data. '''
        self.data.append(data)

    def found_terminator(self):
        ''' End of line reached. '''
        line = ''.join(self.data)
        self.data = []
        self.interpretMessage(line)

    def sendServerMessage(self, instruction, additionalInfo="NONE"):
        ''' Relays message from server to client. '''
        self.send("SVR " + instruction + " " + str(additionalInfo) + "\r\n")
    
    def sendClientMessage(self, senderID, instruction, additionalInfo="NONE"):
        ''' Relays message (via server) between clients.  '''
        self.send(str(senderID) + " " + instruction
                + " " + str(additionalInfo) + "\r\n")
                                
    def getDiceList(self, info):
        ''' Returns dice list received from client to server. '''
        t = info.split()
        owned = int(t[0])
        dice = []
        
        for i in range(owned):
            dice.append(int(t[i+1].strip("[],")))

        return owned, dice
    
    def interpretMessage(self, line):
        ''' Received message from client, work out what to do with it. '''
        tokens = line.split(" ", 2)
        
        for i in range(len(tokens)):
            tokens[i] = tokens[i].strip()
           
        senderID = int(tokens[0])
        command = tokens[1]
        info = tokens[2]
        
        if len(tokens) < 3:
            print "INCORRECT MESSAGE FORMAT", line
        elif command == "CHAT":
            self.server.broadcastChatMessage(line)
        elif command == "NAME":
            registered = self.server.addName(info)
            self.sendServerMessage("NAME_REGISTERED", registered)
        elif command == "REQUEST_ID":
            ID = self.server.requestID(self)
            self.sendServerMessage("REQUEST_ID", ID)
        elif command == "REQUEST_NAMES":
            self.sendServerMessage("REQUEST_NAMES", 
                    " ".join(self.server.names))
        elif command == "REQUEST_DICE":
            owned, dice = self.getDiceList(info)
            self.server.dice[senderID] = dice
        elif command == "BID":
            t = info.split()
            self.server.bid(senderID, t[0], t[1])         
        elif command == "LIAR":
            self.server.broadcastClientMessage(senderID, 
                    "LIAR", self.server.previousPlayer())
            t = info.split()
            num = int(t[0])
            face = int(t[1])
            thread.start_new_thread(self.server.liar, (face,num))
        elif command == "ROLL_DICE":
            self.server.ready[senderID] = True
        elif command == "SPOTON":
            t = info.split()
            num = int(t[0])
            face = int(t[1])
            self.server.broadcastClientMessage(senderID, "SPOTON", info)
            thread.start_new_thread(self.server.spotOn, (senderID,num,face))
        elif command == "NO_DICE":
            self.server.broadcastClientMessage(senderID, "NO_DICE")
            self.server.removePlayer(senderID)
            self.server.checkForWinner()
        else:
            print "Do not recognise command. ", line
