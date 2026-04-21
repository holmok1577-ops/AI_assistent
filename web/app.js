const messagesContainer = document.getElementById('messages');
const msgInput = document.getElementById('msg');
const sendBtn = document.getElementById('send-btn');

// Загрузка истории из localStorage
function loadHistory() {
    const history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    history.forEach(msg => {
        addMessage(msg.role, msg.text, msg.time, false);
    });
    scrollToBottom();
    return history;
}

// Получить историю для отправки на бэкенд
function getHistoryForBackend() {
    const history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    // Возвращаем только последние 6 сообщений
    return history.slice(-6).map(msg => ({
        role: msg.role,
        text: msg.text
    }));
}

// Сохранение истории в localStorage
function saveMessage(role, text) {
    const history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    history.push({ role, text, time });
    localStorage.setItem('chatHistory', JSON.stringify(history));
    return time;
}

// Добавление сообщения в чат
function addMessage(role, text, time = null, save = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    
    const messageText = document.createElement('div');
    messageText.textContent = text;
    messageDiv.appendChild(messageText);
    
    if (time) {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = time;
        messageDiv.appendChild(timeDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    if (save) {
        return saveMessage(role, text);
    }
}

// Показать индикатор печати
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// Убрать индикатор печати
function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// Прокрутка вниз
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Отправка сообщения
async function send() {
    const text = msgInput.value.trim();
    if (!text) return;

    // Отключаем кнопку во время отправки
    sendBtn.disabled = true;
    msgInput.disabled = true;

    // Добавляем сообщение пользователя
    addMessage('user', text);
    msgInput.value = '';

    // Показываем индикатор печати
    showTyping();

    try {
        const r = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 'user123',
                message: text,
                history: getHistoryForBackend()
            })
        });

        const data = await r.json();
        
        // Убираем индикатор печати
        hideTyping();
        
        // Добавляем ответ ИИ
        addMessage('ai', data.reply);
    } catch (error) {
        hideTyping();
        console.error('Error:', error);
        addMessage('ai', 'Извините, произошла ошибка. Попробуйте еще раз.');
    } finally {
        // Включаем кнопку и поле ввода
        sendBtn.disabled = false;
        msgInput.disabled = false;
        msgInput.focus();
    }
}

// Обработка нажатия Enter
msgInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
});

// Очистка истории
function clearHistory() {
    if (confirm('Очистить историю диалога?')) {
        localStorage.removeItem('chatHistory');
        messagesContainer.innerHTML = '';
    }
}

// Инициализация
loadHistory();
msgInput.focus();
