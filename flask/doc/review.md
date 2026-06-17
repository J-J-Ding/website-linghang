纪要

# 启用官方 PostgreSQL 仓库（以 CentOS Stream 9 为例）

sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# 安装 PostgreSQL（例如 15 版本）

sudo dnf install -y postgresql15-server postgresql15

# 初始化数据库（首次安装后必须）

sudo /usr/pgsql-15/bin/postgresql-15-setup initdb

# 启动并启用服务

sudo systemctl start postgresql-15
sudo systemctl enable postgresql-15

# Agent 调试使用

unset http_proxy HTTP_PROXY https_proxy HTTPS_PROXY all_proxy ALL_PROXY no_proxy NO_PROXY

curl -X POST http://10.90.251.221:3001/api/api_chat/Agent \
 -H "Content-Type: application/json" \
 -d '{
"session_id": "dbe0c854-e9c5-427d-9dfa-65280900f112",
"request_id": "dbe0c854-e9c5-427d-9dfa-65280900f222",
"user": "10171727",
"content": "世界上最高的山是什么？",
"agent": "chat",
"model": "nebula",
"icenter": false,
"rdc": false,
"think": false
}'

curl -X POST http://10.90.251.221:3001/api/api_chat/Agent \
 -H "Content-Type: application/json" \
 -d '{
"session_id": "dbe0c854-e9c5-427d-9dfa-65280900f112",
"request_id": "dbe0c854-e9c5-427d-9dfa-65280900f234",
"user": "10171727",
"content": "第二高的呢？",
"agent": "chat",
"model": "nebula",
"icenter": false,
"rdc": false,
"think": false
}'

curl -X POST http://10.90.251.221:3001/api/api_chat/Agent \
 -H "Content-Type: application/json" \
 -d '{
"session_id": "dbe0c854-e9c5-427d-9dfa-65280900f113",
"request_id": "dbe0c854-e9c5-427d-9dfa-65280900f234",
"user": "10171727",
"content": "模块有什么文件？什么函数？",
"agent": "ComponentAgent",
"model": "nebula",
"icenter": false,
"rdc": false,
"think": false,
component: "SERVICE 组件-业务端口模块",
context: "{\"component\":\"SERVICE 组件-业务端口模块\",\"description\":\"\",\"server\":\"10.90.204.255\",\"file\":\"L2/plat/Service/inc/sspServiceUcmd.h\\n L2/plat/Service/src/sspServiceUcmd.c\"}"
}'

component TEXT,
requirement TEXT,
issue TEXT,
testcase TEXT,

CREATE TABLE feature (
feature_id TEXT NOT NULL,
feature_name TEXT PRIMARY KEY,
feature_function TEXT,
feature_level TEXT,
feature_page TEXT,
domain TEXT
);

CREATE TABLE board (
board_id TEXT,
board_name PRIMARY KEY
);

CREATE TABLE feature_board (
feature_name TEXT,
board_name TEXT,
PRIMARY KEY (feature_name, board_name),
FOREIGN KEY (feature_name) REFERENCES feature(feature_name) ON DELETE CASCADE,
FOREIGN KEY (board_name) REFERENCES board(board_name) ON DELETE CASCADE
);

CREATE TABLE requirement (
pr_id PRIMARY KEY,
pr_title TEXT,
pr_description TEXT,
domain TEXT,
team TEXT,
);

CREATE TABLE issue (
issue_id PRIMARY KEY,
issue_title TEXT,
issue_description TEXT,
domain TEXT,
team TEXT,
owner TEXT,
department TEXT,
activity TEXT,
origin TEXT,
product TEXT,
project TEXT,
createtime DATE,
feature TEXT,
board TEXT,
);

CREATE TABLE review (
"标识" TEXT PRIMARY KEY,
"主题" TEXT,
"描述" TEXT,
"开发复盘负责人" TEXT,
"缺陷等级" TEXT,
"发现活动" TEXT,
"发现方法" TEXT,
"提交日期" TEXT,
"关闭日期" TEXT,
"故障引入人" TEXT,
"引入点所属领域" TEXT,
"引入点所属团队" TEXT,
"技术根因分析" TEXT,
"引入来源" TEXT,
"故障引入点根因一级分类" TEXT,
"故障引入点根因二级分类" TEXT,
"故障引入点根因三级分类" TEXT,
"故障引入 gerrit 入库链接" TEXT,
"一级特性" TEXT,
"二级特性" TEXT,
"引入点复盘状态" TEXT,
"最早可拦截阶段" TEXT,
"自测无法拦截的原因" TEXT,
"代码走查未拦截原因" TEXT,
"代码走查未拦截原因说明" TEXT,
"是否可通过补充代码 UT/FT 拦截" TEXT,
"是否可通过补充仿真 FT 拦截" TEXT,
"是否可通过补充硬件 FT / 流水线 FT 拦截" TEXT,
"故障定界定位方式" TEXT,
"是否需要复现定位或者占用环境定位" TEXT,
"定位时长" TEXT,
"控制点复盘状态" TEXT,
"引入点改进举措" TEXT,
"控制点改进举措" TEXT
);

curl -X POST http://10.90.251.221:3001/api/api_data/API_Feature_read \
 -H "Content-Type: application/json" \
 -d '{
"domain": "L2",
"board": "",
}'
