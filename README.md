# 3313-project
### Notes for chat room functionality
* Client
  * Single socket
  * Two threads: One for sending and another for receiving
    * Allows the client to both wait for new messages and send messages. Both threads use the same socket.
* Server
  * Single server socket for welcoming clients
  * One socket and one thread per client
  * Synchronization: Mutex objects used to stop multiple threads from concurrently accessing standard output and the array of clients
    * Mutex: Easier to use than a semaphore, stops other threads from accessing a section of code while it's locked.
    * Used in conjunction with a lock_guard, which keeps a mutex locked after instantiation until the lock_guard is destroyed.
    * By creating a lock_guard at the start of a function, the function becomes a critical section that is locked when called, and unlocked when it finishes.
    * (because the lock_guard is local to the function, it is destroyed at the end of the function, which unlocks the mutex)

### Inspiration:
https://github.com/cjchirag7/chatroom-cpp
* All we need to do is make the server support multiple concurrent rooms
