// scripts/entelligence-chat.js
function injectShadowStyles(interval) {
  const container = document.getElementById("entelligence-chat-root");
  if (container && container.shadowRoot) {    
    const shadow = container.shadowRoot;
    const widgetContainer = document.createElement("div");
    shadow.appendChild(widgetContainer);
    
    fetch("https://dujj2xy9pc7vi.cloudfront.net/entelligence-chat.css")
      .then(r => r.text())
      .then(styles => {
        const style = document.createElement("style");        
        style.textContent = styles;
        shadow.prepend(style);
        document.head.prepend(style.cloneNode(true));
      });
    clearInterval(interval);
  }
}
 
function initEntelligence() {
  const script = document.getElementById("entelligence-chat");
 
  if (!script) {
    const chatScript = document.createElement("script");
    chatScript.type = "module";
    chatScript.id = "entelligence-chat";
    chatScript.src = "https://dujj2xy9pc7vi.cloudfront.net/vanilla/entelligence-chat.es.js";
    chatScript.defer = true;
 
    const initScript = document.createElement("script");
    initScript.type = "module";
    initScript.textContent = `
      window.EntelligenceChat.init({
        analyticsData: {
          repoName: "julep",
          organization: "julep-ai",
          apiKey: "-QPa1vq4X-2-KwLus5GxhDBE71g5BdXKwZs2M3iPh8U",
          theme: 'dark',
          companyName: "Julep AI"
        }
      });
    `;
 
    const head = document.getElementsByTagName("head")[0];
    head.appendChild(chatScript);
 
    chatScript.onload = () => {
      document.head.appendChild(initScript);
      const interval = setInterval(() => {
        injectShadowStyles(interval);
      }, 1000);
    };
  }
}
 
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initEntelligence);
} else {
  initEntelligence();
}