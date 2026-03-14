import tkinter as tk
from tkinter import scrolledtext
import subprocess
import os
import sys
import ctypes

try:
    from dilraj_shell import tokenize
except ImportError:
    print("Error: Could not find your shell file. Make sure tokenize() is accessible.")
    sys.exit()

class TerminalEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Cosmic-SH")
        # --- Dynamic Window Sizing & Centering ---
        # 1. Ask the OS for your monitor's true pixel resolution
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 2. Calculate the window size to take up ~60% of your screen
        window_width = int(screen_width * 0.6)
        window_height = int(screen_height * 0.6)
        
        # 3. Calculate the exact X and Y coordinates to center it on the monitor
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        
        # 4. Inject the dimensions into tkinter (Format: WidthxHeight+X+Y)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # --- OS-Level Glassmorphism ---
        self.root.attributes('-alpha', 0.85)
        
        # --- Color Palette ---
        BG_COLOR = "#08040f"
        TEXT_FG = "#d4c5f9"
        FONT = ("Geom", 11) 
        
        self.root.configure(bg=BG_COLOR)

        # --- 1. The Unified Terminal Display ---
        # Notice state is NORMAL now, because we HAVE to type in it.
        self.terminal = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=BG_COLOR, fg=TEXT_FG, 
            font=FONT, insertbackground=TEXT_FG, 
            bd=0, highlightthickness=0, padx=20, pady=20
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)

        # --- 2. Input Interception Binds ---
        self.terminal.bind("<Return>", self.handle_return)
        self.terminal.bind("<BackSpace>", self.handle_backspace)
        self.terminal.bind("<Left>", self.handle_left)
        # Force cursor to end if they click somewhere else and try to type
        self.terminal.bind("<Key>", self.handle_keypress)

        # --- 3. System Print Hijack ---
        sys.stdout = self
        sys.stderr = self
        
        print("Welcome to Cosmic-SH.")      
        # Boot the first prompt
        self.display_prompt()

    # --- THE TERMINAL BUFFER ENGINE ---

    def write(self, text):
        """Intercepts print() and writes to the terminal."""
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)

    def flush(self):
        pass

    def display_prompt(self):
        """Prints the prompt and sets the write-protection marker."""
        cwd = os.getcwd()
        prompt = f"\ncosmic-sh [{cwd}]> "
        self.terminal.insert(tk.END, prompt)
        
        # Place an invisible marker exactly after the prompt
        self.terminal.mark_set("input_start", "end-1c")
        self.terminal.mark_gravity("input_start", tk.LEFT)
        self.terminal.see(tk.END)

    def handle_backspace(self, event):
        """Prevents backspacing into the prompt."""
        if self.terminal.index(tk.INSERT) <= self.terminal.index("input_start"):
            return "break" # 'break' tells tkinter to cancel the keystroke

    def handle_left(self, event):
        """Prevents left arrow from going into the prompt."""
        if self.terminal.index(tk.INSERT) <= self.terminal.index("input_start"):
            return "break"
            
    def handle_keypress(self, event):
        """If user clicks old text and tries to type, force cursor back to the input area."""
        if event.char and event.keysym not in ("BackSpace", "Return", "Left", "Right", "Up", "Down"):
            if self.terminal.index(tk.INSERT) < self.terminal.index("input_start"):
                self.terminal.mark_set(tk.INSERT, tk.END)

    def handle_return(self, event):
        """Grabs the text typed after the prompt and executes it."""
        # 1. Extract exactly what was typed after the invisible marker
        command = self.terminal.get("input_start", "end-1c").strip()
        
        # 2. Print a newline manually since we are blocking the default Enter key behavior
        self.terminal.insert(tk.END, "\n")
        
        # 3. Process the command if it isn't empty
        if command:
            self.execute_command(command)
            
        # 4. Show the next prompt
        self.display_prompt()
        
        # 5. Block the default tkinter Enter key behavior
        return "break" 

    # --- YOUR EXECUTION LOGIC ---

    def execute_command(self, choice):
        """Runs the parsed command."""
        path = None
        if ">" in choice:
            parts = choice.split(">", 1)
            choice = parts[0].strip()
            path = parts[1].strip()

        tokens = tokenize(choice)
        if not tokens:
            return

        if tokens[0] == "exit":
            self.root.quit() 
        
        elif tokens[0] == "cd":
            if len(tokens) > 1:
                try:
                    os.chdir(tokens[1])
                except FileNotFoundError: 
                    print("Directory not found")
            else:
                print("cd: missing argument")
        
        elif tokens[0] == "echo":
            print(" ".join(tokens[1:]))
            
        else:
            try:
                if "|" in choice:
                    left_str, right_str = choice.split("|", 1)
                    left_tokens = tokenize(left_str.strip())
                    right_tokens = tokenize(right_str.strip())
                    
                    # INJECTED: cmd /c allows built-in Windows commands to pipe
                    p1 = subprocess.Popen(["cmd", "/c"] + left_tokens, stdout=subprocess.PIPE)
                    
                    if path:
                        with open(path, "w") as f:
                            p2 = subprocess.Popen(["cmd", "/c"] + right_tokens, stdin=p1.stdout, stdout=f)
                            p1.stdout.close()
                            p2.communicate()
                    else:
                        p2 = subprocess.Popen(["cmd", "/c"] + right_tokens, stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
                        p1.stdout.close()
                        out, err = p2.communicate()
                        
                        if out: print(out, end="")
                        if err: print(err, end="")

                else:
                    if path:
                        with open(path, "w") as f:
                            subprocess.run(["cmd", "/c"] + tokens, stdout=f)
                    else:
                        # INJECTED: cmd /c allows standard built-in Windows commands
                        result = subprocess.run(["cmd", "/c"] + tokens, capture_output=True, text=True)
                        if result.stdout:
                            print(result.stdout, end="")
                        if result.stderr:
                            print(result.stderr, end="")
                            
            except FileNotFoundError:
                print("Command not found")
            except Exception as e:
                print(f"System Error: {str(e)}")



# --- OS-Level DPI Awareness (Fixes blurry fonts on high-res screens) ---
try:
    # Tells Windows 8.1/10/11 to render fonts crisply
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    # Fails gracefully on older Windows versions or Linux
    pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalEmulator(root)
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalEmulator(root)
    root.mainloop()