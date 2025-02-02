import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
import importlib.util

from bots.abstract_bot import AbstractBot
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
        self.player1_path = tk.StringVar()  # Add this for storing the selected bot path
        
        self.left_selection = None  # Add tracking for left selection
        self.right_selections = set()  # Add tracking for right selections
        self.your_bot = None  # Add this to track the selected bot
        
        # Add tooltip-related attributes
        self.tooltip = None
        self.tooltip_id = None
        self.current_item = -1
        
        self.bot_instances = {}  # Add this to store bot instances
        
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
        style.configure('TLabelframe', 
                       background=Style.COLORS['bg'],
                       foreground=Style.COLORS['text'])
        style.configure('TLabelframe.Label', 
                       background=Style.COLORS['bg'],
                       foreground=Style.COLORS['text'])
        style.configure('Custom.TFrame', 
                       background=Style.COLORS['bg'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=Style.COLORS['text'])
        
        # Also configure the checkbox label color
        style.map('Dark.TCheckbutton',
                 background=[('active', Style.COLORS['bg'])],
                 foreground=[('active', Style.COLORS['text'])])

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
        
        # Same styling for both listboxes
        bot_listbox = tk.Listbox(listbox_frame,
                                selectmode=select_mode,
                                bg=Style.COLORS['button'],  # Light background
                                fg='white',    # White text for visibility
                                font=Style.FONTS['text'],
                                selectbackground=Style.COLORS['button_hover'],
                                selectforeground='white',  # White text when selected
                                disabledforeground='white',  # Add this to keep text white when disabled
                                state='normal')  # Always normal state
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=bot_listbox.yview)
        bot_listbox.configure(yscrollcommand=scrollbar.set)
        
        bot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store reference to listbox
        setattr(self, f"{bot_type}_listbox", bot_listbox)
        
        # Add selection handlers
        if bot_type == "opponent":
            bot_listbox.bind('<<ListboxSelect>>', lambda e: self.handle_right_selection(e))
        
        # Add buttons frame with dark background
        buttons_frame = ttk.Frame(selection_frame, style='Custom.TFrame')  # Add dark background
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Configure buttons frame columns for centering
        buttons_frame.grid_columnconfigure(0, weight=1)  # Left spacer
        buttons_frame.grid_columnconfigure(1, weight=0)  # Button/checkbox
        buttons_frame.grid_columnconfigure(2, weight=1)  # Right spacer
        
        if bot_type == "your_bot":
            # Add browse button with proper styling
            button_style = Style.button_style()
            button_style['width'] = 10  # Smaller width
            browse_btn = tk.Button(buttons_frame,
                                text="Browse",
                                command=lambda: self.browse_file(self.player1_path),  # Fixed method call
                                **button_style)
            browse_btn.grid(row=0, column=1, pady=5)
            
            # Add hover effect
            browse_btn.bind('<Enter>', lambda e: browse_btn.configure(bg=Style.COLORS['button_hover']))
            browse_btn.bind('<Leave>', lambda e: browse_btn.configure(bg=Style.COLORS['button']))
        else:
            # Add select all checkbox with dark styling
            self.select_all_var = tk.BooleanVar()
            select_all_cb = ttk.Checkbutton(buttons_frame, 
                                          text="Select All",
                                          variable=self.select_all_var,
                                          command=lambda: self.toggle_select_all(bot_listbox),
                                          style='Dark.TCheckbutton')
            select_all_cb.grid(row=0, column=1, pady=5)
        
        # Update bot list appropriately
        listbox = bot_listbox  # For clarity
        listbox.delete(0, tk.END)
        
        if bot_type == "your_bot":
            # Add user-created bots with proper styling
            for bot_name in sorted(self.available_bots['user_created'].keys()):
                listbox.insert(tk.END, bot_name)
                # No need to change state, just make sure colors are correct
        else:
            # Add prebuilt bots
            for bot_name in sorted(self.available_bots['prebuilt'].keys()):
                listbox.insert(tk.END, bot_name)
        
        # Add tooltip bindings only for opponent listbox
        if bot_type == "opponent":
            bot_listbox.bind('<Motion>', self.schedule_tooltip)
            bot_listbox.bind('<Leave>', lambda e: self.hide_bot_description())

    def browse_file(self, path_var):
        """Handle file browsing"""
        filename = filedialog.askopenfilename(
            title="Select Bot File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            path_var.set(filename)
            bot_name = os.path.basename(filename)
            
            # Add to available bots and update display
            self.available_bots['user_created'][bot_name] = filename
            self.your_bot = bot_name
            
            # Update left listbox with white text
            self.your_bot_listbox.configure(state='normal')
            self.your_bot_listbox.delete(0, tk.END)
            self.your_bot_listbox.insert(0, bot_name)
            self.your_bot_listbox.selection_set(0)
            self.your_bot_listbox.configure(state='disabled', disabledforeground='white')  # Set both state and color
            
            self.left_selection = 0

    def setup_log_widget(self):
        # Configure center frame for the log
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)
        
        # Create Text widget with improved styling
        self.log_text = tk.Text(
            self.center_frame,
            wrap=tk.NONE,  # Disable text wrapping
            bg=Style.COLORS['button'],  # Use button color for better contrast
            fg=Style.COLORS['text'],
            font=('Consolas', 10),
            width=80
        )
        
        # Add both vertical and horizontal scrollbars
        h_scrollbar = ttk.Scrollbar(self.center_frame, 
                                  orient="horizontal",
                                  command=self.log_text.xview)
        v_scrollbar = ttk.Scrollbar(self.center_frame, 
                                  orient="vertical",
                                  command=self.log_text.yview)
        
        self.log_text.configure(xscrollcommand=h_scrollbar.set,
                              yscrollcommand=v_scrollbar.set)
        
        # Grid layout for text and scrollbars
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Add info label
        info_label = ttk.Label(self.center_frame,
                             text="Complete results will be saved in the logs subdirectory",
                             font=Style.FONTS['text'],
                             foreground=Style.COLORS['text'],
                             background=Style.COLORS['bg'])  # Use button color for consistency
        info_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

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
        # Check if bot file is selected
        your_bot_path = self.player1_path.get()
        opponent_indices = self.opponent_listbox.curselection()
        
        if not your_bot_path or not opponent_indices:
            tk.messagebox.showwarning("Selection Required", 
                "Please select your bot and at least one opponent.")
            return
            
        # Get bot name from file path
        your_bot_name = os.path.splitext(os.path.basename(your_bot_path))[0]
            
        # Load your bot class from file path
        your_bot_class = self.load_bot_from_path(your_bot_path)
        opponent_names = [self.opponent_listbox.get(idx) for idx in opponent_indices]
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

    def load_bot_from_path(self, path):
        """Load a bot class from a file path"""
        try:
            spec = importlib.util.spec_from_file_location("bot_module", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the bot class in the module
            for item in dir(module):
                if item.endswith('Bot') and item != 'AbstractBot':
                    return getattr(module, item)
        except Exception as e:
            logging.error(f"Error loading bot: {e}")
            return None

    def load_bot_class(self, bot_name, is_user_bot=False):
        """Load a bot class from file"""
        try:
            return self.available_bots['user_created' if is_user_bot else 'prebuilt'][bot_name]
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
        
        if not os.path.exists(bots_dir):
            return
            
        # Process prebuilt directory
        prebuilt_dir = os.path.join(bots_dir, 'prebuilt')
        if os.path.exists(prebuilt_dir):
            for file in os.listdir(prebuilt_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    try:
                        full_path = os.path.join(prebuilt_dir, file)
                        # Load the module
                        spec = importlib.util.spec_from_file_location(file[:-3], full_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find the bot class
                        for item in dir(module):
                            obj = getattr(module, item)
                            if isinstance(obj, type) and issubclass(obj, AbstractBot) and obj != AbstractBot:
                                # Store bot class and an instance
                                self.available_bots['prebuilt'][file] = obj
                                self.bot_instances[file] = obj('temp', 1000)  # Temporary instance for description
                                break
                    except Exception as e:
                        logging.error(f"Error loading bot {file}: {e}")
                        continue

        # Process user-created directory (similar logic)
        user_dir = os.path.join(bots_dir, 'user-created')
        if os.path.exists(user_dir):
            for file in os.listdir(user_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    try:
                        full_path = os.path.join(user_dir, file)
                        spec = importlib.util.spec_from_file_location(file[:-3], full_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        for item in dir(module):
                            obj = getattr(module, item)
                            if isinstance(obj, type) and issubclass(obj, AbstractBot) and obj != AbstractBot:
                                self.available_bots['user_created'][file] = obj
                                self.bot_instances[file] = obj('temp', 1000)
                                break
                    except Exception as e:
                        logging.error(f"Error loading bot {file}: {e}")
                        continue

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

    def schedule_tooltip(self, event):
        # Get the item under cursor using the event's widget
        index = event.widget.nearest(event.y)
        
        # If mouse is over a different item or no tooltip exists
        if index >= 0 and (index != self.current_item or not self.tooltip):
            self.current_item = index
            
            # Cancel any pending hide operations
            if self.tooltip_id:
                event.widget.after_cancel(self.tooltip_id)
                self.tooltip_id = None
            
            # Show tooltip immediately
            self.show_bot_description(event)

    def schedule_hide_tooltip(self, event):
        # Schedule hiding with a delay
        if self.tooltip_id:
            event.widget.after_cancel(self.tooltip_id)
        self.tooltip_id = event.widget.after(500, self.hide_bot_description)

    def show_bot_description(self, event):
        # Get listbox's actual size and item count
        listbox = event.widget
        total_height = listbox.winfo_height()
        item_count = listbox.size()
        
        # Each item's height is approximately 25-30 pixels, or we can calculate it
        item_height = 30  # Approximate height of each item
        total_items_height = item_count * item_height
        
        # Check if mouse is below the last item
        if event.y > total_items_height:
            # Mouse is in empty space below items
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
            return
            
        # Get the item under cursor
        index = listbox.nearest(event.y)
        if 0 <= index < item_count:  # Verify index is valid
            bot_name = listbox.get(index)
            
            # Rest of tooltip creation code
            # Get description from bot instance
            description = ""
            if bot_name in self.available_bots['prebuilt']:
                bot_instance = self.bot_instances.get(bot_name)
                if bot_instance:
                    description = bot_instance.description
            elif bot_name in self.available_bots['user_created']:
                bot_instance = self.bot_instances.get(bot_name)
                if bot_instance:
                    description = bot_instance.description
                    
            # Create tooltip if we have a description
            if description:
                # Calculate position to the left of the listbox
                x = event.widget.winfo_rootx() - 205
                y = event.widget.winfo_rooty() + event.y
                
                if self.tooltip:
                    self.tooltip.destroy()
                
                self.tooltip = tk.Toplevel(event.widget)
                self.tooltip.wm_overrideredirect(True)
                self.tooltip.wm_geometry(f"+{x}+{y}")
                
                frame = ttk.Frame(self.tooltip, style='TFrame')
                frame.pack(fill=tk.BOTH, expand=True)
                
                label = ttk.Label(frame, 
                                text=description,
                                background=Style.COLORS['button'],
                                foreground=Style.COLORS['text'],
                                wraplength=200,
                                padding=5)
                label.pack(fill=tk.BOTH, expand=True)

    def hide_bot_description(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        self.current_item = -1
        self.tooltip_id = None