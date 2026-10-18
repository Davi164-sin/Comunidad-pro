from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

chat_messages = []

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat David</title>
    <style>
        :root { --primary: #6366f1; --dark: #1e293b; }
        body { font-family: sans-serif; background: #6366f1; margin: 0; padding: 20px; display: flex; justify-content: center; height: 100vh; box-sizing: border-box; }
        .card { background: white; width: 100%; max-width: 400px; height: 100%; border-radius: 25px; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
        .header { background: var(--dark); color: white; padding: 20px; text-align: center; flex-shrink: 0; }
        .content { padding: 20px; display: flex; flex-direction: column; flex: 1; overflow: hidden; }
        .chat-container { flex: 1; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; margin-bottom: 15px; background: #f8fafc; display: flex; flex-direction: column; gap: 8px; }
        .message-item { background: #e0e7ff; padding: 10px 14px; border-radius: 12px; max-width: 80%; align-self: flex-start; word-break: break-word; font-size: 14px; }
        .message-item.mine { background: #6366f1; color: white; align-self: flex-end; }
        .input-group { display: flex; gap: 10px; flex-shrink: 0; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 10px; outline: none; }
        button { background: var(--primary); color: white; border: none; padding: 10px 15px; border-radius: 10px; cursor: pointer; }
        .btn-clear { background: #ef4444; color: white; border: none; width: 100%; padding: 10px; border-radius: 10px; margin-top: 10px; cursor: pointer; flex-shrink: 0; }
        #sync { font-size: 12px; color: #ef4444; margin-top: 5px; }
        #sync.online { color: #22c55e; }
    </style>
</head>
<body>

<div class="card">
    <div class="header">
        <h1>💬 Chat David</h1>
        <div id="sync">● Desconectado</div>
    </div>

    <div class="content">
        <div id="chatContainer" class="chat-container"></div>

        <div class="input-group">
            <input type="text" id="messageInput" placeholder="Escribe un mensaje..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Enviar</button>
        </div>

        <button class="btn-clear" onclick="clearChat()">🗑️ Limpiar Chat</button>
    </div>
</div>

<script>
    const API_URL = "/api/chat";
    let lastMessagesHash = "";

    async function loadMessages() {
        try {
            const r = await fetch(API_URL);
            const messages = await r.json();
            
            const currentHash = JSON.stringify(messages);
            if (currentHash !== lastMessagesHash) {
                lastMessagesHash = currentHash;
                render(messages);
            }
            
            document.getElementById('sync').innerText = "● Sincronizado";
            document.getElementById('sync').className = "online";
        } catch (e) {
            document.getElementById('sync').innerText = "● Error de red";
            document.getElementById('sync').className = "";
        }
    }

    async function sendMessage() {
        const input = document.getElementById('messageInput');
        const text = input.value.trim();
        if (text) {
            input.value = "";
            await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender: "David", text: text })
            });
            loadMessages();
        }
    }

    async function clearChat() {
        if (confirm("¿Borrar todos los mensajes?")) {
            await fetch(API_URL, { method: "DELETE" });
            loadMessages();
        }
    }

    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    }

    function render(messages) {
        const container = document.getElementById('chatContainer');
        container.innerHTML = "";
        messages.forEach(m => {
            const div = document.createElement('div');
            div.className = `message-item ${m.sender === 'David' ? 'mine' : ''}`;
            div.innerHTML = `<strong>${m.sender}:</strong> ${m.text}`;
            container.appendChild(div);
        });
        container.scrollTop = container.scrollHeight;
    }

    loadMessages();
    setInterval(loadMessages, 1500);
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["GET", "POST", "DELETE"])
def handle_chat():
    global chat_messages
    if request.method == "GET":
        return jsonify(chat_messages)
    elif request.method == "POST":
        data = request.get_json()
        if data and "text" in data:
            chat_messages.append({
                "sender": data.get("sender", "Anónimo"),
                "text": data.get("text")
            })
            if len(chat_messages) > 100:
                chat_messages = chat_messages[-100:]
            return jsonify({"status": "success"}), 201
        return jsonify({"error": "Invalid data"}), 400
    elif request.method == "DELETE":
        chat_messages = []
        return jsonify({"status": "cleared"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
