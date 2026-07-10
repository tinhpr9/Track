from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Bộ nhớ tạm để lưu chỉ số của toàn bộ dàn acc
stats_db = {}

# Đường dẫn để Script Roblox bắn dữ liệu về
@app.route('/api/trackstats', methods=['POST'])
def receive_stats():
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Thiếu tên tài khoản"}), 400
        
        # Cập nhật thông số mới nhất của acc đó vào bộ nhớ
        stats_db[username] = {
            'money': data.get('money', 0),
            'level': data.get('level', 0),
            'last_updated': datetime.now().strftime("%H:%M:%S")
        }
        return jsonify({"status": "Thành công"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Đường dẫn trang chủ để bạn xem bảng thống kê (Dashboard)
@app.route('/')
def dashboard():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bảng Điều Khiển Nông Trại</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; padding: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #45475a; padding: 12px; text-align: left; }
            th { background-color: #313244; color: #a6e3a1; }
            tr:nth-child(even) { background-color: #181825; }
        </style>
    </head>
    <body>
        <h2>📊 Tình trạng dàn máy Farm</h2>
        <p>Tự động tải lại trang sau 30 giây để cập nhật...</p>
        <table>
            <tr>
                <th>Tên Tài Khoản</th>
                <th>Tiền/Vàng</th>
                <th>Cấp Độ</th>
                <th>Lần cập nhật cuối</th>
            </tr>
            {% for user, stat in stats_db.items() %}
            <tr>
                <td>{{ user }}</td>
                <td>{{ stat.money }}</td>
                <td>{{ stat.level }}</td>
                <td>{{ stat.last_updated }}</td>
            </tr>
            {% endfor %}
        </table>
        <script>
            setTimeout(function(){ location.reload(); }, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, stats_db=stats_db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
  
