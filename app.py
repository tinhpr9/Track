from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import time

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

def get_category(key):
    if key == 'Sheckles': return 'money'
    if 'Seed' in key: return 'seed'
    if any(x in key for x in ['Trowel', 'Basic Pot', 'Build', 'Shovel', 'Sprinkler', 'Watering Can']): return 'gear'
    pet_names = ['Bunny', 'Deer', 'Unicorn', 'Raccoon', 'IceSerpent', 'Robin', 'Turtle', 'BlackDragon', 'GoldenDragonfly', '[Active]']
    if any(x in key for x in pet_names) and 'Fruit' not in key: return 'pet'
    return 'other'

@app.route('/api/trackstats', methods=['POST'])
def receive_stats():
    try:
        data = request.json
        username = data.get('username')
        if not username: return jsonify({"error": "Thiếu tên"}), 400
        
        curr_time = time.time()
        user_stats = data.get('stats', {})
        sheckles = float(user_stats.get('Sheckles', 0))
        
        if username not in stats_db:
            stats_db[username] = {'history': [], 'stats': {}, 'sph': 0, 'last_ping': 0}
            
        history = stats_db[username]['history']
        
        if sheckles > 0:
            history.append((curr_time, sheckles))
            
        history = [h for h in history if curr_time - h[0] <= 3600]
        
        sph = 0
        if len(history) > 1:
            oldest_time, oldest_sheck = history[0]
            newest_time, newest_sheck = history[-1]
            time_diff = (newest_time - oldest_time) / 3600.0
            if time_diff > 0:
                sph = (newest_sheck - oldest_sheck) / time_diff
                
        stats_db[username].update({
            'stats': user_stats,
            'last_updated': datetime.now().strftime("%H:%M:%S"),
            'last_ping': curr_time, # Ghi nhận thời gian hoạt động cuối
            'history': history,
            'sph': max(0, sph)
        })
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def dashboard():
    total_stats = {}
    total_sph = 0
    online_count = 0
    offline_count = 0
    current_time = time.time()
    
    for user, data in stats_db.items():
        # Kiểm tra nếu mất kết nối quá 10 phút (600 giây)
        if current_time - data.get('last_ping', 0) <= 600:
            data['status'] = 'ON'
            online_count += 1
            total_sph += data.get('sph', 0) # Chỉ tính SPH cho máy đang chạy
        else:
            data['status'] = 'OFF'
            offline_count += 1
            
        for k, v in data.get('stats', {}).items():
            try: total_stats[k] = total_stats.get(k, 0) + float(v)
            except: pass

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bảng Điều Khiển Nông Trại</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; padding: 15px; margin: 0; }
            h2 { font-size: 20px; margin-top: 0; }
            
            .summary-card { background-color: #313244; border: 2px solid #f9e2af; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            .summary-title { font-size: 16px; font-weight: bold; color: #f9e2af; text-transform: uppercase; margin-bottom: 10px; border-bottom: 1px solid #45475a; padding-bottom: 5px; display: flex; justify-content: space-between; align-items: center;}
            
            .server-status { font-size: 13px; font-weight: normal; background: #181825; padding: 4px 10px; border-radius: 20px; border: 1px solid #45475a;}
            .txt-on { color: #a6e3a1; font-weight: bold; }
            .txt-off { color: #f38ba8; font-weight: bold; }

            .total-sheckles { font-size: 22px; font-weight: bold; color: #a6e3a1; margin-bottom: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 10px;}
            .sph-badge { background-color: #a6e3a1; color: #11111b; padding: 4px 8px; border-radius: 6px; font-size: 14px; font-weight: bold; }
            .summary-items { display: flex; flex-wrap: wrap; gap: 6px; font-size: 13px; }
            .sum-item { background: #181825; padding: 3px 8px; border-radius: 4px; border: 1px solid #45475a; }

            details { margin-bottom: 8px; background-color: #181825; border-radius: 8px; border: 1px solid #45475a; overflow: hidden; }
            summary { padding: 12px 15px; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; font-weight: bold; background-color: #313244; transition: background 0.2s; }
            summary:hover { background-color: #45475a; }
            summary::-webkit-details-marker { display: none; }
            details[open] summary { border-bottom: 1px solid #45475a; }
            
            .acc-name { display: flex; align-items: center; gap: 8px; font-size: 15px; }
            .acc-arrow { color: #89b4fa; transition: transform 0.2s; }
            details[open] .acc-arrow { transform: rotate(90deg); }
            
            .badge-on { background-color: rgba(166, 227, 161, 0.1); border: 1px solid #a6e3a1; color: #a6e3a1; font-size: 10px; padding: 2px 6px; border-radius: 12px; margin-left: 5px; }
            .badge-off { background-color: rgba(243, 139, 168, 0.1); border: 1px solid #f38ba8; color: #f38ba8; font-size: 10px; padding: 2px 6px; border-radius: 12px; margin-left: 5px; }
            
            .acc-quick-stats { display: flex; flex-direction: column; align-items: flex-end; font-size: 13px; }
            .acc-sheckles { color: #f9e2af; }
            .acc-sph { color: #a6e3a1; font-size: 12px; }
            .acc-time { color: #a6adc8; font-size: 11px; margin-top: 2px; }

            .acc-content { padding: 15px; }
            
            .category { margin-bottom: 12px; }
            .cat-title { font-size: 12px; text-transform: uppercase; color: #a6adc8; margin-bottom: 8px; font-weight: bold; border-bottom: 1px dashed #45475a; padding-bottom: 4px;}
            .item-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; display: inline-block; margin-bottom: 5px; font-weight: bold; border: 1px solid #45475a; }
            
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
        
        <div class="summary-card">
            <div class="summary-title">
                <span>🏆 TỔNG TÀI SẢN</span>
                <span class="server-status"><span class="txt-on">🟢 {{ online_count }} ON</span> | <span class="txt-off">🔴 {{ offline_count }} OFF</span></span>
            </div>
            
            <div class="total-sheckles">
                💰 {{ format_num(total_stats.get('Sheckles', 0)) }}
                {% if total_sph > 0 %}
                    <span class="sph-badge">🚀 +{{ format_num(total_sph) }}/giờ</span>
                {% endif %}
            </div>
            
            <div class="summary-items">
                {% for key, val in total_stats.items() %}
                    {% if key != 'Sheckles' %}
                        <span class="sum-item"><span style="color:#a6adc8">{{ key }}:</span> <b>{{ format_num(val) }}</b></span>
                    {% endif %}
                {% endfor %}
            </div>
        </div>

        {% for user, data in stats_db.items() %}
        <details>
            <summary>
                <div class="acc-name">
                    <span class="acc-arrow">▶</span>
                    <span>{{ user }}</span>
                    {% if data.status == 'ON' %}
                        <span class="badge-on">🟢 ONLINE</span>
                    {% else %}
                        <span class="badge-off">🔴 OFFLINE</span>
                    {% endif %}
                </div>
                <div class="acc-quick-stats">
                    <div class="acc-sheckles">💰 {{ format_num(data.stats.get('Sheckles', 0)) }}</div>
                    {% if data.sph > 0 and data.status == 'ON' %}
                        <div class="acc-sph">▲ +{{ format_num(data.sph) }}/h</div>
                    {% endif %}
                    <div class="acc-time">⌚ {{ data.last_updated }}</div>
                </div>
            </summary>
            
            <div class="acc-content">
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
            </div>
        </details>
        {% endfor %}
        
        <script>setTimeout(function(){ location.reload(); }, 30000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template, stats_db=stats_db, total_stats=total_stats, total_sph=total_sph, online_count=online_count, offline_count=offline_count, format_num=format_num, get_category=get_category)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
        
