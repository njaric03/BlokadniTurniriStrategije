from bots.abstract_bot import AbstractBot, PokerAction
import random

class BalancedBot(AbstractBot):
    @property
    def description(self):
        return "A balanced bot that mixes its strategy between aggressive and conservative play, with some randomization to be less predictable."
        
    def strategy(self, community_cards, pot, current_bet, min_raise, max_raise, opponent_chips, previous_bets=[]):
        hand_strength = self._evaluate_hand_strength(self.hand, community_cards)
        pot_odds = current_bet / (pot + current_bet) if current_bet > 0 else 0
        
        # Consider previous betting patterns
        aggressive_betting = any(bet > current_bet * 2 for bet in previous_bets)
        
        # Add some randomization to be less predictable
        random_factor = random.uniform(0.8, 1.2)
        hand_strength *= random_factor

        # Strong hand - play aggressively but not all-in
        if hand_strength > 0.7:
            if self.chips > current_bet * 2:
                raise_amount = min(max_raise, max(min_raise, pot * (1.5 if aggressive_betting else 2)))
                return (PokerAction.RAISE, raise_amount)
            return self.CALL

        # Medium hand - mix between calling and raising
        if hand_strength > 0.4:
            if pot_odds < 0.4 and random.random() > (0.7 if aggressive_betting else 0.6):
                if self.chips > current_bet * 2:
                    return (PokerAction.RAISE, min(max_raise, current_bet * 2))
            if pot_odds < 0.3:
                return self.CALL

        # Weak hand - mostly fold, sometimes call with good odds
        if pot_odds < 0.2 and current_bet < self.chips // 5 and not aggressive_betting:
            return self.CALL

        return self.FOLD
