import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv

# 1. ЗАГРУЗКА НАСТРОЕК
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"

def evaluate_pair(question, ideal, a, b):
    """Функция отправляет пару ответов на оценку нейронке-судье"""
    prompt = f"""
    Ты — строгий и объективный эксперт-оценщик. Твоя задача — сравнить два ответа на вопрос, используя идеальный ответ как эталон.

    ВОПРОС: {question}
    ЭТАЛОН: {ideal}

    ОТВЕТ А: {a}
    ОТВЕТ Б: {b}

    ПРАВИЛА ОЦЕНКИ (Максимум 10 баллов каждому):
    Изначально у каждого ответа 10 баллов. Вычитай баллы за следующие ошибки:
    - Фатальная галлюцинация или искажение фактов: -10 баллов.
    - Неполный ответ (упущена важная часть эталона): -3 балла.
    - Неточность в деталях: -3 балла.
    - Наличие "воды", лишних рассуждений или вводных фраз (например, "Окей, я готов"): -2 балла.

    ВЫВОД:
    Выдай вердикт строго в формате JSON. Сначала распиши логику штрафов, затем итоговые баллы, и только потом назови победителя.

    {{
      "reason": "Пошаговый расчет штрафов для Ответа А и Ответа Б. Кратко объясни, за что сняты баллы.",
      "score_a": <число от 0 до 10>,
      "score_b": <число от 0 до 10>,
      "winner": "A", "B" или "Tie"
    }}
    """
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": { "type": "json_object" },
        "temperature": 0
    }
    
    try:
        r = requests.post(URL, headers=headers, json=payload)
        res_text = r.json()['choices'][0]['message']['content']
        return json.loads(res_text)
    except Exception as e:
        return {"winner": "Error", "reason": f"Ошибка API: {str(e)}", "score_a": 0, "score_b": 0}

