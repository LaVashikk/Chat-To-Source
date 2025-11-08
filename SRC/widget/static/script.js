// Chat2Source Widget JavaScript

class Chat2SourceWidget {
    constructor() {
        this.socket = null;
        this.messagesContainer = document.getElementById('chat-messages');
        this.statusText = document.getElementById('status-text');
        this.statusDot = document.getElementById('status-dot');
        this.clearBtn = document.getElementById('clear-btn');
        this.reconnectBtn = document.getElementById('reconnect-btn');
        
        this.init();
    }
    
    init() {
        this.connectSocket();
        this.setupEventListeners();
        this.showEmptyState();
    }
    
    connectSocket() {
        try {
            this.socket = io();
            this.setupSocketEvents();
        } catch (error) {
            console.error('Failed to connect to socket:', error);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('connected');
            this.addConnectionMessage('Connected to Chat2Source server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('disconnected');
            this.addConnectionMessage('Disconnected from server', 'error');
        });
        
        this.socket.on('new_message', (data) => {
            this.addMessage(data);
        });
        
        this.socket.on('server_message', (data) => {
            this.addServerMessage(data);
        });
        
        this.socket.on('message_history', (data) => {
            this.loadMessageHistory(data.messages);
            this.updateStatus(data.status);
        });
        
        this.socket.on('status_update', (data) => {
            this.updateStatus(data.status);
        });
        
        this.socket.on('messages_cleared', () => {
            this.clearMessages();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.updateConnectionStatus('disconnected');
        });
    }
    
    setupEventListeners() {
        this.clearBtn.addEventListener('click', () => {
            this.clearMessages();
        });
        
        this.reconnectBtn.addEventListener('click', () => {
            this.reconnect();
        });
    }
    
    updateConnectionStatus(status) {
        this.statusDot.className = `status-dot ${status}`;
        
        switch (status) {
            case 'connected':
                this.statusText.textContent = 'Connected';
                break;
            case 'connecting':
                this.statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
            default:
                this.statusText.textContent = 'Disconnected';
                break;
        }
    }
    
    updateStatus(status) {
        // This updates the game/chat status, not connection status
        console.log('Status update:', status);
    }
    
    addMessage(data) {
        this.removeEmptyState();
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message chat';
        
        const headerElement = document.createElement('div');
        headerElement.className = 'message-header';
        
        if (data.author_image) {
            const avatarElement = document.createElement('img');
            avatarElement.className = 'author-avatar';
            avatarElement.src = data.author_image;
            avatarElement.alt = data.author_name;
            avatarElement.onerror = function() {
                this.style.display = 'none';
            };
            headerElement.appendChild(avatarElement);
        }
        
        const nameElement = document.createElement('span');
        nameElement.className = 'author-name';
        nameElement.textContent = data.author_name;
        headerElement.appendChild(nameElement);
        
        const timestampElement = document.createElement('span');
        timestampElement.className = 'message-timestamp';
        timestampElement.textContent = data.timestamp;
        headerElement.appendChild(timestampElement);
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.innerHTML = this.formatMessage(data.message);
        
        messageElement.appendChild(headerElement);
        messageElement.appendChild(contentElement);
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addServerMessage(data) {
        this.removeEmptyState();
        
        const messageElement = document.createElement('div');
        messageElement.className = `message server ${data.message_type}`;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'server-message-content';
        
        const iconElement = document.createElement('div');
        iconElement.className = `server-icon ${data.message_type}`;
        contentElement.appendChild(iconElement);
        
        const textElement = document.createElement('span');
        textElement.textContent = data.message;
        contentElement.appendChild(textElement);
        
        const timestampElement = document.createElement('span');
        timestampElement.className = 'message-timestamp';
        timestampElement.textContent = data.timestamp;
        contentElement.appendChild(timestampElement);
        
        messageElement.appendChild(contentElement);
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addConnectionMessage(message, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `connection-status ${type}`;
        messageElement.textContent = message;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
        
        // Remove connection messages after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 5000);
    }
    
    loadMessageHistory(messages) {
        this.clearMessages();
        
        if (messages.length === 0) {
            this.showEmptyState();
            return;
        }
        
        messages.forEach(message => {
            if (message.type === 'chat') {
                this.addMessage(message);
            } else if (message.type === 'server') {
                this.addServerMessage(message);
            }
        });
    }
    
    formatMessage(message) {
        // Replace [red]text[/red] with styled spans
        return message.replace(/\[red\](.*?)\[\/red\]/g, '<span class="forbidden">$1</span>');
    }
    
    clearMessages() {
        this.messagesContainer.innerHTML = '';
        this.showEmptyState();
    }
    
    showEmptyState() {
        if (this.messagesContainer.children.length === 0) {
            const emptyElement = document.createElement('div');
            emptyElement.className = 'empty-state';
            emptyElement.textContent = 'No messages yet. Waiting for chat activity...';
            this.messagesContainer.appendChild(emptyElement);
        }
    }
    
    removeEmptyState() {
        const emptyState = this.messagesContainer.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    reconnect() {
        this.updateConnectionStatus('connecting');
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        setTimeout(() => {
            this.connectSocket();
        }, 1000);
    }
}

// Initialize the widget when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new Chat2SourceWidget();
});

