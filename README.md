# 前端启动：

cd tdesign
npm run dev

# 后端启动：

cd flask/api
gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 --access-logfile - --error-logfile - app:app

# 数据库启动

sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
sudo systemctl enable postgresql
sudo systemctl disable postgresql
sudo systemctl status postgresql

# 数据库查询

SELECT agent, user FROM table_update_record ORDER BY ROWID DESC LIMIT 1000;

# 服务器守护进程

cd /etc/systemd/system
sudo systemctl daemon-reload

sudo systemctl enable server_scheduler.service
sudo systemctl is-enabled server_scheduler.service

sudo systemctl start server_scheduler.service
sudo systemctl stop server_scheduler.service
sudo systemctl restart server_scheduler.service
sudo systemctl status server_scheduler.service

sudo journalctl -u server_scheduler.service -f
