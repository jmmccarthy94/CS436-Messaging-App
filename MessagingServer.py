import socket
import select #Use the select.select function
import pickle #Send list over a connection socket
import time

HEADER = 512
serverName = "10.9.59.14"
serverPort = 32249
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(5) # Listen with a queue of 5 clients
socketsList = [serverSocket] #All sockets to send information to (via client - to - client)
clients = {} # Clients with socket information
clientList = {} # Client list to send to the client
chatList = {} # Used later for multi chat client
print(f"Server on!\nListening for connections on ... {serverName} , {serverPort} ... ") #Use fstream for readability

# Purpose: Get the entered username of the client and check whether or not it is available to use.
#          If the username is not available, prompt the client to enter another one. If it is,
#          append the proper infomration to all lists and dictionaries for use.
# Params: the client socket that received the username.
def checkName(clientSocket):
    nameCheck = "CHANGE"
    while nameCheck == "CHANGE":
        time.sleep(0.5)
        username = clientSocket.recv(HEADER).decode()
        if username == "": #If the username is blank, client performed a graceful close
            print("Client performed a graceful close.")
            break
        else: #Else the server has received the username
            print("Server has received the name... ", username, "to check.")
            if clientList: #If a client list exists, print available names to the server
                print("Taken names... ")
                for x in clientList:
                    print(x)
            else: #Otherwise no names have been entered yet
                print("No names have been entered into the server.")
            if username in clientList: #If the username is in the client list, prompt client to change username
                print("Client has entered an invalid username. Prompt to change.")
                clientSocket.sendall(nameCheck.encode())
            else: #Else username is valid and append all available information from client to each list
                print("Client has entered a valid username. Continue.")
                nameCheck = "OK"
                clientSocket.sendall(nameCheck.encode()) #Send name check back to client
                # clientList.append(username) #Append username to the client list for pickling
                # clientList.append('Available')
                clientList[username] = 'Available'
                socketsList.append(clientSocket) #Append socket info of this client to a socketsList
                clients[clientSocket] = username #Store the socket as the key and the name as the value
                return username

# Purpose: Send the client the list of all users connected to the server via the pickling module.
#          This is able to send deserialized byte segments through the TCP socket.
# Params: The username of the client and the socket connecting the server to the particular socket.
def pickleUsers(user, someSocket):
    print(user, "wants a list sent to them. Here are the names in the server: ")
    for user, avail in clientList.items():
        print(user, " -> ", avail)
    sendList = pickle.dumps(clientList)
    someSocket.sendall(sendList) #No need to encode because the list is already in bytes
    print("Sending list ... ")

# Purpose: Create the chatroom for two different clients to communicate. Either of the two clients will
#          send a message to the server which will send to the other client. If one of the
#          clients have typed "Quit", the chatroom will close and the users will exit.
# Params:  The socket of the sender and the socket of the receiver.
def chatRoom(currentSocket, other_socket):
    # Get the names of the client
    user1 = clients[currentSocket] #Get user info
    user2 = clients[other_socket]
    clientList[user1] = 'Busy' #Change availability of the clients
    print(user1, "'s availability has been changed to BUSY'")
    clientList[user2] = 'Busy'
    print(user2, "'s availability has been changed to BUSY'")
    # Send welcome message to the socket
    currentSocket.sendall("From server: Welcome to the chatroom!".encode())
    other_socket.sendall("From server: Welcome to the chatroom!".encode())
    while True:
        try: #If the first user has sent a message, receive and send to the other client
            time.sleep(0.1)
            currentSocket.settimeout(3.0)
            msg1 = currentSocket.recv(HEADER).decode()
            currentSocket.settimeout(None)
            if msg1 == "Quit": #If first client has message "Quit", exit the chatroom
                time.sleep(0.1)
                print("Chatroom has ended!")
                other_socket.sendall((user1 + " has left the chat.").encode())
                break
            else: #Else, send the message to the other client
                time.sleep(0.2)
                other_socket.sendall((user1 + " : " + msg1).encode())
                print(user1, " has sent ", msg1)
        except:
            pass

        try: #If the second user has sent a message, receive and send to the other client
            time.sleep(0.1)
            other_socket.settimeout(1.0)
            msg2 = other_socket.recv(HEADER).decode()
            other_socket.settimeout(None)
            if msg2 == "Quit": #If the second client has entered quit, exit the chatroom
                print("Chatroom has ended!")
                currentSocket.sendall((user2 + " has left the chat.").encode())
                break
            else: #Else, send the message to the other client
                time.sleep(0.1)
                currentSocket.sendall((user2 + " : " + msg2).encode())
                print(user2, " has sent ", msg2)
        except:
            pass