def generate_html_report(df):
    """Генерирует HTML-отчет со сводным дашбордом и таблицей"""
    
    # --- СЧИТАЕМ АНАЛИТИКУ ---
    total_q = len(df)
    
    # Подсчет побед
    win_counts = df['winner'].value_counts()
    win_a = win_counts.get('A', 0)
    win_b = win_counts.get('B', 0)
    ties = win_counts.get('Tie', 0)
    
    # Проценты (Win Rate)
    rate_a = (win_a / total_q) * 100 if total_q > 0 else 0
    rate_b = (win_b / total_q) * 100 if total_q > 0 else 0
    rate_tie = (ties / total_q) * 100 if total_q > 0 else 0
    
    # Баллы
    sum_a = df['score_a'].sum()
    sum_b = df['score_b'].sum()
    avg_a = df['score_a'].mean()
    avg_b = df['score_b'].mean()

    # --- HTML ШАБЛОН ---
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>LLM A/B Test Report V3</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 40px; color: #333; }}
            .container {{ max-width: 1500px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h2 {{ color: #1f4e78; border-bottom: 2px solid #1f4e78; padding-bottom: 10px; margin-bottom: 20px; }}
            
            /* Стили для Дашборда */
            .dashboard {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .card {{ flex: 1; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .card h3 {{ margin-top: 0; color: #495057; font-size: 1.2em; }}
            .metric-row {{ display: flex; justify-content: space-between; font-size: 1.1em; margin: 10px 0; border-bottom: 1px dashed #ccc; padding-bottom: 5px; }}
            .metric-value {{ font-weight: bold; color: #1f4e78; }}
            
            /* Стили для таблицы */
            table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
            th, td {{ border: 1px solid #dee2e6; padding: 15px; text-align: left; vertical-align: top; overflow: hidden; }}
            th {{ background: #1f4e78; color: white; position: sticky; top: 0; z-index: 10; }}
            .scroll-box {{ height: 250px; overflow-y: auto; background: #fafafa; border: 1px solid #eee; padding: 10px; border-radius: 4px; font-size: 0.9em; line-height: 1.5; white-space: pre-wrap; }}
            .winner-tag {{ display: inline-block; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85em; text-align: center; }}
            .winner-A {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
            .winner-B {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .winner-Tie {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
            .score-box {{ font-weight: bold; font-size: 1.1em; text-align: center; }}
            .reason-text {{ color: #666; font-size: 0.9em; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 LLM Benchmarking V3: Сводный Дашборд</h2>
            
            <div class="dashboard">
                <div class="card">
                    <h3>🏆 Win Rate (Процент побед)</h3>
                    <div class="metric-row"><span>Промпт А:</span> <span class="metric-value">{win_a} ({rate_a:.1f}%)</span></div>
                    <div class="metric-row"><span>Промпт Б:</span> <span class="metric-value">{win_b} ({rate_b:.1f}%)</span></div>
                    <div class="metric-row" style="border:none;"><span>Ничья (Tie):</span> <span class="metric-value">{ties} ({rate_tie:.1f}%)</span></div>
                </div>
                <div class="card">
                    <h3>🔵 Промпт А (Метрики)</h3>
                    <div class="metric-row"><span>Сумма баллов:</span> <span class="metric-value">{sum_a}</span></div>
                    <div class="metric-row" style="border:none;"><span>Средний балл:</span> <span class="metric-value">{avg_a:.1f} / 10</span></div>
                </div>
                <div class="card">
                    <h3>🟢 Промпт Б (Метрики)</h3>
                    <div class="metric-row"><span>Сумма баллов:</span> <span class="metric-value">{sum_b}</span></div>
                    <div class="metric-row" style="border:none;"><span>Средний балл:</span> <span class="metric-value">{avg_b:.1f} / 10</span></div>
                </div>
            </div>

            <table>
                <tr>
                    <th style="width: 15%;">Вопрос</th>
                    <th style="width: 25%;">Ответ А</th>
                    <th style="width: 25%;">Ответ Б</th>
                    <th style="width: 8%; text-align: center;">Баллы (А / Б)</th>
                    <th style="width: 7%; text-align: center;">Итог</th>
                    <th style="width: 20%;">Логика судьи</th>
                </tr>
    """
    
    for _, row in df.iterrows():
        if row['winner'] == 'A': win_class = "winner-A"
        elif row['winner'] == 'B': win_class = "winner-B"
        else: win_class = "winner-Tie"

        html_template += f"""
                <tr>
                    <td>{row['question']}</td>
                    <td><div class="scroll-box">{row['answer_a']}</div></td>
                    <td><div class="scroll-box">{row['answer_b']}</div></td>
                    <td class="score-box">{row['score_a']} / {row['score_b']}</td>
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

# --- ОСНОВНОЙ ПРОЦЕСС ---

print("🚀 Загрузка данных из file.csv...")
if not os.path.exists('file.csv'):
    print("❌ Ошибка: Файл file.csv не найден!")
    exit()

df = pd.read_csv('file.csv')

winners = []
reasons = []
scores_a = []
scores_b = []

print(f"🧐 Начинаем судейство {len(df)} пар ответов...")

for i, row in df.iterrows():
    print(f"Анализ вопроса №{i+1}...", end=" ", flush=True)
    verdict = evaluate_pair(row['question'], row['ideal_answer'], row['answer_a'], row['answer_b'])
    
    winners.append(verdict.get('winner', 'Error'))
    reasons.append(verdict.get('reason', 'Нет обоснования'))
    scores_a.append(verdict.get('score_a', 0))
    scores_b.append(verdict.get('score_b', 0))
    
    print(f"Готово! Победитель: {verdict.get('winner', 'Error')} | Счёт: {verdict.get('score_a', 0)} / {verdict.get('score_b', 0)}")

df['score_a'] = scores_a
df['score_b'] = scores_b
df['winner'] = winners
df['judge_reason'] = reasons

print("📊 Генерация отчетов...")
df.to_excel('final_report.xlsx', index=False)
generate_html_report(df)

print("\n✨ ВСЁ ГОТОВО! Открой report.html в браузере и оцени новый Дашборд.")