# Fix FB:
    # 1. Add source path
    # 2. Add- source/dest path
    # 3. Support delete
    # 4. Force login
# FIX: DELETE EMPTY FOLDERS FROM THE DESTINATION PATH!


from Backup import *
from Firebase import *

import tkinter as tk
from tkinter import ttk, messagebox

def login():
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    import googleapiclient

    SCOPES = ['https://www.googleapis.com/auth/userinfo.email',
              'https://www.googleapis.com/auth/userinfo.profile',
              'openid']
    CLIENT_SECRET_FILE = 'google_auth.json'
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES)
    flow.run_local_server()
    credentials = flow.credentials
    # Use credentials.access_token to access Google APIs on behalf of the user

    if credentials:
        from googleapiclient.discovery import build
        user_email = build('oauth2', 'v2', credentials=credentials).userinfo().get().execute()['email']
        return user_email
    raise LoginError('Authentication Failed')

def handle_login():
    user_email = login()
    if user_email:
        username.set(user_email)  # Update label text with user's email
        doc = get_or_create_user(user_email)
        print(doc)


def toggle_action(selected_option):
    if selected_option == 1:
        input_label.pack_forget()  # Hide the input field and button
        input_field.pack_forget()
        add_button.pack_forget()
        combobox.pack()
        predefined_button_run.pack()


    elif selected_option == 2:
        predefined_button_run.pack_forget()    # Hide the list of predefined values
        input_label.pack()
        input_field.pack()
        add_button.pack()
        #values_list.pack_forget()


def add_value():
    global username
    print(username)
    user_doc = find_user(username)
    print(user_doc)
    add_path(user_doc, input_field.get())



if __name__ == '__main__':
    window = tk.Tk()
    window.title("Backup")
    window.geometry("800x600")

    username = tk.StringVar()
    username_label = tk.Label(window, textvariable=username)  # Corrected: use textvariable=username
    username_label.pack(pady=20)

    login_button = tk.Button(window, text="Login with Google", command=handle_login)
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
    #combobox.bind("<<ComboboxSelected>>", lambda event: print(combobox_var.get()))
    predefined_button_run = tk.Button(window, text="Run Predefined Backup",
                                      command=lambda: handle_predefined(combobox_var.get(), window))


    # Custom values
    input_label = tk.Label(window, text="Enter a Source Path or a Destination Path:")
    input_field = tk.Entry(window)
    add_button = tk.Button(window, text="Add", command=add_value)


    # Main screen
    predefined_button.pack()
    custom_button.pack()

    window.mainloop()