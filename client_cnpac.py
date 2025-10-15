import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import random
class BingoClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Bingo Game")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.geometry("800x600")
        
        self.card = [[0]*5 for _ in range(5)]
        self.marked = [[False]*5 for _ in range(5)]
        self.sock = None
        self.game_active = False
        self.setup_phase = True
        self.available_numbers = list(range(1, 26))
        self.called_numbers = []
        self.current_turn = None
        
        self.create_setup_ui()
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(("localhost", 1234))
            self.status_var.set("Connected to server. Please enter your card.")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")
            self.master.destroy()
    def create_setup_ui(self):
        self.setup_frame = tk.Frame(self.master)
        self.setup_frame.pack(padx=20, pady=10)
        
        instructions = tk.Label(
            self.setup_frame, 
            text="Enter numbers 1-25 (no duplicates)",
            font=("Arial", 12)
        )
        instructions.grid(row=0, column=0, columnspan=5, pady=(0, 10))
        
        self.entries = []
        for row in range(5):
            row_entries = []
            for col in range(5):
                entry = tk.Entry(
                    self.setup_frame,
                    width=4,
                    font=("Arial", 16, "bold"),
                    justify='center'
                )
                entry.grid(row=row+1, column=col, padx=5, pady=5)
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Enter your 5x5 Bingo card")
        status_label = tk.Label(
            self.master, 
            textvariable=self.status_var,
            font=("Arial", 12)
        )
        status_label.pack(pady=10)
        
        self.submit_btn = tk.Button(
            self.master,
            text="Submit Card & Start Game",
            font=("Arial", 12, "bold"),
            command=self.submit_card
        )
        self.submit_btn.pack(pady=10)
        
        self.random_btn = tk.Button(
            self.master,
            text="Fill with Random Numbers",
            font=("Arial", 12),
            command=self.fill_random
        )
        self.random_btn.pack(pady=5)
    def create_game_ui(self):
        self.game_frame = tk.Frame(self.master)
        self.game_frame.pack(padx=20, pady=10)
        
        self.card_labels = []
        for row in range(5):
            row_labels = []
            for col in range(5):
                label = tk.Label(
                    self.game_frame,
                    text=str(self.card[row][col]),
                    width=4,
                    height=2,
                    font=("Arial", 16, "bold"),
                    relief="ridge",
                    bg="white"
                )
                label.grid(row=row, column=col, padx=5, pady=5)
                row_labels.append(label)
            self.card_labels.append(row_labels)
        
        self.turn_var = tk.StringVar()
        self.turn_var.set("Waiting for game to start...")
        turn_label = tk.Label(
            self.master, 
            textvariable=self.turn_var,
            font=("Arial", 14, "bold")
        )
        turn_label.pack(pady=10)
        
        self.last_number_var = tk.StringVar()
        self.last_number_var.set("No numbers called yet")
        last_number_label = tk.Label(
            self.master, 
            textvariable=self.last_number_var,
            font=("Arial", 12)
        )
        last_number_label.pack(pady=5)
        
        self.call_frame = tk.Frame(self.master)
        self.call_frame.pack(pady=10)
        
        call_label = tk.Label(
            self.call_frame,
            text="Call a number:",
            font=("Arial", 12)
        )
        call_label.grid(row=0, column=0, padx=5)
        
        self.call_entry = tk.Entry(
            self.call_frame,
            width=3,
            font=("Arial", 14)
        )
        self.call_entry.grid(row=0, column=1, padx=5)
        
        self.call_btn = tk.Button(
            self.call_frame,
            text="Call",
            font=("Arial", 12),
            command=self.call_number,
            state=tk.DISABLED
        )
        self.call_btn.grid(row=0, column=2, padx=5)
        
        self.bingo_btn = tk.Button(
            self.master,
            text="BINGO",
            font=("Arial", 16, "bold"),
            bg="light green",
            command=self.declare_bingo
        )
        self.bingo_btn.pack(pady=10)
        
        called_label = tk.Label(
            self.master,
            text="Called Numbers:",
            font=("Arial", 12)
        )
        called_label.pack(pady=(10, 5))
        
        self.called_var = tk.StringVar()
        self.called_var.set("None")
        called_numbers_label = tk.Label(
            self.master,
            textvariable=self.called_var,
            font=("Arial", 10),
            wraplength=700
        )
        called_numbers_label.pack()
    def fill_random(self):
        numbers = random.sample(range(1, 26), 25)
        idx = 0
        for row in range(5):
            for col in range(5):
                self.entries[row][col].delete(0, tk.END)
                self.entries[row][col].insert(0, str(numbers[idx]))
                idx += 1
    def submit_card(self):
        try:
            card_numbers = set()
            for row in range(5):
                for col in range(5):
                    try:
                        num = int(self.entries[row][col].get().strip())
                        if num < 1 or num > 25:
                            raise ValueError(f"Invalid number at row {row+1}, column {col+1}")
                        if num in card_numbers:
                            raise ValueError(f"Duplicate number {num}")
                        self.card[row][col] = num
                        card_numbers.add(num)
                    except ValueError as e:
                        messagebox.showerror("Input Error", str(e))
                        return
            
            self.sock.sendall(json.dumps(self.card).encode('utf-8'))
            self.status_var.set("Card submitted. Waiting for server...")
            self.submit_btn.config(state=tk.DISABLED)
            self.random_btn.config(state=tk.DISABLED)
            threading.Thread(target=self.listen_to_server, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit card: {str(e)}")
    def listen_to_server(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    self.master.after(0, self.show_disconnect_message)
                    break
                
                buffer += data
                messages = buffer.split('\n')
                buffer = messages.pop()
                
                for message in messages:
                    self.master.after(0, self.process_server_message, message)
                    
            except ConnectionError:
                self.master.after(0, self.show_disconnect_message)
                break
            except Exception as e:
                break
    def process_server_message(self, message):
        if message == "CARD_ACCEPTED":
            self.status_var.set("Card accepted by server")
        elif message == "COMPUTER_READY":
            self.setup_phase = False
            self.game_active = True
            self.setup_frame.destroy()
            self.create_game_ui()
        elif message.startswith("TURN:"):
            player = message.split(":")[1]
            self.current_turn = player
            if player == "human":
                self.turn_var.set("YOUR TURN - Call a number")
                self.call_btn.config(state=tk.NORMAL)
            else:
                self.turn_var.set("COMPUTER'S TURN - Please wait")
                self.call_btn.config(state=tk.DISABLED)
        elif message.startswith("NUMBER:"):
            number = int(message.split(":")[1])
            self.last_number_var.set(f"Last number called: {number}")
            self.called_numbers.append(number)
            self.called_var.set(", ".join(map(str, self.called_numbers)))
            if number in self.available_numbers:
                self.available_numbers.remove(number)
            for row in range(5):
                for col in range(5):
                    if self.card[row][col] == number:
                        self.marked[row][col] = True
                        if hasattr(self, 'card_labels'):
                            self.card_labels[row][col].config(bg="light green")
        elif message == "HUMAN_WINS":
            messagebox.showinfo("Game Over", "YOU WIN!")
            self.game_active = False
            self.turn_var.set("GAME OVER - You won!")
            self.call_btn.config(state=tk.DISABLED)
            self.bingo_btn.config(state=tk.DISABLED)
        elif message == "COMPUTER_WINS":
            messagebox.showinfo("Game Over", "Computer won.")
            self.game_active = False
            self.turn_var.set("GAME OVER - Computer won")
            self.call_btn.config(state=tk.DISABLED)
            self.bingo_btn.config(state=tk.DISABLED)
        elif message.startswith("ERROR:"):
            error_msg = message.split(":", 1)[1]
            messagebox.showerror("Error", error_msg)
    def call_number(self):
        if self.current_turn != "human" or not self.game_active:
            return
        try:
            number = int(self.call_entry.get().strip())
            if number < 1 or number > 25:
                messagebox.showerror("Invalid Number", "Enter number between 1 and 25")
                return
            if number in self.called_numbers:
                messagebox.showerror("Invalid Call", f"Number {number} already called")
                return
            self.sock.sendall(f"CALL:{number}".encode('utf-8'))
            self.call_entry.delete(0, tk.END)
            self.call_btn.config(state=tk.DISABLED)
        except ValueError:
            messagebox.showerror("Input Error", "Enter a valid number")
    def declare_bingo(self):
        if not self.game_active:
            return
        if self.check_bingo():
            self.sock.sendall(b"BINGO")
        else:
            messagebox.showerror("Invalid Bingo", "No valid Bingo pattern yet")
    def check_bingo(self):
        for row in self.marked:
            if all(row):
                return True
        for col in range(5):
            if all(self.marked[row][col] for row in range(5)):
                return True
        if all(self.marked[i][i] for i in range(5)) or all(self.marked[i][4-i] for i in range(5)):
            return True
        return False
    def show_disconnect_message(self):
        messagebox.showerror("Disconnected", "Lost connection to server")
        self.game_active = False
        self.on_close()
    def on_close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.master.destroy()
if __name__ == "__main__":
    root = tk.Tk()
    app = BingoClient(root)
    root.mainloop()
