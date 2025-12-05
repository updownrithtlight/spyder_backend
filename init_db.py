# backend/init_db.py
from app import create_app
from app.extensions import db

def main():
    # 使用 dev 配置
    app = create_app("dev")

    # 进入应用上下文，否则 SQLAlchemy 不知道用哪个 app
    with app.app_context():
        print("⏳ 正在创建数据库表...")
        db.create_all()
        print("✅ 数据库表已全部创建完成！")

if __name__ == "__main__":
    main()
