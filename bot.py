import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ChatJoinRequestHandler,
    ChatMemberHandler
)
from telegram.constants import ChatMemberStatus
from datetime import datetime

API_TOKEN = '8000554853:AAG7vmCauc8XcvpPA7VciU6Z0TYixtfqn80'
MAIN_CHANNEL_ID = -1002366098084  # Канал для рассылки
NOTIFICATION_CHANNEL_ID = -1002679234430  # Новый канал для уведомлений
PRIVATE_CHANNEL_ID = -1002594928531
ADMIN_ID = 7567695472
CHANNEL_LINK = 'https://t.me/+NUq2EXMs_to5MzYy'
WELCOME_IMAGE = 'welcome.png'
SUBSCRIBERS = set()
USER_DB = set()  # Все пользователи бота

#Импорты и настройка Google Sheets
GSCOPE = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']
GCREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', GSCOPE)
GCLIENT = gspread.authorize(GCREDS)
SHEET = GCLIENT.open("Результаты теста ген преступника").sheet1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and isinstance(update, Update):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

async def notify_admin(action: str, user: dict, context: CallbackContext, feedback: str = None):
    try:
        text = (f"🚨 <b>СОБЫТИЕ:</b> {action}\n"
                f"▫️ <b>Пользователь:</b> {user['mention']}\n"
                f"▫️ <b>ID:</b> <code>{user['id']}</code>\n"
                f"▫️ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        if feedback:
            text += f"\n\n📝 <b>Отзыв:</b>\n{feedback}"
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Admin notification error: {e}")

async def handle_chat_join_request(update: Update, context: CallbackContext) -> None:
    try:
        user = update.chat_join_request.from_user
        logger.info(f"Auto-approving join request from {user.id}")
        
        # Мгновенное принятие заявки
        await context.bot.approve_chat_join_request(
            chat_id=PRIVATE_CHANNEL_ID,
            user_id=user.id
        )
        
        # Отправка основного приветственного сообщения
        await send_welcome_message(user.id, context)

    except Exception as e:
        logger.error(f"Join request error: {e}")

async def start(update: Update, context: CallbackContext) -> None:
    try:
        context.user_data.clear()
        user = update.effective_user
        USER_DB.add(user.id)
        
        # Всегда отправляем welcome-сообщение
        await send_welcome_message(user.id, context)
        logger.info(f"User {user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in start: {e}")

async def start(update: Update, context: CallbackContext) -> None:
    try:
        context.user_data.clear()
        user = update.effective_user
        USER_DB.add(user.id)
        
        # Всегда отправляем welcome-сообщение
        await send_welcome_message(user.id, context)
        logger.info(f"User {user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in start: {e}")

async def send_welcome_message(user_id: int, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🩸 Ген преступника", callback_data='gen_criminal')],
        [InlineKeyboardButton("📩 Ежедневный инструмент", callback_data='subscribe')],
        [InlineKeyboardButton("🔗 Открыть канал", url=CHANNEL_LINK)]
    ]
    
    try:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=open(WELCOME_IMAGE, 'rb'),
            caption=(
                "<b>🔐 ДОБРО ПОЖАЛОВАТЬ В ПРИКЛАДНУЮ ПСИХОЛОГИЮ БЕЗ ЦЕНЗУРЫ</b>\n\n"
                "🔥 <b>Основная тематика канала:</b>\n"
                "• Глубокий анализ манипулятивных техник\n"
                "• Нейрофизиологические исследования поведения\n"
                "• Эксклюзивные кейсы из криминальной психологии\n\n"
                "🛠 <b>Доступные опции:</b>\n"
                "🩸 <b>Ген преступника</b> - уникальный тест по методике Ломброзо на определение наличия или отсутствия у Вас генетической преступной предрасположенности.\n"
                "📩 <b>Ежедневный инструмент</b> - ежедневные материалы с научными первоисточниками.\n"
                "🔒 <b>Открыть канал</b> - мгновенный доступ ко всем закрытым материалам."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),  # Правильное создание клавиатуры
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Welcome message error: {e}")



async def save_message(update: Update, context: CallbackContext, message_id: int) -> None:
    try:
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(message_id)
    except Exception as e:
        logger.error(f"Error saving message: {e}")

async def delete_previous_messages(update: Update, context: CallbackContext) -> None:
    try:
        for msg_id in context.user_data.get('message_ids', []):
            try:
                await context.bot.delete_message(update.effective_chat.id, msg_id)
            except Exception as e:
                logger.warning(f"Error deleting message: {e}")
        context.user_data['message_ids'] = []
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")

async def main_menu(update: Update, context: CallbackContext) -> None:
    try:
        # Определяем chat_id в зависимости от типа вызова
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            chat_id = query.message.chat_id
            await delete_previous_messages(update, context)
        else:
            chat_id = update.effective_chat.id
            await delete_previous_messages(update, context)
        
        keyboard = [
            [InlineKeyboardButton("📩 Подписаться на рассылку", callback_data='subscribe')],
            [ InlineKeyboardButton("🩸Генетический преступник", callback_data='gen_criminal')],
            [InlineKeyboardButton("🔑 Подать заявку в канал", url=CHANNEL_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=open(WELCOME_IMAGE, 'rb'),
        caption=(
            "<b>🔐 ПРИКЛАДНАЯ ПСИХОЛОГИЯ БЕЗ ЦЕНЗУРЫ</b>\n\n"
            "🔥 <b>Что вас ждёт?</b>\n"
            "• Глубокий разбор манипуляций: реальные приёмы и методы защиты.\n"
            "• Нейрофизиологические инсайты: как мозг и тело реагируют на каждый стресс.\n"
            "• Клинические кейсы: практические примеры, проверенные временем.\n\n"
            "📚 <b>Экспертная рассылка:</b>\n"
            "1️⃣ Антиманипулятивные стратегии — живые сценарии и чек-листы.\n"
            "2️⃣ Нейрофизиологические лайфхаки — простые ежедневные упражнения.\n"
            "3️⃣ Реальные клинические разборы — из первых рук.\n\n"
            "🔒 <b>Закрытый канал:</b>\n"
            "• 1–2 мощных инструмента каждый день\n"
            "• Ссылки на PubMed, Springer и оригинальные исследования\n"
            "• Углублённые материалы по биохимии поведения\n\n"
            "⏺ <b>Выберите действие</b> ниже и начнём трансформировать ваш взгляд на психологию!"
        ),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
        await save_message(update, context, message.message_id)
    except Exception as e:
        logger.error(f"Error in main_menu: {e}")

async def gen_criminal_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await delete_previous_messages(update, context)

    user_id = query.from_user.id
    # Попытка получить статус подписки
    try:
        member = await context.bot.get_chat_member(
            chat_id=PRIVATE_CHANNEL_ID,
            user_id=user_id
        )
        status = member.status
    except Exception as e:
        # Если бот не имеет права читать список участников или другая ошибка —
        # считаем, что статус неизвестен
        logger.warning(f"Cannot fetch chat member: {e}")
        status = None

    # Считаем подписчиком только при явном статусе MEMBER/ADMIN/OWNER
    if status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ):
        # Пользователь подписан — показываем меню теста
        kb = [
            [ InlineKeyboardButton("🎲 Тест на «Генетического преступника»", callback_data='start_test') ],
            [ InlineKeyboardButton("📋 Статья по теме", url='https://telegra.ph/Teoriya-tipov-prestupnikov-Lombrozo-04-28') ]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                "🎲 *Добро пожаловать в тест «Генетического преступника»!* 🎲\n\n"
                "Согласно канонической теории Ломброзо, каждый физический и поведенческий признак несёт в себе информацию о глубинных биологических кодах личности.\n\n"
                "📋 В этом тесте вы пройдёте через 20 строго отобранных вопросов, которые уже доказали свою эффективность в работе криминологов США, Великобритании, Германии и России.\n\n"
                "Готовы ли вы узнать правду о себе и прикоснуться к методике, проверенной более века назад?\n\n"
                "Выберите действие:"
            ),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        # Нет явного подтверждения членства — просим подписаться
        kb_sub = [
            [ InlineKeyboardButton("🔑 Подписаться на канал", url=CHANNEL_LINK) ],
            [ InlineKeyboardButton("🏠 Главное меню",    callback_data='main_menu') ]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                "🔒 *Доступ к тесту «Генетического преступника» временно закрыт!*\n\n"
                "Чтобы пройти этот уникальный тест, вы должны быть подписаны на наш закрытый канал, где мы публикуем эксклюзивные материалы по криминологии и психофизиологии.\n\n"
                "📚 Именно здесь собраны лучшие практики Ломброзо, которыми активно пользуются криминологи США, Германии,Японии и России при первичных допросах и оценке подозреваемых.\n\n"
                "Нажмите «🔑 Подписаться на канал» и вернитесь к тесту."
            ),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb_sub)
        )

QUESTIONS = [
    "У вас низкий/скошенный лоб?\n""Проверьте: если расстояние от бровей до линии роста волос меньше 4 см (низкий) или лоб имеет выраженный наклон назад (скошенный)",
    "У вас близко посаженные глаза?\n""Расстояние между внутренними уголками глаз меньше ширины одного глаза (можно измерить пальцем).",
    "У вас плоский нос или нос с горбинкой?\n""Плоский: почти нет переносицы, крючковатый: кончик носа загнут вниз как «клюв».",
    "У вас толстые губы?\n""Верхняя/нижняя губа заметно объемнее среднестатистической (как у анфас-портретов - фотографий на паспорт).",
    "У вас выступающая челюсть или подбородок?\n""Проверка в профиль: линия подбородка выходит вперед относительно лба и носа.",
    "У вас большие или выступающие уши?\n""Ушная раковина явно выделяется при взгляде спереди/сбоку (более 6.5 см в длину).",
    "Сходятся ли ваши брови посередине?\n""Волоски бровей соединяются над переносицей, образуя сплошную линию.", 
    "Вы лысый или имеете редкую бороду?\n""Для мужчин: облысение по любой шкале Норвуда, редкая/неравномерная растительность на лице.", 
    "У вас избыточная волосатость тела?\n""Волосы покрывают спину, плечи, руки (для женщин — по мужскому типу).",
    "У вас асимметричное лицо или голова?\n""Заметные различия в форме глаз, скул, положения ушей при детальном рассмотрении.",
    "У вас высокий или необычно низкий рост?\n""Для мужчин: ниже 160 см или выше 195 см; для женщин: ниже 150 см или выше 185 см.",
    "У вас необычная форма черепа (например, удлиненный или сплющенный)?\n""Явные отклонения от овальной формы (врожденные/травматические).",
    "У вас большие или необычно формированные зубы?\n""Кривые, выступающие клыки, щели, размер на 20-30% больше нормы.", 
    "У вас есть шрамы или татуировки на видных местах?\n""Лицо, шея, кисти рук — области, которые нельзя скрыть одеждой.", 
    "У вас холодный или жесткий взгляд?\n""Окружающие часто отмечают «тяжелый» или «недружелюбный» взгляд без объективной причины.", 
    "У вас необычная пигментация кожи или волос?\n""Альбинизм, витилиго, сегментированная седина, врожденные пятна.", 
    "У вас слабое здоровье или частые болезни?\n""Хронические диагнозы, госпитализации ≥2 раз в год, постоянный прием лекарств.", 
    "У вас есть склонность к алкоголизму или другим зависимостям?\n""Регулярное употребление наркотических веществ, игровая/цифровая зависимость?", 
    "У вас агрессивное или импульсивное поведение?\n""Срывы на окружающих, неконтролируемые действия в стрессе по оценке близких.",
    "У вас низкий уровень образования или отсутствие профессии?\n""Нет среднего специального/высшего образования или официального трудоустройства."
]

async def start_test(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Очищаем все сообщения пользователя
    context.user_data.clear()

    context.user_data['score'] = 0
    context.user_data['q_index'] = 0
    context.user_data['start_time'] = datetime.now()
    await ask_question(update, context)

async def ask_question(update: Update, context: CallbackContext) -> None:
    idx = context.user_data['q_index']
    # Удаляем предыдущий вопрос, если есть
    last_message_id = context.user_data.get('last_message_id')
    if last_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=last_message_id
            )
        except Exception as e:
            
            logger.warning(f"Failed to delete message: {e}")
    caption = (
        f"*Вопрос {idx+1}/{len(QUESTIONS)}*\n"
        f"{QUESTIONS[idx]}\n\n"
        "_Отвечайте честно и трезво — это критически важно для точности криминального профилирования._"
    )
    keyboard = [
        [InlineKeyboardButton("Да", callback_data='answer_yes')],
        [InlineKeyboardButton("Нет", callback_data='answer_no')]
    ]
    sent_message = await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=caption,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['last_message_id'] = sent_message.message_id

async def answer_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # учёт ответа
    if query.data == 'answer_yes':
        context.user_data['score'] += 1
    context.user_data['q_index'] += 1
    # следующий вопрос или кнопка результата
    if context.user_data['q_index'] < len(QUESTIONS):
        await ask_question(update, context)
    else:
        kb = [[ InlineKeyboardButton("Узнать свой результат", callback_data='show_result') ]]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Тест завершён. Для получение результатов - Вам стоит нажать на кнопку ниже.\n\n""Помните: наличие признаков генетического преступника - не клеймо, а лишь маркер для Вашего личного понимания своей врождённой природы.",
            reply_markup=InlineKeyboardMarkup(kb)
        )

