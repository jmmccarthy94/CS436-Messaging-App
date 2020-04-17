import socket
import errno #Handle for nonblocking recv
import sys
import threading
import time
import pickle
import queue
import tkinter as tk

class guiHandler(tk.Frame):
    def __init__(self, master, msgQ, endCommand):
        tk.Frame.__init__(self, master)
        self.master = master
        self.msgQ = msgQ

        self.master.title("Messaging App")
        self.master.resizable(False, False)
        self.master.tk_setPalette(background='#e6e6e6')

        # Bindings
        self.master.protocol('WM_DELETE_WINDOW', self.quit_app)
        self.master.bind('<Escape>', self.quit_app)

        self.pack()

        ######  Widgets  ######
        # Chat frame
        tk.Label(self, text="Your chat:").pack(padx=15, pady=(10,0), anchor='w')

        chat_frame = tk.Frame(self, borderwidth=1, relief='sunken')
        chat_frame.pack(padx=15, pady=(0,15))
        self.chat = tk.Text(chat_frame, width=60, height=20, highlightbackground='#ffffff', highlightcolor="#7baedc",
                            bg='#ffffff', wrap=tk.WORD, font=("System", 14))
        self.chat.configure(state="disabled")
        self.chat.pack()

        # Input frame
        tk.Label(self, text="Enter text here:").pack(padx=15, pady=0, anchor='w')

        input_frame = tk.Frame(self, borderwidth=1, relief='sunken')
        input_frame.pack(padx=15, pady=(0,15))
        self.input = tk.Text(input_frame, width=60, height=5, highlightbackground='#ffffff', highlightcolor="#7baedc",
                            bg='#ffffff', wrap=tk.WORD, font=("System", 14))
        self.input.pack()

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(padx=15, pady=(0, 15), anchor='e')

        self.send_button = tk.Button(button_frame, text='Send', default='active', command=self.say_hi)
        self.send_button.pack(padx=1, side='right')

        self.quit_button = tk.Button(button_frame, text='Quit', command=self.quit_app)
        self.quit_button.pack(padx=1, side='right')

        # Master window location
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() - self.master.winfo_reqwidth()) / 2
        y = (self.master.winfo_screenheight() - self.master.winfo_reqheight()) / 3
        self.master.geometry("+{}+{}".format(int(x), int(y)))

    '''
        self.onInit()

    def onInit(self, event=None):
        setUsername = UsernameFrame(self.master)
        self._toggle_state('disabled')
    '''

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.msgQ.qsize():
            try:
                msg = self.msgQ.get(0)
                print(msg)

                self.chat.configure(state="normal")
                self.chat.insert("end", "\n")
                self.chat.insert("end", msg)
                self.chat.configure(state="disabled")

            except msg.empty:
                pass

    def quit_app(self, event=None):
        print("The user is closing the application")
        app.running = 0
        self.master.destroy()

    def _toggle_state(self, state):
        state = state if state in ('normal', 'disabled') else 'normal'
        widgets = (self.chat, self.input, self.send_button, self.quit_button)
        for widget in widgets:
            widget.configure(state=state)

    def say_hi(self):
        print("Hello!")
'''
class UsernameFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, borderwidth=5, relief='groove')
        self.pack()
        self.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(self, text="Enter your username:").pack(padx=15, pady=10)
        self.user_input = tk.Entry(self, background='white', width=24)
        self.user_input.pack(padx=5, pady=(0,10))
        self.user_input.focus_set()

        button_frame = tk.Frame(self)
        button_frame.pack(padx=15, pady=(0, 15), anchor='e')
        tk.Button(button_frame, text='OK', height=1, width=6, default='active', command=self.click_ok).pack(side='right')

        tk.Button(button_frame, text='Quit', height=1, width=6, command=self.click_quit).pack(side='right', padx=10)

    def click_ok(self, event=None):
        print("The user clicked 'OK':\nUsername: {}".format(self.user_input.get()))
        
        self.destroy()

    def click_quit(self, event=None):
        print("The user clicked 'Quit'")
        #self.destroy()
        app.gui.quit_app()
'''

