// Julep Chat Widget with Streaming Support
(function() {
  'use strict';
  
  console.log('[Julep Widget] Loading...');
  
  // Configuration
  const PROXY_URL = 'https://julep-chat-proxy.vercel.app/api/chat';
  
  // State
  let sessionId = null;
  let isOpen = false;
  
  // Helper function to create element with attributes
  function createElement(tag, attrs = {}, innerHTML = '') {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'style') {
        el.style.cssText = value;
      } else if (key === 'className') {
        el.className = value;
      } else {
        el.setAttribute(key, value);
      }
    });
    if (innerHTML) el.innerHTML = innerHTML;
    return el;
  }
  
  // Create and inject styles
  const styles = createElement('style', {}, `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* CSS Variables for theming */
    :root {
      --julep-bg-primary: #ffffff;
      --julep-bg-secondary: #f8f9fb;
      --julep-bg-tertiary: #f8fafb;
      --julep-text-primary: #1a202c;
      --julep-text-secondary: #4a5568;
      --julep-border: #e2e8f0;
      --julep-shadow: rgba(0,0,0,0.12);
      --julep-input-bg: #ffffff;
      --julep-code-bg: #1e293b;
      --julep-code-text: #e2e8f0;
    }
    
    /* Dark mode variables */
    #julep-chat-widget[data-theme="dark"] {
      --julep-bg-primary: #1a1a1a;
      --julep-bg-secondary: #0f0f0f;
      --julep-bg-tertiary: #252525;
      --julep-text-primary: #e2e8f0;
      --julep-text-secondary: #a0aec0;
      --julep-border: #2d3748;
      --julep-shadow: rgba(0,0,0,0.4);
      --julep-input-bg: #252525;
      --julep-code-bg: #0f0f0f;
      --julep-code-text: #e2e8f0;
    }
    
    #julep-toggle-btn {
      position: fixed !important;
      bottom: 24px !important;
      right: 24px !important;
      width: 64px !important;
      height: 64px !important;
      background: linear-gradient(135deg, #004E64 0%, #00A5CF 100%) !important;
      border: none !important;
      border-radius: 50% !important;
      cursor: pointer !important;
      box-shadow: 0 4px 20px rgba(0, 78, 100, 0.3) !important;
      z-index: 99999 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: all 0.3s ease !important;
    }
    
    #julep-toggle-btn:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 6px 30px rgba(0, 78, 100, 0.4) !important;
      background: linear-gradient(135deg, #003847 0%, #0091b8 100%) !important;
    }
    
    #julep-toggle-btn svg {
      width: 28px !important;
      height: 28px !important;
    }
    
    #julep-chat-widget {
      position: fixed !important;
      bottom: 100px !important;
      right: 24px !important;
      width: 480px !important;
      height: 680px !important;
      background: var(--julep-bg-primary) !important;
      border-radius: 16px !important;
      box-shadow: 0 10px 40px var(--julep-shadow) !important;
      z-index: 99998 !important;
      display: none !important;
      flex-direction: column !important;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
      overflow: hidden !important;
      transition: all 0.3s ease !important;
      border: 1px solid var(--julep-border) !important;
    }
    
    #julep-chat-widget.open {
      display: flex !important;
    }
    
    /* Expanded mode */
    #julep-chat-widget.expanded {
      width: 600px !important;
      height: 780px !important;
    }
    
    @media (max-width: 768px) {
      #julep-chat-widget {
        width: calc(100vw - 40px) !important;
        height: calc(100vh - 140px) !important;
        right: 20px !important;
        bottom: 80px !important;
      }
      
      #julep-chat-widget.expanded {
        width: calc(100vw - 40px) !important;
        height: calc(100vh - 140px) !important;
      }
    }
    
    #julep-chat-header {
      background: linear-gradient(135deg, #004E64 0%, #00A5CF 100%) !important;
      color: white !important;
      padding: 20px 24px !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      font-weight: 600 !important;
      font-size: 17px !important;
      letter-spacing: -0.02em !important;
    }
    
    #julep-header-buttons {
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
    }
    
    #julep-close-btn {
      background: rgba(255, 255, 255, 0.15) !important;
      border: none !important;
      color: white !important;
      font-size: 24px !important;
      cursor: pointer !important;
      width: 34px !important;
      height: 34px !important;
      border-radius: 8px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: all 0.2s ease !important;
    }
    
    #julep-close-btn:hover {
      background: rgba(255, 255, 255, 0.25) !important;
    }
    
    /* Expand button styling */
    #julep-expand-btn {
      background: rgba(255, 255, 255, 0.15) !important;
      border: none !important;
      color: white !important;
      font-size: 18px !important;
      cursor: pointer !important;
      width: 34px !important;
      height: 34px !important;
      border-radius: 8px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: all 0.2s ease !important;
      margin-right: 8px !important;
    }
    
    #julep-expand-btn:hover {
      background: rgba(255, 255, 255, 0.25) !important;
    }
    
    #julep-messages {
      flex: 1 !important;
      overflow-y: auto !important;
      padding: 24px !important;
      background: var(--julep-bg-secondary) !important;
    }
    
    .julep-message {
      margin-bottom: 16px !important;
      padding: 12px 16px !important;
      border-radius: 12px !important;
      max-width: 85% !important;
      font-size: 14px !important;
      line-height: 1.5 !important;
      position: relative !important;
    }
    
    .julep-message-copy {
      position: absolute !important;
      top: 8px !important;
      right: 8px !important;
      background: transparent !important;
      border: none !important;
      cursor: pointer !important;
      opacity: 0 !important;
      transition: opacity 0.2s ease !important;
      padding: 4px !important;
      border-radius: 4px !important;
    }
    
    .julep-message:hover .julep-message-copy {
      opacity: 0.6 !important;
    }
    
    .julep-message-copy:hover {
      opacity: 1 !important;
      background: rgba(0, 0, 0, 0.1) !important;
    }
    
    .julep-user .julep-message-copy {
      color: white !important;
    }
    
    .julep-assistant .julep-message-copy {
      color: var(--julep-text-primary) !important;
    }
    
    .julep-user {
      background: linear-gradient(135deg, #004E64 0%, #00A5CF 100%) !important;
      color: white !important;
      margin-left: auto !important;
      border-bottom-right-radius: 4px !important;
      box-shadow: 0 2px 8px rgba(0, 78, 100, 0.2) !important;
    }
    
    .julep-assistant {
      background: var(--julep-bg-tertiary) !important;
      color: var(--julep-text-primary) !important;
      border: 1px solid var(--julep-border) !important;
      box-shadow: 0 1px 3px var(--julep-shadow) !important;
    }
    
    .julep-message pre {
      background: var(--julep-code-bg) !important;
      color: var(--julep-code-text) !important;
      padding: 12px !important;
      border-radius: 8px !important;
      overflow-x: auto !important;
      margin: 8px 0 !important;
      border: 1px solid var(--julep-border) !important;
      position: relative !important;
    }
    
    .julep-code-copy {
      position: absolute !important;
      top: 8px !important;
      right: 8px !important;
      background: rgba(255, 255, 255, 0.1) !important;
      border: 1px solid rgba(255, 255, 255, 0.2) !important;
      border-radius: 6px !important;
      padding: 4px 8px !important;
      cursor: pointer !important;
      font-size: 12px !important;
      color: var(--julep-code-text) !important;
      opacity: 0 !important;
      transition: all 0.2s ease !important;
    }
    
    .julep-message pre:hover .julep-code-copy {
      opacity: 1 !important;
    }
    
    .julep-code-copy:hover {
      background: rgba(255, 255, 255, 0.2) !important;
    }
    
    .julep-code-copy.copied {
      background: #25A18E !important;
      border-color: #25A18E !important;
    }
    
    .julep-message code {
      background: var(--julep-code-bg) !important;
      color: #00A5CF !important;
      padding: 2px 4px !important;
      border-radius: 4px !important;
      font-family: monospace !important;
    }
    
    .julep-message pre code {
      background: none !important;
      color: inherit !important;
      padding: 0 !important;
    }
    
    .julep-message h1,
    .julep-message h2,
    .julep-message h3,
    .julep-message h4,
    .julep-message h5,
    .julep-message h6 {
      margin: 12px 0 8px 0 !important;
      font-weight: 600 !important;
      line-height: 1.4 !important;
    }
    
    .julep-message h1 { font-size: 20px !important; }
    .julep-message h2 { font-size: 18px !important; }
    .julep-message h3 { font-size: 16px !important; }
    .julep-message h4 { font-size: 15px !important; }
    .julep-message h5 { font-size: 14px !important; }
    .julep-message h6 { font-size: 13px !important; }
    
    .julep-message ul,
    .julep-message ol {
      margin: 8px 0 !important;
      padding-left: 20px !important;
    }
    
    .julep-message li {
      margin: 4px 0 !important;
      line-height: 1.5 !important;
    }
    
    .julep-message a {
      color: #00A5CF !important;
      text-decoration: none !important;
      border-bottom: 1px solid transparent !important;
      transition: border-color 0.2s !important;
    }
    
    .julep-message a:hover {
      border-bottom-color: #00A5CF !important;
      color: #0091b8 !important;
    }
    
    #julep-input-container {
      padding: 20px !important;
      background: var(--julep-bg-primary) !important;
      border-top: 1px solid var(--julep-border) !important;
      display: flex !important;
      gap: 12px !important;
    }
    
    #julep-input {
      flex: 1 !important;
      padding: 13px 18px !important;
      border: 2px solid var(--julep-border) !important;
      border-radius: 12px !important;
      font-size: 14px !important;
      outline: none !important;
      transition: all 0.2s ease !important;
      background: var(--julep-input-bg) !important;
      color: var(--julep-text-primary) !important;
    }
    
    #julep-input:focus {
      border-color: #00A5CF !important;
      box-shadow: 0 0 0 3px rgba(0, 165, 207, 0.1) !important;
    }
    
    #julep-input::placeholder {
      color: var(--julep-text-secondary) !important;
    }
    
    #julep-send-btn {
      padding: 13px 24px !important;
      background: linear-gradient(135deg, #004E64 0%, #00A5CF 100%) !important;
      color: white !important;
      border: none !important;
      border-radius: 12px !important;
      cursor: pointer !important;
      font-size: 14px !important;
      font-weight: 500 !important;
      transition: all 0.2s ease !important;
      box-shadow: 0 2px 8px rgba(0, 78, 100, 0.2) !important;
    }
    
    #julep-send-btn:hover {
      transform: translateY(-1px) !important;
      box-shadow: 0 4px 12px rgba(0, 78, 100, 0.3) !important;
      background: linear-gradient(135deg, #003847 0%, #0091b8 100%) !important;
    }
    
    #julep-send-btn:active {
      transform: translateY(0) !important;
    }
    
    .julep-loading {
      display: inline-flex !important;
      gap: 4px !important;
    }
    
    .julep-loading span {
      width: 6px !important;
      height: 6px !important;
      background: #00A5CF !important;
      border-radius: 50% !important;
      animation: julep-bounce 1.4s ease-in-out infinite both !important;
    }
    
    .julep-loading span:nth-child(2) {
      animation-delay: 0.16s !important;
    }
    
    .julep-loading span:nth-child(3) {
      animation-delay: 0.32s !important;
    }
    
    @keyframes julep-bounce {
      0%, 80%, 100% {
        transform: scale(0.8);
        opacity: 0.5;
      }
      40% {
        transform: scale(1);
        opacity: 1;
      }
    }
  `);
  
  // Create widget elements
  const toggleBtn = createElement('button', {
    id: 'julep-toggle-btn',
    type: 'button'
  }, '<svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>');
  
  const widget = createElement('div', { id: 'julep-chat-widget' });
  
  const header = createElement('div', { id: 'julep-chat-header' });
  const headerTitle = createElement('span', {}, 'Julep Assistant');
  const headerButtons = createElement('div', { id: 'julep-header-buttons' });
  const expandBtn = createElement('button', { id: 'julep-expand-btn', type: 'button' }, '⤢');
  const closeBtn = createElement('button', { id: 'julep-close-btn', type: 'button' }, '×');
  headerButtons.appendChild(expandBtn);
  headerButtons.appendChild(closeBtn);
  header.appendChild(headerTitle);
  header.appendChild(headerButtons);
  
  const messagesDiv = createElement('div', { id: 'julep-messages' });
  
  const inputContainer = createElement('div', { id: 'julep-input-container' });
  const input = createElement('input', {
    id: 'julep-input',
    type: 'text',
    placeholder: 'Ask about Julep...'
  });
  const sendBtn = createElement('button', {
    id: 'julep-send-btn',
    type: 'button'
  }, 'Send');
  inputContainer.appendChild(input);
  inputContainer.appendChild(sendBtn);
  
  widget.appendChild(header);
  widget.appendChild(messagesDiv);
  widget.appendChild(inputContainer);
  
  // Helper functions
  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(err => {
        console.error('[Julep Widget] Failed to copy:', err);
      });
    } else {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
  }
  
  // Global function for code copy buttons
  window.copyJulepCode = function(codeId) {
    const codeElement = document.getElementById(codeId);
    if (codeElement) {
      const code = codeElement.querySelector('code').textContent;
      copyToClipboard(code);
      
      const copyBtn = codeElement.querySelector('.julep-code-copy');
      copyBtn.textContent = 'Copied!';
      copyBtn.classList.add('copied');
      
      setTimeout(() => {
        copyBtn.textContent = 'Copy';
        copyBtn.classList.remove('copied');
      }, 2000);
    }
  };
  
  function parseMarkdown(text) {
    // First, extract and store code blocks to protect them
    const codeBlocks = [];
    let html = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const index = codeBlocks.length;
      codeBlocks.push({ lang: lang || 'plaintext', code: code.trim() });
      return `__CODEBLOCK_${index}__`;
    });
    
    // Extract inline code
    const inlineCode = [];
    html = html.replace(/`([^`]+)`/g, (match, code) => {
      const index = inlineCode.length;
      inlineCode.push(code);
      return `__INLINECODE_${index}__`;
    });
    
    // Now escape HTML
    html = html.replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[m]);
    
    // Process markdown
    // Headers
    html = html.replace(/^#{6}\s+(.+)$/gm, '<h6>$1</h6>');
    html = html.replace(/^#{5}\s+(.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#{1}\s+(.+)$/gm, '<h1>$1</h1>');
    
    // Bold and italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Lists
    html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    // Restore code blocks with proper escaping and copy button
    codeBlocks.forEach((block, index) => {
      const escapedCode = block.code.replace(/[&<>"']/g, (m) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[m]);
      const codeId = `code-${Date.now()}-${index}`;
      html = html.replace(`__CODEBLOCK_${index}__`, 
        `<pre id="${codeId}"><button class="julep-code-copy" onclick="window.copyJulepCode('${codeId}')">Copy</button><code class="language-${block.lang}">${escapedCode}</code></pre>`
      );
    });
    
    // Restore inline code
    inlineCode.forEach((code, index) => {
      const escapedCode = code.replace(/[&<>"']/g, (m) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[m]);
      html = html.replace(`__INLINECODE_${index}__`, `<code>${escapedCode}</code>`);
    });
    
    // Clean up extra line breaks around block elements
    html = html.replace(/<br>(<[hpd])/g, '$1');
    html = html.replace(/(<\/[hpd][^>]*>)<br>/g, '$1');
    
    return html;
  }
  
  function addMessage(text, sender) {
    const messageDiv = createElement('div', {
      className: 'julep-message julep-' + sender
    });
    
    // Add message content
    messageDiv.innerHTML = parseMarkdown(text);
    
    // Add copy button for message
    const copyBtn = createElement('button', {
      className: 'julep-message-copy',
      title: 'Copy message'
    }, `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>`);
    
    copyBtn.onclick = function() {
      copyToClipboard(text);
      copyBtn.innerHTML = '✓';
      setTimeout(() => {
        copyBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>`;
      }, 2000);
    };
    
    messageDiv.appendChild(copyBtn);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageDiv;
  }
  
  async function createSession() {
    try {
      const response = await fetch(PROXY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'createSession' })
      });
      
      if (!response.ok) throw new Error('Failed to create session');
      
      const data = await response.json();
      sessionId = data.id;
      console.log('[Julep Widget] Session created:', sessionId);
    } catch (error) {
      console.error('[Julep Widget] Session creation failed:', error);
      addMessage('Sorry, I could not connect to the service. Please try again later.', 'assistant');
    }
  }
  
  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;
    
    if (!sessionId) {
      await createSession();
      if (!sessionId) return;
    }
    
    addMessage(message, 'user');
    input.value = '';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'julep-message julep-assistant';
    loadingDiv.innerHTML = '<div class="julep-loading"><span></span><span></span><span></span></div>';
    messagesDiv.appendChild(loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
      const response = await fetch(PROXY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'sendMessage',
          sessionId: sessionId,
          message: message
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      
      // Handle streaming
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      
      loadingDiv.innerHTML = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.choices?.[0]?.delta?.content) {
                fullContent += parsed.choices[0].delta.content;
                loadingDiv.innerHTML = parseMarkdown(fullContent);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
      
      if (!fullContent) {
        loadingDiv.innerHTML = 'Sorry, I received an empty response.';
      }
      
    } catch (error) {
      console.error('[Julep Widget] Message send failed:', error);
      loadingDiv.innerHTML = 'Sorry, I encountered an error. Please try again.';
    }
  }
  
  // Event handlers
  toggleBtn.onclick = async function() {
    console.log('[Julep Widget] Toggle clicked');
    isOpen = !isOpen;
    
    if (isOpen) {
      widget.classList.add('open');
      if (!sessionId) {
        addMessage('Hello! I\'m here to help you with Julep. What would you like to know?', 'assistant');
        await createSession();
      }
    } else {
      widget.classList.remove('open');
    }
  };
  
  closeBtn.onclick = function() {
    console.log('[Julep Widget] Close clicked');
    isOpen = false;
    widget.classList.remove('open');
  };
  
  expandBtn.onclick = function() {
    console.log('[Julep Widget] Expand clicked');
    widget.classList.toggle('expanded');
    expandBtn.textContent = widget.classList.contains('expanded') ? '⤡' : '⤢';
  };
  
  sendBtn.onclick = sendMessage;
  
  input.onkeypress = function(e) {
    if (e.key === 'Enter') sendMessage();
  };
  
  // Theme detection function
  function detectTheme() {
    // Check for Mintlify's theme - they use 'dark' class on html element
    const htmlElement = document.documentElement;
    const isDark = htmlElement.classList.contains('dark');
    
    // Apply theme to widget
    widget.setAttribute('data-theme', isDark ? 'dark' : 'light');
    console.log('[Julep Widget] Theme detected:', isDark ? 'dark' : 'light');
    
    // Debug: log what we're checking
    console.log('[Julep Widget] HTML classes:', htmlElement.className);
  }
  
  // Initialize widget
  function init() {
    console.log('[Julep Widget] Initializing...');
    
    // Inject styles
    if (!document.getElementById('julep-widget-styles')) {
      styles.id = 'julep-widget-styles';
      document.head.appendChild(styles);
    }
    
    // Add elements to body
    if (!document.getElementById('julep-toggle-btn')) {
      document.body.appendChild(toggleBtn);
      document.body.appendChild(widget);
      console.log('[Julep Widget] Widget added to page');
    }
    
    // Detect initial theme
    detectTheme();
    
    // Watch for theme changes
    const observer = new MutationObserver(() => {
      detectTheme();
    });
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'data-theme']
    });
    
    // Also watch for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', detectTheme);
  }
  
  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 100);
  }
})();