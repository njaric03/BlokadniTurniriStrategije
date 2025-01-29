import tkinter as tk
from .shared_style import Style
from .game_screen import GameScreen

class MenuScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Blokadni poker")
        
        # Configure window
        self.root.configure(bg=Style.COLORS['bg'])
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        
        # Configure grid weights for centering
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = tk.Frame(root, bg=Style.COLORS['bg'])
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)  # Title
        main_frame.grid_rowconfigure(2, weight=0)  # Subtitle
        main_frame.grid_rowconfigure(3, weight=0)  # Button
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title = tk.Label(main_frame,
                        text="Blokadni Poker",
                        font=Style.FONTS['title'],
                        fg=Style.COLORS['text'],
                        bg=Style.COLORS['bg'])
        title.grid(row=1, column=0, pady=(0, 10))
        
        # Subtitle
        subtitle = tk.Label(main_frame,
                          text="Simulator",
                          font=Style.FONTS['subtitle'],
                          fg=Style.COLORS['text'],
                          bg=Style.COLORS['bg'])
        subtitle.grid(row=2, column=0, pady=(0, 40))
        
        # Start Game button
        start_btn = tk.Button(main_frame, 
                            text="Start Game", 
                            command=self.start_game, 
                            **Style.button_style())
        start_btn.grid(row=3, column=0)
        
        # Add hover effect
        start_btn.bind('<Enter>', lambda e: start_btn.configure(bg=Style.COLORS['button_hover']))
        start_btn.bind('<Leave>', lambda e: start_btn.configure(bg=Style.COLORS['button']))

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def start_game(self):
        self.clear_window()
        GameScreen(self.root)

    def start_tournament(self):
        pass

    def test_multiple(self):
        pass