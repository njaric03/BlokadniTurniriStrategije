from bots.abstract_bot import AbstractBot, PokerAction

class AlwaysCallBot(AbstractBot):
    def strategy(self, community_cards, pot, current_bet, min_raise, max_raise, opponent_chips, previous_bets=[]):
        # If we have enough chips to call, always call
        if self.chips >= current_bet:
            return self.CALL
        # If we can't call, we have to fold
        return self.FOLD
