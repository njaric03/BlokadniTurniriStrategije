import random
import logging

from bots.abstract_bot import PokerAction
from .dealer import Dealer
from .player import Player

class PokerGame:
    def __init__(self):
        self.dealer = Dealer()
        self.players = []
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.initial_total_chips = 0
        self.dealer_position = 0  # Track dealer position
        self.small_blind = 50
        self.big_blind = 100
        self.round_bets = {}  # Add tracking of round bets
        
    def add_player(self, player):
        """Add a player/bot instance to the game"""
        self.players.append(player)
        self.initial_total_chips += player.chips
        
    def start_round(self):
        self.dealer.create_deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = self.big_blind
        self.round_bets = {player.name: 0 for player in self.players}
        
        # Reset all players' current bets and active status
        for player in self.players:
            player.current_bet = 0
            player.is_active = True
        
        # Post blinds
        small_blind_pos = (self.dealer_position + 1) % len(self.players)
        big_blind_pos = (self.dealer_position + 2) % len(self.players)
        
        # Post small blind
        self.players[small_blind_pos].place_bet(self.small_blind)
        # Post big blind
        self.players[big_blind_pos].place_bet(self.big_blind)
        
        # Deal hole cards
        for _ in range(2):
            for player in self.players:
                if player.is_active:
                    player.add_card(self.dealer.deal_card())
                    
    def deal_flop(self):
        # Burn a card
        self.dealer.deal_card()
        # Deal flop
        for _ in range(3):
            card = self.dealer.deal_card()
            if card:
                self.community_cards.append(card)
            
    def deal_turn(self):
        # Burn a card
        self.dealer.deal_card()
        # Deal turn
        card = self.dealer.deal_card()
        if card:
            self.community_cards.append(card)
        
    def deal_river(self):
        # Burn a card
        self.dealer.deal_card()
        # Deal river
        card = self.dealer.deal_card()
        if card:
            self.community_cards.append(card)
        
    def betting_round(self, is_preflop=False):
        # Get betting order
        if is_preflop:
            start_pos = (self.dealer_position + 3) % len(self.players)
        else:
            start_pos = (self.dealer_position + 1) % len(self.players)
            
        # Collect all current bets into pot at start of any betting round
        for player in self.players:
            self.pot += player.current_bet
            player.current_bet = 0
        self.current_bet = 0 if not is_preflop else self.big_blind
            
        betting_order = self.players[start_pos:] + self.players[:start_pos]
        previous_bets = []
        actions = ["" for _ in self.players]
        
        for player_idx, player in enumerate(betting_order):
            if player.is_active:
                # Calculate what this player needs to call
                to_call = self.current_bet - player.current_bet
                
                action, amount = player.strategy(
                    self.community_cards,
                    self.pot,
                    to_call,  # Send what they need to call, not total current bet
                    max(to_call * 2, self.big_blind),  # Minimum raise
                    player.chips + player.current_bet,  # Maximum raise
                    [p.chips for p in self.players if p != player],
                    previous_bets
                )
                
                orig_pos = (start_pos + player_idx) % len(self.players)
                
                if action == PokerAction.FOLD:
                    self.pot += player.current_bet  # Add their current bet to pot before folding
                    self.round_bets[player.name] += player.current_bet  # Track bet
                    player.current_bet = 0
                    player.fold()
                    actions[orig_pos] = "Fold"
                elif action == PokerAction.CALL:
                    # Return current bet to chips
                    player.chips += player.current_bet
                    player.current_bet = 0
                    # Make new bet
                    bet = player.place_bet(self.current_bet)
                    if bet < self.current_bet:
                        player.fold()
                        actions[orig_pos] = "Fold (couldn't call)"
                    else:
                        # Show "Check" if there's no bet to call
                        if bet == 0:
                            actions[orig_pos] = "Check"
                        else:
                            actions[orig_pos] = f"Call (${bet})"
                        previous_bets.append(bet)
                        self.round_bets[player.name] += bet  # Track bet
                elif action == PokerAction.RAISE:
                    if amount > self.current_bet:
                        # Return current bet to chips
                        player.chips += player.current_bet
                        player.current_bet = 0
                        # Place new bet
                        bet = player.place_bet(amount)
                        if bet > 0:
                            self.current_bet = bet
                            previous_bets.append(bet)
                            actions[orig_pos] = f"Raise to ${bet}"
                            self.round_bets[player.name] += bet  # Track bet
                        else:
                            player.fold()
                            actions[orig_pos] = "Fold (couldn't raise)"
                    else:
                        # Treat as call if raise amount isn't higher
                        player.chips += player.current_bet
                        player.current_bet = 0
                        bet = player.place_bet(self.current_bet)
                        if bet < self.current_bet:
                            player.fold()
                            actions[orig_pos] = "Fold (couldn't call)"
                        else:
                            actions[orig_pos] = f"Call (${bet})"
                            previous_bets.append(bet)
                            self.round_bets[player.name] += bet  # Track bet
                
                active_players = [p for p in self.players if p.is_active]
                if len(active_players) == 1:
                    winner = active_players[0]
                    # Collect any remaining bets
                    for p in self.players:
                        self.pot += p.current_bet
                        p.current_bet = 0
                    # Award pot
                    winner.chips += self.pot
                    self.pot = 0
                    self._verify_balances()
                    return True, actions
                    
                self._verify_balances()
        
        # After betting round, collect any remaining bets into pot
        for player in self.players:
            self.pot += player.current_bet
            player.current_bet = 0
            
        # Only move dealer button after non-preflop rounds
        if not is_preflop:
            self.dealer_position = (self.dealer_position + 1) % len(self.players)
        return False, actions
                    
    def determine_winner(self):
        active_players = [p for p in self.players if p.is_active]
        if active_players:
            # Evaluate each player's hand and find the winner(s)
            hand_rankings = [(player, player.evaluate_hand(self.community_cards)) 
                           for player in active_players]
            
            # First compare by hand rank (higher is better), then by hand value
            best_hand = max(hand_rankings, key=lambda x: (x[1][0], x[1][1]))
            
            # Find all players with the same best hand (in case of a tie)
            winners = [p for p, h in hand_rankings if h[0] == best_hand[1][0] and h[1] == best_hand[1][1]]
            
            # In case of a tie, split the pot
            winner = winners[0]  # For simplicity, just return first winner
            split_pot = len(winners) > 1
            
            # Get hand descriptions
            hand_descriptions = {p.name: p.get_hand_description(self.community_cards) 
                              for p in active_players}
            
            # Calculate total pot
            total_pot = self.pot
            for player in self.players:
                total_pot += player.current_bet
                player.current_bet = 0
            
            # Award pot to winner(s)
            pot_share = total_pot // len(winners)
            for w in winners:
                w.chips += pot_share
            
            profit = pot_share - self.round_bets[winner.name]  # Calculate profit
            self.pot = 0
            
            # Clear all players' hands
            for player in self.players:
                player.clear_hand()
            
            self._verify_balances()
            return winner, total_pot, hand_descriptions, profit
        return None, 0, {}, 0

    def _verify_balances(self):
        current_total = sum(p.chips + p.current_bet for p in self.players) + self.pot
        if current_total != self.initial_total_chips:
            logging.error(f"Balance mismatch! Initial: {self.initial_total_chips}, Current: {current_total}")
            logging.error(f"Pot: {self.pot}")
            for p in self.players:
                logging.error(f"{p.name}: chips={p.chips}, current_bet={p.current_bet}")
            raise ValueError("Chip count doesn't match initial total!")
