#include "thread.h"
#include "socketserver.h"
#include <algorithm>
#include <stdlib.h>
#include <time.h>
#include "Semaphore.h"
#include <list>
#include <vector>
#include <thread>

using namespace Sync;

/*
ClientThread: Manages a single connection to a client
*/
class ClientThread : public Thread
{
private:
    Socket &socket;		// Reference to this thread's socket
    ByteArray data;		// Byte array for data received from/sent to client
	int room;	// Chat room number that this thread belongs to
	int port;			// The port our server is running on
	bool& terminate;	// Reference to a global flag that tells the thread when to terminate

	// Reference to a global vector containing pointers to all existing SocketThreads.
	// Used when this thread needs to determine which other clients to send data to.
    std::vector<ClientThread*> &allClientThreads;

    
public:
	ClientThread(Socket& socket, std::vector<ClientThread*> &clientThreads, bool &terminate, int port) :
		socket(socket), allClientThreads(clientThreads), terminate(terminate), port(port)
	{}

	// Properly terminates the thread after it's finished execution
    ~ClientThread()
    {
		this->terminationEvent.Wait();
	}

	// Accessor for socket - required for sending messages between clients
    Socket& GetSocket()
    {
        return socket;
    }

	// Accessor for room number - allows other ClientThreads to read this thread's room number to determine whether to send a message
    const int GetRoom()
    {
        return room;
    }

    virtual long ThreadMain()
    {
		// Convert port number to a string to use when accessing the semaphore
		std::string stringPort = std::to_string(port);

		// Semaphore shared by all ClientThreads. Used to ensure mutual exclusion when a thread accesses the allClientThreads vector.
		Semaphore semClient(stringPort);

		try {
			// ======== Initially set this thread's chat room number. ========
			// Get first data from client, which will be of the form "/#" where # is a number from 1 to the number of rooms on the server
			socket.Read(data);

			// Convert the received data to a string
			std::string roomStr = data.ToString();

			// Get rid of the leading slash so only the room number is left
			roomStr = roomStr.substr(1, roomStr.size() - 1);

			// Convert the room number to an actual integer and set this thread's room number accordingly
			room = std::stoi(roomStr);

			// Log room number to console
			std::cout << "Room number set to " << room << std::endl;

			// Main loop - loops continuously until either the thread is set to terminate or they close their connection
			while(!terminate) {
				// Get data from the client
				int recvResult = socket.Read(data);

				// If Read() returns zero, then the client closed their socket. Therefore, this thread can end its main loop and terminate.
				if (recvResult == 0){
					break;
				}

				// If execution gets here, then the client is still connected and sent data. So, we can convert it to a string
				std::string recv = data.ToString();

				// If the client sent a command to leave the server, then this thread can terminate.
				if(recv == "exit\n") {
					// Wait for the semaphore to be unblocked, to ensure this thread doesn't try to access the list while another thread is using it.
					semClient.Wait();

					// Find the location of this thread in the list of all ClientThreads using std::remove. Then, delete it from the vector.
					allClientThreads.erase(std::remove(allClientThreads.begin(), allClientThreads.end(), this), allClientThreads.end());

					// The critical section is now over, so the semaphore can be unblocked.
					semClient.Signal();

					std::cout<< "Client sent exit command - Deleting client thread" << std::endl;
					break;
				}

				// If the client sent a command starting with a forward slash, then switch chat rooms to the number after the slash.
				if (recv[0] == '/') {
					// Get the portion of the string after the slash, which should be a number.
					std::string stringChat = recv.substr(1, recv.size() - 1);
				
					// Convert this number to an actual integer and change the chat room to that number.
					room = std::stoi(stringChat);
					std::cout << "Room number changed to " << room << std::endl;

					// Go back to the beginning of the loop and wait for more data
					continue;
				}

				// If execution reaches this point, it means the client sent a regular message.
				// So, it can be broadcast to all other clients in this room.

				// Wait for the semaphore to be unblocked so that we don't try to access the thread list while another thread is using it
				semClient.Wait();
				// === Begin critical section ===
				// Iterate over every ClientThread in the vector containing all existing ClientThreads
				for (int i = 0; i < allClientThreads.size(); i++) {
					// Get the next thread from the list
					ClientThread* clientSocketThread = allClientThreads[i];

					// Check if the thread is in the same chat room as this thread
					if (clientSocketThread->GetRoom() == room)
					{
						// If it's in the same room, then convert the received data back to a byte array and send it to that thread's socket.
						Socket& clientSocket = clientSocketThread->GetSocket();
						ByteArray sendBytes(recv);
						clientSocket.Write(sendBytes);
					}
				}
				// === End critical section ===
				semClient.Signal();
			}
		} 
		// Catch exceptions thrown when string-to-int conversion fails
		catch(std::string &s) {
			std::cout << s << std::endl;
		}
		// Catch the exception generated if the client disconnects abruptly and log it to the console
		catch(std::exception &e){
			std::cout << "Client has disconnected abruptly!" << std::endl;
		}

		// Send message in console right before thread terminates
		std::cout << "Terminating client thread" << std::endl;
	}
};

