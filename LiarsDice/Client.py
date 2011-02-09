from GUI import Layout
from Player import Player
from ClientHelper import ClientHelper
from asyncore import dispatcher
from asynchat import async_chat
import socket, asyncore, wx

class Client(async_chat):
    def __init__(self, host, port):
        ''' Communicates between the GUI and server. '''

        async_chat.__init__(self)
        self.data = []
        self.ID = -1   
        self.ch = ClientHelper(self)
        
        while True:
            if host == None:
                host = raw_input("Enter the IP of the server (leave blank for localhost) >")
                if len(host.strip()) == 0:
                    host = "localhost"
            try:
                print "connecting to...",host
                self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect((host,port))
                self.set_terminator("\n")
                self.register()
                
                try: asyncore.loop()
                except KeyboardInterrupt: print
                break
            except Exception:
                print "Cannot connect, ", Exception
                host = None

    def found_terminator(self):
        ''' Sends messages received from the server to be dealt with. '''
        line = ''.join(self.data)
        self.data = []
        self.ch.interpretMessage(line)
        
    def collect_incoming_data(self, data):
        ''' Collects messages from the server and stores in self.data. '''
        self.data.append(data)
   
    def register(self):
        '''
        Starts the registration process.
        Asks the player for a name, which is received by client helper,
        which then continues registering.
        
        '''
        name = None
        while name == None or len(name) < 1:
            name = raw_input("What name do you wish to go by? >   ")
            name = name.strip().replace(" ", "_")
        self.ch.name = name
        self.broadcast("NAME", self.ch.name)
        
    def broadcast(self, instruction, line="None"):
        ''' 
        Sends a message to the server.

        Arguments:
        instruction -- The type of the message, e.g. request for information
                       See Session and ClientHelper for message types.
        line -- The actual message.
        
        '''
        self.send(str(self.ID) + " " + instruction + " " + line + " \r\n")
        
if __name__ == "__main__":
    #app = wx.App(False)
    c = Client(HOST, PORT)
    try: asyncore.loop()
    except KeyboardInterrupt: print
    #app.MainLoop()
