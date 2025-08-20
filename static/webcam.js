document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo webcam
    Webcam.set({
        width: 640,
        height: 480,
        image_format: 'jpeg',
        jpeg_quality: 90
    });
    Webcam.attach('#camera');

    // Xử lý chụp ảnh
    document.getElementById('capture-btn').addEventListener('click', function() {
        Webcam.snap(function(data_uri) {
            // Hiển thị ảnh vừa chụp
            document.getElementById('result').innerHTML = 
                `<img src="${data_uri}" style="max-width:100%; max-height:300px;"/>`;
            // Lưu data_uri vào input ẩn
            document.getElementById('image-data').value = data_uri;
        });
    });

    // Xử lý gửi form upload
    document.getElementById('upload-form').addEventListener('submit', function(e) {
        e.preventDefault();
        captureAndUpload();
    });
});

async function captureAndUpload() {
    const nameInput = document.getElementById('user-name');
    const name = nameInput.value.trim();
    const imageData = document.getElementById('image-data').value;
    const statusDiv = document.getElementById('status');
    
    // Reset trạng thái
    statusDiv.innerHTML = '';
    statusDiv.className = 'status';
    
    if (!name) {
        showStatus('Vui lòng nhập tên', 'error');
        return;
    }

    if (!imageData) {
        showStatus('Vui lòng chụp ảnh trước khi tải lên', 'error');
        return;
    }

    try {
        // Chuyển data URI sang Blob
        const blob = dataURItoBlob(imageData);
        const formData = new FormData();
        formData.append('file', blob, 'face.jpg');
        formData.append('name', name);

        // Hiển thị trạng thái đang tải
        showStatus('Đang tải lên...', '');
        
        // Gửi request
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        // Kiểm tra response
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Server responded with ${response.status}: ${text}`);
        }

        const result = await response.json();
        
        if (result.success) {
            showStatus(`Đã thêm khuôn mặt thành công: ${name}`, 'success');
            // Reset form
            document.getElementById('upload-form').reset();
            document.getElementById('result').innerHTML = '';
        } else {
            showStatus(`Lỗi: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Upload failed:', error);
        showStatus('Có lỗi xảy ra: ' + error.message, 'error');
    }
}

function dataURItoBlob(dataURI) {
    // Tách phần metadata và dữ liệu base64
    const split = dataURI.split(',');
    const byteString = atob(split[1]);
    const mimeString = split[0].split(':')[1].split(';')[0];

    // Tạo mảng byte
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }

    return new Blob([ab], { type: mimeString });
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = 'status';
    if (type) {
        statusDiv.classList.add(type);
    }
}