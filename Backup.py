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

def is_video_file(file_path):
    """Check if file is a video file based on extension"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg', '.m2v', '.m4p', '.m4b', '.f4v', '.f4p', '.f4a', '.f4b'}
    return os.path.splitext(file_path.lower())[1] in video_extensions

def get_file_hash(file_path, chunk_size=8192):
    """Get MD5 hash of file for content verification"""
    import hashlib
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def should_copy_file(source_file, destination_file, is_video=False):
    """Determine if file should be copied based on type and comparison method"""
    if not os.path.exists(destination_file):
        return True, "new"
    
    if is_video:
        # For video files, use content hash for more reliable comparison
        source_hash = get_file_hash(source_file)
        dest_hash = get_file_hash(destination_file)
        
        if source_hash and dest_hash:
            if source_hash != dest_hash:
                return True, "replaced"
            else:
                return False, "skipped"
        else:
            # Fallback to size and mtime if hash fails
            source_size = os.path.getsize(source_file)
            dest_size = os.path.getsize(destination_file)
            source_mtime = os.path.getmtime(source_file)
            dest_mtime = os.path.getmtime(destination_file)
            
            if source_size != dest_size or source_mtime > dest_mtime:
                return True, "replaced"
            else:
                return False, "skipped"
    else:
        # For non-video files, use size and modification time
        source_mtime = os.path.getmtime(source_file)
        dest_mtime = os.path.getmtime(destination_file)
        source_size = os.path.getsize(source_file)
        dest_size = os.path.getsize(destination_file)
        
        if source_mtime > dest_mtime or source_size != dest_size:
            return True, "replaced"
        else:
            return False, "skipped"

def backup(window, source_paths, destination_path, start=-1):
    # Validate input parameters
    if not source_paths or not destination_path:
        raise ValueError("Source paths and destination path must be provided")
    
    # Check if source paths exist
    for source_path in source_paths:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source path does not exist: {source_path}")
    
    # Ensure the destination path exists
    if not os.path.exists(destination_path):
        try:
            os.makedirs(destination_path)
            print('Destination path has been created')
        except Exception as e:
            raise Exception(f"Failed to create destination path: {e}")

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

                    # Determine if this is a video file and use appropriate comparison method
                    is_video = is_video_file(source_file)
                    should_copy, copy_reason = should_copy_file(source_file, destination_file, is_video)
                    
                    if should_copy:
                        try:
                            shutil.copy2(source_file, destination_file)
                            if copy_reason == "new":
                                new_copied_count += 1
                            elif copy_reason == "replaced":
                                replaced_count += 1
                        except Exception as e:
                            print(f'Error copying {source_file}: {e}')
                            # Decrement counter if copy failed
                            if copy_reason == "new":
                                new_copied_count -= 1
                            elif copy_reason == "replaced":
                                replaced_count -= 1

                    else:
                        skipped_count += 1  # Increment for each file (including folders)
                    overall_pbar.update(1)
                    progress_bar['value'] += 1
                    # Update percent label text
                    try:
                        percent = int((progress_bar['value'] / progress_bar['maximum']) * 100) if progress_bar['maximum'] else 0
                        progress_label.config(text=f"{percent}%")
                    except Exception:
                        pass
                    window.update_idletasks()  # Update the UI

        # Remove deleted files from the destination directory
        for root, dirs, files in os.walk(destination_dir):
            for file in files:
                try:
                    # Calculate relative path from destination to source
                    relative_path = os.path.relpath(root, destination_dir)
                    source_file = os.path.join(source_path, relative_path, file)
                    destination_file = os.path.join(root, file)

                    # Delete the file if it's not present in the source path
                    if not os.path.exists(source_file):
                        os.remove(destination_file)
                        deleted_count += 1
                except Exception as e:
                    print(f'Error processing file {file} in {root}: {e}')

    # Close the overall progress bar and finalize UI to 100%
    overall_pbar.close()
    try:
        progress_bar['value'] = progress_bar['maximum']
        progress_label.config(text="100%")
        window.update_idletasks()
    except Exception:
        pass

    # Remove empty directories from all destination directories
    for source_path in source_paths:
        base_dir = os.path.basename(os.path.normpath(source_path))
        destination_dir = os.path.join(destination_path, base_dir)
        
        if os.path.exists(destination_dir):
            for root, dirs, files in os.walk(destination_dir, topdown=False):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        if not os.listdir(dir_path):  # Check if the directory is empty
                            os.rmdir(dir_path)
                            print(f'Deleted an empty folder: {dir_path}')
                    except Exception as e:
                        print(f'Error removing empty directory {dir_path}: {e}')

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


def handle_predefined(event, window):
    try:
        selected_value = event
        backup_dict = {
            'Test': [r'C:\Users\avivl\Desktop\Test1'],
            'PC -> Backup': [r'C:\המדיה שלי', r'C:\הקבצים שלי', r'C:\Users\avivl\Desktop'],
            'Backup -> Backup2': [r'D:\גיבוי', r'D:\קבוע', r'D:\Series', r'D:\סרטי קולנוע'],
            'Only Movies': [r'D:\סרטי קולנוע'],
        }

        dest_dict = {
            'Test': r'C:\Users\avivl\Desktop\Test2',
            'PC -> Backup': r'D:\גיבוי',
            'Backup -> Backup2': r'E:\\',
            'Only Movies': r'E:\\'
        }

        if selected_value not in backup_dict:
            raise ValueError(f"Unknown backup option: {selected_value}")

        source_paths = backup_dict[selected_value]
        destination_path = dest_dict[selected_value]

        new_copied_count, replaced_count, skipped_count, deleted_count = backup(window, source_paths, destination_path)
    except Exception as e:
        error_text = f"Backup failed: {str(e)}"
        error_label = tk.Label(window, text=error_text, fg='red')
        error_label.pack()
        return
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