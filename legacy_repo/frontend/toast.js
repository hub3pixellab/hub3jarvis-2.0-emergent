/**
 * Toast Notification System para JARVIS v4.2
 * Versao robusta — aguarda o body existir antes de criar o container
 */
(function() {
    function initToast() {
        if (!document.body) {
            setTimeout(initToast, 50);
            return;
        }
        var container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;max-width:360px';
            document.body.appendChild(container);
        }

        window.Toast = {
            show: function(message, type, duration) {
                type = type || 'info';
                duration = duration || 4000;
                var colors = {success:'#00e676',error:'#ff4444',warning:'#ff8c00',info:'#00d4ff'};
                var bgColors = {success:'rgba(0,230,118,0.1)',error:'rgba(255,68,68,0.1)',warning:'rgba(255,140,0,0.1)',info:'rgba(0,212,255,0.1)'};
                var el = document.createElement('div');
                el.style.cssText = 'background:'+bgColors[type]+';border:1px solid '+colors[type]+';border-radius:8px;padding:12px 16px;color:#e0e7f0;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.3);display:flex;align-items:center;gap:8px';
                el.innerHTML = '<span style="color:'+colors[type]+';font-size:16px">'+(type==='success'?'✓':type==='error'?'✕':type==='warning'?'⚠':'ℹ')+'</span>'+message;
                container.appendChild(el);
                setTimeout(function(){
                    el.style.opacity='0';
                    el.style.transition='opacity 0.3s';
                    setTimeout(function(){if(el.parentNode)el.parentNode.removeChild(el)},300);
                }, duration);
            },
            success: function(m){this.show(m,'success')},
            error: function(m){this.show(m,'error')},
            warning: function(m){this.show(m,'warning')},
            info: function(m){this.show(m,'info')}
        };
    }
    initToast();
})();
