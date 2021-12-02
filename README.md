# 3313-project
### Instructions for use
1. Compile Server
2. Launch Server, specifying a port number and number of chat rooms
3. Set IP address and port number in Client.py to match server IP and port
4. Launch Client, select a chat room and *click "Change Room"* (this is important)
5. Enter a username and send messages

### Notes for chat room functionality
* Client
  * Single socket
  * Two threads: One (main program thread) for sending/GUI events and another for receiving
    * Allows the client to both wait for new messages and send messages. Both threads use the same socket.
* Server
  * Single server socket for welcoming clients
  * One socket and one thread per client
  * Synchronization: Semaphore used to prevent multiple threads from concurrently accessing the shared list of clients
