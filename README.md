# 3313-project
### Instructions for use
1. Compile Server
2. Launch Server, specifying a port number and number of chat rooms
3. Launch Client, specifying the server IP and port number.
4. Select a chat room and **click "Change Room"** (this is important, you will disconnect from the server if you don't)
5. Enter a username and send messages

### Command line argument formats
- Server: `./Server <portNumber> <maxRooms>`
- Client: `python ./Client.py <ip_address> <port_number>`

### Notes for chat room functionality
* Client
  * Single socket
  * Two threads: One (main program thread) for sending/GUI events and another for receiving
    * Allows the client to both wait for new messages and send messages. Both threads use the same socket.
* Server
  * Single server socket for welcoming clients
  * One socket and one thread per client
  * Synchronization: Semaphore used to prevent multiple threads from concurrently accessing the shared list of clients
