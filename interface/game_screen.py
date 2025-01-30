import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
import importlib.util
from .shared_style import Style
from simulate_game import GameSimulator
from bots.prebuilt.balanced_bot import BalancedBot
from bots.prebuilt.conservative_bot import ConservativeBot
from bots.prebuilt.always_call_bot import AlwaysCallBot
import logging
from datetime import datetime

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.encoding = 'utf-8'  # Set UTF-8 encoding by default

    def emit(self, record):
        msg = self.format(record)
        try:
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        except Exception:
            self.handleError(record)
        finally:
            self.text_widget.update_idletasks()

class GameScreen:
    def __init__(self, root):
        self.root = root
        self.root.state('zoomed')
        self.root.title("Single Game Mode")
        
        # Initialize bot-related variables with defaults
        self.available_bots = {'prebuilt': {}, 'user_created': {}}  # Initialize with empty dicts
        self.filename_to_display = {}
        self.bot_paths = []
        self.show_prebuilt = tk.BooleanVar(value=True)
        self.show_custom = tk.BooleanVar(value=True)
        
        self.left_selection = None  # Add tracking for left selection
        self.right_selections = set()  # Add tracking for right selections
        self.your_bot = None  # Add this to track the selected bot
        
        # Load bots after initialization
        self.load_bots()
        self.setup_ui()

    def setup_ui(self):
        # Configure dark theme
        self.root.configure(bg=Style.COLORS['bg'])
        
        # Ensure window maximizes properly
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Container.TFrame', 
                       background=Style.COLORS['bg'],
                       borderwidth=0)
        style.configure('Custom.TLabelframe', 
                       background=Style.COLORS['bg'],
                       foreground=Style.COLORS['text'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=Style.COLORS['text'])
        style.configure('TButton', padding=10, width=30)
        style.configure('Dark.TCheckbutton',
                       background=Style.COLORS['bg'],
                       foreground=Style.COLORS['text'])
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20", style='Container.TFrame')
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid weights
        self.main_frame.grid_rowconfigure(0, weight=0)  # Title
        self.main_frame.grid_rowconfigure(1, weight=0)  # Separator
        self.main_frame.grid_rowconfigure(2, weight=0)  # Description
        self.main_frame.grid_rowconfigure(3, weight=1)  # Content
        self.main_frame.grid_rowconfigure(4, weight=0)  # Back button
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title should span all columns
        title_label = tk.Label(self.main_frame, 
                              text="Single Game Mode",
                              font=Style.FONTS['title'],
                              fg=Style.COLORS['text'],
                              bg=Style.COLORS['bg'])
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # Separator should span all columns
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        # Description should span all columns
        description = ttk.Label(self.main_frame,
                              text="Test your bot against a single opponent. Select your bot and choose who to play against.",
                              font=Style.FONTS['text'],
                              foreground=Style.COLORS['text'],
                              background=Style.COLORS['bg'],
                              wraplength=800)
        description.grid(row=2, column=0, columnspan=3, pady=(5, 10))
        
        # Adjust column weights for narrower side frames
        self.main_frame.grid_columnconfigure(0, weight=1)    # Left bot (narrow)
        self.main_frame.grid_columnconfigure(1, weight=8)    # Log (wide)
        self.main_frame.grid_columnconfigure(2, weight=1)    # Right bot (narrow)
        
        # Create frames with bot selection functionality
        self.left_frame = ttk.LabelFrame(self.main_frame, 
                                       text="Your Bot", 
                                       padding="10",
                                       style='Custom.TLabelframe')
        
        self.center_frame = ttk.LabelFrame(self.main_frame, 
                                         text="Game Log", 
                                         padding="10",
                                         style='Custom.TLabelframe')
        
        self.right_frame = ttk.LabelFrame(self.main_frame, 
                                        text="Opponent Bot", 
                                        padding="10",
                                        style='Custom.TLabelframe')
        
        # Grid frames
        self.left_frame.grid(row=3, column=0, sticky="nsew", pady=20, padx=10)
        self.center_frame.grid(row=3, column=1, sticky="nsew", pady=20)
        self.right_frame.grid(row=3, column=2, sticky="nsew", pady=20, padx=10)

        # Setup bot selection in side frames
        self.setup_bot_selection(self.left_frame, "your_bot")
        self.setup_bot_selection(self.right_frame, "opponent")
        
        # Setup log widget
        self.setup_log_widget()
        
        # Create bottom button frame
        self.setup_bottom_buttons()

    def setup_bot_selection(self, frame, bot_type):
        # Create a vertical stack for buttons/listbox
        selection_frame = ttk.Frame(frame)
        selection_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add listbox for bot selection
        listbox_frame = ttk.Frame(selection_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Configure different selection modes for your bot vs opponent
        select_mode = tk.SINGLE if bot_type == "your_bot" else tk.MULTIPLE
        
        bot_listbox = tk.Listbox(listbox_frame,
                                selectmode=select_mode,
                                bg=Style.COLORS['bg'],  # Use background color from style
                                fg=Style.COLORS['text'],
                                font=Style.FONTS['text'],
                                selectbackground=Style.COLORS['button_hover'],
                                selectforeground=Style.COLORS['text'],
                                state='disabled' if bot_type == "your_bot" else 'normal')  # Disable left listbox
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=bot_listbox.yview)
        bot_listbox.configure(yscrollcommand=scrollbar.set)
        
        bot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store reference to listbox with unique name for each side
        setattr(self, f"{bot_type}_listbox", bot_listbox)
        
        # Add selection handlers
        if bot_type == "opponent":
            bot_listbox.bind('<<ListboxSelect>>', lambda e: self.handle_right_selection(e))
        
        # Add buttons frame
        buttons_frame = ttk.Frame(selection_frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Configure buttons frame columns for centering
        buttons_frame.grid_columnconfigure(0, weight=1)  # Left spacer
        buttons_frame.grid_columnconfigure(1, weight=0)  # Button
        buttons_frame.grid_columnconfigure(2, weight=1)  # Right spacer
        
        if bot_type == "your_bot":
            # Add smaller browse button for your bot (centered)
            button_style = Style.button_style()
            button_style['width'] = 15  # Override width in style
            browse_btn = tk.Button(buttons_frame,
                                text="Browse",
                                command=lambda: self.browse_and_add_bot(bot_listbox),
                                **button_style)
            browse_btn.grid(row=0, column=1, pady=5)
            
            # Add hover effect
            browse_btn.bind('<Enter>', lambda e: browse_btn.configure(bg=Style.COLORS['button_hover']))
            browse_btn.bind('<Leave>', lambda e: browse_btn.configure(bg=Style.COLORS['button']))
        else:
            # Add select all checkbox for opponent selection (centered)
            self.select_all_var = tk.BooleanVar()
            select_all_cb = ttk.Checkbutton(buttons_frame, 
                                          text="Select All",
                                          variable=self.select_all_var,
                                          command=lambda: self.toggle_select_all(bot_listbox),
                                          style='Dark.TCheckbutton')  # Use dark style
            select_all_cb.grid(row=0, column=1, pady=5)
        
        # Update bot list appropriately
        if bot_type == "your_bot":
            self.update_user_bot_list(bot_listbox)
        else:
            self.update_prebuilt_bot_list(bot_listbox)

    def browse_and_add_bot(self, listbox):
        """Handle file browsing and add selected bot to the list"""
        filename = filedialog.askopenfilename(
            title="Select Bot File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            # Add to user-created bots
            bot_name = os.path.basename(filename)
            self.available_bots['user_created'][bot_name] = filename
            
            # Update the listbox
            listbox.configure(state='normal')
            self.update_user_bot_list(listbox)
            
            # Auto-select the newly added bot
            listbox.selection_clear(0, tk.END)
            last_idx = listbox.size() - 1
            listbox.selection_set(last_idx)
            self.your_bot = bot_name
            self.left_selection = last_idx
            listbox.configure(state='disabled')

    def update_user_bot_list(self, listbox):
        """Update listbox with user-created bots"""
        listbox.configure(state='normal')
        listbox.delete(0, tk.END)
        for bot_name in sorted(self.available_bots['user_created'].keys()):
            listbox.insert(tk.END, bot_name)
            if bot_name == self.your_bot:  # Restore selection if this was the selected bot
                listbox.selection_set(tk.END)
        listbox.configure(state='disabled')

    def update_prebuilt_bot_list(self, listbox):
        """Update listbox with prebuilt bots"""
        listbox.delete(0, tk.END)
        for bot_name in sorted(self.available_bots['prebuilt'].keys()):
            listbox.insert(tk.END, bot_name)

    def browse_file(self, path_var):
        """Handle file browsing"""
        filename = tk.filedialog.askopenfilename(
            title="Select Bot File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            path_var.set(filename)

    def setup_log_widget(self):
        # Configure center frame for the log
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)
        
        # Create Text widget with vertical scrollbar only
        self.log_text = tk.Text(
            self.center_frame,
            wrap=tk.WORD,
            bg=Style.COLORS['bg'],
            fg=Style.COLORS['text'],
            font=('Consolas', 10),
            width=80
        )
        
        # Create vertical scrollbar only
        y_scrollbar = ttk.Scrollbar(self.center_frame, orient="vertical", command=self.log_text.yview)
        
        # Configure text widget scrolling
        self.log_text.configure(yscrollcommand=y_scrollbar.set)
        
        # Grid layout
        self.log_text.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure logging
        self.setup_logging()

    def setup_logging(self):
        # Create logs directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        log_file = os.path.join(log_dir, f'poker_game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # Create and configure the text handler (removed setEncoding call)
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add handlers with UTF-8 encoding
        root_logger.addHandler(logging.FileHandler(log_file, encoding='utf-8'))
        root_logger.addHandler(text_handler)

    def setup_bottom_buttons(self):
        button_frame = tk.Frame(self.main_frame, bg=Style.COLORS['bg'])
        button_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        button_frame.grid_columnconfigure(0, weight=0)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=0)
        
        # Back button
        back_btn = tk.Button(button_frame, 
                           text="Back to Menu",
                           command=self.back_to_menu,
                           **Style.button_style())
        back_btn.grid(row=0, column=0, padx=5)
        
        # Start button
        start_btn = tk.Button(button_frame,
                            text="Start Game",
                            command=self.start_game,
                            **Style.button_style())
        start_btn.grid(row=0, column=2, padx=5)
        
        # Add hover effects
        for btn in [back_btn, start_btn]:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=Style.COLORS['button_hover']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=Style.COLORS['button']))

    def start_game(self):
        # Get selected bots using tracked selections instead of curselection()
        opponent_indices = self.opponent_listbox.curselection()
        
        if self.your_bot is None or not opponent_indices:
            tk.messagebox.showwarning("Selection Required", 
                "Please select your bot and at least one opponent.")
            return
            
        your_bot_name = self.your_bot  # Use tracked bot name directly
        opponent_names = [self.opponent_listbox.get(idx) for idx in opponent_indices]
        
        # Load the bot classes
        your_bot_class = self.load_bot_class(your_bot_name, is_user_bot=True)
        opponent_classes = [self.load_bot_class(name, is_user_bot=False) for name in opponent_names]
        
        if not your_bot_class or not all(opponent_classes):
            tk.messagebox.showerror("Error", "Failed to load bot classes.")
            return
            
        # Clear the log
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        # Create and run simulation with all selected opponents
        simulator = GameSimulator(max_rounds=2)
        players = [your_bot_class(f"{your_bot_name}", 1000)]
        players.extend(cls(f"{name}", 1000) for cls, name in zip(opponent_classes, opponent_names))
        simulator.run_simulation(players)

    def load_bot_class(self, bot_name, is_user_bot=False):
        """Load a bot class from file"""
        try:
            bot_path = self.available_bots['user_created' if is_user_bot else 'prebuilt'][bot_name]
            spec = importlib.util.spec_from_file_location("bot_module", bot_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the bot class in the module
            for item in dir(module):
                if item.endswith('Bot') and item != 'AbstractBot':
                    return getattr(module, item)
        except Exception as e:
            logging.error(f"Error loading bot: {e}")
            return None

    def back_to_menu(self):
        from .menu_screen import MenuScreen
        for widget in self.root.winfo_children():
            widget.destroy()
        MenuScreen(self.root)

    def load_bots(self):
        """Load bot classes from the bots directory"""
        bots_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bots'))
        
        # Return empty dicts if directory doesn't exist
        if not os.path.exists(bots_dir):
            return
            
        # Process prebuilt directory
        prebuilt_dir = os.path.join(bots_dir, 'prebuilt')
        if os.path.exists(prebuilt_dir):
            for file in os.listdir(prebuilt_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    full_path = os.path.join(prebuilt_dir, file)
                    self.available_bots['prebuilt'][file] = full_path

        # Process user-created directory
        user_dir = os.path.join(bots_dir, 'user-created')
        if os.path.exists(user_dir):
            for file in os.listdir(user_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    full_path = os.path.join(user_dir, file)
                    self.available_bots['user_created'][file] = full_path

    def update_bot_list(self, listbox):
        """Update listbox with available bots"""
        # Clear current items
        listbox.delete(0, tk.END)
        
        # Add prebuilt bots if any
        if self.show_prebuilt.get():
            for bot_name in self.available_bots['prebuilt'].keys():
                listbox.insert(tk.END, bot_name)
        
        # Add custom bots if any
        if self.show_custom.get():
            for bot_name in self.available_bots['user_created'].keys():
                listbox.insert(tk.END, f"{bot_name} (Custom)")

    def handle_right_selection(self, event):
        """Handle selection in the right (opponent) listbox"""
        try:
            listbox = event.widget
            selections = listbox.curselection()
            self.right_selections = set(selections)
        except Exception as e:
            logging.error(f"Error in right selection: {e}")
            pass

    def toggle_select_all(self, listbox):
        """Toggle selection of all items in the opponent listbox"""
        try:
            if self.select_all_var.get():
                listbox.select_set(0, tk.END)
                self.right_selections = set(range(listbox.size()))
            else:
                listbox.selection_clear(0, tk.END)
                self.right_selections.clear()
        except Exception as e:
            logging.error(f"Error in toggle select all: {e}")
            pass