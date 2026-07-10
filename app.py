from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)
stats_db = {}

# Hàm định dạng số thông minh thành K, M, B
def format_num(val):
    try:
        num = float(val)
        if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}B".replace(".0B", "B")
        elif num >= 1_000_000: return f"{num/1_000_000:.1f}M".replace(".0M", "M")
        elif num >= 1_000: return f"{num/1_000:.1f}K".replace(".0K", "K")
        if num == int(num): return str(int(num))
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
            th, td { border: 1px solid #45475a; padding: 12px; text-align: left; vertical-align: top; }
            th { background-color: #313244; color: #a6e3a1; font-size: 16px; }
            tr:nth-child(even) { background-color: #181825; }
            
            .category { margin-bottom: 12px; }
            .cat-title { font-size: 13px; text-transform: uppercase; color: #a6adc8; margin-bottom: 6px; font-weight: bold; border-bottom: 1px dashed #45475a; padding-bottom: 4px;}
            
            .item-badge { padding: 4px 8px; border-radius: 4px; font-size: 13px; margin-right: 5px; display: inline-block; margin-bottom: 5px; font-weight: bold; border: 1px solid #45475a; }
            .stat-name { color: #cdd6f4; }
            .stat-val { font-weight: bold; }
            
            /* Bảng màu phân loại */
            .badge-money { background-color: #f9e2af; color: #11111b; border-color: #f9e2af; }
            .badge-money .stat-name { color: #11111b; }
            
            .badge-seed { background-color: #a6e3a1; color: #11111b; border-color: #a6e3a1; }
            .badge-seed .stat-name { color: #11111b; }
            
            .badge-gear { background-color: #89b4fa; color: #11111b; border-color: #89b4fa; }
            .badge-gear .stat-name { color: #11111b; }

            .badge-pet { background-color: #cba6f7; color: #11111b; border-color: #cba6f7; }
            .badge-pet .stat-name { color: #11111b; }
            
            .badge-other { background-color: #313244; }
            .badge-other .stat-val { color: #fab387; }
        </style>
    </head>
    <body>
        <h2>📊 Bảng Giám Sát Nông Trại</h2>
        <p>Tự động tải lại trang sau 30 giây để cập nhật dữ liệu mới nhất...</p>
        <table>
            <tr>
                <th width="15%">Tên Tài Khoản</th>
                <th width="75%">Kho Đồ (Đã Phân Loại)</th>
                <th width="10%">Cập nhật lúc</th>
            </tr>
            {% for user, data in stats_db.items() %}
            <tr>
                <td><strong style="font-size: 16px;">{{ user }}</strong></td>
                <td>
                    <div class="category">
                        <div class="cat-title">💰 Tiền Tệ</div>
                        {% for key, value in data.stats.items() %}
                            {% if key == 'Sheckles' %}
                                <span class="item-badge badge-money"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                            {% endif %}
                        {% endfor %}
                    </div>
                    
                    <div class="category">
                        <div class="cat-title">🌱 Hạt Giống</div>
                        {% for key, value in data.stats.items() %}
                            {% if 'Seed' in key %}
                                <span class="item-badge badge-seed"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                            {% endif %}
                        {% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">🛠️ Công Cụ (Gear)</div>
                        {% for key, value in data.stats.items() %}
                            {% if key in ['Trowel', 'Basic Pot', 'Build', 'Shovel'] or 'Sprinkler' in key or 'Watering Can' in key %}
                                <span class="item-badge badge-gear"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                            {% endif %}
                        {% endfor %}
                    </div>
                    
                    <div class="category">
                        <div class="cat-title">🐾 Thú Cưng</div>
                        {% for key, value in data.stats.items() %}
                            {% if key in ['Bunny', 'Deer', 'Unicorn', 'Raccoon', 'IceSerpent', 'Robin', 'Big Turtle', 'Huge Deer', 'Big Unicorn', 'BlackDragon', 'GoldenDragonfly'] %}
                                <span class="item-badge badge-pet"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                            {% endif %}
                        {% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">📦 Vật Phẩm Thu Hoạch / Khác</div>
                        {% for key, value in data.stats.items() %}
                            {% if key != 'Sheckles' and 'Seed' not in key and key not in ['Trowel', 'Basic Pot', 'Build', 'Shovel', 'Bunny', 'Deer', 'Unicorn', 'Raccoon', 'IceSerpent', 'Robin', 'Big Turtle', 'Huge Deer', 'Big Unicorn', 'BlackDragon', 'GoldenDragonfly'] and 'Sprinkler' not in key and 'Watering Can' not in key %}
                                <span class="item-badge badge-other"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                            {% endif %}
                        {% endfor %}
                    </div>
                </td>
                <td style="text-align: center;"><strong>{{ data.last_updated }}</strong></td>
            </tr>
            {% endfor %}
        </table>
        <script>setTimeout(function(){ location.reload(); }, 30000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template, stats_db=stats_db, format_num=format_num)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
