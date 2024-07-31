import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import Config

class FileWatcher:
    def __init__(self, file_processor):
        self.file_processor = file_processor
        self.ensure_directories_exist()

    def ensure_directories_exist(self):
        directories = [
            Config.WATCH_DIRECTORY,
            Config.PROCESSED_DIRECTORY,
            Config.FAILED_DIRECTORY
        ]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

    class Handler(FileSystemEventHandler):
        def __init__(self, file_processor):
            self.file_processor = file_processor

        def on_created(self, event):
            if not event.is_directory:
                self.file_processor.file_queue.put(event.src_path)

    def enqueue_existing_files(self):
        for filename in os.listdir(Config.WATCH_DIRECTORY):
            file_path = os.path.join(Config.WATCH_DIRECTORY, filename)
            if os.path.isfile(file_path):
                self.file_processor.file_queue.put(file_path)
        print(f"Enqueued {self.file_processor.file_queue.qsize()} existing files.")

    def start(self):
        self.enqueue_existing_files()
        observer = Observer()
        observer.schedule(self.Handler(self.file_processor), path=Config.WATCH_DIRECTORY, recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()



