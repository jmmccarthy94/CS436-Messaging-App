#import select #Use the select.select function
import pickle #Send list over a connection socket
#import time
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from collections import defaultdict

'''imports for video calling
import sys
import cv2
import numpy as np
import struct 
import zlib
'''


def new_connection_handler():
    '''Accept new clients to the server'''
    while True:
        client_socket, client_addr = SERVER.accept()
        print(f"{client_addr} has connected")
        client_socket.send(bytes("CONNECTION_OK", "utf8"))
        addresses[client_socket] = client_addr
        Thread(target=client_handler, args=(client_socket,)).start()


def client_handler(client):
    '''Handle a single client'''
    name = None
    while True:
        '''Check for valid username'''
        name = client.recv(BUFSIZ).decode("utf8")
        if name == "QUIT_APP":
            print(f"disconnecting client: {client}")
            client.close()
            del addresses[client]
            break

        elif name in usernames.values():
            client.send(bytes("USERNAME_TAKEN", "utf8"))
            continue
        
        ''' #Handled in client
        if (len(name) > 16) and (len(name) < 0):
            print(name, flush=True)
            print(len(name), flush=True)
            client.send(bytes("USERNAME_LENGTH", "utf8"))
            continue
        '''

        client.send(bytes("USERNAME_OK", "utf8"))
        usernames[client] = name
        room_selection_handler(client)
        break


def room_selection_handler(client):
    '''handle room selection/creation'''
    #list_rooms(client)
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if msg == "QUIT_APP":
            client.send(bytes("QUIT_APP", "utf8"))
            client.close()
            del usernames[client]
            del addresses[client]
            break
        elif msg == "REFRESH_ROOMS":
            list_rooms(client)
        elif msg[0:5] == "JOIN:":
            room = msg[5:]
            if room in rooms:
                rooms[room].append(client)
                client.send(bytes("JOIN_OK", "utf8"))
                client_in_room(room, client)
            else:
                print("Error joining room %s by client %s" % room, client)
                client.send(bytes("JOIN_BAD", "utf8"))
        elif msg[0:9] == "CREATE_O:":
            #room = msg[9:]
            room = usernames[client] + "'s Room"
            print("Creating new room: %s" % room)
            rooms[room].append(client)
            # FIXME Handle for duplicate room names
            client.send(bytes("CREATION_OK", "utf8"))
            client_in_room(room, client)
            break
        elif msg[0:9] == "CREATE_P:":
            ''' Impliment to client if time available '''
            arr = msg[9:].split(":")
            room = arr[0]
            password = arr[1]
            print("Creating new room w/ password: %s" % room)
            rooms[room].append(client)
            # FIXME Handle for duplicate room names
            room_pass[room] = password
            client.send(bytes("CREATION_OK", "utf8"))
            client_in_room(room, client)
            break
        else:
            print("%s : Error in room selection. Removing client" % client)
            client.send(bytes("ERROR", "utf8"))
            client.close()
            del usernames[client]
            del addresses[client]
            break


def client_in_room(room, client):
    '''Recieve messages from client to broadcast in room'''
    while True:
        msg = client.recv(BUFSIZ).decode("utf8")
        if msg == "QUIT_APP":
            client.send(bytes("QUIT_APP", "utf8"))
            client.close()
            rooms[room].remove(client)
            del usernames[client]
            del addresses[client]
            check_room(room)
            return
        elif msg == "EXIT_ROOM":
            client.send(bytes("EXIT_ROOM", "utf8"))
            rooms[room].remove(client)
            check_room(room)
            room_selection_handler(client)
            return
        elif msg == "NEW_JOIN":
            broadcast_to_room(room, f"*** {usernames[client]} has joined the room! ***\n", join=True)
        else:
            broadcast_to_room(room, msg ,usernames[client])


def broadcast_to_room(room, msg, sender="", join=False):
    '''Send message to all clients in a room'''
    for sock in rooms[room]:
        print(sock)
        if join:
            sock.send(bytes(msg, "utf8"))
        else:
            sock.send(bytes(sender + ">> ", "utf8") + bytes(msg, "utf8"))


def list_rooms(client):
    '''Send list of open chatrooms'''
    room_arr = []
    for r in rooms.keys():
        room_arr.append(r)
    room_list = pickle.dumps(room_arr)
    client.send(room_list)


def check_room(room):
    '''Check if room is empty. Delete room and password if empty'''
    if len(rooms[room]) == 0:
        if room in room_pass:
            del room_pass[room]
        del rooms[room]


usernames = {}
addresses = {}
rooms = defaultdict(list)
room_pass = {}

#rooms["test1"] = {"tester", "tester2"}
#rooms["test2"] = "alsotest"

BUFSIZ = 1024
SERVER_IP = "0.0.0.0"
SERVER_PORT = 1234
ADDR = (SERVER_IP, SERVER_PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
SERVER.bind(ADDR)

if __name__ == "__main__":
    SERVER.listen()
    print(f"Server on!\nListening for connections on ... {SERVER_IP} , {SERVER_PORT} ... ")
    ACCEPT_THREAD = Thread(target=new_connection_handler)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
