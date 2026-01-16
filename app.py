import os
import fitz  # PyMuPDF
import requests
from flask import Flask, render_template_string, request, send_file, redirect

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CONFIGURATION
API_KEY = "AIzaSyB-6_5iWDlZVQKfNjDcx9j2GbrfG9rO3r0"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def ai_process(text, task="clean"):
    if not text.strip(): return ""
    
    if task == "summary":
        prompt = f"Summarize the main themes of these book highlights in 3 interesting sentences: '{text}'"
    else:
        prompt = f"Fix this broken PDF highlight: '{text}'. Correct cut-off words. Output ONLY the fixed text."
        
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return "" if task == "summary" else text

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>Highlight Pro</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); text-align: center; width: 450px; }
            h1 { color: #1a73e8; margin-bottom: 8px; }
            p { color: #5f6368; margin-bottom: 30px; }
            
            .file-input-container { margin-bottom: 40px; } /* Increased gap to 40px */
            
            .file-label { 
                display: block;
                border: 2px dashed #dadce0; 
                padding: 30px; 
                border-radius: 12px; 
                cursor: pointer; 
                transition: all 0.3s;
                color: #3c4043;
                font-weight: 500;
            }
            .file-label:hover { border-color: #1a73e8; background: #f8f9fa; }
            
            button { background: #1a73e8; color: white; border: none; padding: 15px; border-radius: 30px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; transition: 0.3s; }
            button:hover { background: #1557b0; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(26,115,232,0.4); }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📚 Highlight Pro</h1>
            <p>Transform messy PDF notes into elegant reports.</p>
            <form method="post" enctype="multipart/form-data" action="/upload">
                <div class="file-input-container">
                    <input type="file" name="file" id="file" hidden required onchange="updateFileName()">
                    <label for="file" class="file-label" id="file-display">Click to select PDF</label>
                </div>
                <button type="submit">Generate Report</button>
            </form>
        </div>
        <script>
            function updateFileName() {
                const file = document.getElementById('file').files[0];
                document.getElementById('file-display').innerText = file ? file.name : "Click to select PDF";
                document.getElementById('file-display').style.borderColor = "#1a73e8";
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '': return redirect('/')
    
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_filename = file.filename.replace('.pdf', '_Report.html')
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    file.save(input_path)

    doc = fitz.open(input_path)
    all_text_for_summary = ""
    report_body = ""

    for page_num, page in enumerate(doc):
        annots = page.annots()
        if not annots: continue
        
        page_entries = []
        for annot in annots:
            # Type 8 is Highlight, Type 9 is Underline
            if annot.type[0] in [8, 9]: 
                # Identify which one it is for styling
                is_underline = (annot.type[0] == 9)
                
                # 1. Extract text from the page
                raw_text = page.get_text("text", clip=annot.rect).strip()
                
                # 2. Extract Hover comment
                comment = annot.info.get("content", "").strip()
                
                if raw_text:
                    healed_text = ai_process(raw_text.replace('\n', ' '))
                    
                    # Style differently based on type
                    border_color = "#e67e22" if is_underline else "#1a73e8"
                    label = "UNDERLINE" if is_underline else "HIGHLIGHT"
                    
                    entry = f'''
                    <div class="highlight-box" style="border-left-color: {border_color}">
                        <span class="type-label" style="color: {border_color}">{label}</span><br>
                        {healed_text}
                        {f'<div class="comment">📝 Note: {comment}</div>' if comment else ''}
                    </div>
                    '''
                        
                    page_entries.append(entry)
                    all_text_for_summary += healed_text + " "
        
        # Only add the page section if it contains highlights
        if page_entries:
            report_body += f'<div class="page-block"><div class="page-num">PAGE {page_num + 1}</div>'
            for item in page_entries:
                report_body += item
            report_body += '</div>'

    # Generate Summary
    summary = ai_process(all_text_for_summary[:4000], task="summary")

    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Charter', 'Georgia', serif; background: #fdfdfb; color: #222; max-width: 800px; margin: 50px auto; line-height: 1.7; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 60px; border-bottom: 2px solid #1a73e8; padding-bottom: 20px; }}
            .summary {{ background: #fff9e6; padding: 25px; border-radius: 12px; border-left: 6px solid #f1c40f; margin-bottom: 50px; font-style: italic; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .page-block {{ margin-bottom: 45px; }}
            .page-num {{ font-size: 13px; font-weight: bold; color: #1a73e8; letter-spacing: 2px; margin-bottom: 15px; border-bottom: 1px solid #eee; }}
            .highlight-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 15px; border-left: 4px solid #1a73e8; }}
            .comment {{ color: #555; font-size: 0.95em; display: block; margin-top: 8px; font-style: normal; font-family: sans-serif; background: #f9f9f9; padding: 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Reading Insights</h1>
            <p>Source: {file.filename}</p>
        </div>
        <div class="summary"><strong>✨ AI Executive Summary:</strong><br>{summary if summary else "No summary available."}</div>
        {report_body if report_body else "<p>No highlights found in this document.</p>"}
    </body>
    </html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)