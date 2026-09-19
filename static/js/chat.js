/**
 * Daiva Anughara Chat Widget
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const chatWidget = document.getElementById('da-chat-widget');
    if (!chatWidget) return; // Exit if widget not present

    const chatFab = document.getElementById('chat-fab');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatBadge = document.getElementById('chat-badge');

    // State
    let isOpen = false;
    let lastMessageId = 0;
    let pollInterval = null;
    const POLL_RATE = 10000; // 10 seconds
    const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

    // Events
    chatFab.addEventListener('click', toggleChat);
    chatClose.addEventListener('click', toggleChat);
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    // Toggle Chat Window
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.style.display = 'flex';
            chatFab.style.display = 'none';
            chatInput.focus();
            loadMessages();
            startPolling();
            scrollToBottom();
        } else {
            chatWindow.style.display = 'none';
            chatFab.style.display = 'flex';
            stopPolling();
        }
    }

    // Send Message
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Optimistic UI - add message immediately
        appendMessage({
            message: message,
            is_from_admin: false,
            timestamp: new Date().toISOString(),
            sender_id: 'me', // temporary
            id: 'temp-' + Date.now()
        });

        const originalInput = chatInput.value;
        chatInput.value = '';

        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (data.success) {
                // Determine if we need to replace temp message or just reload
                // For simplicity, we just reload or let polling handle it next time
                // But better to just remove temp and show real if needed
                // Actually, let's just refresh list to sync IDs
                // Or just ignore since we already showed it.
            } else {
                alert('Error sending message: ' + (data.error || 'Unknown error'));
                chatInput.value = originalInput; // Restore
            }
        } catch (error) {
            console.error('Error:', error);
            chatInput.value = originalInput; // Restore
        }
    }

    // Load Messages
    async function loadMessages() {
        try {
            const response = await fetch('/api/chat/history');
            const messages = await response.json();

            if (messages.error) {
                console.error('Error loading chat:', messages.error);
                return;
            }

            renderMessages(messages);
        } catch (error) {
            console.error('Error loading chat:', error);
        }
    }

    // Render Messages
    function renderMessages(messages) {
        // Clear if it's the first load or if we want to be clean
        // Ideally we merge, but simpler to clear and rebuild for this scale
        chatMessages.innerHTML = '';

        if (messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="chat-placeholder">
                    <p>Namaste! How can we guide you on your journey today?</p>
                </div>
            `;
            return;
        }

        messages.forEach(msg => {
            appendMessage(msg);
            if (msg.id > lastMessageId) {
                lastMessageId = msg.id;
            }
        });

        scrollToBottom();
    }

    // Append Single Message
    function appendMessage(msg) {
        // Check if already exists (deduplication)
        // This is a naive check; better to use ID data attributes

        const div = document.createElement('div');
        div.className = `chat-message ${msg.is_from_admin ? 'admin' : 'user'}`;

        const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        div.innerHTML = `
            <div class="message-content">
                ${escapeHtml(msg.message)}
            </div>
            <div class="message-time">${time}</div>
        `;

        chatMessages.appendChild(div);
    }

    // Poll for new messages
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(loadMessages, POLL_RATE);
    }

    function stopPolling() {
        if (pollInterval) clearInterval(pollInterval);
    }

    // Utilities
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
