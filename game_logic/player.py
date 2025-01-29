class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.hand = []
        self.is_active = True
        self.current_bet = 0
        
    def add_card(self, card):
        self.hand.append(card)
        
    def clear_hand(self):
        self.hand = []
        
    def place_bet(self, amount):
        """
        Place a bet, returns the actual amount bet
        """
        actual_bet = min(amount, self.chips)
        if actual_bet > 0:
            self.chips -= actual_bet
            self.current_bet = actual_bet  # Set current_bet to new amount, not add to it
            return actual_bet
        return 0
        
    def fold(self):
        self.is_active = False
