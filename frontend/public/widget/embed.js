(function() {
  const script = document.currentScript;
  const tenantId = script.getAttribute('data-tenant');
  const theme = script.getAttribute('data-theme') || 'light';
  const position = script.getAttribute('data-position') || 'right';
  const lang = script.getAttribute('data-lang') || navigator.language.split('-')[0];

  if (!tenantId) { console.error('FluxAgent Widget: data-tenant is required'); return; }

  // Inject Shadow DOM
  const host = document.createElement('flux-agent-widget');
  host.style.position = 'fixed';
  host.style.bottom = '20px';
  host.style[position] = '20px';
  host.style.zIndex = '9999';
  document.body.appendChild(host);

  const shadow = host.attachShadow({ mode: 'open' });
  
  shadow.innerHTML = `
    <style>
      :host { font-family: system-ui, -apple-system, sans-serif; }
      .bubble { width: 60px; height: 60px; border-radius: 50%; background: #3b82f6; color: white; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.2s; }
      .bubble:hover { transform: scale(1.05); }
      .chat-window { position: absolute; bottom: 80px; ${position}: 0; width: 350px; height: 500px; background: ${theme === 'dark' ? '#111' : '#fff'}; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.2); display: none; flex-direction: column; overflow: hidden; border: 1px solid ${theme === 'dark' ? '#333' : '#eee'}; }
      .chat-window.open { display: flex; }
      .header { padding: 12px; background: ${theme === 'dark' ? '#1a1a1a' : '#f8f9fa'}; border-bottom: 1px solid ${theme === 'dark' ? '#333' : '#eee'}; display: flex; justify-content: space-between; align-items: center; }
      .messages { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
      .msg { max-width: 80%; padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; }
      .msg.agent { background: ${theme === 'dark' ? '#2563eb' : '#e0e7ff'}; color: ${theme === 'dark' ? '#fff' : '#1e293b'}; align-self: flex-start; border-bottom-left-radius: 4px; }
      .msg.user { background: ${theme === 'dark' ? '#333' : '#fff'}; color: ${theme === 'dark' ? '#fff' : '#0f172a'}; align-self: flex-end; border-bottom-right-radius: 4px; border: 1px solid ${theme === 'dark' ? '#444' : '#eee'}; }
      .input-area { padding: 10px; border-top: 1px solid ${theme === 'dark' ? '#333' : '#eee'}; display: flex; gap: 8px; }
      .input-area input { flex: 1; padding: 8px 12px; border: 1px solid ${theme === 'dark' ? '#444' : '#ddd'}; border-radius: 20px; outline: none; background: ${theme === 'dark' ? '#222' : '#fff'}; color: inherit; }
      .input-area button { background: #3b82f6; color: white; border: none; border-radius: 50%; width: 36px; height: 36px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; }
      .close-btn { background: none; border: none; font-size: 18px; cursor: pointer; color: inherit; opacity: 0.6; }
      .typing { font-size: 11px; color: #888; margin-left: 8px; }
    </style>
    <div class="chat-window" id="chatWindow">
      <div class="header">
        <span style="font-weight: 600; font-size: 14px;">FluxAgent</span>
        <button class="close-btn" id="closeBtn">&times;</button>
      </div>
      <div class="messages" id="messages">
        <div class="msg agent">¡Hola! 👋 Soy tu asistente de ventas. ¿En qué puedo ayudarte hoy?</div>
      </div>
      <div class="input-area">
        <input type="text" id="chatInput" placeholder="Escribe tu mensaje..." />
        <button id="sendBtn">➤</button>
      </div>
    </div>
    <div class="bubble" id="bubble">💬</div>
  `;

  const bubble = shadow.getElementById('bubble');
  const chatWindow = shadow.getElementById('chatWindow');
  const messages = shadow.getElementById('messages');
  const input = shadow.getElementById('chatInput');
  const sendBtn = shadow.getElementById('sendBtn');
  const closeBtn = shadow.getElementById('closeBtn');

  bubble.addEventListener('click', () => chatWindow.classList.toggle('open'));
  closeBtn.addEventListener('click', () => chatWindow.classList.remove('open'));

  function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `msg ${sender}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    input.value = '';

    // Simular respuesta del agente (reemplazar con WebSocket/Fetch real)
    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.textContent = 'Escribiendo...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    await new Promise(r => setTimeout(r, 1200));
    typing.remove();
    addMessage('Entendido, déjame verificar eso en nuestro inventario...', 'agent');
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', e => e.key === 'Enter' && sendMessage());

  // Auto-open si hay parámetro ?chat=1 en URL
  if (new URLSearchParams(window.location.search).get('chat') === '1') {
    chatWindow.classList.add('open');
  }
})();