GENE_TYPES = [
    'Ген убийцы',
    'Ген вора',
    'Сексуальный ген преступника',
    'Ген мошенника'
]
THRESHOLD = 10  # новый, более низкий порог для наличия гена

async def show_result(update: Update, context: CallbackContext) -> None:
    from datetime import datetime
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    context.user_data.pop('last_message_id', None)

    pass  # Если не получилось удалить - игнорируем ошибку

    # Получаем результат теста и время начала
    score = context.user_data.get('score', 0)
    start_time = context.user_data.get('start_time')
    end_time = datetime.now()

    # Рассчитываем время прохождения
    if start_time:
        total_seconds = int((end_time - start_time).total_seconds())
    else:
        total_seconds = 0

    # Форматируем время
    if total_seconds >= 60:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_taken = f"{minutes} мин {seconds} сек"
    else:
        time_taken = f"{total_seconds} сек"

    # Оцениваем достоверность анкетирования
    if total_seconds < 59:
        verification = "Недостоверное анкетирование"
    elif total_seconds > 60:
        verification = "Достоверное анкетирование"
    else:
        verification = "Анкетирование на границе допустимого времени"

    # Определяем текстовые блоки и файл фото для отправки
    if score < 8:
        gene_result = "Ген отсутствует"
        header = f"✅ *Ген преступника отсутствует!*"
        gene_text = (
            "🔬 *Детальный отчёт:* По итогам теста вы не набрали достаточного количества признаков...\n"
            "⚙️ *Механизмы контроля:* Ведение ежедневного журнала эмоций, когнитивная реструктуризация...\n"
            "🧠 *Проявления:* Спокойствие и высокий уровень самоконтроля...\n"
            "🔍 *За счёт чего:* Сбалансированный уровень дофамина и серотонина...\n"
            "ℹ️ *Важно:* Это лишь генетическая предрасположенность, а не клеймо."
        )
        photo_file = 'gene_none.png'

    elif 9 <= score <= 12:
        gene_result = "Ген вора"
        header = f"🩸 *У вас выявлен Ген вора!*"
        gene_text = (
            "🔬 *Детальный отчёт:* Вы продемонстрировали признаки «Гена вора»...\n"
            "⚙️ *Механизмы контроля:* Практики осознанности, трекинг импульсов...\n"
            "🧠 *Проявления:* Склонность к импульсивным решениям...\n"
            "🔍 *За счёт чего:* Вариативность рецепторов дофамина и окситоцина...\n"
            "ℹ️ *Важно:* Это лишь генетическая предрасположенность, а не клеймо."
        )
        photo_file = 'gene_thief.png'

    elif 13 <= score <= 15:
        gene_result = "Сексуальный ген преступника"
        header = f"🩸 *У вас выявлен Сексуальный ген преступника!*"
        gene_text = (
            "🔬 *Детальный отчёт:* Признаки сексуального девиантного поведения...\n"
            "⚙️ *Механизмы контроля:* Психотерапия, техники управления импульсами...\n"
            "🧠 *Проявления:* Перепады эмоционального возбуждения...\n"
            "🔍 *За счёт чего:* Полиморфизм рецепторов серотонина и тестостерона...\n"
            "ℹ️ *Важно:* Это лишь генетическая предрасположенность, а не клеймо."
        )
        photo_file = 'gene_sex.png'

    elif 16 <= score <= 18:
        gene_result = "Ген мошенника»"
        header = f"🩸 *У вас выявлена Ген мошенника»!*"
        gene_text = (
        "🔬 *Детальный отчёт:* Признаки «Гена мошенника»...\n"
        "⚙️ *Механизмы контроля:* Интенсивные нагрузки, дыхательные практики...\n"
        "🧠 *Проявления:* Вспышки ярости, тяга к риску...\n"
        "🔍 *За счёт чего:* Вариации в приёме серотонина и адреналина...\n"
        "ℹ️ *Важно:* Это лишь генетическая предрасположенность, а не клеймо."
    )
        photo_file = 'gene_fire.png'

    elif 19 <= score <= 20:
        gene_result = "Ген убийцы"
        header = f"🩸 *У вас выявлен Ген убийцы!*"
        gene_text = (
            "🔬 *Детальный отчёт:* Атрибуты «преступного» гена...\n"
            "⚙️ *Механизмы контроля:* Нейропсихолог, медикаментозная поддержка...\n"
            "🧠 *Проявления:* Холодное, расчетливое поведение...\n"
            "🔍 *За счёт чего:* Дисбаланс окситоциновых и дофаминовых путей...\n"
            "ℹ️ *Важно:* Это лишь генетическая предрасположенность, а не клеймо."
        )
        photo_file = 'gene_killer.png'

    else:
        gene_result = "Ошибка в подсчете"
        header = "⚠️ *Ошибка при определении результата!*"
        gene_text = "_Пожалуйста, попробуйте пройти тест заново._"

    # Записываем данные в Google таблицу
    user = query.from_user
    username = f"@{user.username}" if user.username else "Нет username"
    SHEET.append_row([
        user.id,
        username,
        gene_result,
        time_taken,
        verification
    ])

    # Собираем итоговое сообщение
    caption = (
        f"{header}\n\n"
        f"🎯 Ваш балл: *{score}* из {len(QUESTIONS)}\n"
        f"🕒 Время прохождения: *{time_taken}*\n"
        f"📊 Достоверность: *{verification}*\n\n"
        f"❗_Достоверность зависит от наличия или отсутствия психологических противоречий в ответах_\n\n"
        f"{gene_text}"
    )

    # Кнопки после теста
    kb = [
        [
            InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
            InlineKeyboardButton("ℹ️ Подробнее", url='https://telegra.ph/Teoriya-tipov-prestupnikov-Lombrozo-04-28')
        ]
    ]

    # Отправляем Фото и подпись
    with open(photo_file, 'rb') as photo:
        sent = await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo,
            caption=caption,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # Сохраняем message_id для возможности удаления
    context.user_data['last_message_id'] = sent.message_id

    # Очищаем user_data
    context.user_data.clear()

