from bots.prebuilt.balanced_bot import BalancedBot
from game_logic.poker_game import PokerGame
from bots.prebuilt.all_in_bot import AllInBot
from bots.prebuilt.conservative_bot import ConservativeBot
from bots.prebuilt.always_call_bot import AlwaysCallBot
from interface.menu_screen import MenuScreen  # Add this import
import os
import logging
import sys
from datetime import datetime
from simulate_game import GameSimulator
import tkinter as tk  # Add this import

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging with UTF-8 encoding
    log_file = os.path.join(log_dir, f'poker_game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure handlers
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler(sys.stdout)  # Use stdout instead of stderr
    
    # Setup logging without timestamps
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            file_handler,
            console_handler
        ]
    )

def main():
    # Initialize Tkinter
    root = tk.Tk()
    root.state('zoomed')  # Start maximized
    app = MenuScreen(root)
    root.mainloop()

if __name__ == "__main__":
    main()
