from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import sys
import ipaddress


# Continuously listens for data from the server and displays any received messages.
# This function runs in its own thread so it can listen constantly.
def receive():
    while True:
        try:
            # Wait for new data from the server and decode it to a string
            msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
            
            # Add the new message to the message list
            msg_list.insert(tkinter.END, msg)
            
            # Update the message list to show the new message
            msg_list.see(tkinter.END)
        except OSError:
            break

# Sends whatever is in the message box to the server. This function is called by the send button,
# pressing enter in the message field, or as part of the event handler for closing the program.
def send(event=None):
    # Get message string from message field
    msg = my_msg.get()
    
    # Clear message field after reading message
    my_msg.set("")

    # If the message is the exit command (sent as part of the event handler for closing the window),
    # then send a final message and exit the program.
    if msg == "!exit":
        # Send message "<username> has left"
        client_socket.send(bytes(my_username.get() + " has left", "utf8"))
        
        # Close the socket
        client_socket.close()
        
        # Close window
        top.destroy()
        return
    
    # If execution gets here, then the message is a normal message. So, send it to the server along
    # with the user's username. (it will be broadcast to all other clients in the same room)
    client_socket.send(bytes(my_username.get() + ": " + msg, "utf8"))


# Sends the exit command to the server. This function is called when the user clicks the X button to close the window.
def on_closing(event=None):
    # Set the message variable to the exit command
    my_msg.set("!exit")
    
    #Send the command to the server
    send()

# Sends a command to the server to change the client's room number. Called by the Change Room button
def change_room():
    global current_room
    
    # Get new room number from the selected room option
    current_room = ((chatRoomSelected.get()).split(' '))[2]
    
    # Send room change command to the server
    client_socket.send(bytes("#" + current_room, "utf8"))
    
    # Clear the message list
    msg_list.delete(0, tkinter.END)
    
    # Show a greeting message for the new room
    msg_list.insert(tkinter.END, "You are now in room " + str(current_room))
    msg_list.see(tkinter.END)


# ================ Begin main program ================
number_of_rooms = 0
current_room = 0

# Initialize window
top = tkinter.Tk()
top.title("3313 Chat App")
top['background'] = '#505050'
messages_frame = tkinter.Frame(top)

# Initialize variables to be linked to input elements
# my_msg: used for the message entry field
my_msg = tkinter.StringVar()
my_msg.set("")

# my_username: self-explanatory
my_username = tkinter.StringVar()
my_username.set("")

# Initialize message container, add a scrollbar, and place it in the window
scrollbar = tkinter.Scrollbar(messages_frame, bg = "#505050", troughcolor='#696969')
msg_list = tkinter.Listbox(messages_frame, height=30, width=100, yscrollcommand=scrollbar.set, bg = '#696969', fg = '#ffffff')
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

# Create a frame for configuration (chat rooms and username)
cfg_frame = tkinter.Frame(top, bg = '#505050', width = 25)

# Initialize username entry field and its label, and place them in the window
username_label = tkinter.Label(cfg_frame, text="Enter username: ", bg = '#505050', fg = '#ffffff')
username_label.pack(anchor='w', padx = 10)
username_field = tkinter.Entry(cfg_frame, textvariable=my_username, bg = '#696969', fg = '#ffffff')
username_field.pack(anchor='w', padx = 10, pady = 5)

# Create a frame for the message box and send button
send_frame = tkinter.Frame(top, bg = '#505050')

# Initialize message entry field, Send button, and field label, and place them in the window
message_label = tkinter.Label(send_frame, text="Enter message: ", bg = '#505050', fg = '#ffffff')
message_label.pack(anchor='nw', padx = 10)
entry_field = tkinter.Entry(send_frame, textvariable=my_msg, width=50, bg = '#696969', fg = '#ffffff')
entry_field.bind("<Return>", send)  # Add event listener for pressing enter in the message entry field, which acts the same as the send button
entry_field.pack(anchor='nw', padx = 10, pady = 5)
send_button = tkinter.Button(send_frame, text="Send", command=send, bg = '#696969', fg = '#ffffff')
send_button.pack(anchor='nw', padx = 10, pady = 5)

# Attach event listener for closing the window, which will send an exit command to the server
top.protocol("WM_DELETE_WINDOW", on_closing)

# Get arguments from command line
if (len(sys.argv) < 3):
    print("Usage: Client.py <ip> <port>")
    exit()

# IP address: Use ipaddress module to validate it
ip = sys.argv[1]
try:
    test_ip = ipaddress.ip_address(ip)
except:
    print("Invalid IP address: Must be of the form x.x.x.x where 0 <= x <= 255")

# Port number: Make sure it's an integer and in the correct range
port = sys.argv[2]
try:
    port = int(port)
except:
    print("Invalid port number: Must be an integer")
    exit()
if port < 0 or port > 65535:
    print("Invalid port number: Must be between 0 and 65535 inclusive")
    exit()

# Set up socket parameters
BUFFER_SIZE = 1024
ADDR = (ip, port)

# Create socket and connect to the server
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

# Get first message from server, which will be the number of chat rooms available
first_msg = client_socket.recv(BUFFER_SIZE).decode("utf8")
number_of_rooms = int(first_msg)

# Set up room selection menu
chatRoomSelected = tkinter.StringVar(top)
chatRoomSelected.set("List Of Chat Rooms")

# Populate rooms menu based on maximum number of rooms
rooms_list = []
for i in range(number_of_rooms):
    rooms_list.append("Chat Room " + str(i + 1))
chat_rooms = tkinter.OptionMenu(cfg_frame, chatRoomSelected, *rooms_list)
chat_rooms.config(bg = '#696969', fg = '#ffffff')
chat_rooms.pack(anchor='w', padx = 10, pady = 5)

# Initialize change room button and attach event handler
change_button = tkinter.Button(cfg_frame, text="Change Room", command=change_room, bg = '#696969', fg = '#ffffff')
change_button.pack(anchor='w', padx = 10, pady = 5)
cfg_frame.pack(side = tkinter.LEFT)
send_frame.pack(side = tkinter.RIGHT, expand = True)

# Create thread for receiving data
receive_thread = Thread(target=receive)

# Start receiving thread
receive_thread.start()

# Set window to non-resizable and launch GUI
top.resizable(width=False, height=False)

# Initially join room 1, which will always exist
chatRoomSelected.set("Chat Room 1")
change_room()

tkinter.mainloop()
