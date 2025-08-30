import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import os
from PIL import Image, ImageTk  # For handling logo image

try:
    # pyright: ignore[reportMissingImports] # For desktop notifications
    from plyer import notification  # type: ignore
except ImportError:
    notification = None

try:
    from playsound import playsound  # For custom sound
except ImportError:
    playsound = None


class CountdownTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("ChronoMate")
        # Place window at top-left corner (0,0)
        self.root.geometry("525x699+0+0")
        self.root.resizable(False, False)

        self.time_left = 0
        self.running = False
        self.paused = False
        self.dark_mode = False
        self.custom_sound = None  # Stores custom alarm sound path

        # ================= Header with Logo, Title, Tagline =================
        header_frame = tk.Frame(root, bg="white")
        header_frame.pack(pady=10)

        try:
            logo_img = Image.open("Logo.png")
            logo_img = logo_img.resize(
                (303, 303), Image.LANCZOS)  # Increased size
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header_frame, image=self.logo, bg="white")
            logo_label.pack()
        except Exception as e:
            print(f"⚠ Error loading logo: {e}")
            logo_label = tk.Label(header_frame, text="⏰",
                                  font=("Times New Roman", 40), bg="white")
            logo_label.pack()

        # ================= Input =================
        self.label = tk.Label(root, text="Enter Time:",
                              font=("Times New Roman", 12))
        self.label.pack(pady=5)

        self.entry = tk.Entry(root, font=(
            "Times New Roman", 12), justify="center")
        self.entry.pack(pady=5)

        # Choice for time unit (minutes or seconds)
        self.unit_choice = tk.StringVar(value="Minutes")
        self.unit_menu = ttk.Combobox(
            root,
            textvariable=self.unit_choice,
            values=["Minutes", "Seconds"],
            state="readonly",
            width=10,
        )
        self.unit_menu.pack(pady=5)

        # Time display
        self.time_display = tk.Label(
            root, text="00:00", font=("Times New Roman", 32, "bold"))
        self.time_display.pack(pady=10)

        # Progress bar
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.progress = ttk.Progressbar(root, length=320, mode="determinate")
        self.progress.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.start_btn = tk.Button(
            button_frame, text="▶ Start", command=self.start_timer, width=8
        )
        self.start_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = tk.Button(
            button_frame, text="⏸ Pause", command=self.pause_timer, state="disabled", width=8
        )
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.resume_btn = tk.Button(
            button_frame, text="▶ Resume", command=self.resume_timer, state="disabled", width=8
        )
        self.resume_btn.grid(row=0, column=2, padx=5)

        self.reset_btn = tk.Button(
            button_frame, text="🔄 Reset", command=self.reset_timer, state="disabled", width=8
        )
        self.reset_btn.grid(row=0, column=3, padx=5)

        # Dark mode toggle
        self.toggle_btn = tk.Button(
            root, text="🌙 Dark Mode", command=self.toggle_mode, width=15)
        self.toggle_btn.pack(pady=5)

        # Choose custom sound button
        self.sound_btn = tk.Button(
            root, text="🎵 Choose Alarm Sound", command=self.choose_sound, width=20
        )
        self.sound_btn.pack(pady=5)

        # Label to show selected sound
        self.sound_label = tk.Label(
            root, text="Default Buzzer", font=("Times New Roman", 10))
        self.sound_label.pack(pady=5)

        # Apply initial theme
        self.apply_theme()

    def apply_theme(self):
        """Apply light or dark mode theme dynamically"""
        if self.dark_mode:
            bg_color = "#1e1e1e"
            fg_color = "#ffffff"
            btn_bg = "#333333"
            btn_fg = "#ffffff"
            bar_color = "#4caf50"
            self.toggle_btn.config(text="☀ Light Mode")
        else:
            bg_color = "#ffffff"
            fg_color = "#000000"
            btn_bg = "#f0f0f0"
            btn_fg = "#000000"
            bar_color = "#0078d7"
            self.toggle_btn.config(text="🌙 Dark Mode")

        self.root.configure(bg=bg_color)
        self.label.config(bg=bg_color, fg=fg_color)
        self.entry.config(
            bg="#ffffff" if not self.dark_mode else "#555555",
            fg=fg_color,
            insertbackground=fg_color,
        )
        self.time_display.config(bg=bg_color, fg=fg_color)
        self.sound_label.config(bg=bg_color, fg=fg_color)

        for btn in [
            self.start_btn,
            self.pause_btn,
            self.resume_btn,
            self.reset_btn,
            self.toggle_btn,
            self.sound_btn,
        ]:
            btn.config(bg=btn_bg, fg=btn_fg,
                       activebackground="#666666", activeforeground="#ffffff")

        self.style.configure(
            "TProgressbar", troughcolor=bg_color, background=bar_color)

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def choose_sound(self):
        """Let user pick a custom sound file"""
        file_path = filedialog.askopenfilename(
            title="Select Alarm Sound", filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file_path:
            self.custom_sound = file_path
            self.sound_label.config(text=f"🎵 {os.path.basename(file_path)}")

    def update_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.time_display.config(text=f"{mins:02}:{secs:02}")
        if self.total_time > 0:
            progress_val = (
                (self.total_time - self.time_left) / self.total_time) * 100
            self.progress["value"] = progress_val

    def countdown(self):
        while self.time_left > 0 and self.running:
            if not self.paused:
                self.time_left -= 1
                self.update_display()
                time.sleep(1)
            else:
                time.sleep(0.2)

        if self.time_left == 0 and self.running:
            self.finish_timer()

    def start_timer(self):
        try:
            value = int(self.entry.get())
            if value <= 0:
                messagebox.showerror(
                    "Error", "Please enter a number greater than 0")
                return

            # Convert to seconds if user selected minutes
            if self.unit_choice.get() == "Minutes":
                self.time_left = value * 60
            else:
                self.time_left = value

            self.total_time = self.time_left
            self.running = True
            self.paused = False
            self.update_display()

            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.reset_btn.config(state="normal")

            threading.Thread(target=self.countdown, daemon=True).start()

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

    def pause_timer(self):
        if self.running:
            self.paused = True
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="normal")

    def resume_timer(self):
        if self.running:
            self.paused = False
            self.pause_btn.config(state="normal")
            self.resume_btn.config(state="disabled")

    def reset_timer(self):
        self.running = False
        self.paused = False
        self.time_left = 0
        self.progress["value"] = 0
        self.time_display.config(text="00:00")
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")

    def finish_timer(self):
        self.running = False
        self.time_display.config(text="00:00")
        self.progress["value"] = 100

        # Play alarm loop FIRST, then show message
        threading.Thread(target=self.alarm_and_message, daemon=True).start()

        # Desktop notification
        if notification:
            notification.notify(
                title="⏰ Timer Finished", message="Your countdown has ended!", timeout=5
            )

        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")

    def alarm_and_message(self):
        """Play alarm loop first, then show message"""
        if self.custom_sound and playsound:
            try:
                for _ in range(2):  # Play 2 times as loop
                    playsound(self.custom_sound)
            except Exception as e:
                print(f"⚠ Error playing sound: {e}")
                self.play_buzzer()
        else:
            self.play_buzzer()

        # After alarm, show warning message
        self.root.after(
            0,
            lambda: messagebox.showwarning(
                "⏰ Time's Up!", "⚠️ Timer has finished! Take a break or start next task."
            ),
        )

    def play_buzzer(self):
        """Simulate buzzer sound loop"""
        for _ in range(5):  # beep 5 times
            print("\a")
            time.sleep(0.5)


if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root)
    root.mainloop()
