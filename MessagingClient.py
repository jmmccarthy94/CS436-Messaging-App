import socket
import errno #Handle for nonblocking recv
import sys
import time
import pickle
import tkinter

#Find a way to timeout the input from the options loop
HEADER = 512
serverName = "192.168.1.47"
serverPort = 12000
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
check = "CHANGE"
clientSocket.setblocking(False)# Make the socket non blocking to receive messages in a steady stream

# Purpose: Create a chatroom for the client side of the application. Try to receive messages.
#          If there is no message to receive, then send one to the server. If the client types
#          "Quit", then the chatroom wil exit.
def clientChatroom():
    while True:
        time.sleep(0.2)
        try:
            clientSocket.settimeout(3.0)
            anyMsg = clientSocket.recv(HEADER).decode() #Try to receive a message
            clientSocket.settimeout(None)
            print(anyMsg)
        except:
            pass

        time.sleep(0.1)
        message = input(f"{username} : ")
        clientSocket.sendall(message.encode()) #Otherwise send one from the client
        time.sleep(0.2)
        if message == "Quit":
            break


while(check == "CHANGE"):
    username = input("Username: ")
    if not username.isspace(): #Prevent sending a username with no characters or a blank message
        clientSocket.sendall(username.encode()) #Send a name to the server to check
        time.sleep(0.2) #apply a sleep to the client to wait for the bytes to come through the socket
        newCheck = clientSocket.recv(HEADER).decode() #Receive the check from the server
        if newCheck == "CHANGE":
            print("Name has been taken. Please enter another user name.")
            continue
        else:
            print("Name is ok! Continue ... ")
            break
    else: #Retry entering another name
        continue


# Loop the options until the client enteres (3) or "Exit"

while True:
    print("(1) List")
    print("(2) Chat")
    print("(3) Exit")
    message = input(f"{username} > ")

    try:
        # # If message is not empty, send it to the server
        if not message.isspace():
            clientSocket.sendall(message.encode())

        #If the client types 1, send it to the server and receive the list of clients in the server
        if message == "1" or message == "List users":
            print("Here is a list of all users connected to the server: ")
            time.sleep(0.5)
            serverSend = clientSocket.recv(HEADER)
            time.sleep(0.2)
            serverList = pickle.loads(serverSend)
            for user, avail in serverList.items(): #Get only available names in the list
                if username != user:
                    print(user, " -> ", avail)
            continue
        #If the client types 2, send to server and engage in chat if the other user accepts.
        elif message == "2" or message == "Chat":
            time.sleep(1)
            serverSend = clientSocket.recv(HEADER) #Receive a list of available clients
            availableList = pickle.loads(serverSend) #Load the byte list in
            print("List of available clients to chat with: ")
            for names, avail in availableList.items():
                print(names, avail)
            print("Pick someone to chat with!")
            otherUser = input(f"{username} : ")
            clientSocket.sendall(otherUser.encode()) #Sends the name to the server to see if available
            print("Waiting for input from other user ... Please wait.")
            clientSocket.setblocking(True) #Blocks for input from server to wait on other client to respond
            otherUserCheck = clientSocket.recv(HEADER).decode() #otherUser has accept or declined
            clientSocket.setblocking(False) #Unblock to constantly stream messages
            print(otherUserCheck)
            if otherUserCheck[0:18] == "invitationAccepted":
                clientChatroom() #Engage in a chatroom if the other user has accepted and has been notified from the server
                continue
            else:
                continue
        #If the client types 3, exit the server and close the client side application
        elif message == "3" or message == "Exit":
            print("Closing client. Bye bye!")
            clientSocket.shutdown(socket.SHUT_RDWR)
            clientSocket.close()
            sys.exit()
        #Receive messages from the server. If at any point the client receives a chat invitation from someone,
        #respond accordingly.
        while True:
            time.sleep(0.5)
            try:
                anyMsg = clientSocket.recv(HEADER).decode() #From server elif 2
                #If at any point another client wishes to invite to chat, handle for it
                if anyMsg[0:14] == "chatInvitation":
                    print(anyMsg)
                    print("Accept? Yes or No.")
                    message = input(f"{username} : ")
                    clientSocket.sendall(message.encode()) #Send "Yes" to server -> client
                    if message == "Yes":
                        time.sleep(0.2)
                        clientChatroom()
                        break
                    else:
                        break
            except:
                break
    #If the recv returns an error for EWOULDBLOCK, handle for it and close the client applciation.
    # EAGAIN is also handled incase the application is used un UNIX.
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print("Reading error", e)
            clientSocket.shutdown(SHUT_RDWR)
            clientSocket.close()
