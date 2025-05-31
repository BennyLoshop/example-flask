# 中育API代理

## 项目概述

本项目是一个基于Flask框架的API代理服务，旨在拦截和修改特定API请求，同时提供预设的响应结果。主要功能包括：

- **请求拦截与修改**：对特定路径的请求进行拦截，修改请求体中的关键字。
- **预设响应**：针对特定接口返回预设的响应结果，不转发请求到目标服务器。
- **日志记录**：记录请求的详细信息，包括请求时间、方法、路径、状态码和耗时。

## 依赖

- Flask
- requests

## 配置

- **目标域名**：`TARGET_DOMAIN = 'sxz.api.zykj.org'`
- **特殊路径**：`SPECIAL_PATH = '/api/services/app/CtrlStrategy/GetControlPolicyByDeviceNumberAsync'`
- **拦截路径前缀**：`BLOCK_PATH_PREFIX = '/api/services/app/[WebWhiteList]/'`

## 运行

```bash
pip install -r requirements.txt
python app.py
```

## 主要功能说明

1. **请求体修改**
   - 修改请求体中的`deviceNumber`为`dn`。
   - 支持多种Content-Type，包括`application/json`、`text/plain`等。

2. **预设响应**
   - **发现接口拦截**：当请求路径为`/api/discovery/sxz`时，返回预设的发现接口响应结果。
   - **受保护接口拦截**：当请求路径以`/api/services/app/[WebWhiteList]/`开头时，返回403错误响应。
   - **特殊预定义路径拦截**：当请求路径为`SPECIAL_PATH`时，返回预设的响应结果。

3. **日志记录**
   - 记录请求的时间、方法、路径、状态码、耗时和拦截原因（如果有）。

## 示例请求

- **发现接口拦截**
  - 请求：`GET /api/discovery/sxz`
  - 响应：`DISCOVERY_RESPONSE`

- **受保护接口拦截**
  - 请求：`GET /api/services/app/[WebWhiteList]/any_path`
  - 响应：`BLOCKED_RESPONSE`

- **特殊预定义路径拦截**
  - 请求：`GET /api/services/app/CtrlStrategy/GetControlPolicyByDeviceNumberAsync`
  - 响应：`PRESET_RESPONSE`

## 注意事项

- 确保目标域名`TARGET_DOMAIN`配置正确，否则代理请求将无法正常转发。
- 修改请求体和预设响应的逻辑可根据实际需求进行调整。