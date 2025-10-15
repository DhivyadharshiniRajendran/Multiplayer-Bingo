import socket
import threading
import json
import random
import time
human_client = None
human_card = None
human_marked = [[False]*5 for _ in range(5)]
computer_card = None
computer_marked = [[False]*5 for _ in range(5)]
called_numbers = set()
winner_declared = False
lock = threading.Lock()
current_turn = "human"
def generate_computer_card():
    numbers = random.sample(range(1, 26), 25)
    return [numbers[i*5:(i+1)*5] for i in range(5)]
def check_bingo(marked):
    for row in marked:
        if all(row):
            return True
    for col in range(5):
        if all(marked[row][col] for row in range(5)):
            return True
    if all(marked[i][i] for i in range(5)) or all(marked[i][4-i] for i in range(5)):
        return True
    return False
def send_to_human(message):
    global human_client
    if human_client:
        try:
            human_client.send((message + "\n").encode('utf-8'))
        except:
            pass
def handle_human_client(client_socket):
    global human_client, human_card, human_marked, winner_declared, current_turn, computer_card, computer_marked, called_numbers
    try:
        human_client = client_socket
        card_data = client_socket.recv(4096).decode('utf-8').strip()
        if not card_data:
            raise ValueError("Empty card data received")
        human_card = json.loads(card_data)
        if not isinstance(human_card, list) or len(human_card) != 5 or any(len(row) != 5 for row in human_card):
            raise ValueError("Invalid card format")
        all_numbers = []
        for row in human_card:
            all_numbers.extend(row)
        if len(set(all_numbers)) != 25 or any(num < 1 or num > 25 for num in all_numbers):
            raise ValueError("Card must contain unique numbers from 1 to 25")
        computer_card = generate_computer_card()
        send_to_human("CARD_ACCEPTED")
        send_to_human("COMPUTER_READY")
        send_to_human("TURN:human")
        while not winner_declared:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if message.startswith("CALL:"):
                    number = int(message.split(":")[1])
                    if number < 1 or number > 25:
                        send_to_human("ERROR:Invalid number (must be 1-25)")
                        continue
                    if number in called_numbers:
                        send_to_human("ERROR:Number already called")
                        continue
                    with lock:
                        called_numbers.add(number)
                        send_to_human(f"NUMBER:{number}")
                        for row in range(5):
                            for col in range(5):
                                if human_card[row][col] == number:
                                    human_marked[row][col] = True
                        for row in range(5):
                            for col in range(5):
                                if computer_card[row][col] == number:
                                    computer_marked[row][col] = True
                        if check_bingo(human_marked):
                            winner_declared = True
                            send_to_human("HUMAN_WINS")
                            break
                        if check_bingo(computer_marked):
                            winner_declared = True
                            send_to_human("COMPUTER_WINS")
                            break
                        current_turn = "computer"
                        send_to_human("TURN:computer")
                        time.sleep(1.5)
                        available_numbers = list(set(range(1, 26)) - called_numbers)
                        if available_numbers:
                            computer_number = random.choice(available_numbers)
                            called_numbers.add(computer_number)
                            send_to_human(f"NUMBER:{computer_number}")
                            for row in range(5):
                                for col in range(5):
                                    if computer_card[row][col] == computer_number:
                                        computer_marked[row][col] = True
                            for row in range(5):
                                for col in range(5):
                                    if human_card[row][col] == computer_number:
                                        human_marked[row][col] = True
                            if check_bingo(computer_marked):
                                winner_declared = True
                                send_to_human("COMPUTER_WINS")
                                break
                            if check_bingo(human_marked):
                                winner_declared = True
                                send_to_human("HUMAN_WINS")
                                break
                            current_turn = "human"
                            send_to_human("TURN:human")
                        else:
                            winner_declared = True
                            send_to_human("TIE_GAME")
                            break
                elif message == "BINGO":
                    with lock:
                        if not winner_declared:
                            if check_bingo(human_marked):
                                winner_declared = True
                                send_to_human("HUMAN_WINS")
                            else:
                                send_to_human("ERROR:Invalid BINGO claim - no winning pattern found")
                            break
            except json.JSONDecodeError:
                break
            except Exception as e:
                break
    except Exception as e:
        pass
    finally:
        if client_socket:
            client_socket.close()
def start_server():
    global human_client, human_card, human_marked, computer_card, computer_marked, called_numbers, current_turn, winner_declared
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 1234))
    server.listen(1)
    try:
        while True:
            client_socket, addr = server.accept()
            human_client = None
            human_card = None
            human_marked = [[False]*5 for _ in range(5)]
            computer_card = None
            computer_marked = [[False]*5 for _ in range(5)]
            called_numbers = set()
            winner_declared = False
            current_turn = "human"
            client_thread = threading.Thread(
                target=handle_human_client,
                args=(client_socket,),
                daemon=True
            )
            client_thread.start()
            while not winner_declared and human_client is not None:
                time.sleep(1)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
if __name__ == "__main__":
    start_server()
