import os
import shutil
from tqdm.auto import tqdm
from html import escape
from datetime import datetime
import json
import logging

import tkinter as tk
from tkinter import ttk

# Configure logging with RTL support
class RTLFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        # Reverse Hebrew text segments for better readability
        msg = self._fix_hebrew_display(msg)
        return msg
    
    def _fix_hebrew_display(self, text):
        """Fix Hebrew text display by reversing Hebrew segments"""
        import re
        
        # Find Hebrew text segments
        hebrew_pattern = r'[\u0590-\u05FF\u200F]+'
        hebrew_segments = re.findall(hebrew_pattern, text)
        
        # Replace each Hebrew segment with its reversed version
        for segment in hebrew_segments:
            reversed_segment = segment[::-1]  # Reverse the Hebrew text
            text = text.replace(segment, reversed_segment, 1)
        
        return text

# Create custom formatter
formatter = RTLFormatter('%(asctime)s - %(levelname)s - %(message)s')

# Configure logging
file_handler = logging.FileHandler('backup.log', encoding='utf-8')
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

def is_video_file(file_path):
    """Check if file is a video file based on extension"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg', '.m2v', '.m4p', '.m4b', '.f4v', '.f4p', '.f4a', '.f4b'}
    return os.path.splitext(file_path.lower())[1] in video_extensions

def get_file_hash(file_path, chunk_size=8192, max_size=100*1024*1024):
    """Get MD5 hash of file for content verification with size limit"""
    import hashlib
    
    # For very large files, only hash first and last chunks for performance
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Hash first chunk
                first_chunk = f.read(chunk_size)
                hash_md5.update(first_chunk)
                
                # Hash last chunk
                f.seek(-chunk_size, 2)  # Seek to last chunk
                last_chunk = f.read(chunk_size)
                hash_md5.update(last_chunk)
                
                # Include file size in hash for better uniqueness
                hash_md5.update(str(file_size).encode())
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating hash for {file_path}: {e}")
            return None
    else:
        # For smaller files, use full hash
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating hash for {file_path}: {e}")
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

def backup(window, source_paths, destination_path, start=-1, ui_elements=None):
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
            logging.info('Destination path has been created')
        except Exception as e:
            raise Exception(f"Failed to create destination path: {e}")

    # Initialize counters and performance tracking
    new_copied_count, replaced_count, skipped_count, deleted_count = 0, 0, 0, 0
    start_time = datetime.now()
    bytes_copied = 0

    # Initialize the overall progress bar
    total_files = 0
    for source_path in source_paths:
        total_files += sum(len(files) for _, _, files in os.walk(source_path))
    overall_pbar = tqdm(total=total_files, desc='Overall Progress')  # Py
    
    # Create UI elements only if not provided
    if ui_elements is None:
        ui_elements = {}
        
        # Enhanced UI elements
        ui_elements['description_label'] = tk.Label(window, text="Starting backup...", font=("Arial", 10))
        ui_elements['description_label'].pack(pady=5)
        
        ui_elements['current_file_label'] = tk.Label(window, text="", font=("Arial", 8), fg="gray")
        ui_elements['current_file_label'].pack(pady=2)
        
        ui_elements['stats_frame'] = tk.Frame(window)
        ui_elements['stats_frame'].pack(pady=5)
        
        ui_elements['speed_label'] = tk.Label(ui_elements['stats_frame'], text="Speed: 0 MB/s", font=("Arial", 8))
        ui_elements['speed_label'].pack(side=tk.LEFT, padx=10)
        
        ui_elements['eta_label'] = tk.Label(ui_elements['stats_frame'], text="ETA: Calculating...", font=("Arial", 8))
        ui_elements['eta_label'].pack(side=tk.LEFT, padx=10)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Horizontal.TProgressbar",
                    thickness=30,  # Change thickness/height
                    troughcolor='grey',  # Background color
                    background='blue',  # Progress bar color
                    borderwidth=2,  # Border width
                    troughrelief='flat')  # Trough relief style (e.g., flat, raised)

    ui_elements['frame'] = tk.Frame(window)
    ui_elements['frame'].pack(pady=10)
    ui_elements['progress_bar'] = ttk.Progressbar(ui_elements['frame'], orient="horizontal", length=500, maximum=total_files, mode="determinate",
                                   style="Custom.Horizontal.TProgressbar")
    ui_elements['progress_bar'].pack(pady=10)
    style.configure("Custom.Horizontal.TLabel",
                    background='blue',  # Background color
                    foreground='white',  # Text color
                    borderwidth=2)  # Border width
    ui_elements['progress_label'] = tk.Label(ui_elements['frame'], text="0%", anchor='center', background='blue', foreground='white')
    ui_elements['progress_label'].pack(pady=5)

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
            ui_elements['description_label'].config(text=f"Processing {root}")

            # Copy new or modified files to the destination directory
            for file in files:  # Skip a few if the last update has failed to complete
                if start > -1 and overall_pbar.n < start:
                    overall_pbar.update(1)
                    ui_elements['progress_bar']['value'] += 1
                    continue
                    source_file = os.path.join(root, file)
                    destination_file = os.path.join(destination_root, file)

                    # Determine if this is a video file and use appropriate comparison method
                    is_video = is_video_file(source_file)
                    should_copy, copy_reason = should_copy_file(source_file, destination_file, is_video)
                    
                    
                    if should_copy:
                        try:
                            # Track file size for speed calculation
                            file_size = os.path.getsize(source_file)
                            copy_start = datetime.now()
                            
                            shutil.copy2(source_file, destination_file)
                            bytes_copied += file_size
                            
                            if copy_reason == "new":
                                new_copied_count += 1
                            elif copy_reason == "replaced":
                                replaced_count += 1
                                
                            # Calculate and update speed/ETA
                            elapsed_time = (datetime.now() - start_time).total_seconds()
                            if elapsed_time > 0:
                                speed_mbps = (bytes_copied / (1024 * 1024)) / elapsed_time
                                remaining_files = total_files - overall_pbar.n
                                if speed_mbps > 0:
                                    eta_seconds = (remaining_files * (file_size / (1024 * 1024))) / speed_mbps
                                    eta_text = f"ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s" if eta_seconds > 60 else f"ETA: {int(eta_seconds)}s"
                                else:
                                    eta_text = "ETA: Calculating..."
                                
                                ui_elements['speed_label'].config(text=f"Speed: {speed_mbps:.1f} MB/s")
                                ui_elements['eta_label'].config(text=eta_text)
                                
                        except Exception as e:
                            logging.error(f'Error copying {source_file}: {e}')
                            # Decrement counter if copy failed
                            if copy_reason == "new":
                                new_copied_count -= 1
                            elif copy_reason == "replaced":
                                replaced_count -= 1

                    else:
                        skipped_count += 1  # Increment for each file (including folders)
                    overall_pbar.update(1)
                    ui_elements['progress_bar']['value'] += 1
                    
                    # Update UI less frequently for better performance (every 10 files or at end)
                    if ui_elements['progress_bar']['value'] % 10 == 0 or ui_elements['progress_bar']['value'] == ui_elements['progress_bar']['maximum']:
                        try:
                            percent = int((ui_elements['progress_bar']['value'] / ui_elements['progress_bar']['maximum']) * 100) if ui_elements['progress_bar']['maximum'] else 0
                            ui_elements['progress_label'].config(text=f"{percent}%")
                            window.update_idletasks()  # Update the UI
                        except Exception as e:
                            logging.warning(f"Failed to update progress label: {e}")

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
                    logging.error(f'Error processing file {file} in {root}: {e}')

    # Close the overall progress bar and finalize UI to 100%
    overall_pbar.close()
    try:
        ui_elements['progress_bar']['value'] = ui_elements['progress_bar']['maximum']
        ui_elements['progress_label'].config(text="100%")
        
        # Final statistics
        total_time = (datetime.now() - start_time).total_seconds()
        avg_speed = (bytes_copied / (1024 * 1024)) / total_time if total_time > 0 else 0
        
        ui_elements['current_file_label'].config(text="Backup completed!")
        ui_elements['speed_label'].config(text=f"Final Speed: {avg_speed:.1f} MB/s")
        ui_elements['eta_label'].config(text=f"Total Time: {int(total_time//60)}m {int(total_time%60)}s")
        
        window.update_idletasks()
    except Exception as e:
        logging.warning(f"Error finalizing UI: {e}")

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
                            logging.info(f'Deleted an empty folder: {dir_path}')
                    except Exception as e:
                        logging.error(f'Error removing empty directory {dir_path}: {e}')

    return new_copied_count, replaced_count, skipped_count, deleted_count, bytes_copied, total_time


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


def handle_predefined(event, window, ui_elements):
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

        new_copied_count, replaced_count, skipped_count, deleted_count, bytes_copied, total_time = backup(window, source_paths, destination_path, -1, ui_elements)
    except Exception as e:
        error_text = f"Backup failed: {str(e)}"
        error_label = tk.Label(window, text=error_text, fg='red')
        error_label.pack()
        return
    # Enhanced summary display
    total_processed = new_copied_count + replaced_count + skipped_count + deleted_count
    data_size_gb = bytes_copied / (1024 * 1024 * 1024)
    avg_speed = (bytes_copied / (1024 * 1024)) / total_time if total_time > 0 else 0
    
    summary_text = f"""Backup Summary:
