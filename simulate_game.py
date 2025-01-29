import logging
from game_logic.poker_game import PokerGame
import time

class GameSimulator:
    def __init__(self, max_rounds=10):
        self.max_rounds = max_rounds
        self.game = PokerGame()
        self.round_bets = {}  # Track bets made by each player in current round
        self.current_round_pot = 0  # Add this to track total pot for the round
        self.suit_symbols = {
            'spades': '♠',
            'hearts': '♥',
            'diamonds': '♦',
            'clubs': '♣'
        }

    def format_card(self, card):
        """Format card with Unicode suit symbols"""
        rank, suit = card
        suit_symbol = self.suit_symbols.get(suit.lower(), suit)
        return f"{rank}{suit_symbol}"

    def log_game_state(self, round_num, stage, actions=None):
        state = f"\nRound {round_num} - {stage}\n"
        state += "-" * 40 + "\n"
        
        # Format community cards more intuitively
        if self.game.community_cards:
            cards_str = ' | '.join(self.format_card(card) for card in self.game.community_cards)
            state += f"Board: {cards_str}\n"
        else:
            state += "Board: []\n"
        state += f"Pot: ${self.game.pot}\n\n"
        
        # Get blind positions for pre-flop
        small_blind_pos = (self.game.dealer_position + 1) % len(self.game.players)
        big_blind_pos = (self.game.dealer_position + 2) % len(self.game.players)
        
        # Player information
        for i, player in enumerate(self.game.players):
            # Handle inactive/folded players
            if not player.is_active:
                if stage == "Pre-Flop":
                    # Show hands but mark as folded in Pre-Flop
                    cards_str = ' | '.join(self.format_card(card) for card in player.hand)
                    state += f"{player.name}: {cards_str} (${player.chips})"
                    # Add blind indicator if applicable
                    if stage == "Pre-Flop":
                        if i == small_blind_pos:
                            state += " (SB)"
                        elif i == big_blind_pos:
                            state += " (BB)"
                    if actions and i < len(actions):
                        state += f" - {actions[i]}"
                else:
                    # Just show folded status after Pre-Flop
                    state += f"{player.name}: Folded (${player.chips})"
            else:
                # Show active players normally
                cards_str = ' | '.join(self.format_card(card) for card in player.hand)
                state += f"{player.name}: {cards_str} (${player.chips})"
                # Add blind indicator if applicable
                if stage == "Pre-Flop":
                    if i == small_blind_pos:
                        state += " (SB)"
                    elif i == big_blind_pos:
                        state += " (BB)"
                if actions and i < len(actions):
                    state += f" - {actions[i]}"
            state += "\n"
            
        state += "-" * 40
        logging.info(state)
        
        # Add summary if all active players checked
        active_actions = [a for p, a in zip(self.game.players, actions or []) if p.is_active and a]
        if active_actions and all(a == "Check" for a in active_actions):
            logging.info("All players checked")

    def run_betting_round(self, round_num, stage):
        is_preflop = (stage == "Pre-Flop")
        round_actions = []
        early_end, actions = self.game.betting_round(is_preflop)
        
        # Track total pot for this round
        self.current_round_pot = self.game.pot + sum(p.current_bet for p in self.game.players)
        
        # Update round_bets with current bets from this betting round
        for player in self.game.players:
            self.round_bets[player.name] += player.current_bet
        
        if early_end:
            active_player = [p for p in self.game.players if p.is_active][0]
            self.log_game_state(round_num, stage, actions)
            # Calculate profit as total pot minus player's total investment
            winner_bet = self.round_bets[active_player.name]
            profit = self.current_round_pot - winner_bet
            logging.info(f"\nRound {round_num}: {active_player.name} wins ${self.current_round_pot} (profit: ${profit})")
            # Clear hands and prepare for next round
            for player in self.game.players:
                player.clear_hand()
                player.is_active = True
            return True
        self.log_game_state(round_num, f"{stage} (After Betting)", actions)
        return False

    def get_board_string(self):
        """Get formatted string of community cards"""
        if not self.game.community_cards:
            return "[]"
        return ' | '.join(self.format_card(card) for card in self.game.community_cards)

    def run_simulation(self, players):
        # Add players to game
        for player in players:
            self.game.add_player(player)

        for round_num in range(1, self.max_rounds + 1):
            # Reset round bets tracking at the start of each round
            self.round_bets = {player.name: 0 for player in self.game.players}
            
            logging.info(f"\n{'='*20} ROUND {round_num} {'='*20}")
            
            self.game.start_round()
            # Track blinds in round_bets
            small_blind_pos = (self.game.dealer_position + 1) % len(self.game.players)
            big_blind_pos = (self.game.dealer_position + 2) % len(self.game.players)
            self.round_bets[self.game.players[small_blind_pos].name] += self.game.small_blind
            self.round_bets[self.game.players[big_blind_pos].name] += self.game.big_blind
            
            self.log_game_state(round_num, "Pre-Flop")
            
            # If betting round ends early, skip to next round
            if self.run_betting_round(round_num, "Pre-Flop"):
                continue
            
            active_players = [p for p in self.game.players if p.is_active]
            if len(active_players) > 1:
                # Deal and log flop
                self.game.deal_flop()
                self.log_game_state(round_num, "Flop")
                if self.run_betting_round(round_num, "Flop"):
                    continue
                
                active_players = [p for p in self.game.players if p.is_active]
                if len(active_players) > 1:
                    # Deal and log turn
                    self.game.deal_turn()
                    self.log_game_state(round_num, "Turn")
                    if self.run_betting_round(round_num, "Turn"):
                        continue
                    
                    active_players = [p for p in self.game.players if p.is_active]
                    if len(active_players) > 1:
                        # Deal and log river
                        self.game.deal_river()
                        self.log_game_state(round_num, "River")
                        if self.run_betting_round(round_num, "River"):
                            continue
            
            # Determine winner
            winner, total_pot, hand_descriptions, profit = self.game.determine_winner()
            if winner:
                board_str = self.get_board_string()
                
                # Log final board state
                if self.game.community_cards:
                    logging.info(f"\nFinal board: {board_str}")
                
                # Create hand comparison string with ranks
                hand_comparison = []
                for player_name, (desc, rank_info) in hand_descriptions.items():
                    if player_name == winner.name:
                        winner_desc = desc
                        winner_rank = rank_info
                    else:
                        hand_comparison.append(f"{player_name}'s {desc} ({rank_info})")
                
                # Log winner announcement
                comparison_str = " vs ".join(hand_comparison)
                if comparison_str:
                    logging.info(f"\nWinner Determination:")
                    logging.info(f"{winner.name} wins with {winner_desc} ({winner_rank})")
                    logging.info(f"Against: {comparison_str}")
                else:
                    logging.info(f"\nWinner Determination:")
                    logging.info(f"{winner.name} wins (others folded)")
                
                # Log financial outcome separately
                logging.info(f"\nRound Results:")
                logging.info(f"Pot: ${total_pot}")
                logging.info(f"{winner.name}'s profit: ${profit}")
            
            # Check if game should end early
            active_players = [p for p in self.game.players if p.chips > 0]
            if len(active_players) < 2:
                logging.info(f"\nGame Over! {active_players[0].name} wins!")
                return active_players[0]
                
            time.sleep(1)

        # Final results - separate section
        logging.info("\n" + "="*40)
        logging.info("FINAL STANDINGS")
        logging.info("="*40)
        winner = max(self.game.players, key=lambda p: p.chips)
        logging.info(f"Winner: {winner.name}")
        logging.info("\nFinal Chip Counts:")
        for player in sorted(self.game.players, key=lambda p: p.chips, reverse=True):
            logging.info(f"{player.name}: ${player.chips}")
            
        return winner