async def handle_subscription(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        SUBSCRIBERS.add(user_id)
        USER_DB.add(user_id)
        
        await notify_admin(
            action="ПОДПИСКА НА РАССЫЛКУ",
            user={'id': user_id, 'mention': query.from_user.mention_html()},
            context=context
        )
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>✅ ПОДПИСКА АКТИВИРОВАНА</b>\n\n"
                 "▫️ В рассылку входит:\n"
                 "— Когнитивные техники 🧩\n"
                 "— Разбор клинических кейсов\n"
                 "— Экстренные рекомендации при необходимости\n\n"
                 "<i>Отписаться: /stop</i>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu'),
                InlineKeyboardButton("🔑 Подать заявку", url=CHANNEL_LINK)
            ]]),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Subscription error: {e}")

async def forward_from_main_channel(update: Update, context: CallbackContext) -> None:
    try:
        if update.channel_post and update.channel_post.chat.id == MAIN_CHANNEL_ID:
            for user_id in SUBSCRIBERS.copy():
                try:
                    await context.bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=MAIN_CHANNEL_ID,
                        message_id=update.channel_post.message_id
                    )
                except Exception as e:
                    logger.error(f"Forward error to {user_id}: {e}")
                    SUBSCRIBERS.discard(user_id)
    except Exception as e:
        logger.error(f"Error in forward_from_main_channel: {e}")

