import threading
from config import Config
from database import Database
from file_processor import FileProcessor
from file_watcher import FileWatcher
from invoice_api import InvoiceAPI, app

file_processor = None

def initialize():
    global file_processor
    Database.init_db()
    file_processor = FileProcessor()
    file_watcher = FileWatcher(file_processor)
    api = InvoiceAPI(file_processor)

    file_watcher_thread = threading.Thread(target=file_watcher.start)
    file_processor_thread = threading.Thread(target=file_processor.process_files_in_queue)
    
    file_watcher_thread.start()
    file_processor_thread.start()

initialize()

if __name__ == '__main__':
    app.run(debug=True)