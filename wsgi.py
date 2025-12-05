# backend/wsgi.py
from app import create_app

app = create_app("dev")

if __name__ == "__main__":
    # 本地开发可以直接跑这个
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
