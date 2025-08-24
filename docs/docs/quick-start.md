确保你已安装并配置了所需的环境

## 1. 克隆仓库
```bash
git clone https://github.com/apconw/sanic-web.git
```

## 2. 启动服务
- 根据情况修改docker/docker-compose.yml里的环境变量的值
- **以下配置本机启动默认不用修改,在服务器上部署时host.docker.internal需修改为实际IP地址**
    - 可修改**MYSQL_HOST** MySQL数据服务地址
    - 可修改**MODEL_API_KEY** 大模型服务API-KEY
    - 可修改**MCP_HUB_URL** MCP_HUB服务地址
    - 可修改**MINIO_ENDPOINT** MinIO服务地址
    - 可修改**DIFY_SERVER_URL** Dify服务地址
    - 必须修改**DIFY_DATABASE_QA_API_KEY** Dify智能体Api-Key
    - 可修改**MODEL_BASE_URL** 公网大模型服务地址默认使用阿里云公网模型服务
    - 可修改**MODEL_NAME** 大模型名称如openai:qwen-plus ***(v1.1.5版本需要加上openai:前缀)***

```bash
   # 拉起前后端服务和中间件
   cd docker
   docker compose up -d
```

## 3. Minio配置
   - 访问MinIO服务，http://localhost:19001/ 账号:admin 密码:12345678
   - 创建一个bucket，名称filedata，同时配置Access Key
   - 修改docker-compose里的chat-service服务的MINIO_开头的环境变量重启服务

```bash
# 修改docker-compose.yml文件minio密钥
MINIO_ACCESS_KEY
MiNIO_SECRET_KEY
  
# 重新拉起前后端服务和中间件
cd docker
docker compose up -d
```


## 4. 数据初始化
- 如果使用已安装的mysql,初始化数据时需要修改源码initialize_mysql里面的链接信息
- 运行初始化脚本
```bash
   # 安装依赖包
   pip install pymysql
   
   # Mac or Linux 用户执行
   cd docker
   ./init_data.sh
   
   # Windows 用户执行
   cd common
   python initialize_mysql.py
```
   
   
## 5. **访问服务**
- 前端服务：http://localhost:8081