Files: {new_copied_count} New, {replaced_count} Replaced, {skipped_count} Skipped, {deleted_count} Deleted
Data: {data_size_gb:.2f} GB processed
Total Time: {int(total_time//60)}m {int(total_time%60)}s
Average Speed: {avg_speed:.1f} MB/s

Comparison:"""
    
    text_label = tk.Label(window, text=summary_text, font=("Arial", 9), justify=tk.LEFT)
    text_label.pack(pady=10)

    # Build comparison text more efficiently
    comparison_lines = []
    for i, source_path in enumerate(source_paths):
        base_name = os.path.basename(os.path.normpath(source_path))
        dest_path = os.path.join(destination_path, base_name)
        
        try:
            source_count = sum(len(files) for _, _, files in os.walk(source_path))
            dest_count = sum(len(files) for _, _, files in os.walk(dest_path)) if os.path.exists(dest_path) else 0
            comparison_lines.append(f"\nSource: {source_count}, Dest: {dest_count}, Path: {dest_path}")
        except Exception as e:
            comparison_lines.append(f"\nError comparing {dest_path}: {e}")
    
    comparison_text = summary_text + "".join(comparison_lines)
    text_label.config(text=comparison_text)

    if selected_value == 'PC -> Backup':
        chrome_bookmarks_path = r'C:\Users\avivl\AppData\Local\Google\Chrome\User Data\Default\Bookmarks'  # Update with your Chrome profile path
        output_html_file = rf'D:\גיבוי\מועדפים ישן\Chrome Bookmarks {str(datetime.today()).split()[0]}.html'
        with open(chrome_bookmarks_path, 'r', encoding='utf-8') as bookmarks_file:
            bookmarks_data = json.load(bookmarks_file)
        convert_bookmarks_to_html(bookmarks_data, output_html_file)
        bookmarks_text = comparison_text + f"\n\nBookmarks converted to HTML. Output saved to {output_html_file}"
        text_label.config(text=bookmarks_text)

        # Copy current script to backup location
        try:
            script_dest = os.path.join(destination_path, 'Backup.py')
            shutil.copy2(os.path.abspath(__file__), script_dest)
            logging.info(f"Script copied to {script_dest}")
        except Exception as e:
            logging.error(f"Failed to copy script: {e}")
        final_text = bookmarks_text + '\n\nThe updated script has been copied and the backup has been completed!\nDone!'
    else:
        final_text = comparison_text + '\n\nDone!'
    
    text_label.config(text=final_text)