/**
 * JARVIS v4.2 — Configuração Centralizada
 * Hub3 Pixel Lab
 *
 * Detecta automaticamente ambiente local vs produção
 * e expõe os endpoints corretos para o frontend.
 */

const CONFIG = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;

    const isLocal = hostname === '127.0.0.1' || hostname === 'localhost';

    return {
        env: isLocal ? 'local' : 'production',
        API_BASE: isLocal
            ? 'http://127.0.0.1:8000'
            : `${protocol}//${hostname}${port ? ':' + port : ''}`,
        TIMEOUT: 30000,
        HEALTH_CHECK_INTERVAL: 30000,
        DEFAULT_MODEL: 'llama3.2:1b',
        VOICE_LANG: 'pt-BR',
        VOICE_RATE: 1.05,
        VOICE_PITCH: 1.0,
    };
})();

window.CONFIG = CONFIG;
console.log(`[JARVIS] Ambiente: ${CONFIG.env} | API: ${CONFIG.API_BASE}`);
