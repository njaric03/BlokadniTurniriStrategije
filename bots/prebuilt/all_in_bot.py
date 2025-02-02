from bots.abstract_bot import AbstractBot, PokerAction

class AllInBot(AbstractBot):
    @property
    def description(self):
        return "An aggressive bot that always tries to go all-in when possible."
        
    def strategy(self, community_cards, pot, current_bet, min_raise, max_raise, opponent_chips, previous_bets=[]):
        # AllInBot doesn't care about previous bets - always goes all in if possible
        if self.chips > current_bet and max_raise > current_bet:
            return (PokerAction.RAISE, self.chips)
        
        if self.chips >= current_bet:
            return self.CALL
            
        return self.FOLD
