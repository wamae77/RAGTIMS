import os
import platform

class Config:
    if platform.system() == "Windows":
        BASE_DIR = os.path.join(os.environ['ProgramData'], 'invoice_processor')
    elif platform.system() == "Darwin":  # macOS
        BASE_DIR = os.path.join('/Library/Application Support', 'invoice_processor')
    else:  # Assume Linux/Unix
        BASE_DIR = os.path.join('/var/opt', 'invoice_processor')

    # Define subdirectories
    WATCH_DIRECTORY = os.path.join(BASE_DIR, 'watch')
    PROCESSED_DIRECTORY = os.path.join(BASE_DIR, 'extracted')
    FAILED_DIRECTORY = os.path.join(BASE_DIR, 'failed')
    MAX_FILES_TO_PROCESS = 5
    DB_PATH = "processed_files.db"
    GROQ_API_KEY = "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"
    ALLOWED_EXTENSIONS = {'pdf'}