async def handle_notification_channel_post(update: Update, context: CallbackContext) -> None:
    try:
        if update.channel_post and update.channel_post.chat.id == NOTIFICATION_CHANNEL_ID:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
                [InlineKeyboardButton("🔑 Подать заявку", url=CHANNEL_LINK)]
            ])
            
            for user_id in USER_DB:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🚀 <b>НОВЫЙ ПСИХОЛОГИЧЕСКИЙ ИНСТРУМЕНТ!</b>\n\n"
                             "🧠 Только что в канале .mindset application:\n"
                             "▫️ Эксклюзивный психологический лайфхак\n"
                             "▫️ Научно доказанные техники\n"
                             "▫️ Уникальный кейс из практики\n\n"
                             "🔥 Не упусти возможность прокачать свои навыки!",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in handle_notification_channel_post: {e}")

async def stop(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да", callback_data='confirm_unsub')],
            [InlineKeyboardButton("❌ Нет", callback_data='cancel_unsub')]
        ])
        
        await context.bot.send_message(
            chat_id=user_id,
            text="<b>⚠️ ВЫ УВЕРЕНЫ?</b>\n\n"
                 "Вы действительно хотите отписаться от рассылки?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Stop command error: {e}")

async def handle_unsub_confirmation(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        user_id = user.id
        
        if query.data == 'confirm_unsub':
            SUBSCRIBERS.discard(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text="<b>🔴 ВЫ ОТПИСАНЫ</b>\n\n"
                     "Рассылка больше не будет приходить.\n"
                     "Чтобы возобновить подписку, используйте /start",
                reply_markup=InlineKeyboardMarkup(
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
                    [InlineKeyboardButton("🔑 Подать заявку", url=CHANNEL_LINK)]
                ),
                parse_mode='HTML'
            )
            await notify_admin(
                action="ОТПИСКА ОТ РАССЫЛКИ",
                user={'id': user_id, 'mention': user.mention_html()},
                context=context
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="<b>Подписка сохранена 🟢</b>",
                reply_markup=InlineKeyboardMarkup(
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
                    [InlineKeyboardButton("🔑 Подать заявку", url=CHANNEL_LINK)]
                ),
                parse_mode='HTML'
            )
            
        await delete_previous_messages(update, context)
    except Exception as e:
        logger.error(f"Unsubscription error: {e}")

async def handle_chat_member_update(update: Update, context: CallbackContext) -> None:
    try:
        if update.chat_member.new_chat_member.status == ChatMemberStatus.LEFT:
            user = update.chat_member.from_user
            if update.chat_member.chat.id == PRIVATE_CHANNEL_ID:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔑 Подать заявку снова", url=CHANNEL_LINK)
                ]])
                
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f"<b>🌀 Ты уверен, что хочешь покинуть канал Mindset Psychology?</b>\n\n"
                         "Это решение безвозвратно стирает твой прогресс. Еще не поздно вернуться.\n\n"
                         "▫️ Если тебя не устроил контент:\n"
                         "— Выскажи <a href='@adhdpacan'>администратору</a>\n"
                         "— Напиши свои пожелания ниже ⤵️\n\n"
                         "<i>У тебя одна попытка обратной связи</i> ⏳",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                await notify_admin(
                    action="ВЫХОД ИЗ КАНАЛА",
                    user={'id': user.id, 'mention': user.mention_html()},
                    context=context
                )
                
                context.user_data['feedback_allowed'] = True
    except Exception as e:
        logger.error(f"Chat member update error: {e}")

