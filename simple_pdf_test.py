import pdfkit
import os
from datetime import datetime

# wkhtmltopdfの設定
wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

# パスが存在するか確認
if os.path.exists(wkhtmltopdf_path):
    print(f"wkhtmltopdf found at: {wkhtmltopdf_path}")
else:
    print(f"wkhtmltopdf NOT found at: {wkhtmltopdf_path}")
    exit(1)

# 設定オブジェクトを作成
config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

# シンプルなHTMLを作成
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MLB Test Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .team {
            background-color: #f0f0f0;
            padding: 20px;
            margin: 10px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>MLB Game Report Test</h1>
    <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    
    <div class="team">
        <h2>New York Yankees</h2>
        <p>Test data for Yankees</p>
    </div>
    
    <div class="team">
        <h2>Boston Red Sox</h2>
        <p>Test data for Red Sox</p>
    </div>
</body>
</html>
"""

# PDFを生成
try:
    # オプション設定
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    
    # PDFを生成
    output_file = 'test_report.pdf'
    pdfkit.from_string(html_content, output_file, configuration=config, options=options)
    
    print(f"Success! PDF created: {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()