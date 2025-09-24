import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time

class GUIInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Controle de Robô por Gestos")
        self._setup_gui()
        self.log_messages = []

    def _setup_gui(self):
        """Setup the GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Video frame (Left)
        video_frame = ttk.Frame(main_frame, borderwidth=2, relief="sunken")
        video_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=2)
        main_frame.rowconfigure(0, weight=1)
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(expand=True, fill="both")
        
        # Info frame (Right)
        info_frame = ttk.Frame(main_frame, padding="10")
        info_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)

        # Instructions
        self._create_instructions(info_frame)
        # Status display
        self._create_status_display(info_frame)
        # Log display
        self._create_log_display(info_frame)

    def _create_instructions(self, parent):
        """Create instructions section"""
        instr_label = ttk.Label(parent, text="Instruções", font=("Helvetica", 14, "bold"))
        instr_label.pack(anchor="w", pady=(0, 5))
        
        instr_text = (
            "1. Mão Aberta (Open): Segure por 3s para HABILITAR.\n\n"
            "2. Mão Fechada (Close): Segure por 3s para DESABILITAR.\n\n"
            "3. Gesto Dinâmico (CW/CCW): Seleciona o programa.\n\n"
            "4. Manter Gesto Dinâmico: Confirma e executa o programa."
        )
        instr_message = ttk.Label(parent, text=instr_text, justify=tk.LEFT)
        instr_message.pack(anchor="w", pady=(0, 20), fill="x")

    def _create_status_display(self, parent):
        """Create status display section"""
        status_label = ttk.Label(parent, text="Status do Sistema", font=("Helvetica", 14, "bold"))
        status_label.pack(anchor="w", pady=(0, 5))
        
        self.status_vars = {
            "Estado": tk.StringVar(value="DISABLED"),
            "Gesto Estático": tk.StringVar(value="N/A"),
            "Gesto Dinâmico": tk.StringVar(value="N/A"),
            "Seleção Pendente": tk.StringVar(value="N/A"),
        }
        
        for name, var in self.status_vars.items():
            frame = ttk.Frame(parent)
            frame.pack(fill='x', pady=1)
            label_name = ttk.Label(frame, text=f"{name}:", width=18, anchor='w')
            label_name.pack(side='left')
            label_value = ttk.Label(frame, textvariable=var, anchor='w')
            label_value.pack(side='left')

    def _create_log_display(self, parent):
        """Create log display section"""
        log_label = ttk.Label(parent, text="Log de Eventos", font=("Helvetica", 14, "bold"))
        log_label.pack(anchor="w", pady=(20, 5))
        
        log_frame = ttk.Frame(parent)
        log_frame.pack(expand=True, fill="both")
        self.log_text = tk.Text(log_frame, height=15, width=50, state="disabled")
        self.log_text.pack(side="left", expand=True, fill="both")
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.log_messages.append(f"[{timestamp}] {message}")

    def update_display(self, image, state, static_gesture, dynamic_gesture, pending_selection, log_messages):
        """Update the GUI display"""
        # Update status variables
        self.status_vars["Estado"].set(state)
        self.status_vars["Gesto Estático"].set(static_gesture if static_gesture else "N/A")
        self.status_vars["Gesto Dinâmico"].set(dynamic_gesture if dynamic_gesture else "N/A")
        self.status_vars["Seleção Pendente"].set(pending_selection if pending_selection else "N/A")
        
        # Update video feed
        img = Image.fromarray(image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)
        
        # Update log messages
        for message in log_messages:
            if message not in self.log_messages:
                self.log_message(message.replace("[timestamp] ", ""))

    def set_on_closing_callback(self, callback):
        """Set callback for window closing"""
        self.root.protocol("WM_DELETE_WINDOW", callback)

    def cleanup(self):
        """Cleanup GUI resources"""
        self.root.destroy()

    def get_log_messages(self):
        """Get current log messages"""
        return self.log_messages.copy()