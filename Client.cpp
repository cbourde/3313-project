
#include "thread.h"
#include "socket.h"
#include <iostream>
#include <stdlib.h>
#include <time.h>

using namespace Sync;

// Testing client: Used to test connection between VM and host
// If you're looking for the chat room client, that's Client.py

// This thread handles the connection to the server
class ClientThread : public Thread
{
private:
	// Reference to the connected socket
	Socket& socket;

	// Data to send to server
	ByteArray data;
	std::string data_str;
public:
	ClientThread(Socket& socket)
	: socket(socket)
	{}

	~ClientThread()
	{}

	virtual long ThreadMain()
	{
		int result = socket.Open();
		std::cout << "Enter data to send: ";
		std::cout.flush();

		// Get user input
		std::getline(std::cin, data_str);
		data = ByteArray(data_str);

		// Send it to the server
		socket.Write(data);

		// Get the response and print it
		socket.Read(data);
		data_str = data.ToString();
		std::cout << "Server Response: " << data_str << std::endl;
		return 0;
	}
};

int main(void)
{
	// Welcome the user 
	std::cout << "3313 Project Testing Client" << std::endl;

	// Create our socket
	Socket socket("127.0.0.1", 42069);
	ClientThread clientThread(socket);
	while(1)
	{
		// just wait until user presses ctrl C lol
		sleep(1);
	}
	socket.Close();

	return 0;
}
