# FIX: DELETE EMPTY FOLDERS FROM THE DESTINATION PATH!
# Firebase

from Backup import *
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']
CLIENT_SECRET_FILE = 'google_auth.json'


import tkinter as tk
from tkinter import ttk, messagebox

def login():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES)
    flow.run_local_server()
    credentials = flow.credentials
    # Use credentials.access_token to access Google APIs on behalf of the user
    print(credentials)

def toggle_action(selected_option):
    if selected_option == 1:
        input_label.pack_forget()  # Hide the input field and button
        input_field.pack_forget()
        add_button.pack_forget()
        combobox.pack()
        predefined_button_run.pack()


    elif selected_option == 2:
        # Show the list of predefined values

        predefined_button_run.pack_forget()
        input_label.pack()
        input_field.pack()
        add_button.pack()
        values_list.pack_forget()





def add_value():
    value = input_field.get()


if __name__ == '__main__':
    window = tk.Tk()
    window.title("Backup")
    window.geometry("800x600")

    login_button = tk.Button(window, text="Login with Google", command=login)
    login_button.pack(pady=20)

    # Create a variable to store the selected option
    toggle_var = tk.IntVar()

    # Create the toggle buttons
    predefined_button= tk.Radiobutton(window, text="Predefined", variable=toggle_var, value=1, command=lambda: toggle_action(toggle_var.get()))
    custom_button = tk.Radiobutton(window, text="Custom", variable=toggle_var, value=2,command=lambda: toggle_action(toggle_var.get()))



    # Predefined values
    options = ['Test', "PC -> Backup", "Backup -> Backup2", 'Only Movies']
    combobox_var = tk.StringVar(value=options[0])
    combobox = ttk.Combobox(window, textvariable=combobox_var, values=options)
    #combobox.bind("<<ComboboxSelected>>", handle_predefined)


    # Custom values
    input_label = tk.Label(window, text="Enter a value:")
    input_field = tk.Entry(window)
    predefined_button_run = tk.Button(window, text="Run Predefined Backup",
                                      command=lambda: handle_predefined(toggle_var.get()))
    add_button = tk.Button(window, text="Add Value", command=add_value)


    # Main screen
    predefined_button.pack()
    custom_button.pack()

    window.mainloop()