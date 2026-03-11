import pandas as pd
import requests
import os
import json
import math
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

# 1. ЗАГРУЗКА НАСТРОЕК
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"

def evaluate_pair(question, ideal, a, b):
    """Функция отправляет пару ответов на оценку нейронке-судье"""
    prompt = f"""
    Ты — экспертный судья. Сравни два ответа на вопрос, используя идеальный ответ как эталон.
    
    ВОПРОС: {question}
    ЭТАЛОН: {ideal}
    
    ОТВЕТ А: {a}
    ОТВЕТ Б: {b}
    
    КРИТЕРИИ: 
    1. Точность (соответствие эталону).
    2. Полнота.
    3. Отсутствие галлюцинаций и воды.

    Выдай вердикт строго в формате JSON:
    {{
      "winner": "A" или "B",
      "reason": "короткое и жесткое обоснование"
    }}
    """
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": { "type": "json_object" }
    }
    
    try:
        r = requests.post(URL, headers=headers, json=payload)
        res_text = r.json()['choices'][0]['message']['content']
        return json.loads(res_text)
    except Exception as e:
        return {"winner": "Error", "reason": str(e)}

def generate_html_report(df):
    """Генерирует современный HTML-отчет с прокруткой внутри ячеек"""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>LLM A/B Test Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 40px; color: #333; }}
            .container {{ max-width: 1400px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h2 {{ color: #1f4e78; border-bottom: 2px solid #1f4e78; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; table-layout: fixed; }}
            th, td {{ border: 1px solid #dee2e6; padding: 15px; text-align: left; vertical-align: top; overflow: hidden; }}
            th {{ background: #1f4e78; color: white; position: sticky; top: 0; z-index: 10; }}
            .scroll-box {{ height: 250px; overflow-y: auto; background: #fafafa; border: 1px solid #eee; padding: 10px; border-radius: 4px; font-size: 0.9em; line-height: 1.5; white-space: pre-wrap; }}
            .winner-tag {{ display: inline-block; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85em; }}
            .winner-A {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
            .winner-B {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .reason-text {{ color: #666; font-style: italic; font-size: 0.9em; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f4f7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 LLM Benchmarking: Результаты A/B теста</h2>
            <p><strong>Модель-судья:</strong> Gemini 2.0 Flash Lite</p>
            <table>
                <tr>
                    <th style="width: 15%;">Вопрос</th>
                    <th style="width: 30%;">Ответ А (Base)</th>
                    <th style="width: 30%;">Ответ Б (CoT)</th>
                    <th style="width: 8%; text-align: center;">Победитель</th>
                    <th style="width: 17%;">Вердикт судьи</th>
                </tr>
    """
    
    for _, row in df.iterrows():
        win_class = "winner-A" if row['winner'] == 'A' else "winner-B"
        html_template += f"""
                <tr>
                    <td>{row['question']}</td>
                    <td><div class="scroll-box">{row['answer_a']}</div></td>
                    <td><div class="scroll-box">{row['answer_b']}</div></td>
                    <td style="text-align: center;"><span class="winner-tag {win_class}">{row['winner']}</span></td>
                    <td class="reason-text">{row['judge_reason']}</td>
                </tr>
        """
    
    html_template += """
            </table>
        </div>
    </body>
    </html>
    """
    
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("🌐 HTML-отчет успешно создан: report.html")

# --- ОСНОВНОЙ ПРОЦЕСС ---

print("🚀 Шаг 1: Загрузка данных из data.csv...")
if not os.path.exists('data.csv'):
    print("❌ Ошибка: Файл data.csv не найден!")
    exit()

df = pd.read_csv('data.csv')
winners = []
reasons = []

print(f"🧐 Шаг 2: Оценка {len(df)} пар ответов...")

for i, row in df.iterrows():
    print(f"Анализ вопроса №{i+1}...", end=" ", flush=True)
    verdict = evaluate_pair(row['question'], row['ideal_answer'], row['answer_a'], row['answer_b'])
    winners.append(verdict['winner'])
    reasons.append(verdict['reason'])
    print(f"Готово! Победитель: {verdict['winner']}")

df['winner'] = winners
df['judge_reason'] = reasons

# --- СОХРАНЕНИЕ EXCEL (Для структуры) ---
print("📊 Шаг 3: Генерация Excel-архива...")
output_excel = 'final_report.xlsx'
writer = pd.ExcelWriter(output_excel, engine='openpyxl')
df.to_excel(writer, index=False, sheet_name='Results')

# Минимальное оформление для Excel, чтобы не было совсем страшно
worksheet = writer.sheets['Results']
for col in ['A', 'B', 'C', 'D', 'F']:
    worksheet.column_dimensions[col].width = 40
writer.close()

# --- ГЕНЕРАЦИЯ HTML (Для удобного чтения) ---
print("🌐 Шаг 4: Генерация визуального HTML-отчета...")
generate_html_report(df)

print("\n--- ИТОГИ ТЕСТА ---")
print(df['winner'].value_counts())
print(f"\n✨ ВСЁ ГОТОВО! \n📁 Excel: {output_excel}\n🌐 HTML: report.html (открой его в браузере)")