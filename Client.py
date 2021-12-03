from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import sys
import ipaddress


# Sends whatever is in the message box to the server. This function is called by the send button,
# pressing enter in the message field, or as part of the event handler for closing the program.
def sendMessage(event=None):
    # Get message string from message field
    message = myMessage.get()
    
    # Clear message field after reading message
    myMessage.set("")

    # If the message is the exit command (sent as part of the event handler for closing the window),
    # then send a final message and exit the program.
    if message == "!exit":
        # Send message "<username> has left"
        clntSocket.send(bytes(myUsername.get() + " has left", "utf8"))
        
        # Close the socket
        clntSocket.close()
        
        # Close window
        wind.destroy()
        return
    
    # If execution gets here, then the message is a normal message. So, send it to the server along
    # with the user's username. (it will be broadcast to all other clients in the same room)
    clntSocket.send(bytes(myUsername.get() + ": " + message, "utf8"))

# Continuously listens for data from the server and displays any received messages.
# This function runs in its own thread so it can listen constantly.
def receiveData():
    while True:
        try:
            # Wait for new data from the server and decode it to a string
            message = clntSocket.recv(BUFFER_SIZE).decode("utf8")
            
            # Add the new message to the message list
            messagelist.insert(tkinter.END, message)
            
            # Update the message list to show the new message
            messagelist.see(tkinter.END)
        except OSError:
            break


# Sends a command to the server to change the client's room number. Called by the Change Room button
def changeRoom():
    global currRoom
    
    # Get new room number from the selected room option
    currRoom = ((chatRoomSel.get()).split(' '))[2]
    
    # Send room change command to the server
    clntSocket.send(bytes("#" + currRoom, "utf8"))
    
    # Clear the message list
    messagelist.delete(0, tkinter.END)
    
    # Show a greeting message for the new room
    messagelist.insert(tkinter.END, "Welcome! You are in room " + str(currRoom))
    messagelist.see(tkinter.END)

# Sends the exit command to the server. This function is called when the user clicks the X button to close the window.
def closing(event=None):
    # Set the message variable to the exit command
    myMessage.set("!exit")
    
    #Send the command to the server
    sendMessage()




# ================ Begin main program ================
currRoom = 0
numberOfRooms = 0


# Initialize window
wind = tkinter.Tk()
wind.title("3313 Chat App")
wind['background'] = '#505050'
msgFrame = tkinter.Frame(wind)

# Initialize variables to be linked to input elements
# myMessage: used for the message entry field
myMessage = tkinter.StringVar()
myMessage.set("")

# myUsername: self-explanatory
myUsername = tkinter.StringVar()
myUsername.set("")

# Initialize message container, add a scrollbar, and place it in the window
scroll = tkinter.Scrollbar(msgFrame, bg = "#505050", troughcolor='#696969')
messagelist = tkinter.Listbox(msgFrame, height=30, width=100, yscrollcommand=scroll.set, bg = '#696969', fg = '#ffffff')
scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
messagelist.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
messagelist.pack()
msgFrame.pack()

# Create a frame for configuration (chat rooms and username)
cfg_frame = tkinter.Frame(wind, bg = '#505050', width = 25)

# Initialize username entry field and its label, and place them in the window
username_label = tkinter.Label(cfg_frame, text="Enter your username: ", bg = '#505050', fg = '#ffffff')
username_label.pack(anchor='w', padx = 10)
username_field = tkinter.Entry(cfg_frame, textvariable=myUsername, bg = '#696969', fg = '#ffffff')
username_field.pack(anchor='w', padx = 10, pady = 5)

# Create a frame for the message box and send button
send_frame = tkinter.Frame(wind, bg = '#505050')

# Initialize message entry field, Send button, and field label, and place them in the window
msgLabel = tkinter.Label(send_frame, text="Enter your message: ", bg = '#505050', fg = '#ffffff')
msgLabel.pack(anchor='nw', padx = 10)
entryField = tkinter.Entry(send_frame, textvariable=myMessage, width=50, bg = '#696969', fg = '#ffffff')
entryField.bind("<Return>", sendMessage)  # Add event listener for pressing enter in the message entry field, which acts the same as the send button
entryField.pack(anchor='nw', padx = 10, pady = 5)
sndBtn = tkinter.Button(send_frame, text="Send", command=sendMessage, bg = '#696969', fg = '#ffffff')
sndBtn.pack(anchor='nw', padx = 10, pady = 5)

# Attach event listener for closing the window, which will send an exit command to the server
wind.protocol("WM_DELETE_WINDOW", closing)

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
clntSocket = socket(AF_INET, SOCK_STREAM)
clntSocket.connect(ADDR)

# Get first message from server, which will be the number of chat rooms available
firstMesssage = clntSocket.recv(BUFFER_SIZE).decode("utf8")
numberOfRooms = int(firstMesssage)

# Set up room selection menu
chatRoomSel = tkinter.StringVar(wind)
chatRoomSel.set("List Of Chat Rooms")

# Populate rooms menu based on maximum number of rooms
listOfRooms = []
for i in range(numberOfRooms):
    listOfRooms.append("Chat Room " + str(i + 1))
chatRooms = tkinter.OptionMenu(cfg_frame, chatRoomSel, *listOfRooms)
chatRooms.config(bg = '#696969', fg = '#ffffff')
chatRooms.pack(anchor='w', padx = 10, pady = 5)

# Initialize change room button and attach event handler
chngBtn = tkinter.Button(cfg_frame, text="Change Room", command=changeRoom, bg = '#696969', fg = '#ffffff')
chngBtn.pack(anchor='w', padx = 10, pady = 5)
cfg_frame.pack(side = tkinter.LEFT)
send_frame.pack(side = tkinter.RIGHT, expand = True)

# Create thread for receiving data
rcvThread = Thread(target=receiveData)

# Start receiving thread
rcvThread.start()

# Set window to non-resizable and launch GUI
wind.resizable(width=False, height=False)

# Initially join room 1, which will always exist
chatRoomSel.set("Chat Room 1")
changeRoom()

tkinter.mainloop()
