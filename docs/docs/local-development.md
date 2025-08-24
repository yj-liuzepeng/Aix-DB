
确保你已安装并配置了所需的环境

## 1. 克隆仓库
```bash
git clone https://github.com/apconw/sanic-web.git
```

## 2. 后端依赖安装  
   - uv安装 [参考uv官方文档](https://docs.astral.sh/uv/getting-started/installation/)
```bash
   # 安装uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   #进入项目目录
   cd sanic-web

   # 创建虚拟环境
   uv venv --clear

   # 激活虚拟环境
   
   # Mac or Linux 用户执行
   source .venv/bin/activate

   # Windows 用户执行
   .venv\Scripts\activate
   
   # 安装依赖
   uv sync --no-cache
   
   # pycharm 配置虚拟环境
   Settings -> Project: sanic-web -> Project Interpreter -> Add -> Existing environment
   选择.venv目录
```

## 3. **安装中间件**
- 启动mysql和minio容器
```bash
cd docker
docker compose up -d mysql minio
```

## 4. 修改.env.dev配置文件
- 修改minio的配置
    - 访问MinIO服务，http://localhost:19001/ 账号:admin 密码:12345678
    - 创建一个bucket，名称filedata，同时配置Access Key
    - 修改.evn.dev里的MINIO_开头的密钥消息
- 修改大模型&MCP-HUB配置
    - 修改**MODEL_BASE_URL** 公网大模型服务地址默认使用阿里云公网大模型服务
    - 修改**MODEL_NAME** 大模型名称如qwen-plus
    - 修改**MODEL_API_KEY** 大模型服务API-KEY
    - 修改**MCP_HUB_URL** MCP_HUB服务地址本地启动,默认不用修改

  
## 5. 初始化数据库
   - 如果使用已安装的mysql,初始化数据时需修改源码initialize_mysql里面的连接信息
```bash
# Mac or Linux 用户执行
cd docker
  ./init_data.sh

# Windows 用户执行
cd common
  python initialize_mysql.py
```

## 6. 前端依赖安装  
 - 前端是基于开源项目[可参考chatgpt-vue3-light-mvp安装](https://github.com/pdsuwwz/chatgpt-vue3-light-mvp)二开
 
```bash
# 安装前端依赖&启动服务
cd web
   
#安装依赖
npm install -g pnpm

pnpm i
   
#启动服务
pnpm dev
```

## 7. 启动后端服务
```bash
#启动后端服务
python serv.py
```

## 8. 访问服务
- 前端服务：http://localhost:2048


## 9. 构建镜像

- 执行构建命令：
```bash
   # 构建前端镜像 
   make web-build
  
   # 构建后端镜像
   make service-build
```