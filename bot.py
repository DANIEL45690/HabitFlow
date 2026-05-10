import json
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import sys
import socket

TOKEN = "your-token(BRO)"
PORT = int(os.environ.get("PORT", 8080))

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>HabitFlow — трекер привычек</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background: #121212;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 12px;
        }
        .app-container {
            max-width: 500px;
            width: 100%;
            background: #1E1E2E;
            border-radius: 40px;
            box-shadow: 0 25px 45px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05);
            overflow: hidden;
        }
        .header {
            padding: 28px 24px 16px;
            background: linear-gradient(135deg, #1E1E2E 0%, #2A2A3A 100%);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(120deg, #FFFFFF, #A78BFA);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        .header p {
            font-size: 14px;
            color: #9CA3AF;
            margin-top: 6px;
        }
        .stats-row {
            display: flex;
            gap: 16px;
            margin-top: 20px;
            background: rgba(0,0,0,0.3);
            padding: 12px 16px;
            border-radius: 28px;
        }
        .stat-card {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(255,255,255,0.04);
            border-radius: 24px;
            padding: 10px 0;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 800;
            color: #C4B5FD;
        }
        .stat-label {
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
        }
        .tabs {
            display: flex;
            padding: 16px 20px 0;
            gap: 12px;
        }
        .tab-btn {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 0;
            font-size: 16px;
            font-weight: 600;
            color: #9CA3AF;
            border-radius: 32px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab-btn.active {
            background: #2D2D3F;
            color: #E0D6FF;
        }
        .content-pane {
            padding: 20px 20px 28px;
            min-height: 520px;
        }
        .pane {
            display: none;
            animation: fade 0.25s ease;
        }
        .pane.active-pane {
            display: block;
        }
        @keyframes fade {
            from { opacity: 0; transform: translateY(6px);}
            to { opacity: 1; transform: translateY(0);}
        }
        .add-task-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            background: #272738;
            padding: 6px 6px 6px 18px;
            border-radius: 48px;
        }
        .add-task-bar input {
            flex: 1;
            background: transparent;
            border: none;
            color: #F3F4F6;
            font-size: 15px;
            padding: 12px 0;
            outline: none;
        }
        .add-task-bar input::placeholder {
            color: #6B7280;
        }
        .add-btn {
            background: #8B5CF6;
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            cursor: pointer;
            transition: 0.15s;
        }
        .add-btn:active {
            transform: scale(0.96);
        }
        .list-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 420px;
            overflow-y: auto;
            padding-right: 4px;
        }
        .list-container::-webkit-scrollbar {
            width: 4px;
        }
        .list-container::-webkit-scrollbar-track {
            background: #252535;
            border-radius: 8px;
        }
        .list-container::-webkit-scrollbar-thumb {
            background: #6B7280;
            border-radius: 8px;
        }
        .task-item {
            background: #272738;
            border-radius: 24px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .task-left {
            display: flex;
            align-items: center;
            gap: 14px;
            flex: 1;
        }
        .task-check {
            width: 22px;
            height: 22px;
            border-radius: 30px;
            border: 2px solid #6B7280;
            background: transparent;
            cursor: pointer;
        }
        .task-check.completed {
            background: #10B981;
            border-color: #10B981;
            position: relative;
        }
        .task-check.completed::after {
            content: "✓";
            color: white;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .task-text {
            font-size: 16px;
            font-weight: 500;
            color: #E5E7EB;
            word-break: break-word;
        }
        .task-text.line-through {
            text-decoration: line-through;
            color: #6B7280;
        }
        .delete-item {
            background: rgba(239,68,68,0.15);
            border: none;
            width: 34px;
            height: 34px;
            border-radius: 30px;
            color: #F87171;
            font-size: 18px;
            cursor: pointer;
        }
        .habit-streak {
            font-size: 12px;
            background: #1E1E2E;
            padding: 4px 8px;
            border-radius: 40px;
            color: #A78BFA;
            font-weight: 600;
        }
        .empty-state {
            text-align: center;
            padding: 48px 24px;
            color: #6B7280;
        }
        .footer-note {
            text-align: center;
            font-size: 11px;
            color: #4B5563;
            margin-top: 20px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
    </style>
</head>
<body>
<div class="app-container">
    <div class="header">
        <h1>HabitFlow</h1>
        <p>привычки + задачи, каждый день</p>
        <div class="stats-row">
            <div class="stat-card"><span class="stat-value" id="totalTasksCount">0</span><span class="stat-label">задач</span></div>
            <div class="stat-card"><span class="stat-value" id="completedTasksCount">0</span><span class="stat-label">выполнено</span></div>
            <div class="stat-card"><span class="stat-value" id="totalHabitsCount">0</span><span class="stat-label">привычек</span></div>
        </div>
    </div>
    <div class="tabs">
        <button class="tab-btn active" data-tab="tasks">📋 Задачи</button>
        <button class="tab-btn" data-tab="habits">🔥 Привычки</button>
    </div>
    <div class="content-pane">
        <div id="tasksPane" class="pane active-pane">
            <div class="add-task-bar">
                <input type="text" id="taskInput" placeholder="Новая задача..." autocomplete="off">
                <button class="add-btn" id="addTaskBtn">+</button>
            </div>
            <div id="tasksList" class="list-container"><div class="empty-state">✨ Добавьте задачу</div></div>
        </div>
        <div id="habitsPane" class="pane">
            <div class="add-task-bar">
                <input type="text" id="habitInput" placeholder="Новая привычка..." autocomplete="off">
                <button class="add-btn" id="addHabitBtn">+</button>
            </div>
            <div id="habitsList" class="list-container"><div class="empty-state">🌱 Создайте привычку</div></div>
        </div>
    </div>
    <div class="footer-note">✓ отмечай задачи и привычки — прогресс сохраняется</div>
</div>
<script>
    const STORAGE_KEYS = { TASKS: 'habitflow_tasks', HABITS: 'habitflow_habits' };
    let tasks = [], habits = [];
    function saveTasks() { localStorage.setItem(STORAGE_KEYS.TASKS, JSON.stringify(tasks)); }
    function saveHabits() { localStorage.setItem(STORAGE_KEYS.HABITS, JSON.stringify(habits)); }
    function getTodayDateStr() { const d=new Date(); return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); }
    function getYesterdayStr() { const d=new Date(); d.setDate(d.getDate()-1); return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); }
    function loadData() {
        const storedTasks = localStorage.getItem(STORAGE_KEYS.TASKS);
        if(storedTasks) { try { tasks = JSON.parse(storedTasks); } catch(e) {} }
        if(!tasks.length) { tasks = [{ id:'t1', text:'Выпить воду', completed:false },{ id:'t2', text:'Сделать зарядку', completed:false }]; saveTasks(); }
        const storedHabits = localStorage.getItem(STORAGE_KEYS.HABITS);
        if(storedHabits) { try { habits = JSON.parse(storedHabits); } catch(e) {} }
        if(!habits.length) { habits = [{ id:'h1', name:'🏃 Зарядка', streak:0, lastTrackedDate:null },{ id:'h2', name:'📚 Чтение', streak:0, lastTrackedDate:null }]; saveHabits(); }
    }
    function isHabitTrackedToday(habitId) { const habit = habits.find(h=>h.id===habitId); return habit ? habit.lastTrackedDate === getTodayDateStr() : false; }
    function updateStreak(habitId, markComplete) {
        const habit = habits.find(h=>h.id===habitId);
        if(!habit) return;
        const today = getTodayDateStr();
        if(markComplete) {
            if(habit.lastTrackedDate === today) return;
            const yesterday = getYesterdayStr();
            habit.streak = habit.lastTrackedDate === yesterday ? (habit.streak||0)+1 : 1;
            habit.lastTrackedDate = today;
        } else {
            if(habit.lastTrackedDate === today) { habit.lastTrackedDate = null; habit.streak = 0; }
        }
        saveHabits();
    }
    function renderTasks() {
        const container = document.getElementById('tasksList');
        if(!tasks.length) { container.innerHTML='<div class="empty-state">📭 Нет задач</div>'; updateStats(); return; }
        container.innerHTML = tasks.map(t => `<div class="task-item" data-task-id="${t.id}"><div class="task-left"><div class="task-check ${t.completed?'completed':''}" data-action="toggle"></div><span class="task-text ${t.completed?'line-through':''}">${escapeHtml(t.text)}</span></div><button class="delete-item" data-action="delete">✕</button></div>`).join('');
        updateStats();
    }
    function renderHabits() {
        const container = document.getElementById('habitsList');
        if(!habits.length) { container.innerHTML='<div class="empty-state">🌟 Нет привычек</div>'; updateStats(); return; }
        container.innerHTML = habits.map(h => `<div class="task-item" data-habit-id="${h.id}"><div class="task-left"><div class="task-check ${isHabitTrackedToday(h.id)?'completed':''}" data-action="toggle-habit"></div><span class="task-text">${escapeHtml(h.name)}</span></div><div style="display:flex;gap:10px;align-items:center;"><span class="habit-streak">🔥 ${h.streak||0} дн.</span><button class="delete-item" data-action="delete-habit">✕</button></div></div>`).join('');
        updateStats();
    }
    function escapeHtml(str) { if(!str) return ''; return str.replace(/[&<>]/g, function(m) { if(m==='&') return '&amp;'; if(m==='<') return '&lt;'; if(m==='>') return '&gt;'; return m; }); }
    function updateStats() { document.getElementById('totalTasksCount').innerText = tasks.length; document.getElementById('completedTasksCount').innerText = tasks.filter(t=>t.completed).length; document.getElementById('totalHabitsCount').innerText = habits.length; }
    function addTask(text) { if(!text.trim()) return; tasks.unshift({ id:Date.now()+'-'+Math.random(), text:text.trim(), completed:false }); saveTasks(); renderTasks(); }
    function toggleTask(id) { const t = tasks.find(t=>t.id===id); if(t) { t.completed = !t.completed; saveTasks(); renderTasks(); } }
    function deleteTask(id) { tasks = tasks.filter(t=>t.id!==id); saveTasks(); renderTasks(); }
    function addHabit(name) { if(!name.trim()) return; habits.push({ id:Date.now()+'-'+Math.random(), name:name.trim(), streak:0, lastTrackedDate:null }); saveHabits(); renderHabits(); }
    function toggleHabit(id) { const tracked = isHabitTrackedToday(id); updateStreak(id, !tracked); renderHabits(); }
    function deleteHabit(id) { habits = habits.filter(h=>h.id!==id); saveHabits(); renderHabits(); }
    document.getElementById('addTaskBtn').onclick = () => { addTask(document.getElementById('taskInput').value); document.getElementById('taskInput').value=''; };
    document.getElementById('addHabitBtn').onclick = () => { addHabit(document.getElementById('habitInput').value); document.getElementById('habitInput').value=''; };
    document.getElementById('taskInput').onkeypress = (e) => { if(e.key==='Enter') document.getElementById('addTaskBtn').click(); };
    document.getElementById('habitInput').onkeypress = (e) => { if(e.key==='Enter') document.getElementById('addHabitBtn').click(); };
    document.getElementById('tasksPane').onclick = (e) => { const item = e.target.closest('.task-item'); if(!item) return; const id = item.dataset.taskId; if(e.target.closest('[data-action="toggle"]')) toggleTask(id); if(e.target.closest('[data-action="delete"]')) deleteTask(id); };
    document.getElementById('habitsPane').onclick = (e) => { const item = e.target.closest('.task-item'); if(!item) return; const id = item.dataset.habitId; if(e.target.closest('[data-action="toggle-habit"]')) toggleHabit(id); if(e.target.closest('[data-action="delete-habit"]')) deleteHabit(id); };
    document.querySelectorAll('.tab-btn').forEach(btn => { btn.onclick = () => { document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); document.getElementById('tasksPane').classList.toggle('active-pane', btn.dataset.tab==='tasks'); document.getElementById('habitsPane').classList.toggle('active-pane', btn.dataset.tab==='habits'); if(btn.dataset.tab==='tasks') renderTasks(); else renderHabits(); }; });
    loadData(); renderTasks(); renderHabits();
