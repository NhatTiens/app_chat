# WeApRous – HTTP Backend · Proxy · ChatApp (CS) · P2P

Dự án mô phỏng hệ thống truyền thông gồm **Backend HTTP**, **Proxy reverse**, **ChatApp theo mô hình Client–Server**, và **P2P**.
Phục vụ bài tập lớn **CO3093/CO3094 – HCMUT**.

---

## 1) Yêu cầu môi trường

- **Python** ≥ 3.10 (khuyến nghị 3.12/3.13)
- Hệ điều hành: Windows / Linux / macOS
- Không phụ thuộc thư viện ngoài (dùng `socket`, `threading`, … của Python)

> **Lưu ý tương thích:** Nếu gặp lỗi `MutableMapping`, đã chuyển `from collections.abc import MutableMapping` trong `daemon/dictionary.py`.

---

## 2) Cấu trúc thư mục (rút gọn)

```
.
├─ daemon/
│  ├─ __init__.py
│  ├─ backend.py
│  ├─ httpadapter.py
│  ├─ request.py
│  ├─ response.py
│  ├─ dictionary.py
│  └─ p2p.py
├─ start_backend.py
├─ start_proxy.py
├─ start_sampleapp.py
├─ start_chatapp.py
├─ start_p2p.py
├─ static/
│  ├─ login.html
│  └─ index.html
├─ Images/
└─ README.md
```

---

## 3) Chạy nhanh

### Backend
```
python start_backend.py
```
Truy cập `http://localhost:9000/login.html`

### ChatApp Server
```
python start_chatapp.py
```

### P2P Peers
```
python start_p2p.py --peer-id tien --listen-port 4000
python start_p2p.py --peer-id long --listen-port 5000
```

---

## 4) API Backend

| Method | Path | Mô tả |
|-------:|------|-------|
| GET | /login.html | Trang đăng nhập |
| POST | /login | Xác thực người dùng |
| GET | /index.html | Trang chính |
| POST | /echo | Trả lại dữ liệu gửi đến |

---

## 5) API ChatApp

| Method | Path | Mô tả |
|-------:|------|-------|
| POST | /login | Đăng nhập |
| POST | /submit-info | Đăng ký peer |
| GET | /get-list | Lấy danh sách peer |
| POST | /connect-peer | Kết nối peer |
| POST | /broadcast-peer | Gửi tin broadcast |
| POST | /send-peer | Gửi tin nhắn trực tiếp |
| GET | /get-messages | Lấy tin nhắn |
| GET | /channels | Lấy danh sách kênh |

---

## 6) Demo flow

1. **Task 1A/1B** – Kiểm thử backend login, cookie, echo
2. **Task 2 (CS)** – Gửi thông tin peer, lấy danh sách, broadcast, gửi tin
3. **Task 2 (P2P)** – Kết nối và gửi tin nhắn giữa 2 peer



