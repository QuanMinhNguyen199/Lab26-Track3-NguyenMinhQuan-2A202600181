# Lab 26: SQLite MCP Server
Tên: Nguyễn Minh Quân - 2A202600181

## Tổng quan

Server MCP Python này dùng FastMCP để cung cấp truy cập vào một database SQLite. Dữ liệu mẫu gồm ba bảng:

- `students`
- `courses`
- `enrollments`

Công cụ được hỗ trợ:

- `search`
- `insert`
- `aggregate`

Tài nguyên schema MCP:

- `schema://database`
- `schema://table/{table_name}`

## Cấu trúc implementation

- `db.py` — lớp `SQLiteAdapter` chứa logic:
  - kết nối database
  - liệt kê bảng
  - lấy schema bảng
  - tìm kiếm với filter, pagination và sắp xếp
  - chèn dữ liệu an toàn
  - tổng hợp với COUNT / SUM / AVG / MIN / MAX
  - xác thực tên bảng, tên cột và toán tử lọc

- `init_db.py` — tạo `lab26.db`, schema và dữ liệu ban đầu.
- `mcp_server.py` — định nghĩa các tool và resource FastMCP, chạy server.
- `verify_server.py` — script kiểm tra nhanh các chức năng cơ bản.
- `tests/test_server.py` — bộ test pytest cho các công cụ và xử lý lỗi.

## Thiết lập

1. Tạo môi trường ảo và kích hoạt (Windows):

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Cài đặt phụ thuộc:

```powershell
pip install fastmcp pytest
```

3. Khởi tạo database:

```powershell
cd implementation
python init_db.py
```

## Chạy server

- Chạy server mặc định (stdio):

```powershell
python mcp_server.py
```

- Chạy server qua HTTP:

```powershell
python mcp_server.py --http
```

## Kiểm tra

- Kiểm tra nhanh mà không cần server:

```powershell
python verify_server.py
```

- Chạy pytest:

```powershell
python -m pytest tests/test_server.py -v
```

## Ví dụ sử dụng

### Search

```json
{
  "table": "students",
  "filters": {"cohort": "A1"},
  "order_by": "score",
  "descending": true
}
```

### Insert

```json
{
  "table": "students",
  "values": {"name": "Frank", "cohort": "C3", "score": 77.5}
}
```

### Aggregate

```json
{
  "table": "students",
  "metric": "AVG",
  "column": "score",
  "group_by": "cohort"
}
```

## Screenshot minh họa

Các screenshot đã có trong thư mục `screenshots/`:

- `Search.png`
- `SearchWithFilter(cohort, A1).png`
- `Insert.png`
- `Aggregate.png`
- `Resources.png`
- `Tools.png`
- Thư mục `ErrorHandling/` chứa ảnh minh họa xử lý lỗi

## Lưu ý

- `mcp_server.py` có thể chạy dưới hai transport: `stdio` hoặc `http`.
- `db.py` bảo vệ SQL bằng kiểm tra giá trị và không ghép chuỗi SQL trực tiếp với dữ liệu người dùng.
- Nếu cần demo, có thể sử dụng MCP client như Claude, Gemini CLI hoặc Inspector để gọi các tool và resource.