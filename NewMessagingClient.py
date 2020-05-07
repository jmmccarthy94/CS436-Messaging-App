import socket
#import errno #Handle for nonblocking recv
#import sys
import time
import pickle
#import queue
import getpass
import tkinter as tk
from threading import Thread
from tkinter import filedialog
#from PIL import Image, ImageTk


class App(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        self.protocol("WM_DELETE_WINDOW", self.terminate)

        self.BUFSIZ = 1024
        HOST = "proxy17.rt3.io"
        PORT = 32158
        ADDR = (HOST, PORT)
        self.username = ""
        self.rooms = []

        # container setup
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.tk_setPalette(background='#e6e6e6')
        container.winfo_toplevel().title("Chat Room App")

        # initialize frames
        self.frames = {}
        for F in (ConfigPage, UsernamePage, ChannelSelect, ChatPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        # start connection
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(ADDR)

        init_thread = Thread(target=self.socket_thread)
        init_thread.start()

        # start app processes
        '''self.show_frame("ConfigPage")'''
        self.show_frame("UsernamePage")


    # Show the specified frame
    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        for frame in self.frames.values():
            frame.grid_remove()
        frame = self.frames[page_name]
        frame.grid()
        frame.tkraise()
        frame.winfo_toplevel().geometry("")
        frame.update_idletasks()
        x = (frame.winfo_screenwidth() - frame.winfo_reqwidth()) / 2
        y = (frame.winfo_screenheight() - frame.winfo_reqheight()) / 3
        self.geometry("+{}+{}".format(int(x), int(y)))

    def socket_thread(self):
        msg = self.client_socket.recv(self.BUFSIZ).decode("utf8")
        print(msg)
        if msg != "CONNECTION_OK":
            self.terminate()

    def terminate(self):
        print("Ending Application")
        try:
            self.client_socket.send(bytes("QUIT_APP", "utf8"))
        except:
            print("failed to tell server")
        self.destroy()


class ConfigPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Considering allowing users to input server ip and port
        # Adjust start frame if implimented
        '''
        self.host_IP = tk.StringVar()
        self.host_port = tk.StringVar()

        label = tk.Label(self, text="Input server information:")
        label.grid(pady=(5,0))
        addr_frame = tk.Frame(self, width=100, height=50, pady=10, padx=20)
        addr_frame.grid()

        IP_label = tk.Label(addr_frame, text="IP").grid(row=1, sticky="e")

        IP_in = tk.Entry(addr_frame, width=25, font=20, textvariable=self.host_IP, bg="white")
        IP_in.grid(row=1, column=1)

        port_label = tk.Label(addr_frame, text="Port").grid(row=2, sticky="e")

        port_in = tk.Entry(addr_frame, width=25, font=20, textvariable=self.host_port, bg="white")
        port_in.grid(row=2, column=1, pady=(5,0))

        file_button = tk.Button(addr_frame, text="Select files", command=self.connect_server)
        file_button.grid(row=3, column=1, pady=(5,0), sticky="e")

        #IP_label.focus_set()
        

    def connect_server(self):
        self.controller.HOST = int(self.host_IP)
        self.controller.PORT = int(self.host_port)
    '''

class UsernamePage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="Input a username:")
        label.grid(pady=(5,0))
        user_frame = tk.Frame(self, width=100, height=50, pady=10, padx=20)
        user_frame.grid()

        tk.Label(user_frame, text="Username").grid(row=1, sticky="e")

        self.user_in = tk.Entry(user_frame, width=25, font=20, bg="white")
        self.user_in.bind("<Return>", self.check_name)
        self.user_in.grid(row=1, column=1)

        sub_button = tk.Button(user_frame, text="Submit", command=self.check_name)
        sub_button.grid(row=2, column=1, pady=(5,0), sticky="e")

        self.user_error1 = tk.Label(user_frame, fg="red", text="ERROR: username must be 1-16 characters.")
        self.user_error2 = tk.Label(user_frame, fg="red", text="ERROR: username is taken. Try again.")
        self.user_error3 = tk.Label(user_frame, fg="red", text="ERROR: server may be down. Try relaunching app")

    def check_name(self, event=None):
        self.del_labels()
        self.controller.username = self.user_in.get()
        if len(self.controller.username) <= 0 or len(self.controller.username) > 16:
            self.user_error1.grid(row=0, column=1)
            return
        else:
            self.controller.client_socket.send(bytes(self.controller.username, "utf8"))
            msg = self.controller.client_socket.recv(self.controller.BUFSIZ).decode("utf8")
            if msg == "USERNAME_TAKEN":
                self.user_error2.grid(row=0, column=1)
                return
            elif msg == "USERNAME_OK":
                self.controller.frames["ChannelSelect"].refresh_rooms()
                self.controller.show_frame("ChannelSelect")
            else:
                self.user_error3.grid(row=0, column=1)

    def del_labels(self):
        self.user_error1.grid_forget()
        self.user_error2.grid_forget()
        self.user_error3.grid_forget()


class ChannelSelect(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        tk.Label(self, text="Available chatrooms:").pack(side="top", fill="x", pady=10)

        self.room_list = tk.Listbox(self, height=20, width=50, bg='#ffffff')
        self.room_list.pack(padx=15, fill='both')

        tk.Button(self, text="Refresh Rooms", command=self.refresh_rooms).pack(pady=(5,0))
        tk.Button(self, text="Select Room", command=self.select_room).pack(pady=(5,0))
        tk.Button(self, text="Create Rooms", command=self.create_room).pack(pady=5)

    def refresh_rooms(self):
        self.controller.client_socket.send(bytes("REFRESH_ROOMS", "utf8"))
        pickled_rooms = self.controller.client_socket.recv(self.controller.BUFSIZ)
        room_arr = pickle.loads(pickled_rooms)
        for key in room_arr:
            if key not in self.controller.rooms:
                try:
                    self.room_list.insert('end', key)
                    self.controller.rooms.append(key)
                except:
                    print(f"Unable to insert room: {key}")
        self.room_list.select_set(0)

    def select_room(self):
        try:
            selected = self.room_list.curselection()
        except:
            print("No room selected")
        value = self.room_list.get(selected[0])
        self.controller.client_socket.send(bytes("JOIN:" + value, "utf8"))
        self.controller.frames["ChatPage"].init_room()
        self.controller.show_frame("ChatPage")

    def create_room(self):
        value = "testRoom"
        self.controller.client_socket.send(bytes("CREATE_O:" + value, "utf8"))
        self.controller.frames["ChatPage"].init_room()
        self.controller.show_frame("ChatPage")


class ChatPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.recieve_thread = None
        
        chat_frame = tk.Frame(self, width=100, height=50, pady=10, padx=20)
        enter_frame = tk.Frame(self, width=100, height=50, pady=0, padx=10)
        #self.emoji_frame = tk.Frame(self, width=100, height=50, pady=0, padx=10)

        #self.photo = tk.PhotoImage(self)

        scrollbar = tk.Scrollbar(chat_frame)
        self.chat_list = tk.Text(chat_frame, height=20, width=60, yscrollcommand=scrollbar.set, bg="white")
        self.chat_list.config(state=tk.DISABLED)
        scrollbar.pack(side="right", fill="y")
        self.chat_list.pack(side="left", fill="both")
        chat_frame.pack()

        #entry_field = tk.Entry(self, textvariable=my_msg, bg="white")
        self.entry_field = tk.Text(enter_frame, bg="white", height=3, width = 40)
        self.entry_field.bind("<Return>", self.send)
        self.entry_field.pack(side="left", pady=5, padx=(0,10), fill="both")
        send_button = tk.Button(enter_frame, text="Send Image", command=self.send_image)
        send_button.pack(side="right", pady=5, padx=(0,5))
        #send_button = tk.Button(enter_frame, text="Emoji", command=self.display_emoji)
        #send_button.pack(side="right", pady=5, padx=(0,5))
        send_button = tk.Button(enter_frame, text="Send", command=self.send)
        send_button.pack(side="right", pady=5, padx=(0,5))
        
        
        enter_frame.pack()

        '''
        self.show_emoji = False
        tk.Button(self.emoji_frame, text="\U0001F600", command=lambda: self.emoji("\U0001F600")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F601", command=lambda: self.emoji("\U0001F601")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F606", command=lambda: self.emoji("\U0001F606")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F605", command=lambda: self.emoji("\U0001F605")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F923", command=lambda: self.emoji("\U0001F923")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F602", command=lambda: self.emoji("\U0001F602")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F642", command=lambda: self.emoji("\U0001F642")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F643", command=lambda: self.emoji("\U0001F643")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F609", command=lambda: self.emoji("\U0001F609")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F60A", command=lambda: self.emoji("\U0001F60A")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F60D", command=lambda: self.emoji("\U0001F60D")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F618", command=lambda: self.emoji("\U0001F618")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F60B", command=lambda: self.emoji("\U0001F60B")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F61C", command=lambda: self.emoji("\U0001F61C")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F611", command=lambda: self.emoji("\U0001F611")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F636", command=lambda: self.emoji("\U0001F636")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F928", command=lambda: self.emoji("\U0001F928")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F62C", command=lambda: self.emoji("\U0001F62C")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F62A", command=lambda: self.emoji("\U0001F62A")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F922", command=lambda: self.emoji("\U0001F922")).pack(side="right")
        tk.Button(self.emoji_frame, text="\U0001F635", command=lambda: self.emoji("\U0001F635")).pack(side="right")

    def display_emoji(self):
        if not self.show_emoji:
            self.emoji_frame.pack(pady=3)
            self.show_emoji = True
        else:
            self.emoji_frame.pack_forget()
            self.show_emoji = False

    def emoji(self, face):
        self.entry_field.insert(tk.END, face)
        self.entry_field.see(tk.END)
    '''

    def init_room(self):
        self.recieve_thread = Thread(target=self.recieve)
        self.recieve_thread.start()

    def recieve(self):
        while True:
            try:
                msg = self.controller.client_socket.recv(self.controller.BUFSIZ).decode("utf8")

                if msg == "CREATION_OK":
                    msg = "*** Your room has been created ***\n"
                elif msg == "JOIN_OK":
                    msg = "NEW_JOIN"
                    self.send(notif=msg)
                    continue
                '''
                elif msg == "IMAGE_SENT":
                    msg = self.controller.client_socket.recv(self.controller.BUFSIZ)#.decode("utf8")
                    msg = open(msg, 'wb')

                    photo = tk.PhotoImage(image=msg)
                    labelphoto = tk.Label(self, image=photo)
                    labelphoto.image = photo
                    self.chat_list.window_create(tk.END, window=labelphoto)
                    self.chat_list.insert(tk.END, ' \n')
                    self.chat_list.see(tk.END)
                    self.chat_list.config(state=tk.DISABLED)
                    msg.close()
                    continue
                '''

                self.chat_list.config(state=tk.NORMAL)
                self.chat_list.insert(tk.END, msg)
                self.chat_list.config(state=tk.DISABLED)
                self.chat_list.see(tk.END)
            except OSError:  # Possibly client has left the chat.
                print("something went wrong")
                self.chat_list.config(state=tk.NORMAL)
                self.chat_list.insert(tk.END, "Server has crashed, closing application")
                self.chat_list.config(state=tk.DISABLED)
                self.chat_list.see(tk.END)
                time.sleep(3)
                self.controller.terminate()
                break

    def send(self, event=None, notif=None):
        if notif == None:
            msg = self.entry_field.get("1.0", tk.END)
            self.entry_field.delete("1.0", tk.END)
            self.entry_field.mark_set("insert", "%d.%d" % (0,0))
        else:
            msg = notif
        if msg.strip() != "":
            print("Sent message:", msg, end=" ")
            self.controller.client_socket.send(bytes(msg, "utf8"))
        return 'break'

    def send_image(self):
        self.chat_list.config(state=tk.NORMAL)
        user = getpass.getuser()
        image_path = tk.filedialog.askopenfilename(initialdir='C:/Users/%s' % user)

        '''
        picture = open(image_path, 'rb')
        print(picture)
        self.controller.client_socket.send(bytes("IMAGE_SENT", "utf8"))
        self.controller.client_socket.send(picture)
        picture.clost()
        '''
        #image = Image.open(image_path)
        #print(image_path)
        #photo = tk.PhotoImage(self, file='Tiny6pixel.png')
        #self.photo = ImageTk.PhotoImage(image_path)
        #self.chat_list.image_create(tk.END, image=photo)
        #self.chat_list.image = photo

        #self.photo = ImageTk.PhotoImage(image_path)
        #self.chat_list.image_create(tk.END, image=photo)

        photo = tk.PhotoImage(file=image_path)
        labelphoto = tk.Label(self, image=photo)
        labelphoto.image = photo
        self.chat_list.window_create(tk.END, window=labelphoto)
        self.chat_list.insert(tk.END, ' \n')
        self.chat_list.see(tk.END)
        self.chat_list.config(state=tk.DISABLED)
        #labelphoto.pack()
        
        

if __name__ == "__main__":
    app = App()
    app.mainloop()
