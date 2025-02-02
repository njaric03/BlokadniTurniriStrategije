from bots.abstract_bot import AbstractBot, PokerAction  # Changed to absolute import
import random

class ConservativeBot(AbstractBot):
    @property
    def description(self):
        return "A cautious bot that only plays strong hands and folds when there's aggressive betting."
        
    def strategy(self, community_cards, pot, current_bet, min_raise, max_raise, opponent_chips, previous_bets=[]):
        hand_strength = self._evaluate_hand_strength(self.hand, community_cards)
        pot_odds = current_bet / (pot + current_bet) if current_bet > 0 else 0
        
        # Consider previous betting patterns to be more cautious
        aggressive_betting = any(bet > current_bet * 2 for bet in previous_bets)
        
        # Very strong hand - but be more cautious if others are betting aggressively
        if hand_strength > 0.8:
            if self.chips > current_bet * 3 and not aggressive_betting:
                return (PokerAction.RAISE, min(max_raise, self.chips // 2))
            return self.CALL
            
        # Medium strength hand
        if hand_strength > 0.5 and not aggressive_betting:
            if pot_odds < 0.3:
                return self.CALL
            
        # Weak hand but good pot odds - only if no aggressive betting
        if pot_odds < 0.15 and current_bet < self.chips // 10 and not aggressive_betting:
            return self.CALL
            
        return self.FOLD
