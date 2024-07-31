import os
from flask import Flask, jsonify
from database import Database
from config import Config
from flask import Flask, jsonify, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.WATCH_DIRECTORY
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB max-limit

class InvoiceAPI:
    def __init__(self, file_processor):
        self.file_processor = file_processor
        self.setup_routes()

    def setup_routes(self):
        @app.route('/', methods=['GET', 'POST'])
        def upload_files():
            if request.method == 'POST':
                uploaded_files = request.files.getlist("files")
                if not uploaded_files:
                    return redirect(request.url)
                
                for file in uploaded_files:
                    if file and self.allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                return redirect(url_for('upload_files'))
            
            return render_template('upload.html')
        
        @app.route("/status", methods=['GET'])
        def get_status():
            return {"message": "File watcher and processor are running", "queued_files": self.file_processor.file_queue.qsize()}, 200

        @app.route('/api/failed_invoices', methods=['GET'])
        def failed_invoices():
            try:
                failed_invoices = Database.get_failed_invoices()
                return jsonify(failed_invoices)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route('/api/invoices', methods=['GET'])
        def get_all_invoices_with_products():
            return jsonify(Database.get_all_invoices_with_products())
        
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}
    
    def run(self):
        app.run(debug=True)