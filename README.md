# 🤖 LLM Benchmarking & Evaluation Tool (v2.0)

Профессиональный инструмент для автоматизированного A/B тестирования и глубокой аналитики ответов больших языковых моделей (LLM).

## 🚀 Как это работает

Проект объединяет гибкость low-code автоматизации и мощь Python-аналитики:

1.  **Сбор данных (n8n):** Воркфлоу параллельно опрашивает разные модели, контролирует ошибки API и собирает результаты в единый CSV-датасет.
2.  **Аналитика (Python + Pandas):** Скрипт-судья проводит кросс-валидацию ответов по эталону, начисляет штрафные баллы и генерирует наглядный отчет.

---

## 📐 Визуализация системы

### Воркфлоу сбора данных в n8n:
Спроектирован с учетом отказоустойчивости (Fault Tolerance) и автоматической обработки сбоев.
![n8n Workflow](n8n_workflow.png)

### Интерактивный Дашборд аналитики:
Визуализация Win Rate, средних баллов и детальной логики судейства.
![Dashboard Preview](dashboard_preview.png)

---

## 🛠 Технологический стек

* **Automation:** n8n (Fault Tolerant architecture).
* **Data Science:** Python 3.x, Pandas (Data processing).
* **LLM Integration:** OpenRouter (Gemini, GPT, Claude).
* **Reporting:** HTML5/CSS3 Dashboard & Excel exports.
* **DevOps:** Docker (Containerization).

---

## 📦 Установка и запуск

### Вариант 1: Через Docker (Рекомендуется)
Гарантирует работу без установки Python и библиотек на ваш компьютер.

1. **Сборка образа:**
   docker build -t ai-judge-v2 .

2. **Запуск анализа:**
   docker run -v ${PWD}:/app ai-judge-v2

### Вариант 2: Локально (Python)
1. Установите зависимости: pip install pandas requests python-dotenv openpyxl
2. Настройте API-ключ в файле .env.
3. Запустите: python judge.py