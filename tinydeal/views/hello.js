  // Hàm để lấy dữ liệu JSON
  async function fetchData() {
    try {
        // Thay đổi URL nếu cần thiết
        const response = await fetch('data.json');
        // Kiểm tra nếu phản hồi là OK
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        
        // Hiển thị dữ liệu lên trang
        document.getElementById('json-data').innerHTML = `
            <p>Name: ${data.title}</p>
            <p>Age: ${data.link}</p>

        `;
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
    }
}

// Gọi hàm để lấy dữ liệu khi trang được tải
fetchData();