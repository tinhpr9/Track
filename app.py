from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)
stats_db = {}

# Hàm định dạng số thông minh thành K, M, B để hiển thị trên Web
def format_num(val):
    try:
        num = float(val)
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B".replace(".0B", "B")
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M".replace(".0M", "M")
        elif num >= 1_000:
            return f"{num/1_000:.1f}K".replace(".0K", "K")
        if num == int(num):
            return str(int(num))
        return str(num)
    except (ValueError, TypeError):
        return str(val)

@app.route('/api/trackstats', methods=['POST'])
def receive_stats():
    try:
        data = request.json
        username = data.get('username')
        if not username: return jsonify({"error": "Thiếu tên"}), 400
        
        stats_db[username] = {
            'stats': data.get('stats', {}),
            'last_updated': datetime.now().strftime("%H:%M:%S")
        }
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            .item-badge { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 4px 8px; border-radius: 4px; font-size: 13px; margin-right: 5px; display: inline-block; margin-bottom: 5px; font-weight: bold;}
            .stat-name { color: #89b4fa; }
            .stat-val { color: #f9e2af; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>📊 Tình trạng dàn máy Farm</h2>
        <p>Tự động tải lại trang sau 30 giây để cập nhật...</p>
        <table>
            <tr>
                <th>Tên Tài Khoản</th>
                <th>Thông Số & Vật Phẩm</th>
                <th>Cập nhật lúc</th>
            </tr>
            {% for user, data in stats_db.items() %}
            <tr>
                <td><strong>{{ user }}</strong></td>
                <td>
                    {% for key, value in data.stats.items() %}
                        <span class="item-badge">
                            <span class="stat-name">{{ key }}:</span> 
                            <span class="stat-val">{{ format_num(value) }}</span>
                        </span>
                    {% endfor %}
                </td>
                <td>{{ data.last_updated }}</td>
            </tr>
            {% endfor %}
        </table>
        <script>setTimeout(function(){ location.reload(); }, 30000);</script>
    </body>
    </html>
    """
    # Truyền hàm format_num vào trong giao diện HTML
    return render_template_string(html_template, stats_db=stats_db, format_num=format_num)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
