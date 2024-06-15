import os
import shutil
from tqdm.auto import tqdm
from html import escape
import os
import shutil
from datetime import datetime
import json

import tkinter as tk
from tkinter import ttk

def backup(window, source_paths, destination_path, start=-1):
    # Ensure the destination path exists
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
        print('Destination path has been created')

    # Initialize counters
    new_copied_count, replaced_count, skipped_count, deleted_count = 0, 0, 0, 0

    # Initialize the overall progress bar
    total_files = 0
    for i in range(len(source_paths)):
        total_files += sum(len(files) for _, _, files in os.walk(source_paths[i]))
    overall_pbar = tqdm(total=total_files, desc='Overall Progress')  # Py
    description_label = tk.Label(window, text="Starting...")  # tk
    description_label.pack(pady=10)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Horizontal.TProgressbar",
                    thickness=30,  # Change thickness/height
                    troughcolor='grey',  # Background color
                    background='blue',  # Progress bar color
                    borderwidth=2,  # Border width
                    troughrelief='flat')  # Trough relief style (e.g., flat, raised)

    frame = tk.Frame(window)
    frame.pack(pady=10)
    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, maximum=total_files, mode="determinate",
                                   style="Custom.Horizontal.TProgressbar")
    progress_bar.pack(pady=10)
    style.configure("Custom.Horizontal.TLabel",
                    background='blue',  # Background color
                    foreground='white',  # Text color
                    borderwidth=2)  # Border width
    progress_label = tk.Label(frame, text="0%", anchor='center', background='blue', foreground='white')
    progress_label.place(relx=0.5, rely=0.5, anchor='center')

    # Iterate through source paths
    for source_path in source_paths:
        # Get the base directory name from the source path
        base_dir = os.path.basename(os.path.normpath(source_path))

        # Set up the destination path for the current source
        destination_dir = os.path.join(destination_path, base_dir)

        # If the destination path doesn't exist, create it
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Iterate through files and directories in the source path
        for root, dirs, files in os.walk(source_path):
            # Create the corresponding directory structure in the destination path
            relative_path = os.path.relpath(root, source_path)
            destination_root = os.path.join(destination_dir, relative_path)
            os.makedirs(destination_root, exist_ok=True)
            overall_pbar.set_description(f"Processing {root}")
            description_label.config(text=f"Processing {root}")

            # Copy new or modified files to the destination directory
            for file in files:  # Skip a few if the last update has failed to complete
                if overall_pbar.n < start:
                    pass
                else:
                    source_file = os.path.join(root, file)
                    destination_file = os.path.join(destination_root, file)

                    # Copy the file if it's new or modified (based on size)
                    if not os.path.exists(destination_file) or os.path.getsize(source_file) != os.path.getsize(
                            destination_file):
                        try:
                            shutil.copy2(source_file, destination_file)
                        except Exception as e:
                            print(f'{e}: {source_file}')
                        if not os.path.exists(destination_file):
                            new_copied_count += 1
                        else:
                            replaced_count += 1

                    else:
                        skipped_count += 1  # Increment for each file (including folders)
                    overall_pbar.update(1)
                    progress_bar['value'] += 1
                    window.update_idletasks()  # Update the UI

        # Remove deleted files from the destination directory
        for root, dirs, files in os.walk(destination_dir):
            for file in files:
                source_file = os.path.join(source_path, os.path.relpath(root, destination_dir), file)
                destination_file = os.path.join(root, file)

                # Delete the file if it's not present in the source path
                if not os.path.exists(source_file):
                    try:
                        os.remove(destination_file)
                        deleted_count += 1
                    except Exception as e:
                        print(f'{e}: {source_file}')

    # Close the overall progress bar
    overall_pbar.close()

    # Remove empty directories from the destination directory
    for root, dirs, files in os.walk(destination_dir, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the directory is empty
                os.rmdir(dir_path)
                print(f'Deleted an empty folder: {dir_path}')

    return new_copied_count, replaced_count, skipped_count, deleted_count


# In[2]:


def convert_bookmarks_to_html(bookmarks, output_file):
    with open(output_file, 'w', encoding='utf-8') as html_file:
        html_file.write('<!DOCTYPE html>\n')
        html_file.write('<html>\n<head>\n<title>Chrome Bookmarks</title>\n</head>\n<body>\n')
        html_file.write('<h1>Google Chrome Bookmarks</h1>\n<ul>\n')

        for item in bookmarks['roots']['bookmark_bar']['children']:
            write_bookmark_item(html_file, item)

        html_file.write('</ul>\n</body>\n</html>\n')


def write_bookmark_item(html_file, item, indentation=2):
    url = item.get('url', '')
    title = escape(item.get('name', 'Untitled'))

    html_file.write(' ' * indentation)
    if url:
        html_file.write(f'<li><a href="{url}" target="_blank">{title}</a></li>\n')
    else:
        html_file.write(f'<li>{title}</li>\n')

    if 'children' in item:
        html_file.write(' ' * (indentation + 2))
        html_file.write('<ul>\n')
        for child_item in item['children']:
            write_bookmark_item(html_file, child_item, indentation + 4)
        html_file.write(' ' * (indentation + 2))
        html_file.write('</ul>\n')


def handle_predefined(event):
    selected_value = combobox_var.get()
    backup_dict = {
        'Test': [r'C:\Users\avivl\Desktop\Test1'],
        'PC -> Backup': [r'C:\המדיה שלי', r'C:\הקבצים שלי', r'C:\Users\avivl\Desktop'],
        'Backup -> Backup2': [r'D:\גיבוי', r'D:\קבוע', r'D:\סרטי קולנוע'],
        'Only Movies': [r'D:\סרטי קולנוע'],
    }

    dest_dict = {
        'Test': r'C:\Users\avivl\Desktop\Test2',
        'PC -> Backup': r'D:\גיבוי',
        'Backup -> Backup2': r'E:\\',
        'Only Movies': r'E:\\'

    }

    source_paths = backup_dict[selected_value]
    destination_path = dest_dict[selected_value]

    new_copied_count, replaced_count, skipped_count, deleted_count = backup(window, source_paths, destination_path)
    text_for_show = f"\n\nBackup Completed: {new_copied_count} Copied, {replaced_count} Replaced, {skipped_count} Skipped & {deleted_count} Deleted! \n Compare:"
    text_label = tk.Label(window, text=text_for_show)
    text_label.pack()

    destination_list = [destination_path+"\\"+folder.split("\\")[-1] for folder in source_paths]
    for i in range(len(source_paths)):
        text_for_show += f"\n{sum(len(files) for _, _, files in os.walk(source_paths[i])), sum(len(files) for _, _, files in os.walk(destination_list[i])), destination_list[i]}"
        text_label.config(text=text_for_show)

    if selected_value == 'PC -> Backup':
        chrome_bookmarks_path = r'C:\Users\avivl\AppData\Local\Google\Chrome\User Data\Default\Bookmarks'  # Update with your Chrome profile path
        output_html_file = rf'D:\גיבוי\מועדפים ישן\Chrome Bookmarks {str(datetime.today()).split()[0]}.html'
        with open(chrome_bookmarks_path, 'r', encoding='utf-8') as bookmarks_file:
            bookmarks_data = json.load(bookmarks_file)
        convert_bookmarks_to_html(bookmarks_data, output_html_file)
        text_for_show += f"\nBookmarks converted to HTML. Output saved to {output_html_file}"
        text_label.config(text=text_for_show)

        shutil.copy2(os.path.abspath(__file__), destination_path+'\Backup.py')    #MainApp.py
        text_for_show += '\nThe updated script has been copied and the backup has been completed!'
        text_label.config(text=text_for_show)

    text_for_show += '\nDone!'
    text_label.config(text=text_for_show)