import os
import time
import shutil
import json
from database import Database
from watchdog.observers import Observer
from config import Config
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from llama_index.core.tools import QueryEngineTool
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader, SummaryIndex, VectorStoreIndex, Settings
from llama_index.core.query_engine.router_query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class FileProcessor:
    def __init__(self):
        self.file_queue = Queue()
        self.setup_llm()

    def setup_llm(self):
        os.environ['GROQ_API_KEY'] = Config.GROQ_API_KEY
        llm = Groq(model="llama3-8b-8192")
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.llm = llm
        Settings.embed_model = embed_model

    def get_router_query_engine(self, file_path):
        """Get router query engine."""
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        splitter = SentenceSplitter(chunk_size=1024)
        nodes = splitter.get_nodes_from_documents(documents)
        summary_index = SummaryIndex(nodes)
        vector_index = VectorStoreIndex(nodes)

        summary_query_engine = summary_index.as_query_engine(
            response_mode="tree_summarize",
            use_async=True,

        )
        vector_query_engine = vector_index.as_query_engine()

        summary_tool = QueryEngineTool.from_defaults(
            query_engine=summary_query_engine,
            description="Useful for summarization questions related to pdf"
        )

        vector_tool = QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
            description="Useful for retrieving specific context from the pdf."
        )

        query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[
                summary_tool,
                vector_tool,
            ],
            verbose=True
        )
        return query_engine

    def validate_data(self, invoice_data, products):
        # Ensure all necessary fields in invoice_data and products are not empty
        required_invoice_fields = ['CUIN', 'CN_No', 'CN_Date', 'Invoice_No', 'Buyers_PIN_No', 'Companys_PIN']
        required_product_fields = ['Product_Code', 'Description', 'Qty', 'Amount_Incl_Tax_USD', 'Amount_Incl_Tax_KES']
        
        for field in required_invoice_fields:
            if not invoice_data.get(field):
                print(f"Missing value for {field} in invoice data")
                raise ValueError(f"Missing value for {field} in invoice data")
        
        for product in products:
            for field in required_product_fields:
                if not product.get(field):
                    print(f"Missing value for {field} in invoice data")
                    raise ValueError(f"Missing value for {field} in product data")


    def process_file(self, file_path):
        try:
            query = """
            From the invoice extract the following properties.
            Return the result as a json with the following structure:
                  {
                    "invoice": {
                        "CUIN": " ",
                        "CN_No": " ",
                        "CN_Date": " ",
                        "Invoice_No": " ",
                        "Buyers_PIN_No": " ",
                        "Companys_PIN": " ",
                        "products": [{
                            "Product_Code": " ",
                            "Description": " " ,
                            "Qty": 0,
                            "Amount_Incl_Tax_USD": 0,
                            "Amount_Incl_Tax_KES": 0,
                        }]
                    }
                }
            """
            print(f"-------{file_path}")
            query_engine = self.get_router_query_engine(file_path)
            response = query_engine.query(query)
            cleaned_response = response.response.replace("Here is the answer:", "")
            response_data = json.loads(cleaned_response)
            
            invoice_data = response_data.get('invoice')
            self.validate_data(invoice_data, invoice_data.get('products'))
            
            processed_path = os.path.join(Config.PROCESSED_DIRECTORY, os.path.basename(file_path))
            shutil.move(file_path, processed_path)
            
            Database.insert_invoice(invoice_data, processed_path)
        except Exception as e:
            failed_path = os.path.join(Config.FAILED_DIRECTORY, os.path.basename(file_path))
            shutil.move(file_path, failed_path)
            Database.insert_failed_file(failed_path, str(e)+"+++"+str(response))

    def process_files_in_queue(self):
        while True:
            files_to_process = []
            while not self.file_queue.empty() and len(files_to_process) < Config.MAX_FILES_TO_PROCESS:
                files_to_process.append(self.file_queue.get())

            if files_to_process:
                with ThreadPoolExecutor(max_workers=len(files_to_process)) as executor:
                    print("********************************************")
                    executor.map(self.process_file, files_to_process)
            
            time.sleep(10)