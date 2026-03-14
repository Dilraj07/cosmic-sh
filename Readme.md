# Cosmic-SH: A Custom Terminal Emulator and Shell Environment

Cosmic-SH is a custom-built, UNIX-style shell and terminal emulator written entirely in Python. It bypasses standard command-line wrappers to interact directly with the Operating System kernel.

This project was engineered to demonstrate core systems architecture concepts, including lexical parsing, asynchronous process spawning, I/O memory stream manipulation, and custom GUI rendering with OS-level DPI awareness.

## System Architecture

The environment is decoupled into two primary layers: the Command Line Engine (Backend) and the Graphical Terminal Emulator (Frontend).

### Data Flow Visualization

```text
+-------------------+
|  User Keystroke   |  (Frontend GUI)
+-------------------+
         |
         v
+-------------------+
|   Lexical Parser  |  (State Machine: Strips quotes, preserves spaces)
+-------------------+
         |
         |  Tokenized Array: ['ping', 'google.com', '>', 'out.txt']
         v
+-------------------+
| Execution Routing |  (Interprets Command Type)
+-------------------+
    /      |      \
   /       |       \
[Built-in] |      [OS Execution]
(cd, exit) |      (cmd /c wrapper)
           v
+-------------------+
| Stream Management |  (Memory Routing)
+-------------------+
    /             \
[Piping ( | )]   [Redirection ( > )]
Wire p1.stdout   Wire stdout to 
to p2.stdin      File Descriptor
         \       /
          v     v
+-------------------+
| sys.stdout Hijack |  (Intercepts OS output streams)
+-------------------+
         |
         v
+-------------------+
|   GUI Renderer    |  (Displays on DPI-Aware Glassmorphism Window)
+-------------------+
```

## Core Features

### 1. The Lexical State Machine
Standard string splitting breaks when handling command-line arguments containing spaces. Cosmic-SH implements a custom lexical parser that reads user input character-by-character, toggling a boolean state to preserve spaces nested inside quotation marks.

Input:  `echo "Hello World" > log.txt`
Output: `['echo', 'Hello World', '>', 'log.txt']`

### 2. Process Spawning and Memory Piping
The shell uses Python's `subprocess` module to fork processes. 
* **Redirection (`>`):** Intercepts standard output (`stdout`) and writes the byte stream directly to a hard drive file descriptor.
* **Piping (`|`):** Utilizes `subprocess.Popen` to run two processes simultaneously in memory, hardwiring the `stdout` of the first process directly into the `stdin` of the second process without writing to the disk.

### 3. I/O Stream Hijacking
To display OS-level outputs inside a custom graphical window rather than the hidden background console, the shell reassigns `sys.stdout` and `sys.stderr` to a custom Python class. This forces all system print commands to route their text buffers into the GUI's `ScrolledText` widget.

### 4. Glassmorphism and DPI-Awareness
The frontend is built using `tkinter`. To bypass legacy Windows rendering, the application injects a C-level call to the Windows Desktop Window Manager (DWM) via `ctypes.windll.shcore.SetProcessDpiAwareness(1)`. This forces 1:1 pixel rendering for razor-sharp fonts. Translucency is achieved via OS-level alpha channel manipulation.

## Deployment & System Integration

Cosmic-SH is compiled into a standalone, console-free binary using PyInstaller. 

### Windows Explorer Integration
The executable is injected into the Windows Registry to provide native context-menu support.

[Registry Structure]
HKEY_CLASSES_ROOT
 └── Directory
      └── Background
           └── shell
                └── Cosmic
                     ├── (Default) = "Open Cosmic-SH Here"
                     ├── Icon      = "C:\Cosmic\cosmic.exe"
                     └── command
                          └── (Default) = "C:\Cosmic\cosmic.exe"