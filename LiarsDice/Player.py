import random

class Player:
    def __init__(self, name=None):
        '''
        
        Stores information on the player.

        Methods
        rollDice() - gives each die a random number between 1 and 6
        removeDice() - removes and returns one die

        '''

        self.name = name
        self.numDice = 5
        self.dice = [0] * 5
        
        self.rollDice()
    
    def rollDice(self):
        '''Rolls all the dice the player holds.'''
        for x in range(self.numDice):
            self.dice[x] = random.randrange(1,6)
               
    def removeDice(self):
        '''Removes one die and returns it.'''
        if self.numDice != 0:
            self.numDice -= 1
            return self.dice.pop()
