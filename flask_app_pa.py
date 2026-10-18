import os
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

# 1. Instancia de la Aplicación
app = Flask(__name__)
CORS(app) # Habilitar CORS para evitar problemas de origen

# Configuración de Gemini
# Usar variable de entorno si está disponible, o dejar None para manejar el error
api_key = os.getenv("GEMINI_API_KEY") 
if api_key:
    from google import generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# Diseño de la interfaz de chat
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Asistente de David</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #e5ddd5; margin: 0; padding: 20px; }
        #chat-container { max-width: 600px; margin: auto; background: #efeae2; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); display: flex; flex-direction: column; height: 85vh; }
        #header { background: #075e54; color: white; padding: 15px; border-top-left-radius: 10px; border-top-right-radius: 10px; text-align: center; font-size: 1.2em; }
        #messages { flex-grow: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .message { max-width: 75%; padding: 10px 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
        .user { background: #d9fdd3; align-self: flex-end; color: #303030; }
        .bot { background: #ffffff; align-self: flex-start; color: #303030; }
        #input-container { display: flex; padding: 10px; background: #f0f0f0; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }
        #user-input { flex-grow: 1; padding: 12px; border: none; border-radius: 20px; outline: none; font-size: 1em; }
        #send-btn { background: #00a884; color: white; border: none; padding: 0 20px; margin-left: 10px; border-radius: 20px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="header">Asistente de David 🇨🇴 (Cali)</div>
        <div id="messages">
            <div class="message bot">¡Hola David! Ya estás conectado. ¿En qué te puedo colaborar hoy?</div>
        </div>
        <div id="input-container">
            <input type="text" id="user-input" placeholder="Escribe un mensaje aquí..." onkeypress="handleKeyPress(event)">
            <button id="send-btn" onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        function handleKeyPress(e) {
            if(e.key === 'Enter') sendMessage();
        }
        function sendMessage() {
            var input = document.getElementById('user-input');
            var text = input.value.trim();
            if(!text) return;

            var messages = document.getElementById('messages');
            messages.innerHTML += "<div class='message user'>" + text + "</div>";
            input.value = '';
            messages.scrollTop = messages.scrollHeight;

            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            })
            .then(response => response.json())
            .then(data => {
                messages.innerHTML += "<div class='message bot'>" + data.response + "</div>";
                messages.scrollTop = messages.scrollHeight;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    if not model:
        return jsonify({'response': "Error: GEMINI_API_KEY no configurada correctamente en el servidor."})

    try:
        response = model.generate_content(user_message)
        response_text = response.text
    except Exception as e:
        response_text = f"Error al conectar con Gemini: {str(e)}"

    return jsonify({'response': response_text})

# Alias para WSGI en PythonAnywhere
application = app

if __name__ == '__main__':
    app.run()
