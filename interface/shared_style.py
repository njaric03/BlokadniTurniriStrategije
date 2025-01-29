class Style:
    COLORS = {
        'bg': '#1E2337',           # Dark blue background
        'button': '#2A3F54',       # Button color
        'button_hover': '#3C5876', # Button hover color
        'text': '#E0E7FF'          # Light text color
    }
    
    FONTS = {
        'title': ('Segoe UI', 42, 'bold'),
        'subtitle': ('Segoe UI Light', 24),
        'text': ('Segoe UI', 12),
    }
    
    @staticmethod
    def button_style():
        return {
            'font': ('Segoe UI', 12),
            'bg': Style.COLORS['button'],
            'fg': Style.COLORS['text'],
            'activebackground': Style.COLORS['button_hover'],
            'activeforeground': Style.COLORS['text'],
            'width': 30,
            'height': 2,
            'bd': 0,
            'cursor': 'hand2'
        }