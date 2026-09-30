/**
 * Bhairava Anugraha - Seeker Spiritual Guidance Chat Widget
 */
document.addEventListener('DOMContentLoaded', function () {
    const chatWidget = document.getElementById('da-chat-widget');
    if (!chatWidget) return;

    const chatFab = document.getElementById('chat-fab');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatBadge = document.getElementById('chat-badge');

    let isOpen = false;
    let lastRenderedCount = -1;
    let pollInterval = null;
    const POLL_RATE = 4000;
    const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

    // Events
    if (chatFab) chatFab.addEventListener('click', toggleChat);
    if (chatClose) chatClose.addEventListener('click', toggleChat);
    if (chatSend) chatSend.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Toggle Chat Window
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.style.display = 'flex';
            chatFab.style.display = 'none';
            if (chatInput) chatInput.focus();
            loadMessages(true);
            startPolling();
            markAsRead();
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

        // Clear placeholder
        const placeholder = chatMessages.querySelector('.chat-placeholder');
        if (placeholder) placeholder.remove();

        // Optimistic UI
        const tempDiv = document.createElement('div');
        tempDiv.className = 'chat-message user';
        tempDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
            <div class="message-time">Just now</div>
        `;
        chatMessages.appendChild(tempDiv);
        scrollToBottom();

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
                loadMessages(true);
            } else {
                alert('Error sending message: ' + (data.error || 'Failed to deliver'));
                chatInput.value = originalInput;
            }
        } catch (error) {
            console.error('Error sending chat message:', error);
            chatInput.value = originalInput;
        }
    }

    // Load Messages
    async function loadMessages(scrollDown = false) {
        try {
            const response = await fetch('/api/chat/history');
            const data = await response.json();
            const messages = Array.isArray(data) ? data : (data.messages || []);

            if (messages.length !== lastRenderedCount) {
                renderMessages(messages);
                lastRenderedCount = messages.length;
                if (scrollDown) {
                    scrollToBottom();
                }
            }

            // Check unread count for badge if closed
            if (!isOpen && chatBadge) {
                const unreadAdminMsgs = messages.filter(m => (m.is_admin || m.is_from_admin) && !m.is_read).length;
                if (unreadAdminMsgs > 0) {
                    chatBadge.textContent = unreadAdminMsgs;
                    chatBadge.style.display = 'inline-flex';
                } else {
                    chatBadge.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    // Render Messages
    function renderMessages(messages) {
        chatMessages.innerHTML = '';

        if (!messages || messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="chat-placeholder">
                    <p>॥ ॐ भैरवाय नमः ॥</p>
                    <p>Namaste! Ask any guidance regarding your Sādhana, japa, or daily discipline.</p>
                </div>
            `;
            return;
        }

        messages.forEach(msg => {
            const div = document.createElement('div');
            const isFromAdmin = Boolean(msg.is_from_admin || msg.is_admin);
            div.className = `chat-message ${isFromAdmin ? 'admin' : 'user'}`;

            const timeStr = msg.created_at || (msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '');

            div.innerHTML = `
                ${isFromAdmin ? '<div class="msg-author-tag"><i class="fas fa-shield-halved"></i> Guru Bhairava Guidance</div>' : ''}
                <div class="message-content">${escapeHtml(msg.message || msg.content || '')}</div>
                <div class="message-time">${escapeHtml(timeStr)}</div>
            `;

            chatMessages.appendChild(div);
        });

        scrollToBottom();
    }

    // Mark as read
    function markAsRead() {
        if (chatBadge) chatBadge.style.display = 'none';
        fetch('/api/chat/mark-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            }
        }).catch(err => console.error('Error marking read:', err));
    }

    // Polling
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(() => loadMessages(false), POLL_RATE);
    }

    function stopPolling() {
        if (pollInterval) clearInterval(pollInterval);
    }

    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Check for unread on load
    loadMessages(false);
});
