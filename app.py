from flask import Flask, request, Response, jsonify
import requests
import time

app = Flask(__name__)
TARGET_DOMAIN = 'sxz.api.zykj.org'
TARGET_URL = f'http://{TARGET_DOMAIN}'

SPECIAL_PATH = '/services/app/CtrlStrategy/GetControlPolicyByDeviceNumberAsync'
BLOCK_PATH_PREFIX = '/services/app/[WebWhiteList]/'

PRESET_RESPONSE = {
    "result": {"type": 4, "policies": []},
    "targetUrl": None,
    "success": True,
    "error": None,
    "unAuthorizedRequest": False,
    "__abp": True
}

BLOCKED_RESPONSE = {
    "success": False,
    "error": {
        "code": 403,
        "message": "访问被禁止",
        "details": "该接口已禁用"
    },
    "__abp": True
}

DISCOVERY_RESPONSE = {
    "name": "江苏省锡中",
    "server": "http://127.0.0.1:8080",
    "lcid": "6ee30ace-f3c3-4ed0-a1b8-ce2855c9eb99"
}

def modify_request_body(original_data, content_type):
    processable_types = [
        'application/json',
        'text/plain',
        'application/xml',
        'text/xml',
        'application/x-www-form-urlencoded',
        'text/html'
    ]
    if not any(content_type.startswith(t) for t in processable_types):
        return original_data, False
    try:
        charset = 'utf-8'
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[1].split(';')[0].strip().lower()
        decoded = original_data.decode(charset)
        modified = decoded.replace('deviceNumber', 'dn')
        return modified.encode(charset), True
    except Exception as e:
        print(f"请求体修改失败: {str(e)}")
        return original_data, False

@app.before_request
def before_request():
    raw_data = request.get_data(cache=False)
    content_type = request.headers.get('Content-Type', '')
    modified_data, is_modified = modify_request_body(raw_data, content_type)
    request.modified_data = modified_data
    request.is_modified = is_modified
    request._cached_data = modified_data

def log_request(response):
    duration = (time.time() - request.start_time) * 1000 if hasattr(request, 'start_time') else 0
    status = "已拦截" if getattr(response, 'is_blocked', False) else "已代理"
    log_msg = [
        f"\n{'='*40} 请求日志 {'='*40}",
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}",
        f"状态: {status} | 耗时: {duration:.2f}ms | 状态码: {response.status_code}"
    ]
    if status == "已拦截":
        log_msg.append("拦截原因: " + getattr(response, 'block_reason', '未指明原因'))
    print('\n'.join(log_msg))

@app.route('/', methods=['GET'])
def home():
    return '''
    <!DOCTYPE html>
    <html lang="zh-cn">
    <head>
        <meta charset="utf-8">
        <title>欢迎访问主页</title>
        <!-- Material 3 (MD3) Design: Google Fonts + Material Symbols + Material Web -->
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
        <script type="module" src="https://unpkg.com/@material/web@1.0.0-rc.4/all.js"></script>
        <style>
            body {
                font-family: 'Roboto', Arial, sans-serif;
                background: #f5f5f5;
                margin: 0;
            }
            .mdc-card {
                max-width: 600px;
                margin: 48px auto 0 auto;
                padding: 32px 24px;
                background: #fff;
                border-radius: 18px;
                box-shadow: 0 2px 8px rgba(60,60,60,.11);
            }
            h1 {
                color: #181c23;
                font-size: 2.1rem;
                font-weight: 500;
                letter-spacing: .01em;
                margin-bottom: 16px;
            }
            ul {
                color: #444;
                margin-left: 18px;
            }
            .github-btn {
                margin-top: 22px;
                display: inline-flex;
                align-items: center;
                background: #0061a6;
                color: #fff;
                border-radius: 8px;
                padding: 10px 22px;
                text-decoration: none;
                font-weight: 500;
                font-size: 1rem;
                gap: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,.06);
                transition: background .2s;
            }
            .github-btn:hover {
                background: #003d6f;
            }
            .material-symbols-rounded {
                font-size: 1.3em;
                vertical-align: middle;
            }
        </style>
    </head>
    <body>
        <div class="mdc-card">
            <h1>
                <span class="material-symbols-rounded" style="color:#0061a6;">cloud</span>
                Flask Proxy Demo
            </h1>
            <p>本项目是一个基于 Flask 的反向代理和接口拦截服务，采用 Material Design 3 风格主页。</p>
            <ul>
                <li>支持 API 请求转发与日志记录</li>
                <li>可自定义拦截和响应策略</li>
                <li>内置演示接口，方便测试</li>
            </ul>
            <a class="github-btn" href="https://github.com/BennyLoshop/example-flask" target="_blank">
                <span class="material-symbols-rounded">star</span> GitHub 项目主页
            </a>
        </div>
    </body>
    </html>
    '''

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy_api(path):
    request.start_time = time.time()
    # /api/discovery/sxz 优先处理
    if path == 'discovery/sxz' and request.method == 'GET':
        base_url = request.host_url.rstrip('/')
        resp = dict(DISCOVERY_RESPONSE)
        resp['server'] = f"{base_url}/api"
        response = jsonify(resp)
        response.is_blocked = True
        response.block_reason = "发现接口拦截"
        log_request(response)
        return response
    # WebWhiteList 路径
    if path.startswith(BLOCK_PATH_PREFIX.lstrip('/')):
        response = jsonify(BLOCKED_RESPONSE)
        response.status_code = 403
        response.is_blocked = True
        response.block_reason = "受保护接口范围"
        log_request(response)
        return response
    # 特殊预定义路径
    if path == SPECIAL_PATH.lstrip('/'):
        response = jsonify(PRESET_RESPONSE)
        response.headers['Content-Type'] = 'application/json'
        response.is_blocked = True
        response.block_reason = "预设响应接口"
        log_request(response)
        return response
    # 代理转发，去除 /api/ 前缀
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    headers['Host'] = TARGET_DOMAIN
    if 'Content-Length' in headers and request.is_modified:
        headers['Content-Length'] = str(len(request.modified_data))
    try:
        resp = requests.request(
            method=request.method,
            url=f'{TARGET_URL}/{path}',
            headers=headers,
            data=request.modified_data,
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        response = jsonify({
            "success": False,
            "error": f"代理请求失败: {str(e)}"
        })
        response.status_code = 502
        log_request(response)
        return response
    response = Response(resp.content, resp.status_code)
    response.headers.extend({
        k: v for k, v in resp.headers.items()
        if k.lower() not in ['content-encoding', 'transfer-encoding']
    })
    log_request(response)
    return response

# 旧发现接口，路径不变，返回 server 字段为当前服务/api
@app.route('/discovery/sxz', methods=['GET'])
def discovery_sxz():
    base_url = request.host_url.rstrip('/')
    resp = dict(DISCOVERY_RESPONSE)
    resp['server'] = f"{base_url}/api"
    return jsonify(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)