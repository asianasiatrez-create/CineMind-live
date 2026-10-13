document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chatToggle');
    const aiSidebar = document.getElementById('aiSidebar');
    const closeSidebar = document.getElementById('closeSidebar');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatHistory = document.getElementById('chatHistory');
    const mainGrid = document.getElementById('mainGrid');
    const mainArea = document.getElementById('mainArea');

    // IMPORTANT: When deploying live, change this to your Render.com URL
    const API_URL = "http://127.0.0.1:5000/chat"; 

    // Sidebar Toggles
    chatToggle.addEventListener('click', () => {
        aiSidebar.classList.add('active');
        if(window.innerWidth <= 768) mainArea.classList.add('shrunk');
        chatInput.focus();
    });

    closeSidebar.addEventListener('click', () => {
        aiSidebar.classList.remove('active');
        mainArea.classList.remove('shrunk');
    });

    function addBubble(text, sender) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}-bubble`;
        bubble.innerHTML = text;
        chatHistory.appendChild(bubble);
        chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to bottom
    }

    async function handleChat() {
        const message = chatInput.value.trim();
        if (!message) return;

        // 1. Show user message
        addBubble(message, 'user');
        chatInput.value = '';

        // 2. Show Nova typing indicator
        addBubble('<i class="fa-solid fa-ellipsis fa-fade"></i>', 'ai');
        const typingIndicator = chatHistory.lastChild;

        try {
            // 3. Send message to Python Backend
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            const data = await response.json();

            // 4. Remove typing indicator & show Nova's response
            typingIndicator.remove();
            addBubble(data.reply, 'ai');

            // 5. Update the Main Movie Grid if movies were found
            if (data.movies && data.movies.length > 0) {
                mainGrid.innerHTML = ''; // Clear grid
                data.movies.forEach(movie => {
                    const card = document.createElement('div');
                    card.className = 'movie-card';
                    card.innerHTML = `
                        <img src="${movie.poster}" alt="Poster" onerror="this.src='https://via.placeholder.com/200x300?text=No+Poster'">
                        <div class="movie-info">
                            <div class="movie-title">${movie.title}</div>
                            <div class="match-score"><i class="fa-solid fa-bolt"></i> ${movie.match}% Vector Match</div>
                        </div>
                    `;
                    mainGrid.appendChild(card);
                });
            }

        } catch (error) {
            typingIndicator.remove();
            addBubble("My servers are currently offline! Make sure the Python backend is running.", 'ai');
        }
    }

    sendBtn.addEventListener('click', handleChat);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChat();
    });
});