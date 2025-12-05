
# create_super_admin.py
from app import create_app
from app.extensions import db
from app.models import User

"""
使用方式：
1）激活你的虚拟环境
   conda activate spyder   （按你自己环境名）

2）cd 到 backend 目录
   cd D:\dev\heng\chrome-extensions\backend

3）运行：
   python create_super_admin.py
"""

def main():
    app = create_app("dev")

    with app.app_context():
        username = "admin"
        password = "admin123"          # 你可以改成更安全的
        email = "admin@example.com"

        # 已存在就不重复创建
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"用户 {username} 已存在，跳过创建。")
            print(f"可以用账号：{username}，原来的密码登录（如果记得的话）。")
            return

        user = User(
            username=username,
            email=email,
            user_fullname="超级管理员",
            status="active",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print("超级管理员创建成功！")
        print(f"用户名：{username}")
        print(f"密码：{password}")

if __name__ == "__main__":
    main()
