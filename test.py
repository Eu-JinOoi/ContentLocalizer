#!/usr/bin/python
import sys
import time
import logging
import os
import hashlib
import shutil
import RPi.GPIO
import pickle
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
        #TODO Save Hash Table
        print "Destuct"
HashTablePath = ".images.hash"
HashHandler = FileHashes(HashTablePath); #TODO [OOI] Find a better way to inject this
def get_files_in_directory(path, fileExtensionFilter=None):
    files_to_copy=[]
    try:
        for fileInPath in os.listdir(path):
            fullPath = os.path.join(path,fileInPath);
            if os.path.isdir(fullPath) is True:
                print("Directory: "+ fullPath)
                subdirectory_files_to_copy=get_files_in_directory(fullPath, fileExtensionFilter)
                files_to_copy = files_to_copy + subdirectory_files_to_copy
            elif os.path.islink(fullPath) is True:
                print("Link: "+ fullPath)
            elif os.path.isfile(fullPath) is True and (fileExtensionFilter is None or fileInPath.endswith(tuple(fileExtensionFilter))):
                files_to_copy.append(fullPath)
                print("  File:"+ fullPath)
    except Exception as e:
        print "Directory Unavailable:"+str(e)
    return files_to_copy
def copyFiles(fileHashes,  files_to_copy):
    print("==============COPY=============")
    for file_to_copy in files_to_copy:
        if fileHashes.file_seen(file_to_copy) is False:
            print ("Need to Copy: "+file_to_copy)
            fileHashes.add_file(file_to_copy)
        else:
            print ("Already seen: "+file_to_copy);

    fileHashes.save()
def on_created(event):
    allowed_extensions = ["jpg","jpeg","JPG","JPEG","tiff","TIFF"]
    if(os.path.ismount(event.src_path)):
        files_to_copy = get_files_in_directory(event.src_path, allowed_extensions)
        copyFiles(HashHandler, files_to_copy);
    else:
        print("Not Mount Point: " + event.src_path)


def on_deleted(event):
    print("Deleted: "+event.src_path)
    #pprint(event)
def on_modified(event):
    print("Modified: "+event.src_path)
    #pprint(event)
def on_moved(event):
    print("Moved: "+event.src_path)
    #pprint(event)
if __name__ == "__main__":
    patterns="*"
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
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
