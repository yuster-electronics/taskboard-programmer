from tkinter import *
from tkinter.ttk import Label, Style, Treeview
import serial.tools.list_ports
import serial
from PIL import Image, ImageTk

class Task():
    @staticmethod
    def calc_crc(text):
        crc = 0
        for c in text:
            crc ^= c
        return crc

    @staticmethod
    def clean_text(text):
        char_map = [
            ['å', 'a'],
            ['ä', 'a'],
            ['ö', 'o'],
            ['Å', 'A'],
            ['Ä', 'A'],
            ['Ö', 'O']
        ]
        text = text[:200]
        for pair in char_map:
            text = text.replace(pair[0], pair[1])
        return text

    @staticmethod
    def program(com, title, desc):
        title = Task.clean_text(title)
        desc = Task.clean_text(desc)

        bytestream = [0]
        bytestream += len(title).to_bytes(1)
        bytestream += bytes(title, 'utf-8')
        bytestream += len(desc).to_bytes(1)
        bytestream += bytes(desc, 'utf-8')
        crc = Task.calc_crc(bytestream)
        bytestream += crc.to_bytes(1)

        ser = serial.Serial(port=com,
                            baudrate=115200,
                            bytesize=8,
                            parity='N',
                            stopbits=1,
                            timeout=2,
                            dsrdtr=None)
        ser.setRTS(False)
        ser.setDTR(False)
        ser.write(bytestream)
        print(bytes(bytestream))

        recv_buf = ""
        while True:
            x = ser.read(8)
            if len(x) == 0:
                break
            else:
                recv_buf += x.decode('utf-8')
            if (recv_buf.rfind("_PowerOff") > 0):
                ser.read(8)
                break;

        print("done")
        ser.close()

class Programmer():
    def __init__(self, root):
        self.com = ""

        self.form_window = root
        self.form_window.title("TaskBoard")
        self.form_window.geometry("300x180")

        self.frame = Frame(self.form_window, width=250, height=122)
        self.frame.pack()
        self.frame.configure(bg='#cccccc')

        # Title entry
        self.T = Entry(self.form_window, justify='center', width=12, bd=0,
            bg="#cccccc", fg="#222222", font=("Pockota Bold", 20, "bold"))
        self.T.place(x=33, y=0, height=36, width=232)
        self.T.insert(index=0, string="Title") 

        # Description entry
        self.D = Text(self.form_window, height=4, width=29, bd=0, bg="#cccccc",
            fg="#222222", font=("Vaisala Sans Light", 10))
        self.D.place(x=33, y=42, height=74, width=232)
        self.D.insert(1.0, "Description") 

        # Program button
        self.B = Button(self.form_window, command=self.create_task,
            text="Create task", font=("Vaisala Sans Medium", 12, "bold"))
        self.B.place(x=140, y=130, height=36, width=130)

        # Refresh button
        self.R = Button(self.form_window, command=self.refresh_com_list,
            text="↺", font=("Vaisala Sans Medium", 12, "bold"))
        self.R.place(x=24, y=132, height=32, width=32)

        self.refresh_com_list()


    def refresh_com_list(self):
        # Preselect previously selected COM port if it is still available
        selection = None
        try:
            file = open("conf", "r")
            com = file.read()
            file.close()
        except:
            com = None
        ports = serial.tools.list_ports.comports()
        options = []
        for port, desc, hwid in sorted(ports):
            # print("{}: {}".format(port, desc))
            options.append(desc)
            if com != None and port == com:
                selection = com

        if len(options) == 0:
            options.append("No COM ports available")
            selection = "Select"
        else:
            if selection == None:
                selection = "Select"

        self.value_inside = StringVar(self.form_window, value=selection)
        self.O = OptionMenu(self.form_window, self.value_inside, *options, command=self.option_changed)
        self.O.place(x=56, y=130, height=36, width=80)

    def create_task(self):
        print("Selected COM: {}".format(self.value_inside.get()))
        print("Title: {}".format(self.T.get())) 
        print("Desc: {}".format(self.D.get("1.0",END))) 
        Task.program(self.value_inside.get(), self.T.get(), self.D.get("1.0",END))

    def option_changed(self, *args):
        line = self.value_inside.get().rstrip(")")
        com = line[line.rfind("(")+1:]
        self.value_inside.set(com)
        file = open("conf", "w")
        file.write(com)
        file.close()
        print(com)

if __name__ == "__main__":
    form_window = Tk()
    icon = ImageTk.PhotoImage(file = 'Yuster.ico')
    form_window.wm_iconphoto(False, icon)

    T = Task()
    P = Programmer(form_window)
    form_window.resizable(False, False)
    form_window.mainloop()
