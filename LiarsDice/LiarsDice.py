from Server import Server
from Player import Player
from Client import Client
import asyncore, wx, time

NUM_PLY = 4

class LiarsDice:
    def __init__(self, address="localhost", port=22222, startServer=False):
        ''' Starts the game. '''
        if startServer == True:
            self.server = Server(address, port, self) 
            #self.players = []
            #Client("localhost", PORT)
        else:
            Client(None, port)           
        
#        try: asyncore.loop()
#        except KeyboardInterrupt: print
#    def addPlayer(self, name, ID):
#        self.players.append(Player(name,ID))
##        
#    def startGame(self):
#        self.server.playerTurn(0)