</script>
</body>
</html>"""


class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run_web_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), WebAppHandler)
        print(f"✅ Веб-сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        web_app_url = f"http://{local_ip}:{PORT}/"
    except:
        web_app_url = f"http://localhost:{PORT}/"

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Открыть трекер привычек", web_app=WebAppInfo(url=web_app_url)
            )
        ]
    ]

    welcome_text = (
        f"🌟 *Добро пожаловать в HabitFlow, {user.first_name}!* 🌟\n\n"
        "✅ *Отслеживай задачи*\n"
        "🔥 *Развивай привычки*\n"
        "📊 *Следи за прогрессом*\n\n"
        "Нажми на кнопку ниже, чтобы открыть приложение!\n\n"
        "💡 *Совет:* Добавь ежедневные привычки и отмечай их каждый день!"
    )

    await update.message.reply_text(
        welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Как пользоваться HabitFlow:*\n\n"
        "1️⃣ Нажми на кнопку «Открыть трекер привычек»\n"
        "2️⃣ Добавляй задачи и привычки через специальные поля\n"
        "3️⃣ Отмечай выполненные ✓ нажатием на кружок\n"
        "4️⃣ Привычки считают дни подряд 🔥 — не пропускай!\n"
        "5️⃣ Удаляй ненужное крестиком ✕\n\n"
        "📌 *Важно:* Все данные сохраняются на твоём устройстве!\n"
        "🔄 При смене браузера или очистке кэша данные могут потеряться.\n\n"
        "📊 *Статистика:* Сверху отображается количество задач и привычек."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 *HabitFlow v1.0*\n\n"
        "Твой персональный помощник для формирования полезных привычек\n"
        "и управления задачами.\n\n"
        "✨ *Особенности:*\n"
        "• Трекер задач с отметкой выполнения\n"
        "• Трекер привычек с подсчётом дней подряд\n"
        "• Статистика прогресса\n"
        "• Сохранение данных на устройстве\n\n"
        "📱 *Разработчик:* Telegram Mini App\n"
        "💡 *Идея:* Сделай свою жизнь лучше каждый день!"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Ошибка: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте позже или используйте /start заново."
            )
        except:
            pass


def main():
    print("=" * 50)
    print("🚀 ЗАПУСК HABITFLOW БОТА")
    print("=" * 50)

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    import time

    time.sleep(1)

    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_error_handler(error_handler)

        print("✅ Бот успешно инициализирован")
        print(f"🤖 Токен: {TOKEN[:10]}...")
        print("🌐 Запуск polling...")
        print("=" * 50)
        print("\n💡 Бот готов к работе!")
        (
            print(f"📱 Откройте Telegram и напишите @{TOKEN.split(':')[0]}")
            if TOKEN != "ВАШ_ТОКЕН"
            else None
        )
        print("\n")

        application.run_polling(
            allowed_updates=["message", "callback_query"], drop_pending_updates=True
        )

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Пробуем перезапустить через 5 секунд...")
        time.sleep(5)
        main()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    print("""
    ╔═══════════════════════════════════════╗
    ║     HABITFLOW - Трекер привычек      ║
    ║         Telegram Mini App            ║
    ╚═══════════════════════════════════════╝
    """)

    if TOKEN == "8706331779:AAGud8ziujulNiFjGbSO7Y31nSa1B1GzIu0":
        print("⚠️ ВНИМАНИЕ: Используется старый токен!")
        print("⚠️ СРОЧНО замените токен через @BotFather!")
        print()

    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Необработанная ошибка: {e}")
        sys.exit(1)
