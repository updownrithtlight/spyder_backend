# from flask import Flask, request, send_file
# from flask_cors import CORS
# import pandas as pd
# import io
# import requests
# from PIL import Image
# from concurrent.futures import ThreadPoolExecutor, as_completed
#
# app = Flask(__name__)
# CORS(app)
#
# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
#                   'Chrome/120.0.0.0 Safari/537.36'
# }
#
# MAX_WORKERS = 8   # 你可以根据机器情况调大/调小
#
#
# def download_and_resize_image(img_url: str, row_index: int):
#     """在线程里执行：下载 + 缩放图片，返回 (row_index, img_bytes 或 None, 文字状态)"""
#     if not img_url or not str(img_url).startswith('http'):
#         return row_index, None, "无图"
#
#     try:
#         resp = requests.get(img_url, headers=HEADERS, timeout=5)
#         if resp.status_code != 200:
#             return row_index, None, "下载失败"
#
#         image_data = io.BytesIO(resp.content)
#         img = Image.open(image_data)
#         img.thumbnail((180, 180))
#
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_arr.seek(0)
#
#         return row_index, img_byte_arr, None  # None 表示无错误文字
#     except Exception as e:
#         print(f"❌ 第 {row_index + 1} 行图片出错: {e}")
#         return row_index, None, "错误"
#
#
# @app.route('/generate_excel', methods=['POST'])
# def generate_excel():
#     print("收到数据，正在生成 Excel...")
#
#     req_data = request.json
#     rows = req_data.get('rows', [])
#
#     if not rows:
#         return {"error": "No data"}, 400
#
#     columns = [
#         '标题', '图片链接', '价格', '公司名称',
#         '类目', '年销量', '月代销', '48h揽收', '上架日期', '开店时长', '商品链接'
#     ]
#     df = pd.DataFrame(rows, columns=columns)
#
#     output = io.BytesIO()
#     writer = pd.ExcelWriter(output, engine='xlsxwriter')
#     df.to_excel(writer, sheet_name='Sheet1', index=False)
#
#     workbook = writer.book
#     worksheet = writer.sheets['Sheet1']
#
#     cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
#     worksheet.set_column('A:Z', 18, cell_format)
#     worksheet.set_column('B:B', 16)
#     worksheet.set_column('A:A', 30)
#     worksheet.set_column('K:K', 40)
#
#     img_col_idx = 1
#
#     # 🧵 1）多线程并发下载 + 处理图片
#     results = {}  # row_index -> (img_bytes 或 None, status_text)
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = []
#         for index, row in df.iterrows():
#             img_url = row['图片链接']
#             fut = executor.submit(download_and_resize_image, img_url, index)
#             futures.append(fut)
#
#         for fut in as_completed(futures):
#             row_index, img_bytes, status_text = fut.result()
#             results[row_index] = (img_bytes, status_text)
#
#     # 🧵 2）主线程里串行写入 Excel（安全）
#     for index, row in df.iterrows():
#         excel_row = index + 1
#         worksheet.set_row(excel_row, 100)
#
#         img_bytes, status_text = results.get(index, (None, "错误"))
#
#         if img_bytes is None:
#             # 没有图片数据，就写入状态文字
#             worksheet.write(excel_row, img_col_idx, status_text or "错误")
#         else:
#             worksheet.insert_image(excel_row, img_col_idx, "img.png", {
#                 'image_data': img_bytes,
#                 'x_scale': 0.7,
#                 'y_scale': 0.7,
#                 'x_offset': 5,
#                 'y_offset': 5,
#                 'positioning': 1
#             })
#             print(f"✅ 第 {index + 1} 行图片处理完成")
#
#     writer.close()
#     output.seek(0)
#
#     return send_file(
#         output,
#         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         as_attachment=True,
#         download_name='1688_Full_Data.xlsx'
#     )
#
#
# if __name__ == '__main__':
#     app.run(
#         debug=True,
#         port=5000,
#         host="0.0.0.0",    # 要在局域网访问的话就加上
#         threaded=True,
#         use_reloader=False  # ⭐ 关键：关闭 Flask 自带重启器
#     )
#
