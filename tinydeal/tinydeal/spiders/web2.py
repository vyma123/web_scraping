from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re
import unicodedata
import os
import time
import logging
import urllib.parse

# Thiết lập ghi log
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Hàm chuẩn hóa nội dung để tạo tên file hợp lệ, không dấu
def sanitize_filename(content):
    content = content.lower()
    content = unicodedata.normalize('NFKD', content).encode('ASCII', 'ignore').decode('ASCII')
    content = re.sub(r'\s+', '_', content)
    content = re.sub(r'[^\w]', '', content)
    return content[:255]

# Đường dẫn tùy chỉnh để lưu dữ liệu
output_directory = '../../views/data'  # Thay thế với đường dẫn của bạn
os.makedirs(output_directory, exist_ok=True)

# Hàm lấy HTML bằng Selenium
def fetch_html_with_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    retries = 3  # Số lần thử lại nếu có lỗi
    for attempt in range(retries):
        try:
            driver.get(url)
            driver.implicitly_wait(10)
            time.sleep(5)  # Thêm thời gian chờ để trang hoàn toàn tải
            return driver.page_source
        except Exception as e:
            logging.error(f"Error fetching {url} on attempt {attempt + 1}: {e}")
            time.sleep(5)  # Thời gian chờ giữa các lần thử lại
        finally:
            driver.quit()  # Đảm bảo driver được đóng

    return None

# Hàm trích xuất các phần tử theo class từ HTML
def extract_elements(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(class_='AdItem_wrapperAdItem__S6qPH AdItem_big__70CJq')

# URL của trang web
urls = [
    "https://www.chotot.com/mua-ban-quat?page=2",
    "https://www.chotot.com/mua-ban-quat?page=3",
    # "https://www.chotot.com/mua-ban-quat?page=4",
]

# Lấy HTML và xử lý dữ liệu
def getdata(url):
    html_content = fetch_html_with_selenium(url)

    if html_content:
        # Tải dữ liệu hiện có từ file để xác định ID tiếp theo
        try:
            with open(os.path.join(output_directory, 'data.json'), 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if not content:
                    existing_data = {'List': []}
                else:
                    existing_data = json.loads(content)
        except FileNotFoundError:
            existing_data = {'List': []}
        except json.JSONDecodeError:
            existing_data = {'List': []}
            logging.error(f"JSON decode error in data.json")

        # Xác định ID tiếp theo và các tiêu đề đã tồn tại
        if 'List' in existing_data and existing_data['List']:
            ids = [item.get('ID') for item in existing_data['List'] if 'ID' in item]
            ids = [int(id) for id in ids]
            last_id = max(ids) if ids else 0
            existing_titles = {item.get('Title') for item in existing_data['List'] if 'Title' in item}
        else:
            last_id = 0
            existing_titles = set()

        # Bộ đếm cho các ID duy nhất
        next_id = last_id + 1

        # Trích xuất các phần tử theo class
        elements = extract_elements(html_content)
        
        # Tạo danh sách chứa dữ liệu dưới dạng từ điển
        data_list = []
        
        for element in elements:
            # Xử lý ảnh
            img_tag = element.find('img')
            if img_tag:
                image_src = img_tag.get('src', '')
                
                if image_src.startswith('/_next/image?url='):
                    # Giải mã URL từ tham số 'url'
                    image_src = image_src.split('url=')[1].split('&')[0]
                    image_url = urllib.parse.unquote(image_src)
                elif image_src.startswith('http'):
                    image_url = image_src
                else:
                    image_url = 'No image'
                
                # Kiểm tra URL ảnh nếu là URL bắt đầu bằng 'https://static.chotot.com'
                if image_url.startswith('https://static.chotot.com'):
                    continue  # Bỏ qua item này

                # Kiểm tra URL ảnh nếu là URL mặc định
                if image_url == 'https://static.chotot.com/storage/chotot-icons/svg/user.svg':
                    image_url = 'No image'
            else:
                image_url = 'No image'
            
            # Xử lý tiêu đề
            title = element.find('h3', {'class': 'commonStyle_adTitle__g520j'})
            title_text = title.get_text(strip=True) if title else 'No title'
            
            # Xử lý liên kết
            link = "https://www.chotot.com/" + element.find('a')['href'] if element.find('a') else 'No link'
            
            # Xử lý giá
            price = element.find('p', {'class': 'AdBody_adPriceNormal___OYFU'})
            price_text = price.get_text(strip=True) if price else 'No price'
            
            # Xử lý vị trí
            location_elements = element.find_all('span', {'class': 'AdItemFooter_item__v9Cg0'})
            location_text = location_elements[-1].get_text(strip=True) if location_elements else 'No location'

            # Kiểm tra xem tiêu đề đã tồn tại trong tập các tiêu đề đã tồn tại chưa
            if title_text not in existing_titles:
                existing_titles.add(title_text)
                data_list.append({
                    'ID': next_id,
                    'Title': title_text,
                    'Link': link,
                    'Image URL': image_url,
                    'Price': price_text,
                    'Location': location_text
                })
                next_id += 1

        # Tìm thẻ h1 với class cụ thể
        soup = BeautifulSoup(html_content, 'html.parser')
        div_element = soup.find('span', {'itemprop': 'name', 'style': 'color:#222222'})
        
        if div_element:
            div_text = div_element.text.strip()
            div_text = ' '.join(div_text.split(' ')) if div_text else 'No content'
        else:
            div_text = 'No content'

        # Tạo một từ điển để chứa dữ liệu kết hợp với 'Content' xuất hiện trước 'List'
        new_data = {
            'Content': div_text,
            'List': data_list
        }

        # Cập nhật dữ liệu mới vào phần tử 'List'
        if 'List' in existing_data:
            existing_data['List'].extend(new_data['List'])
        else:
            existing_data['List'] = new_data['List']

        # Cập nhật phần tử 'Content'
        existing_data['Content'] = new_data['Content']

        # Tạo từ điển kết quả với 'Content' trước 'List'
        final_data = {
            'Content': existing_data.get('Content', 'No content'),
            'List': existing_data.get('List', [])
        }

        # Tạo tên file dựa trên nội dung 'Content'
        filename = sanitize_filename(final_data['Content']) + '.json'
        filepath = os.path.join(output_directory, filename)

        # Ghi dữ liệu cập nhật vào file JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(final_data, file, ensure_ascii=False, indent=4)
            logging.info(f"Dữ liệu từ URL: {url} đã ghi vào file: {filepath}")
        except IOError as e:
            logging.error(f"Error writing file {filepath}: {e}")
    else:
        logging.error(f"Lỗi khi lấy nội dung từ URL: {url}")
    time.sleep(6)  # Dừng 6 giây

for url in urls:
    logging.info(f"Đang xử lý URL: {url}")
    getdata(url)

# Tạo file tổng hợp từ tất cả các file JSON

# Thư mục chứa các file JSON
directory = output_directory

# Danh sách để chứa dữ liệu từ tất cả các file JSON
all_items = []

# Duyệt qua tất cả các file trong thư mục
for filename in os.listdir(directory):
    if filename.endswith('.json') and filename != 'data.json':
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                
                # Thêm nội dung file hiện tại vào danh sách
                all_items.append(data)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON from file {filename}")

# # Tạo dữ liệu tổng hợp
# combined_data = {
#     'Items': all_items
# }

# # Ghi dữ liệu tổng hợp vào file data.json
# with open(os.path.join(directory, 'data.json'), 'w', encoding='utf-8') as file:
#     json.dump(combined_data, file, ensure_ascii=False, indent=4)
