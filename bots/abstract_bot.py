from abc import ABC, abstractmethod
from enum import Enum
from collections import Counter
from game_logic.player import Player  # Changed to absolute import

class PokerAction(Enum):
    FOLD = 0
    CALL = 1
    RAISE = 2

class AbstractBot(Player, ABC):
    @property
    def description(self):
        return ""
        
    # Constants for simple actions that don't need chip amounts
    FOLD = (PokerAction.FOLD, 0)
    CALL = (PokerAction.CALL, None)  # None means "whatever the current bet is"
    
    # Card ranks and their values
    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    def __init__(self, name, starting_chips):
        super().__init__(name, starting_chips)

    def _evaluate_hand_strength(self, hand, community_cards):
        """
        Protected method to evaluate hand strength
        Returns float between 0 and 1
        """
        all_cards = hand + (community_cards or [])
        if not all_cards:
            return 0.0
            
        # Get all ranks and suits
        ranks = [card[0] for card in all_cards]
        suits = [card[1] for card in all_cards]
        
        # Calculate various hand features
        score = 0.0
        
        # High card points
        score += self._high_card_score(ranks) * 0.1
        
        # Pair points
        score += self._pair_score(ranks) * 0.3
        
        # Flush potential
        score += self._flush_potential(suits) * 0.2
        
        # Straight potential
        score += self._straight_potential(ranks) * 0.2
        
        return min(1.0, score)
    
    def _high_card_score(self, ranks):
        """Calculate score based on high cards"""
        values = [self.CARD_VALUES[rank] for rank in ranks]
        max_value = max(values) if values else 0
        return max_value / 14.0
    
    def _pair_score(self, ranks):
        """Calculate score based on pairs/three of a kind/four of a kind"""
        counter = Counter(ranks)
        score = 0.0
        for rank, count in counter.items():
            if count == 2:  # Pair
                score += 0.2
            elif count == 3:  # Three of a kind
                score += 0.4
            elif count == 4:  # Four of a kind
                score += 0.8
        return min(1.0, score)
    
    def _flush_potential(self, suits):
        """Calculate potential for a flush"""
        counter = Counter(suits)
        max_suit_count = max(counter.values()) if counter else 0
        return max_suit_count / 5.0
    
    def _get_values_with_ace_low(self, ranks):
        """Helper method to get card values considering Ace as both 1 and 14"""
        values = set()
        for rank in ranks:
            if (rank == 'A'):
                values.add(1)  # Add Ace as 1
                values.add(14)  # Add Ace as 14
            else:
                values.add(self.CARD_VALUES[rank])
        return sorted(values)

    def _straight_potential(self, ranks):
        """Calculate potential for a straight, considering Ace as both high and low"""
        values = self._get_values_with_ace_low(ranks)
        if not values:
            return 0.0
            
        max_consecutive = 1
        current_consecutive = 1
        
        # Check normal straights
        for i in range(1, len(values)):
            if values[i] == values[i-1] + 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        # Special check for Ace-low straight (A,2,3,4,5)
        if 14 in values:  # If we have an Ace
            low_straight_count = sum(1 for v in values if v in [2, 3, 4, 5])
            if low_straight_count >= 3:  # If we have at least 3 cards for a wheel
                max_consecutive = max(max_consecutive, low_straight_count + 1)
                
        return max_consecutive / 5.0

    def get_hand_description(self, community_cards):
        """Returns a tuple (description, rank_info) of the player's best hand"""
        hand_eval = self.evaluate_hand(community_cards)
        if not hand_eval:
            return "no hand", "rank 0"
            
        hand_rank, hand_value = hand_eval
        
        # Get basic description first
        all_cards = self.hand + (community_cards or [])
        ranks = [card[0] for card in all_cards]
        rank_counts = Counter(ranks)
        
        # Check for pairs, three of a kind, etc.
        pairs = [r for r, count in rank_counts.items() if count == 2]
        trips = [r for r, count in rank_counts.items() if count == 3]
        quads = [r for r, count in rank_counts.items() if count == 4]
        
        # Create description and rank info
        if hand_rank == 10:
            return "royal flush", f"rank {hand_rank}"
        elif hand_rank == 9:
            return f"straight flush to the {ranks[hand_value]}", f"rank {hand_rank}.{hand_value}"
        elif quads:
            return f"four of a kind, {quads[0]}s", f"rank {hand_rank}.{hand_value}"
        elif hand_rank == 7:  # Full house
            return f"full house", f"rank {hand_rank}.{hand_value}"
        elif hand_rank == 6:  # Flush
            return "flush", f"rank {hand_rank}.{hand_value}"
        elif hand_rank == 5:  # Straight
            return f"straight to the {ranks[hand_value]}", f"rank {hand_rank}.{hand_value}"
        elif trips:
            return f"three of a kind, {trips[0]}s", f"rank {hand_rank}.{hand_value}"
        elif len(pairs) == 2:
            return f"two pair, {pairs[0]}s and {pairs[1]}s", f"rank {hand_rank}.{hand_value}"
        elif len(pairs) == 1:
            return f"pair of {pairs[0]}s", f"rank {hand_rank}.{hand_value}"
        else:
            # High card
            values = [self.CARD_VALUES[r] for r in ranks]
            highest = max(values)
            for rank, value in self.CARD_VALUES.items():
                if value == highest:
                    return f"high card {rank}", f"rank {hand_rank}.{hand_value}"
        
        return "high card", f"rank {hand_rank}.{hand_value}"

    def evaluate_hand(self, community_cards):
        """
        Evaluates the complete hand (hole cards + community cards)
        Returns tuple (hand_rank, hand_value) where:
        hand_rank: 1-10 (1=high card, 10=royal flush)
        hand_value: tie-breaker value within same rank
        """
        all_cards = self.hand + (community_cards or [])
        ranks = [card[0] for card in all_cards]
        suits = [card[1] for card in all_cards]
        
        # Convert ranks to values
        values = [self.CARD_VALUES[r] for r in ranks]
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # Check for flush
        flush_suit = next((s for s, c in suit_counts.items() if c >= 5), None)
        flush_cards = [c for c in all_cards if c[1] == flush_suit] if flush_suit else []
        
        # Check for straight
        value_set = sorted(set(values))
        if 14 in value_set:  # Handle Ace-low straight
            value_set.append(1)
        straight_height = 0
        for i in range(len(value_set)-4):
            if value_set[i+4] - value_set[i] == 4:
                straight_height = value_set[i+4]
                
        # Determine hand rank and value
        if flush_suit and straight_height:
            flush_values = sorted([self.CARD_VALUES[c[0]] for c in flush_cards])
            if set(range(flush_values[-5], flush_values[-1]+1)) == set(flush_values[-5:]):
                if flush_values[-1] == 14:  # Royal Flush
                    return (10, 0)
                return (9, straight_height)  # Straight Flush
                
        # Four of a kind
        quads = [r for r, c in rank_counts.items() if c == 4]
        if quads:
            kicker = max(v for v in values if v != self.CARD_VALUES[quads[0]])
            return (8, self.CARD_VALUES[quads[0]] * 20 + kicker)
            
        # Full House
        trips = [r for r, c in rank_counts.items() if c == 3]
        pairs = [r for r, c in rank_counts.items() if c == 2]
        if trips and pairs:
            return (7, self.CARD_VALUES[trips[0]] * 20 + self.CARD_VALUES[pairs[0]])
        if len(trips) >= 2:
            return (7, self.CARD_VALUES[trips[0]] * 20 + self.CARD_VALUES[trips[1]])
            
        # Flush
        if flush_cards:
            flush_values = sorted([self.CARD_VALUES[c[0]] for c in flush_cards])[-5:]
            return (6, sum(v * (100 ** i) for i, v in enumerate(flush_values)))
            
        # Straight
        if straight_height:
            return (5, straight_height)
            
        # Three of a kind
        if trips:
            other_cards = sorted([v for v in values if v != self.CARD_VALUES[trips[0]]])[-2:]
            return (4, self.CARD_VALUES[trips[0]] * 1000 + sum(v * (100 ** i) for i, v in enumerate(other_cards)))
            
        # Two pair
        if len(pairs) >= 2:
            pair_values = sorted([self.CARD_VALUES[p] for p in pairs])[-2:]
            kicker = max(v for v in values if v not in pair_values)
            return (3, pair_values[1] * 1000 + pair_values[0] * 20 + kicker)
            
        # One pair
        if pairs:
            other_cards = sorted([v for v in values if v != self.CARD_VALUES[pairs[0]]])[-3:]
            return (2, self.CARD_VALUES[pairs[0]] * 1000 + sum(v * (100 ** i) for i, v in enumerate(other_cards)))
            
        # High card
        high_cards = sorted(values)[-5:]
        return (1, sum(v * (100 ** i) for i, v in enumerate(high_cards)))

    @abstractmethod
    def strategy(self, community_cards, pot, current_bet, min_raise, max_raise, opponent_chips, previous_bets=[]):
        """
        Implement poker strategy here
        
        Args:
            community_cards (list): List of community cards on the table
            pot (int): Current pot size
            current_bet (int): Current bet to call
            min_raise (int): Minimum allowed raise
            max_raise (int): Maximum allowed raise
            opponent_chips (list): List of opponent chip counts
            previous_bets (list): List of bets made this round in order
            
        Returns:
            tuple: (PokerAction, amount)
        """
        pass
