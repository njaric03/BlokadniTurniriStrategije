import random

class Dealer:
    def __init__(self):
        self.deck = []
        self.create_deck()
        
    def create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = [(rank, suit) for suit in suits for rank in ranks]
        self.shuffle()
    
    def shuffle(self):
        random.shuffle(self.deck)
        
    def deal_card(self):
        if len(self.deck) > 0:
            return self.deck.pop()
        return None
