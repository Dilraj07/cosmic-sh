import os
import subprocess
import atexit  


BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
# --- THE PERSISTENT MEMORY ENGINE ---
try:
    import readline
except ImportError:
    # If on Windows, we fall back to the library you just pip installed
    import pyreadline3 as readline

# Define a hidden file in your User directory (e.g., C:\Users\Dilraj\.cosmic_history)
histfile = os.path.join(os.path.expanduser("~"), ".cosmic_history")

# 1. Boot Sequence: Load history into RAM if the file exists
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass # First time running the shell, no file exists yet!

# 2. Shutdown Sequence: Define what happens when the shell dies
def save_history():
    """Writes the RAM buffer to the hard drive on exit."""
    readline.write_history_file(histfile)

# Tell the OS: "No matter how this script closes (exit, Ctrl+C, EOF), run save_history() first."
atexit.register(save_history)

def tokenize(command_string):
    tokens = []
    current_token = ""
    in_quotes = False
    for char in command_string:
        if char == "\"" or char == "'":
            in_quotes = not in_quotes
        elif char == " " and not in_quotes:
            if current_token:
                tokens.append(current_token)
            current_token = ""
        else:
            current_token += char
            
    if current_token:
        tokens.append(current_token)
        
    return tokens
if __name__ == "__main__":
    while True:
        try:
            current_dir = os.getcwd()
            choice = input(f"{BLUE}{current_dir}{RESET}> ").strip()

            # 1. Reset variables for this specific loop iteration
            path = None

            # 2. Safely check for redirection
            if ">" in choice:
                # Split exactly once, in case they typed multiple > by accident
                parts = choice.split(">", 1)
                choice = parts[0].strip()  # The command part
                path = parts[1].strip()    # The file name part, stripped of spaces

            tokens = tokenize(choice)

            if not tokens:
                continue

            if tokens[0] == "exit":
                break
            elif tokens[0] == "echo":
                # Note: Right now, 'echo' is handled internally by your shell,
                # so the OS redirection below won't catch it.
                # To test redirection, run an OS command like: ping 8.8.8.8 > log.txt
                print(" ".join(tokens[1:]))
            elif tokens[0] == "cd":
                if len(tokens) > 1:
                    try:
                        os.chdir(tokens[1])
                    except FileNotFoundError:
                        print("Directory not found")
                else:
                    print("cd: missing argument")
            else:
                try:
                    if "|" in choice:
                        # --- THE PIPING ENGINE ---
                        left_str, right_str = choice.split("|", 1)
                        left_tokens = tokenize(left_str.strip())
                        right_tokens = tokenize(right_str.strip())

                        # 1. Start the first process, trap its stdout
                        p1 = subprocess.Popen(left_tokens, stdout=subprocess.PIPE)

                        # 2. Start the second process, wire its stdin to p1's stdout
                        if path:
                            # If the user also used '>', wire p2's stdout to the file!
                            with open(path, "w") as f:
                                p2 = subprocess.Popen(right_tokens, stdin=p1.stdout, stdout=f)
                        else:
                            # Otherwise, let p2 print normally to the screen
                            p2 = subprocess.Popen(right_tokens, stdin=p1.stdout)

                        # 3. Close p1's stdout in Python (crucial so p2 knows when the stream ends)
                        p1.stdout.close()

                        # 4. Wait for the second process to finish
                        p2.communicate()

                    else:
                        # --- STANDARD EXECUTION (Your existing code) ---
                        if path:
                            with open(path, "w") as f:
                                subprocess.run(tokens, stdout=f)
                        else:
                            subprocess.run(tokens)

                except FileNotFoundError:
                    print(f"{RED}[Error] Command not found{RESET}")

        except KeyboardInterrupt:
            print()
            continue

        except EOFError:
            print("\nExiting cosmic-sh...")
            break
