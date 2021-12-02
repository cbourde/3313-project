from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter


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
        top.quit()
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
top.title("OS Messenger App")
messages_frame = tkinter.Frame(top)

# Initialize variables to be linked to input elements
# my_msg: used for the message entry field
my_msg = tkinter.StringVar()
my_msg.set("")

# my_username: self-explanatory
my_username = tkinter.StringVar()
my_username.set("")

# Initialize message container, add a scrollbar, and place it in the window
scrollbar = tkinter.Scrollbar(messages_frame)
msg_list = tkinter.Listbox(messages_frame, height=30, width=100, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

# Initialize username entry field and its label, and place them in the window
username_label = tkinter.Label(top, text="Enter username: ")
username_label.pack()
username_field = tkinter.Entry(top, textvariable=my_username)
username_field.pack()

# Initialize message entry field, Send button, and field label, and place them in the window
message_label = tkinter.Label(top, text="Enter message: ")
message_label.pack()
entry_field = tkinter.Entry(top, textvariable=my_msg, width=50)
entry_field.bind("<Return>", send)  # Add event listener for pressing enter in the message entry field, which acts the same as the send button
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

# Attach event listener for closing the window, which will send an exit command to the server
top.protocol("WM_DELETE_WINDOW", on_closing)

# Set up socket parameters
HOST = "127.0.0.1"
PORT = 42069
BUFFER_SIZE = 1024
ADDR = (HOST, PORT)

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
chat_rooms = tkinter.OptionMenu(top, chatRoomSelected, *rooms_list)
chat_rooms.pack()

# Initialize change room button and attach event handler
change_button = tkinter.Button(top, text="Change Room", command=change_room)
change_button.pack()

# Create thread for receiving data
receive_thread = Thread(target=receive)

# Start receiving thread
receive_thread.start()

# Set window to non-resizable and launch GUI
top.resizable(width=False, height=False)
tkinter.mainloop()
