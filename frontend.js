const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const fileInput = document.getElementById('file-input');
const sendBtn = document.getElementById('send-btn');

async function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'grok-message');
    supercontent = await convert2markdown(content)
    messageDiv.innerHTML = supercontent.html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}


async function convert2markdown(message){
    // Send to backend for markdown conversion
    console.log('convert2markdown message:')
    console.log(message)
    const response = await fetch('/convert-markdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: message })
    });
    const userData = await response.json();
    return userData
}

async function callApi(message, file = null) {
    try {
        const formData = new FormData();
        if (message) formData.append('message', message);
        if (file) formData.append('file', file);

        const response = await fetch('/grok', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) throw new Error('API request failed');

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let result = '';
        const messageDiv = await addMessage('', false);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            result += chunk;

            aiData = await convert2markdown(result)

            messageDiv.innerHTML = aiData.html+(aiData.hasCodeOrTable ? '<button class="copy-button" onclick="copyMessage(this)">Copy</button>' : '');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        return result;
    } catch (error) {
        console.error('Error:', error);
        return 'Sorry, something went wrong! Is the backend running?';
    }
}

sendBtn.addEventListener('click', async () => {
    const message = userInput.value.trim();
    const file = fileInput.files[0];

    if (!message && !file) return;

    if (message) {
        await addMessage(message, true);
    } else if (file) {
        await addMessage(`Uploaded file: ${file.name}`, true);
    }

    userInput.value = '';
    fileInput.value = '';

    await callApi(message, file);
});

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendBtn.click();
    }
});

function copyMessage(button) {
    const messageDiv = button.parentElement;
    const rawText = messageDiv.dataset.rawText;
    navigator.clipboard.writeText(rawText)
        .then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy: ', err);
        });
}