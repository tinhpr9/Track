from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)
stats_db = {}

def format_num(val):
    try:
        num = float(val)
        if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}B".replace(".0B", "B")
        elif num >= 1_000_000: return f"{num/1_000_000:.1f}M".replace(".0M", "M")
        elif num >= 1_000: return f"{num/1_000:.1f}K".replace(".0K", "K")
        if num == int(num): return str(int(num))
        return str(num)
    except: return str(val)

# BỘ LỌC ĐÃ ĐƯỢC NÂNG CẤP
def get_category(key):
    if key == 'Sheckles': return 'money'
    if 'Seed' in key: return 'seed'
    if any(x in key for x in ['Trowel', 'Basic Pot', 'Build', 'Shovel', 'Sprinkler', 'Watering Can']): return 'gear'
    
    # Chỉ nhận diện đúng tên Pet, loại bỏ trái cây
    pet_names = ['Bunny', 'Deer', 'Unicorn', 'Raccoon', 'IceSerpent', 'Robin', 'Turtle', 'BlackDragon', 'GoldenDragonfly', '[Active]']
    if any(x in key for x in pet_names) and 'Fruit' not in key: return 'pet'
    
    return 'other'

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
            
            .active-pet { border: 2px solid #f38ba8; box-shadow: 0 0 6px #f38ba8; }
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
                        {% for key, value in data.stats.items() %}{% if get_category(key) == 'money' %}
                            <span class="item-badge badge-money"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>
                    
                    <div class="category">
                        <div class="cat-title">🌱 Hạt Giống</div>
                        {% for key, value in data.stats.items() %}{% if get_category(key) == 'seed' %}
                            <span class="item-badge badge-seed"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">🛠️ Công Cụ (Gear)</div>
                        {% for key, value in data.stats.items() %}{% if get_category(key) == 'gear' %}
                            <span class="item-badge badge-gear"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>
                    
                    <div class="category">
                        <div class="cat-title">🐾 Thú Cưng</div>
                        {% for key, value in data.stats.items() %}{% if get_category(key) == 'pet' %}
                            <span class="item-badge badge-pet {% if 'Active' in key %}active-pet{% endif %}"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">📦 Khác</div>
                        {% for key, value in data.stats.items() %}{% if get_category(key) == 'other' %}
                            <span class="item-badge badge-other"><span class="stat-name">{{ key }}:</span> <span class="stat-val">{{ format_num(value) }}</span></span>
                        {% endif %}{% endfor %}
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
    return render_template_string(html_template, stats_db=stats_db, format_num=format_num, get_category=get_category)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
