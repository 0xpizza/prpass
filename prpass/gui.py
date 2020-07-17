import threading

from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import pyperclip

from . import __version__
from .passwordgenerator import PasswordGenerator
from .util import ValuedThread


# coming soon!
class StyleChanger(Frame):
    '''
    Allow the user to choose between the various ugly ttk themes.
    Sorry user, there's not much to do about fixing the ugly.
    '''        



class CredentialEntry(Entry):
    '''
    Special Entry class that hides text when it loses focus.
    '''
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pw_char = b'\xe2\x80\xa2'.decode()
        self.bind("<FocusIn>", self.show_text)
        self.bind("<FocusOut>", self.hide_text)
        
    def hide_text(self, event):
        self.config(show=self.pw_char)
        
    def show_text(self, event):
        self.config(show='')
    


class PasswordLabel(Label):
    '''
    This widget hides your passwords until you click them!
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pw_char = b'\xe2\x80\xa2'.decode()
        self.bind('<Button-1>', self.show_text)
        self.bind('<ButtonRelease-1>', self.hide_text)
        
    def hide_text(self, event=None):
        if self.cget("text"):
            self.config(style="BB.TLabel")
        
    def show_text(self, event=None):
        self.config(style="WB.TLabel")

    

    
class About(Frame):
    '''
    This is a simple "about" page that reads the about.txt file and
    writes it on the screen. When the user clicks the confirmation 
    button, an indication file is created on the disk.
    '''
    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('callback')
        super().__init__(*args, **kwargs)
        
        txt = ScrolledText(self, height=1, width=1, wrap=WORD)
        btn = Button(self, text='Confirm', state=DISABLED, command=self.accept)
        
        txt.pack(fill=BOTH, expand=True, padx=40, pady=5)
        btn.pack(anchor='center', pady=6)
        
        with open('about.txt') as f:
            txt.insert(1.0, f.read())
        
        txt.configure(state=DISABLED)
        
        try:
            with open('confirmed') as f:
                btn.configure(state=NORMAL)
        except FileNotFoundError:
            self.after(3000, lambda: btn.configure(state=NORMAL))
        
    def accept(self):
        # creates the file
        open('confirmed', 'w').close()
        self.callback()
        
        
        
class InputInfo(Frame):
    def __init__(self, *args, **kwargs):
        self.about = kwargs.pop('about')
        super().__init__(*args, **kwargs)
        self.secret_hash = b''
        about_button = Label(self, text="About", style="GF.TLabel")
        self.pw = PasswordGenerator()
        
        # using a list instead of a dict to guarantee item order
        self._entry_refs = []  # this list corresponds with self.fields
        self.fields = [
                'name',
                'email',
                'username',
                'password',
                'service',
            ]

        self.init_body()        
        about_button.bind('<Button-1>', lambda e: self.about())
        about_button.pack(anchor=W)
    
    def _new_entry(self, parent):
        '''
        This method is used to create the text boxes that the user will
        enter the password entropy data into. The data itself is decoupled 
        into stringvar objects that are kept in a separate list. 
        '''
        s = StringVar()
        c = CredentialEntry(parent, textvariable=s, width=40)
        self._entry_refs.append(s)
        return c
        
    def init_body(self):
        '''
        this function builds the body of the object. 
        it should only be called once.
        '''
        f = Frame(self)
        f.pack(pady=5, anchor=E) # anonymous frame to hold hash selector and label
        Label(f, text='Hash function: ').pack(side=LEFT)
        
        algorithms = self.pw.available_algorithms
        self.algorithm_menu = Combobox(f, values=algorithms)
        self.algorithm_menu.pack(side=LEFT, padx=6)
        self.algorithm_menu.set(algorithms[0])
        self._prev_algo = algorithms[0]
        self.algorithm_menu.bind('<<ComboboxSelected>>', self.confirm_algo_change)
            
        Frame(self).pack(pady=5)  # spacer
        entry_frame = Frame(self)
        entry_frame.pack(fill=Y)
        for i, field in enumerate(self.fields):
            Label(entry_frame, text=field.title() + ':')\
                .grid(row=i, column=0, sticky=W, pady=4)
            c = self._new_entry(entry_frame)
            c.grid(row=i, column=1, sticky=E)
            if i  == 0:
                c.focus_set()
        
        Frame(self).pack(pady=5)  # spacer
        
        Button(self, text='Get Password', command=self.make_password).pack()

        # this will be used to show a password
        self.password_area = PasswordLabel(self, text='')
        self.password_area.pack(expand=True)
        self.password_area.bind('<Button-3>', self.copy_to_clipboard)
        
        # This is used to show information about the user's actions
        self.message_area = Label(self)
        self.message_area.pack(expand=True)

    
    def copy_to_clipboard(self, event=None):
        pw = self.password_area.cget("text")
        pyperclip.copy(pw)
        self.message_area.config(style='M.TLabel', text='Copied to clipboard')
        
        
    def confirm_algo_change(self, event=None):
        algo = self.algorithm_menu.get()
        if algo != self._prev_algo:
            c = messagebox.askyesno(
                'Warning', 
                ('Changing this will change all subsequent passwords. '
                'Are you sure you want to continue?')
            )
            if c is False:
                self.algorithm_menu.set(self._prev_algo)
            else:
                self._prev_algo = algo
                self.pw.set_algorithm(algo)
                
        
    
    def make_password(self):
        '''
        spawns another thread which executes the password crunch in another
        process. This is all done to avoid blocking tkinter.
        '''
        threading.Thread(target=self._make_password, daemon=True).start()
        
    def _make_password(self):
        '''
        this function blocks
        '''
        # this is probably a bad way to do it, but whatever
        # configure the pw object with out parameters:
        d = [e.get() for e in self._entry_refs]
        self.pw.data = d
        # TODO: break out into multiprocessing in case of longer crunch times
        p = ValuedThread(target=self.pw.make_password)
        p.start()
        p.join()
        if p.error:
            self.message_area.config(text=p.result, style='ER.TLabel')
            self.password_area.config(text='')
            self.password_area.show_text() # this should make it disappear
        else:
            self.message_area.config(text='')
            self.password_area.config(text=p.result)
            self.password_area.hide_text()
        
    


class App(Frame):
    '''
    Main view that handles the screen switching through callbacks
    in daughter views. This view has no widgets of its own and 
    only acts as a container for the application views.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # define views
        self.about = About(self, callback=self.return_from_about)
        self.info = InputInfo(self, about=self.show_about)
        
        # this makes the grid fill the available space, like pack
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.about.grid_rowconfigure(0, weight=1)
        self.about.grid_columnconfigure(0, weight=1)
        self.info.grid_rowconfigure(0, weight=1)
        self.info.grid_columnconfigure(0, weight=1)
        
        # gridding them in the same cell allows tkraise to switch them
        self.about.grid(column=0, row=0, sticky="nesw")
        self.info.grid(column=0, row=0, sticky="nesw")
        
        try:
            open('confirmed').close()
            self.info.tkraise()
        except FileNotFoundError:
            self.about.tkraise()
        
            
    def return_from_about(self):
        self.info.tkraise()
    
    
    def show_about(self):
        self.about.tkraise()
        
    
        
        
        

class Root(Tk):
    '''
    This is the root window that all the other widgets live inside of.
    It handles the widgets' style and creates the main screen.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry('400x330')
        self.title('prpass v' + __version__)
        self.style = Style(self)
        for theme in ('vista', 'clam'):
            if theme in self.style.theme_names():
                self.style.theme_use(theme)
                break
            
        self.style.configure("TEntry", padding=4)
        self.style.configure("TLabel", padding=3)
        self.style.configure("TFrame", background="white")
        self.style.configure("GF.TLabel", foreground="grey", font='helvitica 9')
        self.style.configure("BB.TLabel", background="black", font='courier 15')
        self.style.configure("WB.TLabel", background="white", font='courier 15')
        self.style.configure("ER.TLabel", foreground="red", font='courier 10')
        self.style.configure("M.TLabel", font='courier 10')
        
        App(self).pack(expand=True, fill=BOTH)


def run():
    Root().mainloop()

