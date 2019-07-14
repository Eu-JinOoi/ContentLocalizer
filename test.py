#!/usr/bin/python
import sys
import time
import logging
import os
from pprint import pprint
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import PatternMatchingEventHandler

class ExternalStorageImageHandler(PatternMatchingEventHandler):
    patterns=["*.jpg","*.jpeg","*.JPG","*.JPEG","*.png","*.tiff"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            /media
        """
        # the file will be processed there
        print event.src_path, event.event_type  # print now only for degug
    def on_modified(self, event):
        self.process(event)
    def on_created(self, event):
        self.process(event)
def get_files_in_directory(path, files_to_copy, fileExtensionFilter=None):
    try:
        for fileInPath in os.listdir(path):
            fullPath = os.path.join(path,fileInPath);
            if os.path.isdir(fullPath) is True:
                print("Is Directory: "+ fullPath)
                get_files_in_directory(fullPath, fileExtensionFilter)
            elif os.path.islink(fullPath) is True:
                print("Is Link: "+ fullPath)
            elif os.path.isfile(fullPath) is True and (fileExtensionFilter is None or fileInPath.endswith(tuple(fileExtensionFilter))):
                files_to_copy.append(fullPath)
                print(" File:"+ fullPath)
    except Exception as e:
        print "Directory Unavailable:"+str(e)
def on_created(event):
    allowed_extensions = ["jpg","jpeg","JPG","JPEG","tiff","TIFF"]
    if(os.path.ismount(event.src_path)):
        get_files_in_directory(event.src_path, allowed_extensions)
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
    #patterns=["*.jpg","*.jpeg","*.JPG","*.JPEG","*.png","*.tiff"]
    patterns="*"
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    #event_handler = LoggingEventHandler()
    observer = Observer()
    #observer.schedule(ExternalStorageImageHandler, path, recursive=True)
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
