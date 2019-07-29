#!/usr/bin/python
import sys
import time
import logging
import os
import hashlib
import shutil
import RPi.GPIO
import pickle
import psutil
import datetime
from pprint import pprint
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class FileHashes:
    HashTable = dict() 
    PathToPersistentHashTable=""
    def __init__(self, path_to_persistent_hashtable):
        self.PathToPersistentHashTable = path_to_persistent_hashtable
        try:
            with open(self.PathToPersistentHashTable, 'rb') as f:
                self.HashTable=pickle.load(f);
        except:
            self.HashTable = dict()

    def file_seen(self, absolute_path):
        hashValue = self.get_file_hash(absolute_path)
        if hashValue in self.HashTable:
            return True
        return False

    def add_file(self, absolute_path):
        hashValue = self.get_file_hash(absolute_path)
        self.HashTable[hashValue]=True

    def get_file_hash(self, absolute_path):
        BLOCKSIZE = 65536
        hasher = hashlib.sha1()
        with open(absolute_path, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()

    def save(self):
        with open(self.PathToPersistentHashTable,'wb') as f:
                pickle.dump(self.HashTable, f, pickle.HIGHEST_PROTOCOL)

    def __del__(self):
        self.save()

HashTablePath = ".images.hash"
HashHandler = FileHashes(HashTablePath); #TODO [OOI] Find a better way to inject this
def PrintTimestamp(log):
        print("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] - " + log)
def get_files_in_directory(path, fileExtensionFilter=None):
    files_to_copy=[]
    try:
        for fileInPath in os.listdir(path):
            fullPath = os.path.join(path,fileInPath);
            if os.path.isdir(fullPath) is True:
                PrintTimestamp("Directory: "+ fullPath)
                subdirectory_files_to_copy=get_files_in_directory(fullPath, fileExtensionFilter)
                files_to_copy = files_to_copy + subdirectory_files_to_copy
            elif os.path.islink(fullPath) is True:
                PrintTimestamp("Link: "+ fullPath)
            elif os.path.isfile(fullPath) is True and (fileExtensionFilter is None or fileInPath.endswith(tuple(fileExtensionFilter))):
                files_to_copy.append(fullPath)
                PrintTimestamp("  File:"+ fullPath)
    except Exception as e:
        PrintTimestamp("Directory Unavailable:"+str(e))
    return files_to_copy
def copyFiles(fileHashes,  files_to_copy):
    PrintTimestamp("==============COPY=============")
    for file_to_copy in files_to_copy:
        if fileHashes.file_seen(file_to_copy) is False:
            PrintTimestamp ("File has not been copied before. Copying "+file_to_copy)
            sourcePath, filename = os.path.split(file_to_copy)
            #destination_path = os.path.join("/TemporaryImageHosting", filename);
            destination_path = os.path.join("/media/sda1/photos", filename);
            if os.path.exists(destination_path):
                PrintTimestamp("Filename "+ destination_path+" already exists. Skipping till next iteration to prevent duplicate.");
                continue
            try:
                while is_space_for_transfer(file_to_copy) is False:
                    PrintTimestamp("Not enough room to save file "+file_to_copy + ". Waiting for more disk space.");
                    time.sleep(5);
                shutil.copy2(file_to_copy, destination_path)
                fileHashes.add_file(file_to_copy)
                PrintTimestamp("Copied file "+file_to_copy)
            except Exception as e:
                PrintTimestamp("Unable to copy image "+file_to_copy+" to " + destination_path + ". Details: "+str(e));
        else:
            PrintTimestamp("Already seen file: "+file_to_copy);

    fileHashes.save()

def is_space_for_transfer(absolute_path_to_file):
    buffer_space = 536870912 #512 MB buffer
    file_size_in_bytes =  get_file_size_in_bytes(absolute_path_to_file)
    disk_stats = psutil.disk_usage('/')
    if disk_stats.free - buffer_space >= file_size_in_bytes:
        return True
    return False

def get_file_size_in_bytes(absolute_path_to_file):
    file_info = os.stat(absolute_path_to_file)
    return file_info.st_size

def on_created(event):
    allowed_extensions = ["jpg","jpeg","JPG","JPEG","tiff","TIFF"]
    if(os.path.ismount(event.src_path)):
        files_to_copy = get_files_in_directory(event.src_path, allowed_extensions)
        copyFiles(HashHandler, files_to_copy);
    else:
        PrintTimestamp("Not Mount Point: " + event.src_path)


def on_deleted(event):
    PrintTimestamp("Deleted: "+event.src_path)

def on_modified(event):
    PrintTimestamp("Modified: "+event.src_path)

def on_moved(event):
    PrintTimestamp("Moved: "+event.src_path)

if __name__ == "__main__":
    patterns="*"
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    #path = sys.argv[1] if len(sys.argv) > 1 else '.'
    path = '/media'
    observer = Observer()
    ignore_patterns = "pi"
    ignore_directories = False
    case_sensitive = False
    handler=PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    handler.on_created = on_created
    handler.on_deleted = on_deleted
    handler.on_modified = on_modified
    handler.on_moved = on_moved
    observer.schedule(handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