// ServerThread: Handles welcoming clients and assigning them sockets and threads
class ServerThread : public Thread
{
private:
    SocketServer &server;						// Reference to the socket server
    std::vector<ClientThread*> clientThreads; 	// Vector with pointers to all existing ClientThreads
	int port;									// Port number the server is using
	int numberRooms;							// Maximum number of chat rooms
    bool terminate = false;						// Global termination flag - used by this thread and all ClientThreads
    
public:
    ServerThread(SocketServer& server, int numberRooms, int port)
    : server(server), numberRooms(numberRooms), port(port)
    {}

	// Clean up all client threads, including closing their sockets
    ~ServerThread()
    {
		// Close all ClientThread sockets
        for (auto thread : clientThreads)
        {
            try
            {
                // Close the socket
                Socket& toClose = thread->GetSocket();
                toClose.Close();
            }
            catch (...)
            {
                // If any exception occurs, it would be because the socket or thread no longer exists.
				// So, we don't need to do anything here because the work has already been done
            }
        }

		// Swap the contents of the allClientThreads vector with an empty vector.
		// This stops the threads from being able to access each other.
		std::vector<ClientThread*>().swap(clientThreads);

		// Set global termination flag, which tells all ClientThreads to terminate.
        terminate = true;
    }

    virtual long ThreadMain()
    {
		// Main loop - runs continuously until externally terminated
        while (true)
        {
            try {
				// Create the semaphore that protects the allClientThreads vector, using the port number as the semaphore name.
                std::string portStr = std::to_string(port);
                Semaphore semClients(portStr, 1, true);

				// Create string for maximum number of rooms, to be sent to new clients when they connect
                std::string maxRoomsStr = std::to_string(numberRooms) + '\n';
				// Convert string to byte array so it can be sent
                ByteArray maxRooms(maxRoomsStr); 

                // Wait for a client to connect and generate a new socket for this connection
                Socket sock = server.Accept();

				// Send the max rooms message to the client using the new socket
                sock.Write(maxRooms);

				// Create a pointer to the new socket so the ClientThread can be created
                Socket* newConnection = new Socket(sock);

                // Create a new ClientThread, passing a reference to this pointer
                Socket &socketReference = *newConnection;

				// Add the new thread to the vector containing all ClientThreads
                clientThreads.push_back(new ClientThread(socketReference, std::ref(clientThreads), terminate, port));
            }
			// Catch string-thrown exceptions.
            catch (std::string error)
            {
                std::cout << "ERROR: " << error << std::endl;
				// Exit thread function.
                return 1;
            }
			// Catch exception generated by unexpected server shutdown
			catch (TerminationException terminationException)
			{
				std::cout << "Server has shut down!" << std::endl;
				// Exit with exception thrown.
				return terminationException;
			}
        }
    }
};

int main(int argc, char* argv[]) {
	// If there are not enough command line arguments, then exit
	if (argc < 3)
	{
		std::cerr << "Usage: " << argv[0] << " port maxrooms" << std::endl;
		return 1;
	}
	
	// Server port number
    int port = 42069;
	// Get port number from command line args
	try {
		port = std::stoi(argv[1]);
	}
	// Catch exception generated if argument is not an integer
	catch (...)
	{
		std::cerr << "Invalid port number: Must be an integer" << std::endl;
		return 1;
	}
	// Check if port number is valid
	if (port < 1024 && port > 0)
	{
		// Port number likely reserved
		std::cout << "Warning: This port number is likely reserved for another protocol or application. Unexpected behaviour may occur." << std::endl;
	}
	else if (port <= 0 || port > 65535)
	{
		// Invalid port
		std::cerr << "Invalid port number: Must be between 1 and 65535 inclusive" << std::endl;
		return 1;
	}

	// Maximum number of chat rooms
    int rooms = 20;
	// Get number of rooms from command liune args
	try {
		rooms = std::stoi(argv[2]);
	}
	// Catch exception generated if argument is not a number
	catch (...)
	{
		// Print an error message and terminate the program
		std::cerr << "Invalid number of rooms: Must be an integer" << std::endl;
		return 1;
	}
	// Terminate the program if maximum rooms less than 1
	if (rooms < 1)
	{
		std::cerr << "Invalid number of rooms: Must be at least 1" << std::endl;
		return 1;
	}

    std::cout << "3313 Chat Server" << std::endl <<"Press enter to terminate" << std::endl;

	// Create the socket server
    SocketServer server(port);

	// Create the server thread using the newly created socket server and the port and maximum rooms from the command line arguments
    ServerThread st(server, rooms, port);

	// Once the server thread is running, the main thread waits for any user input
	FlexWait cinWaiter(1, stdin);
	cinWaiter.Wait();
	std::cin.get();

	// Once the user presses enter, shut down the socket server.
	server.Shutdown();

    std::cout << "Good-bye!" << std::endl;

	// Once execution reaches the end of the main program, the destructor of the ServerThread is called.
	// This ultimately results in all of the ClientThreads being properly cleaned up, followed by the ServerThread.
}