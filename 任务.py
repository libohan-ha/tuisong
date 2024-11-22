from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from wxauto import WeChat
import os
import pythoncom

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# 定义任务模型
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建数据库表
with app.app_context():
    db.create_all()

# 发送微信消息的函数
def send_wx_message():
    try:
        # 在线程中初始化COM
        pythoncom.CoInitialize()
        
        wx = WeChat()
        # 获取所有激活的任务
        with app.app_context():
            tasks = Task.query.filter_by(active=True).all()
            if tasks:
                message = "今日任务清单：\n"
                for i, task in enumerate(tasks, 1):
                    message += f"{i}. {task.content}\n"
                
                # 发送到你的微信
                wx.SendMsg(message, '文件传输助手')
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
    finally:
        # 清理COM
        pythoncom.CoUninitialize()

# 设置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(send_wx_message, 'cron', hour=7, minute=0)
scheduler.start()

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    content = request.form.get('content')
    if content:
        new_task = Task(content=content)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.active = not task.active
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