while True:
    time.sleep(1)
    #Select module allows for multiplexing of events with different sockets
    read_sockets, _, exception_sockets = select.select(socketsList, [], [], 2)
    #Iterate over all of the read descriptor sockets in the list
    for currentSocket in read_sockets:
        if currentSocket == serverSocket: #If the current socket is new,
            clientSocket, client_address = serverSocket.accept() #Accept the connection
            user = checkName(clientSocket) #Check the name of the client and handle
            print("\nCurrent list of users in the server ...")
            for x in clientList:
                print(x)

        else: #Else, an existing socket is sending a message to the server
            handlerText = currentSocket.recv(HEADER).decode()
            user = clients[currentSocket] #Obtain which client is sending messages through this socket
            if handlerText == "": #If the message received is blank, client must have disconnected
                print(user, " performed a graceful close.")
                # Remove from socket list, client list
                socketsList.remove(currentSocket)
                del clients[currentSocket]
                continue
            print("Received message from", user, ":", handlerText)
            #If the message typed by client is 1, send them a list
            if handlerText == "1" or handlerText == "List users":
                print("handler works here")
                pickleUsers(user, currentSocket)
            #If client sends 2, they want to chat with someone else
            elif handlerText == "2" or handlerText == "Chat":
                pickleUsers(user, currentSocket)
                time.sleep(0.2)
                otherUser = currentSocket.recv(HEADER).decode() #Get the username of desired chat partner
                time.sleep(0.2)
                print(user, "wishes to speak to", otherUser)
                otherSocket = ""
                for someSocket, users in clients.items():#Get the key (someSocket) of the desired
                    if users == otherUser:
                        otherSocket = someSocket
                print(otherUser, "'s key is ... '")
                print(otherSocket)
                time.sleep(0.5)
                #Send to the socket if available.
                print("Sent chat invitation to", otherUser)
                otherSocket.sendall("chatInvitation".encode()) #Send chat invitation to desired chat partner
                time.sleep(0.2)
                otherSocket.sendall(" from ".encode())
                time.sleep(0.2)
                otherSocket.sendall(user.encode())
                time.sleep(0.2)
                otherUserCheck = otherSocket.recv(HEADER).decode() #Receive check from the otherUser
                if otherUserCheck == "Yes": #If the client says yes, engage in chat
                    currentSocket.sendall("invitationAccepted. Entering chatroom ... ".encode())
                    chatRoom(currentSocket, otherSocket) #Create the chatroom
                else: #Else the client has declined from chat, send message and do nothing else
                    otherUserCheck == "No"
                    print(otherUser, "has declined to chat with", user)
                    currentSocket.sendall((otherUser + " has declined to chat. Sorry!").encode())
                    continue
            #If the client has typed 3, remove the client from the server
            elif handlerText == "3" or handlerText == "Exit":
                print(user, "has left the server.")
                del clientList[user] #Remove user from client list
                socketsList.remove(currentSocket) #Remove from sockets list
                del clients[currentSocket] #Remove the information from client dictionary
                currentSocket.close()
                continue
            # elif handlerText == "4" or handlerText == "Group Chat":
            #

serverSocket.shutdown(SHUT_RDWR)
serverSocket.close()