class messagingClient(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master

        self.msgQ = queue.Queue()
        self.username = ""

        #Find a way to timeout the input from the options loop
        self.HEADER = 512
        serverName = "127.0.0.1"
        serverPort = 12000
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect((serverName, serverPort))
        self.check = "CHANGE"
        self.clientSocket.setblocking(False)# Make the socket non blocking to receive messages in a steady stream

        self.gui = guiHandler(master, self.msgQ, self.endApplication)

        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        self.periodicCall()

    # Check every 200 ms if there is something new in the queue.
    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            import sys
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    # Handle tcp stuff
    def workerThread1(self):

        while(self.check == "CHANGE"):
            self.username = input("Username: ")
            if not self.username.isspace(): #Prevent sending a username with no characters or a blank message
                self.clientSocket.sendall(self.username.encode()) #Send a name to the server to check
                time.sleep(0.2) #apply a sleep to the client to wait for the bytes to come through the socket
                newCheck = self.clientSocket.recv(self.HEADER).decode() #Receive the check from the server
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
            message = input(f"{self.username} > ")

            try:
                # # If message is not empty, send it to the server
                if not message.isspace():
                    self.clientSocket.sendall(message.encode())

                #If the client types 1, send it to the server and receive the list of clients in the server
                if message == "1" or message == "List users":
                    print("Here is a list of all users connected to the server: ")
                    time.sleep(0.5)
                    serverSend = self.clientSocket.recv(self.HEADER)
                    time.sleep(0.2)
                    serverList = pickle.loads(serverSend)
                    for user, avail in serverList.items(): #Get only available names in the list
                        if self.username != user:
                            print(user, " -> ", avail)
                    continue
                #If the client types 2, send to server and engage in chat if the other user accepts.
                elif message == "2" or message == "Chat":
                    time.sleep(1)
                    serverSend = self.clientSocket.recv(self.HEADER) #Receive a list of available clients
                    availableList = pickle.loads(serverSend) #Load the byte list in
                    print("List of available clients to chat with: ")
                    for names, avail in availableList.items():
                        print(names, avail)
                    print("Pick someone to chat with!")
                    otherUser = input(f"{self.username} : ")
                    self.clientSocket.sendall(otherUser.encode()) #Sends the name to the server to see if available
                    print("Waiting for input from other user ... Please wait.")
                    self.clientSocket.setblocking(True) #Blocks for input from server to wait on other client to respond
                    otherUserCheck = self.clientSocket.recv(self.HEADER).decode() #otherUser has accept or declined
                    self.clientSocket.setblocking(False) #Unblock to constantly stream messages
                    print(otherUserCheck)
                    if otherUserCheck[0:18] == "invitationAccepted":
                        self.clientChatroom() #Engage in a chatroom if the other user has accepted and has been notified from the server
                        continue
                    else:
                        continue
                #If the client types 3, exit the server and close the client side application
                elif message == "3" or message == "Exit":
                    print("Closing client. Bye bye!")
                    self.clientSocket.shutdown(socket.SHUT_RDWR)
                    self.clientSocket.close()
                    sys.exit()
                #Receive messages from the server. If at any point the client receives a chat invitation from someone,
                #respond accordingly.
                while True:
                    time.sleep(0.5)
                    try:
                        anyMsg = self.clientSocket.recv(self.HEADER).decode() #From server elif 2
                        #If at any point another client wishes to invite to chat, handle for it
                        if anyMsg[0:14] == "chatInvitation":
                            print(anyMsg)
                            print("Accept? Yes or No.")
                            message = input(f"{self.username} : ")
                            self.clientSocket.sendall(message.encode()) #Send "Yes" to server -> client
                            if message == "Yes":
                                time.sleep(0.2)
                                self.clientChatroom()
                                
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
                    self.clientSocket.shutdown(SHUT_RDWR)
                    self.clientSocket.close()

    # Purpose: Create a chatroom for the client side of the application. Try to receive messages.
    #          If there is no message to receive, then send one to the server. If the client types
    #          "Quit", then the chatroom wil exit.
    def clientChatroom(self):
        while True:
            time.sleep(0.2)
            try:
                self.clientSocket.settimeout(3.0)
                anyMsg = self.clientSocket.recv(self.HEADER).decode() #Try to receive a message
                self.clientSocket.settimeout(None)
                print(anyMsg)
                self.msgQ.put(anyMsg)
            except:
                pass

            time.sleep(0.1)
            message = input(f"{self.username} : ")
            self.clientSocket.sendall(message.encode()) #Otherwise send one from the client
            time.sleep(0.2)
            if message == "Quit":
                break




    def endApplication(self):
        self.running = 0

root = tk.Tk()
app =  messagingClient(master=root)
app.mainloop()
