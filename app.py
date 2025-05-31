# {"name": "中育api代理", "version": "2.1.0", "dependencies": ["flask", "requests"]}
from flask import Flask, request, Response, jsonify
import requests
import time

app = Flask(__name__)
TARGET_DOMAIN = 'sxz.api.zykj.org'
TARGET_URL = f'http://{TARGET_DOMAIN}'

# 特殊路径配置
SPECIAL_PATH = '/api/services/app/CtrlStrategy/GetControlPolicyByDeviceNumberAsync'
BLOCK_PATH_PREFIX = '/api/services/app/[WebWhiteList]/'

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
    """修改请求体内容"""
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
    """统一请求日志记录"""
    duration = (time.time() - request.start_time) * 1000
    status = "已拦截" if getattr(response, 'is_blocked', False) else "已代理"
    
    log_msg = [
        f"\n{'='*40} 请求日志 {'='*40}",
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}",
        f"状态: {status} | 耗时: {duration:.2f}ms | 状态码: {response.status_code}"
    ]
    
    if status == "已拦截":
        log_msg.append("拦截原因: " + getattr(response, 'block_reason', '未指明原因'))
    
    print('\n'.join(log_msg))

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy_request(path):
    request.start_time = time.time()
    
    # 最高优先级：发现接口
    if request.path == '/api/discovery/sxz' and request.method == 'GET':
        response = jsonify(DISCOVERY_RESPONSE)
        response.is_blocked = True
        response.block_reason = "发现接口拦截"
        log_request(response)
        return response

    # 第二优先级：WebWhiteList路径范围
    if request.path.startswith(BLOCK_PATH_PREFIX):
        response = jsonify(BLOCKED_RESPONSE)
        response.status_code = 403
        response.is_blocked = True
        response.block_reason = "受保护接口范围"
        log_request(response)
        return response

    # 第三优先级：特殊预定义路径
    if request.path == SPECIAL_PATH:
        response = jsonify(PRESET_RESPONSE)
        response.headers['Content-Type'] = 'application/json'
        response.is_blocked = True
        response.block_reason = "预设响应接口"
        log_request(response)
        return response

    # 正常代理逻辑
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
