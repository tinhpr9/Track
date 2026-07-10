from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import time, json, os

app = Flask(__name__)
DB_FILE = "farm_data.json"

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            stats_db = json.load(f)
            if 'accounts' not in stats_db: stats_db = {'accounts': {}, 'history_logs': []}
    except:
        stats_db = {'accounts': {}, 'history_logs': []}
else:
    stats_db = {'accounts': {}, 'history_logs': []}

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats_db, f, ensure_ascii=False, indent=2)

def format_num(val):
    try:
        num = float(val)
        if num >= 1_000_000_000: return f"{num/1_000_000_000:.2f}B"
        elif num >= 1_000_000: return f"{num/1_000_000:.2f}M"
        elif num >= 1_000: return f"{num/1_000:.1f}K"
        if num == int(num): return str(int(num))
        return str(num)
    except: return str(val)

def get_category(key):
    if key == 'Sheckles': return 'money'
    if '[Planted]' in key: return 'planted'
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
        new_sheckles = float(user_stats.get('Sheckles', 0))
        
        if username not in stats_db['accounts']:
            stats_db['accounts'][username] = {'stats': {}, 'last_ping': 0, 'sph': 0, 'sheckles_history': []}
            
        acc = stats_db['accounts'][username]
        old_sheckles = float(acc['stats'].get('Sheckles', 0))
        
        if old_sheckles > 0 and new_sheckles != old_sheckles:
            diff = new_sheckles - old_sheckles
            action = "TĂNG" if diff > 0 else "GIẢM"
            log_entry = {
                "time": (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m %H:%M:%S"),
                "user": username,
                "action": action,
                "amount": abs(diff),
                "new_total": new_sheckles
            }
            stats_db['history_logs'].insert(0, log_entry)
            if len(stats_db['history_logs']) > 1000: stats_db['history_logs'].pop()

        acc['sheckles_history'].append([curr_time, new_sheckles])
        acc['sheckles_history'] = [h for h in acc['sheckles_history'] if curr_time - h[0] <= 3600]
        
        sph = 0
        if len(acc['sheckles_history']) > 1:
            time_diff = (acc['sheckles_history'][-1][0] - acc['sheckles_history'][0][0]) / 3600.0
            if time_diff > 0:
                sph = (acc['sheckles_history'][-1][1] - acc['sheckles_history'][0][1]) / time_diff

        acc['stats'] = user_stats
        acc['last_ping'] = curr_time
        acc['last_updated'] = (datetime.utcnow() + timedelta(hours=7)).strftime("%H:%M:%S")
        acc['sph'] = max(0, sph)
        
        save_db()
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    stats_db['history_logs'] = []
    save_db()
    return jsonify({"status": "OK"}), 200
@app.route('/')
def dashboard():
    total_stats = {}
    total_sph = online_count = offline_count = 0
    current_time = time.time()
    
    for user, data in stats_db['accounts'].items():
        # Trở về cơ chế ON/OFF đơn giản: Nếu có ping trong 10 phút là ON
        if current_time - data.get('last_ping', 0) <= 600:
            data['status'] = 'ON'
            online_count += 1
            total_sph += data.get('sph', 0)
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
        <title>Nông Trại Command Center</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root { --bg: #11111b; --card: #181825; --card-hover: #313244; --text: #cdd6f4; --accent: #89b4fa; --green: #a6e3a1; --red: #f38ba8; --yellow: #f9e2af; --border: #45475a; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; }
            .navbar { display: flex; background-color: var(--card); border-bottom: 2px solid var(--border); padding: 0 20px; overflow-x: auto; white-space: nowrap; }
            .tab-btn { background: none; border: none; color: var(--text); padding: 15px 20px; font-size: 15px; font-weight: bold; cursor: pointer; opacity: 0.6; transition: 0.3s; border-bottom: 3px solid transparent; }
            .tab-btn:hover { opacity: 1; background-color: var(--card-hover); }
            .tab-btn.active { opacity: 1; border-bottom: 3px solid var(--accent); color: var(--accent); }
            
            .container { padding: 20px; max-width: 1200px; margin: auto; }
            .tab-content { display: none; animation: fadeIn 0.3s; }
            .tab-content.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

            .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .stat-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; position: relative; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
            .stat-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 10px 10px 0 0; }
            .card-online::before { background: var(--green); }
            .card-money::before { background: var(--yellow); }
            .card-seeds::before { background: #cba6f7; }
            .card-planted::before { background: #fab387; }
            
            .card-title { font-size: 12px; font-weight: bold; text-transform: uppercase; color: #a6adc8; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
            .card-value { font-size: 28px; font-weight: bold; }
            .card-sub { font-size: 13px; color: var(--green); margin-top: 5px; font-weight: bold; }

            table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 10px; overflow: hidden; font-size: 14px; }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid var(--border); }
            th { background-color: #313244; color: #a6adc8; font-size: 12px; text-transform: uppercase; }
            tr:hover { background-color: var(--card-hover); }
            
            .badge-on { background: rgba(166,227,161,0.1); color: var(--green); border: 1px solid var(--green); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .badge-off { background: rgba(243,139,168,0.1); color: var(--red); border: 1px solid var(--red); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            
            .category { margin-bottom: 20px; }
            .cat-title { font-size: 14px; text-transform: uppercase; color: #a6adc8; margin-bottom: 10px; font-weight: bold; border-bottom: 1px dashed var(--border); padding-bottom: 5px;}
            .item-badge { padding: 6px 12px; border-radius: 6px; font-size: 14px; display: inline-block; margin: 4px; border: 1px solid var(--border); background: #313244; }
            .stat-name { color: var(--text); }
            .stat-val { font-weight: bold; }
            
            .badge-planted { background-color: rgba(166, 227, 161, 0.1); color: var(--green); border: 1px dashed var(--green); }
            .badge-planted .stat-name { color: var(--green); }
            .badge-seed { border-color: var(--green); }
            .badge-seed .stat-val { color: var(--green); }
            .badge-gear { border-color: var(--accent); }
            .badge-gear .stat-val { color: var(--accent); }
            .badge-pet { border-color: #cba6f7; }
            .badge-pet .stat-val { color: #cba6f7; }
            .badge-other .stat-val { color: #fab387; }
            
            .text-green { color: var(--green); font-weight: bold; }
            .text-red { color: var(--red); font-weight: bold; }
            .btn-danger { background: var(--red); color: #11111b; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 15px; }
            .btn-danger:hover { opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="navbar">
            <button class="tab-btn active" onclick="openTab('tab-overview', this)">📊 Tổng Quan</button>
            <button class="tab-btn" onclick="openTab('tab-accounts', this)">👥 Tài Khoản ({{ online_count }}/{{ stats_db['accounts']|length }})</button>
            <button class="tab-btn" onclick="openTab('tab-inventory', this)">📦 TỔNG KHO</button>
            <button class="tab-btn" onclick="openTab('tab-history', this)">🕒 Lịch Sử GD</button>
        </div>

        <div class="container">
            <div id="tab-overview" class="tab-content active">
                <div class="dashboard-grid">
                    <div class="stat-card card-online">
                        <div class="card-title">
                            <span>TÌNH TRẠNG MÁY</span>
                        </div>
                        <div style="display: flex; gap: 8px; margin-top: 10px;">
                            <span class="badge-on">🟢 {{ online_count }} ĐANG CÀY</span>
                            <span class="badge-off">🔴 {{ offline_count }} OFF</span>
                        </div>
                    </div>
                    <div class="stat-card card-money">
                        <div class="card-title">TỔNG SHECKLES <span style="color:var(--yellow)">💰</span></div>
                        <div class="card-value">{{ format_num(total_stats.get('Sheckles', 0)) }}</div>
                        <div class="card-sub">▲ {{ format_num(total_sph) }} / giờ</div>
                    </div>
                    <div class="stat-card card-planted">
                        <div class="card-title">CÂY ĐANG TRỒNG (Ngoài vườn) 🌳</div>
                        <div class="card-value">
                            {% set ns = namespace(planted=0) %}
                            {% for k, v in total_stats.items() %}{% if '[Planted]' in k %}{% set ns.planted = ns.planted + v %}{% endif %}{% endfor %}
                            {{ format_num(ns.planted) }}
                        </div>
                        <div class="card-sub" style="color: #fab387">Gốc cây</div>
                    </div>
                    <div class="stat-card card-seeds">
                        <div class="card-title">HẠT GIỐNG (Trong túi) 🌱</div>
                        <div class="card-value">
                            {% set ns2 = namespace(seeds=0) %}
                            {% for k, v in total_stats.items() %}{% if 'Seed' in k %}{% set ns2.seeds = ns2.seeds + v %}{% endif %}{% endfor %}
                            {{ format_num(ns2.seeds) }}
                        </div>
                        <div class="card-sub" style="color: #cba6f7">Tổng hạt giống</div>
                    </div>
                </div>
            </div>

            <div id="tab-accounts" class="tab-content">
                <table>
                    <tr>
                        <th>Trạng Thái</th>
                        <th>Tên Người Chơi</th>
                        <th>Sheckles 💰</th>
                        <th>Tốc Độ (SPH)</th>
                        <th>Cập nhật cuối</th>
                    </tr>
                    {% for user, data in stats_db['accounts'].items() %}
                    <tr>
                        <td>
                            {% if data.status == 'ON' %}<span class="badge-on">🟢 TRỰC TUYẾN</span>
                            {% else %}<span class="badge-off">🔴 MẤT KẾT NỐI</span>{% endif %}
                        </td>
                        <td><strong>{{ user }}</strong></td>
                        <td style="color: var(--yellow); font-weight: bold;">{{ format_num(data.stats.get('Sheckles', 0)) }}</td>
                        <td style="color: var(--green);">+{{ format_num(data.sph) }}/h</td>
                        <td style="color: #a6adc8; font-size: 12px;">{{ data.last_updated }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div id="tab-inventory" class="tab-content">
                <div style="background: var(--card); padding: 25px; border-radius: 10px; border: 1px solid var(--border);">
                    <h3 style="margin-top:0; color: var(--yellow); border-bottom: 1px solid var(--border); padding-bottom: 15px;">📦 TÀI SẢN TOÀN SERVER (GỘP TỪ TẤT CẢ TÀI KHOẢN)</h3>
                    
                    <div class="category">
                        <div class="cat-title">🌳 CÂY ĐANG TRỒNG NGOÀI VƯỜN</div>
                        {% for k, v in total_stats.items() %}{% if get_category(k) == 'planted' %}
                            <span class="item-badge badge-planted"><span class="stat-name">{{ k.replace('[Planted] ', '') }}:</span> <span class="stat-val">{{ format_num(v) }} gốc</span></span>
                        {% endif %}{% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">🌱 HẠT GIỐNG (TỒN KHO)</div>
                        {% for k, v in total_stats.items() %}{% if get_category(k) == 'seed' %}
                            <span class="item-badge badge-seed"><span class="stat-name">{{ k }}:</span> <span class="stat-val">{{ format_num(v) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">🛠️ CÔNG CỤ & GEAR</div>
                        {% for k, v in total_stats.items() %}{% if get_category(k) == 'gear' %}
                            <span class="item-badge badge-gear"><span class="stat-name">{{ k }}:</span> <span class="stat-val">{{ format_num(v) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>
                    
                    <div class="category">
                        <div class="cat-title">🐾 THÚ CƯNG</div>
                        {% for k, v in total_stats.items() %}{% if get_category(k) == 'pet' %}
                            <span class="item-badge badge-pet"><span class="stat-name">{{ k.replace('[Active] ', '🌟 ') }}:</span> <span class="stat-val">{{ format_num(v) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>

                    <div class="category">
                        <div class="cat-title">📦 TRÁI CÂY & VẬT PHẨM KHÁC</div>
                        {% for k, v in total_stats.items() %}{% if get_category(k) == 'other' and k != 'Sheckles' %}
                            <span class="item-badge badge-other"><span class="stat-name">{{ k }}:</span> <span class="stat-val">{{ format_num(v) }}</span></span>
                        {% endif %}{% endfor %}
                    </div>
                </div>
            </div>

            <div id="tab-history" class="tab-content">
                <button class="btn-danger" onclick="clearHistory()">🗑️ Xóa Lịch Sử</button>
                <table>
                    <tr>
                        <th>Thời Gian</th>
                        <th>Tài Khoản</th>
                        <th>Hành Động</th>
                        <th>Số Lượng (Sheckles)</th>
                        <th>Số dư mới</th>
                    </tr>
                    {% for log in stats_db['history_logs'] %}
                    <tr>
                        <td style="color:#a6adc8">{{ log.time }}</td>
                        <td><strong>{{ log.user }}</strong></td>
                        <td>
                            {% if log.action == 'TĂNG' %}<span class="text-green">▲ TĂNG</span>
                            {% else %}<span class="text-red">▼ GIẢM</span>{% endif %}
                        </td>
                        <td>
                            {% if log.action == 'TĂNG' %}<span class="text-green">+{{ format_num(log.amount) }}</span>
                            {% else %}<span class="text-red">-{{ format_num(log.amount) }}</span>{% endif %}
                        </td>
                        <td style="color:var(--yellow)">{{ format_num(log.new_total) }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <script>
            function openTab(tabId, element) {
                document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                element.classList.add('active');
            }
            
            function clearHistory() {
                if(confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử không?")) {
                    fetch('/api/clear_history', { method: 'POST' }).then(() => location.reload());
                }
            }

            setInterval(() => {
                fetch('/').then(res => res.text()).then(html => {
                    let parser = new DOMParser();
                    let newDoc = parser.parseFromString(html, 'text/html');
                    document.getElementById('tab-overview').innerHTML = newDoc.getElementById('tab-overview').innerHTML;
                    document.getElementById('tab-accounts').innerHTML = newDoc.getElementById('tab-accounts').innerHTML;
                    document.getElementById('tab-inventory').innerHTML = newDoc.getElementById('tab-inventory').innerHTML;
                    document.getElementById('tab-history').innerHTML = newDoc.getElementById('tab-history').innerHTML;
                });
            }, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, stats_db=stats_db, total_stats=total_stats, total_sph=total_sph, online_count=online_count, offline_count=offline_count, format_num=format_num, get_category=get_category)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
