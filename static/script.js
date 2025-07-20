document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => e.key === "Enter" && sendMessage());
    newChatBtn.addEventListener("click", startNewChat);

    function addMessage(content, sender) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);

        if (sender === 'user') {
            const p = document.createElement("p");
            p.textContent = content;
            messageElement.appendChild(p);
        } else { // This is a bot message
            const messageText = content.data || content;
            const thinkRegex = /<think>(.*?)<\/think>/s;
            const match = messageText.match(thinkRegex);

            if (match) {
                const thinkText = match[1].trim();
                const restOfMessage = messageText.replace(thinkRegex, '').trim();

                // Create and append the formatted 'thinking' part
                const thinkElement = document.createElement("p");
                thinkElement.classList.add("think-text");
                thinkElement.innerHTML = `<i>*thinking* ${thinkText} *end thinking*</i><br><br>`;
                messageElement.appendChild(thinkElement);

                // Create and append the answer part if it exists
                if (restOfMessage) {
                    const answerElement = document.createElement("p");
                    answerElement.textContent = restOfMessage;
                    messageElement.appendChild(answerElement);
                }
            } else {
                // No <think> tags, just display the message as is
                const p = document.createElement("p");
                p.textContent = messageText;
                messageElement.appendChild(p);
            }
        }

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === "") return;

        addMessage(messageText, "user");
        userInput.value = "";
        showThinking(true);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ message: messageText }),
            });
            
            const data = await response.json();
            if (response.ok) {
                addMessage(data, "bot");
            } else {
                addMessage({data: data.error || "An unknown error occurred."}, "bot");
            }
        } catch (error) {
            console.error("Error:", error);
            addMessage({data: "Error communicating with the agent."}, "bot");
        } finally {
            showThinking(false);
        }
    }

    async function startNewChat() {
        await fetch("/reset", { method: "POST" });
        chatBox.innerHTML = `
            <div class="message bot-message">
                <p>Hello! I am the AUTALIC Agent. How can I help you today?</p>
            </div>
        `;
    }
    
    let thinkingMessageElement = null;
    function showThinking(isThinking) {
        if (isThinking && !thinkingMessageElement) {
            thinkingMessageElement = document.createElement("div");
            thinkingMessageElement.classList.add("message", "bot-message");
            thinkingMessageElement.innerHTML = `<p>Thinking...</p>`;
            chatBox.appendChild(thinkingMessageElement);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else if (!isThinking && thinkingMessageElement) {
            thinkingMessageElement.remove();
            thinkingMessageElement = null;
        }
    }
}); 