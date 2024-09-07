from flask import Flask, jsonify, send_from_directory
import subprocess
import os
import json

app = Flask(__name__)

def run_scrapy_spider():
    try:
        # Chạy file Scrapy spider
        result = subprocess.run(['scrapy', 'runspider', '../tinydeal/spiders/special_offers.py'], capture_output=True, text=True)

        
        # In ra nội dung stdout từ kết quả chạy script
        print("Script Output:")
        print(result.stdout)
        
        # In ra lỗi nếu có
        if result.stderr:
            print("Script Error Output:")
            print(result.stderr)
        
    except Exception as e:
        print(f"Error occurred: {e}")

@app.route('/')
def index():
    # run_scrapy_spider()  # Chạy Scrapy spider để thu thập dữ liệu vào file JSON
    return send_from_directory('.', 'index.html')

@app.route('/run-script')
def run_script():
    try:
        # run_scrapy_spider()  # Chạy Scrapy spider để thu thập dữ liệu vào file JSON
        
        # Đọc dữ liệu từ file JSON nếu tồn tại
        if os.path.exists('data/data.json'):
            with open('data/data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'message': 'File data/data.json not found.'}), 500

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/data/data.json')
def json_data():
    return send_from_directory('.', 'data/data.json')

if __name__ == '__main__':
    app.run(debug=True)
