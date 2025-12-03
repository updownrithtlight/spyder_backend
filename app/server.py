from flask import Flask, request, send_file
from flask_cors import CORS
import pandas as pd
import io
import requests
from PIL import Image

app = Flask(__name__)
CORS(app)


@app.route('/generate_excel', methods=['POST'])
def generate_excel():
    print("收到数据，正在生成 Excel...")

    req_data = request.json
    rows = req_data.get('rows', [])

    if not rows:
        return {"error": "No data"}, 400

    # 1. 定义所有要保存的列 (对应 content.js 发送的数据顺序)
    columns = [
        '标题', '图片链接', '价格', '公司名称',
        '类目', '年销量', '月代销', '48h揽收', '上架日期', '开店时长', '商品链接'
    ]

    df = pd.DataFrame(rows, columns=columns)

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)

    workbook = writer.book
    worksheet = writer.sheets['Sheet1']

    # 设置格式
    cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
    worksheet.set_column('A:Z', 18, cell_format)  # 默认宽度
    worksheet.set_column('B:B', 16)  # 图片列宽度
    worksheet.set_column('A:A', 30)  # 标题列宽一点
    worksheet.set_column('K:K', 40)  # 链接列宽一点

    # 2. 下载图片并插入 (在第2列，索引为1)
    img_col_idx = 1

    for index, row in df.iterrows():
        img_url = row['图片链接']
        excel_row = index + 1
        worksheet.set_row(excel_row, 100)  # 行高

        if not img_url or not str(img_url).startswith('http'):
            worksheet.write(excel_row, img_col_idx, "无图")
            continue

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(img_url, headers=headers, timeout=5)
            if response.status_code == 200:
                image_data = io.BytesIO(response.content)
                img = Image.open(image_data)
                img.thumbnail((180, 180))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')

                worksheet.insert_image(excel_row, img_col_idx, "img.png", {
                    'image_data': img_byte_arr, 'x_scale': 0.7, 'y_scale': 0.7,
                    'x_offset': 5, 'y_offset': 5, 'positioning': 1
                })
                print(f"✅ 第 {index + 1} 行图片下载成功")
            else:
                worksheet.write(excel_row, img_col_idx, "下载失败")
        except:
            worksheet.write(excel_row, img_col_idx, "错误")

    writer.close()
    output.seek(0)

    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='1688_Full_Data.xlsx')


if __name__ == '__main__':
    app.run(debug=True, port=5000)