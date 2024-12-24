import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
from PIL import Image, ImageTk

class SantaUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Santa Claus Problem Demo")
        self.geometry("950x600")

        # -----------------------------
        # State variables
        # -----------------------------
        self.reindeer_count = 0
        self.elf_count = 0
        self.angle = 0  # for "spinning wheel"
        self.output_queue = queue.Queue()  # For backend output

        # Bouncing animation
        self.bounce_offset = 0
        self.bounce_direction = 1
        self.max_bounce = 3  # Reduced from 10 to 3 pixels for subtler movement

        # -----------------------------
        # UI Elements
        # -----------------------------
        self.main_canvas = tk.Canvas(self, width=950, height=600)
        self.main_canvas.grid(row=0, column=0, rowspan=4, columnspan=3, sticky="nsew")

        # Load background image
        self.background_image = ImageTk.PhotoImage(
            Image.open("images/background.png").resize((950, 600))
        )
        self.main_canvas.create_image(0, 0, image=self.background_image, anchor="nw")

        #
        # Center area: bed (left) and santa (right)
        #
        self.bed_x = 220   # Store as instance variable
        self.bed_y = 200   # Already stored as instance variable
        santa_x = 450
        santa_y = 150

        # Bed
        self.bed_img = ImageTk.PhotoImage(
            Image.open("images/bed.png").convert("RGBA").resize((180, 180))
        )
        self.main_canvas.create_image(self.bed_x, self.bed_y, image=self.bed_img, anchor="nw")

        # Santa (bigger) - adjusted position to be on top of bed
        original_santa = Image.open("images/santa.png").convert("RGBA")
        aspect_ratio = original_santa.width / original_santa.height
        new_height = 220
        new_width = int(new_height * aspect_ratio)
        # Rotate santa slightly clockwise (positive angle)
        rotated_santa = original_santa.resize((new_width, new_height)).rotate(45, expand=True)
        self.santa_img = ImageTk.PhotoImage(rotated_santa)
        self.main_canvas.create_image(self.bed_x - 10, self.bed_y - 110, image=self.santa_img, anchor="nw")

        # Store santa's original image and canvas ID
        self.original_santa = original_santa
        self.santa_canvas_id = self.main_canvas.create_image(self.bed_x - 10, self.bed_y - 110, 
                                                            image=self.santa_img, anchor="nw")

        #
        # Bottom center: console
        #
        console_width = 500
        console_height = 120
        console_x = (950 - console_width) // 2
        console_y = 600 - console_height - 10
        self.txt_console = tk.Text(
            self,
            height=5,
            width=40,
            bg="#8B4513",
            fg="white",
            font=("Comic Sans MS", 12, "bold"),
            relief="solid",
            bd=2,
            highlightbackground="black",
            highlightthickness=2
        )
        self.txt_console.place(x=console_x, y=console_y, width=console_width, height=console_height)

        # Add sample text
        self.txt_console.insert(tk.END, "[Test] Console initialized.\n")
        self.txt_console.insert(tk.END, "[Santa] Ho-ho-ho! Starting the simulation...\n")
        self.txt_console.see(tk.END)

        #
        # Above console, center: "Making presents" text
        #
        label_x = 615
        label_y = console_y - 20
        self.lbl_spinner_text = tk.Label(
            self, 
            text="Making presents", 
            font=("Comic Sans MS", 14, "bold"), 
            fg="white", 
            bg="#8B4513", 
            relief="solid", 
            bd=2,
            padx=10,
            pady=5
        )
        self.lbl_spinner_text.place(x=label_x, y=label_y, anchor="center")

        #
        # Spinner above "Making presents" text
        #
        self.spinner_center_x = 615    # Changed from 625 to 615 (moved left 10px)
        self.spinner_center_y = label_y - 70

        self.spinner_base = Image.open("images/spinner.png").resize((80, 80)).convert("RGBA")
        self.spinner_imgTK = ImageTk.PhotoImage(self.spinner_base)

        # Brown background square for spinner
        self.spinner_bg = self.main_canvas.create_rectangle(
            self.spinner_center_x - 50, self.spinner_center_y - 50,
            self.spinner_center_x + 50, self.spinner_center_y + 50,
            fill='#8B4513',
            outline='black',
            width=2,
            tags='spinner_bg'
        )
        self.spinner_id = self.main_canvas.create_image(
            self.spinner_center_x, self.spinner_center_y,
            image=self.spinner_imgTK,
            anchor="center"
        )

        #
        # Left side: Reindeer
        #
        reindeer_x = 20
        reindeer_y = 380
        original_reindeer = Image.open("images/reindeer.png").convert("RGBA")
        reindeer_aspect_ratio = original_reindeer.width / original_reindeer.height
        reindeer_height = 180
        reindeer_width = int(reindeer_height * reindeer_aspect_ratio)
        self.reindeer_img = ImageTk.PhotoImage(original_reindeer.resize((reindeer_width, reindeer_height)))
        self.main_canvas.create_image(reindeer_x, reindeer_y, image=self.reindeer_img, anchor="nw")

        # Reindeer bar graph
        bar_width = 50
        bar_height = 200
        reindeer_bar_x = reindeer_x + (reindeer_width / 2) - (bar_width / 2)
        # Move bar higher up, now 180px above reindeer (was 120px)
        reindeer_bar_y = reindeer_y - 180

        self.canvas_reindeer = tk.Canvas(
            self, width=bar_width, height=bar_height, 
            bg='#8B4513', 
            highlightbackground='black', 
            highlightthickness=0
        )
        self.canvas_reindeer.place(x=reindeer_bar_x, y=reindeer_bar_y)

        # Outline rectangle
        self.canvas_reindeer.create_rectangle(
            0, 0, bar_width, bar_height,
            outline="black",
            width=3,
            tags="outline"
        )

        # Reindeer count label (adjust to maintain same relative position above bar)
        label_reindeer_y = reindeer_bar_y - 30
        self.lbl_reindeer_count = tk.Label(
            self, 
            text="Reindeer: 0", 
            font=("Comic Sans MS", 12, "bold"), 
            fg="white", 
            bg="#8B4513", 
            relief="solid", 
            bd=2, 
            padx=10, 
            pady=5
        )
        self.lbl_reindeer_count.place(
            x=reindeer_bar_x + bar_width/2, 
            y=label_reindeer_y, 
            anchor="center"
        )

        #
        # Right side: Elf
        #
        elf_x = 780
        elf_y = 380
        original_elf = Image.open("images/elf.png").convert("RGBA")
        elf_aspect_ratio = original_elf.width / original_elf.height
        elf_height = 180
        elf_width = int(elf_height * elf_aspect_ratio)
        self.elf_img = ImageTk.PhotoImage(original_elf.resize((elf_width, elf_height)))
        self.main_canvas.create_image(elf_x, elf_y, image=self.elf_img, anchor="nw")

        # Elf bar graph
        elf_bar_x = elf_x + (elf_width / 2) - (bar_width / 2)
        # Move bar higher up, now 180px above elf (was 120px)
        elf_bar_y = elf_y - 180

        self.canvas_elf = tk.Canvas(
            self, width=bar_width, height=bar_height, 
            bg='#8B4513', 
            highlightbackground='black', 
            highlightthickness=0
        )
        self.canvas_elf.place(x=elf_bar_x, y=elf_bar_y)

        self.canvas_elf.create_rectangle(
            0, 0, bar_width, bar_height,
            outline="black",
            width=3,
            tags="outline"
        )

        # Elf count label (adjust to maintain same relative position)
        label_elf_y = elf_bar_y - 30
        self.lbl_elf_count = tk.Label(
            self, 
            text="Elves: 0", 
            font=("Comic Sans MS", 12, "bold"), 
            fg="white", 
            bg="#8B4513", 
            relief="solid", 
            bd=2, 
            padx=10, 
            pady=5
        )
        self.lbl_elf_count.place(
            x=elf_bar_x + bar_width/2, 
            y=label_elf_y, 
            anchor="center"
        )

        # Create (but don't place) the wake text label
        self.wake_label = tk.Label(
            self, 
            text="Who has woken me?", 
            font=("Comic Sans MS", 14, "bold"), 
            fg="black", 
            bg="white", 
            relief="solid", 
            bd=2
        )

        # Create and place the sleeping "ZZZ" label
        self.sleep_label = tk.Label(
            self, 
            text="Z.Z.z.z...", 
            font=("Comic Sans MS", 14, "bold"), 
            fg="black", 
            bg="white", 
            relief="solid", 
            bd=2,
            padx=5,
            pady=2
        )
        self.sleep_label.place(x=self.bed_x + 160, y=self.bed_y - 30, anchor="s")

        # -----------------------------
        # Start C++ process in a thread
        # -----------------------------
        self.proc_thread = threading.Thread(target=self.run_cpp_program, daemon=True)
        self.proc_thread.start()
        
        # Periodically check the queue
        self.after(100, self.process_output_queue)
        
        # Periodically rotate the spinner
        self.after(50, self.update_spinner)

    def update_bar_graph(self, canvas, count, max_count):
        """
        Update a vertical bar graph on the given canvas based on the count.
        """
        canvas.delete("bar")
        height = 200  # same as the canvas
        bar_height = int((count / max_count) * height)
        bar_color = "red" if canvas == self.canvas_reindeer else "green"
        
        canvas.create_rectangle(
            0, height - bar_height, 50, height,
            fill=bar_color,
            width=3,
            outline="black",
            tags="bar"
        )

    def run_cpp_program(self):
        """
        Launch the compiled C++ binary as a subprocess and capture its output.
        """
        cmd = ["./santa"]  # Ensure the binary path is correct
        self.txt_console.insert(tk.END, "[Info] Starting C++ binary...\n")
        self.txt_console.see(tk.END)
        try:
            with subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
            ) as proc:
                for line in proc.stdout:
                    self.output_queue.put(line.strip())
                for error_line in proc.stderr:
                    self.output_queue.put(f"[Error] {error_line.strip()}")
        except FileNotFoundError:
            self.output_queue.put("[Error] C++ binary not found. Check './santa'.\n")
        except Exception as e:
            self.output_queue.put(f"[Error] Failed to start C++ binary: {str(e)}\n")

    def process_output_queue(self):
        """
        Read from the output queue, update the console, and pass lines to handle_cpp_output.
        """
        while not self.output_queue.empty():
            line = self.output_queue.get_nowait()
            self.txt_console.insert(tk.END, line + "\n")
            self.txt_console.see(tk.END)
            self.handle_cpp_output(line)

        self.after(100, self.process_output_queue)

    def handle_cpp_output(self, line):
        """
        Parse output from the C++ backend and update the GUI.
        """
        if "[Santa] All reindeer have arrived! Preparing the sleigh..." in line or \
           "[Santa] 3 elves need help. Letting them in..." in line:
            # Move Santa to working position (upright, further right)
            new_height = 220
            new_width = int(new_height * (self.original_santa.width / self.original_santa.height))
            upright_santa = self.original_santa.resize((new_width, new_height))
            self.santa_img = ImageTk.PhotoImage(upright_santa)
            self.main_canvas.itemconfig(self.santa_canvas_id, image=self.santa_img)
            self.main_canvas.coords(self.santa_canvas_id, 450, self.bed_y - 110)  # Move right
            
            # Show the wake text label and hide the sleep label
            self.wake_label.place(x=535, y=self.bed_y - 80, anchor="s")
            self.sleep_label.place_forget()

        elif "[Santa] Done delivering toys; back to sleep!" in line or \
             "[Santa] Done helping these elves!" in line:
            # Return Santa to sleeping position (rotated, on bed)
            new_height = 220
            new_width = int(new_height * (self.original_santa.width / self.original_santa.height))
            rotated_santa = self.original_santa.resize((new_width, new_height)).rotate(45, expand=True)
            self.santa_img = ImageTk.PhotoImage(rotated_santa)
            self.main_canvas.itemconfig(self.santa_canvas_id, image=self.santa_img)
            self.main_canvas.coords(self.santa_canvas_id, self.bed_x - 10, self.bed_y - 110)  # Original position
            
            # Hide the wake text label and show the sleep label
            self.wake_label.place_forget()
            self.sleep_label.place(x=self.bed_x + 160, y=self.bed_y - 30, anchor="s")

        if "[Reindeer" in line and "Returned. ReindeerCount=" in line:
            parts = line.split("ReindeerCount=")
            if len(parts) > 1:
                try:
                    self.reindeer_count = int(parts[1])
                    self.lbl_reindeer_count.config(text=f"Reindeer: {self.reindeer_count}")
                    self.update_bar_graph(self.canvas_reindeer, self.reindeer_count, 9)
                except ValueError:
                    pass

        # New handler for reindeer going on vacation
        elif "[Reindeer" in line and "Going back on vacation..." in line:
            self.reindeer_count = max(0, self.reindeer_count - 1)  # Ensure we don't go below 0
            self.lbl_reindeer_count.config(text=f"Reindeer: {self.reindeer_count}")
            self.update_bar_graph(self.canvas_reindeer, self.reindeer_count, 9)

        elif "[Elf" in line and "Has a problem! ElfCount=" in line:
            parts = line.split("ElfCount=")
            if len(parts) > 1:
                try:
                    self.elf_count = int(parts[1])
                    self.lbl_elf_count.config(text=f"Elves: {self.elf_count}")
                    self.update_bar_graph(self.canvas_elf, self.elf_count, 3)
                except ValueError:
                    pass

        elif "[Santa] Done helping these elves!" in line:
            # Return Santa to sleeping position (rotated, on bed)
            new_height = 220
            new_width = int(new_height * (self.original_santa.width / self.original_santa.height))
            rotated_santa = self.original_santa.resize((new_width, new_height)).rotate(45, expand=True)
            self.santa_img = ImageTk.PhotoImage(rotated_santa)
            self.main_canvas.itemconfig(self.santa_canvas_id, image=self.santa_img)
            self.main_canvas.coords(self.santa_canvas_id, self.bed_x - 10, self.bed_y - 110)  # Original position
            
            # Hide the wake text label
            self.wake_label.place_forget()
            
            # Reset elf count and update UI
            self.elf_count = 0
            self.lbl_elf_count.config(text="Elves: 0")
            self.update_bar_graph(self.canvas_elf, self.elf_count, 3)

    def update_spinner(self):
        """
        Rotate the spinner image and add a stretch/squish effect.
        """
        # Rotate
        self.angle = (self.angle - 15) % 360
        rotated = self.spinner_base.rotate(self.angle, expand=True)
        self.spinner_imgTK = ImageTk.PhotoImage(rotated)

        # Stretching/squishing
        self.bounce_offset += self.bounce_direction
        if abs(self.bounce_offset) >= self.max_bounce:
            self.bounce_direction *= -1
        
        # The base dimensions
        base_size = 100  # 50 pixels on each side of center
        height_adjustment = self.bounce_offset * 2  # Multiply by 2 to make the effect more visible

        # Calculate new coordinates for the background rectangle
        new_x1 = self.spinner_center_x - base_size/2
        new_y1 = self.spinner_center_y - base_size/2 - height_adjustment  # Only adjust top edge
        new_x2 = self.spinner_center_x + base_size/2
        new_y2 = self.spinner_center_y + base_size/2  # Bottom edge stays fixed

        # Move the background rectangle
        self.main_canvas.coords(self.spinner_bg, new_x1, new_y1, new_x2, new_y2)
        # Keep the spinner image centered
        self.main_canvas.coords(self.spinner_id, self.spinner_center_x, self.spinner_center_y)

        self.main_canvas.itemconfig(self.spinner_id, image=self.spinner_imgTK)

        # Next update
        self.after(50, self.update_spinner)

if __name__ == "__main__":
    app = SantaUI()
    app.mainloop()
