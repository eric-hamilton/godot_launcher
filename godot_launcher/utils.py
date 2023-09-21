import os
import re
import random
import math
import zipfile
import platform
from datetime import datetime, timedelta
from godot_launcher.exceptions import *
from PyQt5.QtCore import QObject, pyqtSignal


class Signaler(QObject):
    percent_signal = pyqtSignal(int, int, int)
    install_finished_signal = pyqtSignal()
    download_finished_signal = pyqtSignal()
    unzip_percent_signal = pyqtSignal(int, int)
    unzip_finished_signal = pyqtSignal()
    message_queue = {}
    
    

    def emit_signal(self, signal_name, *args):
        if signal_name == "dl_percent":
            self.percent_signal.emit(*args)
            
        if signal_name == "install_finished":
            self.install_finished_signal.emit()
        
        if signal_name == "download_finished":
            self.download_finished_signal.emit()
        
        if signal_name == "unzip_percent":
            self.unzip_percent_signal.emit(*args)
            
        if signal_name == "unzip_finished":
            self.unzip_finished_signal.emit()

signaler = Signaler()


def time_diff_greater_than(date_str1, date_str2, p_days):
    time_format = "%Y-%m-%d_%H-%M-%S"
    date1 = datetime.strptime(date_str1, time_format)
    date2 = datetime.strptime(date_str2, time_format)
    difference = abs(date2 - date1)
    return difference > timedelta(days=p_days)
    
def get_machine_info():
    
    # This is commented out until I add linux/mac support
    #supported_os = ["windows", "linux", "darwin"]
    
    supported_os = ["windows"]
    os_name = platform.system().lower()
    if os_name not in supported_os:
        return False
    
    if os_name == "darwin":
        os_name = "mac_os"
        
    arch = platform.machine()
    bits = 0
    if arch.endswith('64'):
        bits = 64
    else:
        bits = 32
    
    return {"os_name":os_name, "bits":bits}

def get_download_url_for_platform(asset_data, use_mono):
    machine_info = get_machine_info()
    os_name = machine_info["os_name"]
    platform_tags = {
        "windows": "win",
        "mac_os": "macos",
        "linux": "linux"
    }
    
    platform_tag = platform_tags.get(os_name, "")
    bits = str(machine_info["bits"])
    
    for asset in asset_data.keys():
        if asset.endswith(".zip"):
            search_string = asset.split("stable")[1]
            if use_mono:                
                term = search_string.split("_")[1]
                if term == "mono":                    
                    if platform_tag+bits in search_string:
                        return asset_data[asset]
            else:
                if platform_tag and bits in search_string and "mono" not in search_string:
                    return asset_data[asset]

def get_latest_version(release_list):
    if not release_list:
        return ""
    
    pattern = r'\d+\.\d+(?:\.\d+)?'
    
    def compare_versions(version1, version2):
        parts1 = tuple(map(int, version1.split('.')))
        parts2 = tuple(map(int, version2.split('.')))
        
        if parts1 > parts2:
            return 1
        elif parts1 < parts2:
            return -1
        else:
            return 0

    latest_release = max(release_list, key=lambda x: re.search(pattern, x).group(0), default='',)
    return latest_release


def generate_hex(length):
    hex_digits = "0123456789abcdef"
    hex_string = ""
    for _ in range(length):
        hex_string += random.choice(hex_digits)
    return hex_string

import urllib.request

def download_file_with_progress(download_url, destination):
    def progress_hook(count, block_size, total_size):

        percent = int(count * block_size * 100 / total_size)
        signaler.emit_signal("dl_percent", count, block_size, total_size)

    urllib.request.urlretrieve(download_url, destination, reporthook=progress_hook)
    
    signaler.emit_signal("download_finished")

    
def unzip_file(source_file, output_dir):
    with zipfile.ZipFile(source_file, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
        
def unzip_file_with_progress(source_file, output_dir):
    def progress_hook(current, total):
        percent = int((current / total) * 100)
        signaler.emit_signal("unzip_percent", current, total)

    with zipfile.ZipFile(source_file, 'r') as zip_ref:
        total_files = len(zip_ref.infolist())
        extracted_files = 0

        for file_info in zip_ref.infolist():
            extracted_files += 1
            signaler.emit_signal("unzip_percent", extracted_files, total_files)

            zip_ref.extract(file_info, output_dir)

    signaler.emit_signal("unzip_finished")        
        
def convert_bytes(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])       

def get_executable_in_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.exe') and 'console' in file.lower():
                executable_path = os.path.join(root, file)
                return executable_path