async def handle_feedback(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        if context.user_data.get('feedback_allowed', False):
            feedback_text = update.message.text
            await notify_admin(
                action="ОБРАТНАЯ СВЯЗЬ",
                user={'id': user.id, 'mention': user.mention_html()},
                context=context,
                feedback=feedback_text
            )
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu'),
                 InlineKeyboardButton("🔑 Подать заявку повторно", url=CHANNEL_LINK)]
            ])
            await context.bot.send_message(
                chat_id=user.id,
                text="<b>📬 Ваше сообщение доставлено</b>\nСпасибо за обратную связь!",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            context.user_data['feedback_allowed'] = False
        else:
            await update.message.delete()
    except Exception as e:
        logger.error(f"Feedback error: {e}")

def main():
    application = Application.builder().token(API_TOKEN).build()

    # Основные обработчики
    application.add_handler(CommandHandler('start', start))  # Теперь start вызывает main_menu
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CallbackQueryHandler(gen_criminal_menu, pattern='^gen_criminal$'))
    application.add_handler(CallbackQueryHandler(start_test,        pattern='^start_test$'))
    application.add_handler(CallbackQueryHandler(answer_handler,    pattern='^answer_(yes|no)$'))
    application.add_handler(CallbackQueryHandler(show_result,       pattern='^show_result$'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^start_bot$'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(handle_subscription, pattern='^subscribe$'))
    application.add_handler(CallbackQueryHandler(handle_unsub_confirmation, pattern='^(confirm_unsub|cancel_unsub)$'))
    application.add_handler(ChatJoinRequestHandler(handle_chat_join_request))

    # Обработчики каналов
    application.add_handler(MessageHandler(
        filters.Chat(MAIN_CHANNEL_ID) & filters.ChatType.CHANNEL,
        forward_from_main_channel
    ))
    application.add_handler(MessageHandler(
        filters.Chat(NOTIFICATION_CHANNEL_ID) & filters.ChatType.CHANNEL,
        handle_notification_channel_post
    ))
    
    application.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))
    
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    main()