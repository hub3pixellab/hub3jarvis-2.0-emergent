# Grok CLI + ApiPass — Configuração

## Visão Geral

Tutorial oficial para instalar o Grok CLI (xAI) e configurar o **ApiPass** como endpoint de modelo, permitindo usar o **Grok 4.5** diretamente do terminal como agente de codigo.

## Pré-requisitos

- Chave de API do ApiPass ([API Keys](https://api.apipass.dev/keys))
- Creditos suficientes no ApiPass para requisicoes Grok Build
- Terminal Bash no macOS, Linux ou Windows WSL2

## Instalação

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

Apos finalizar, abra um **novo terminal** para que o PATH atualizado seja carregado.

## Configuração do ApiPass

Crie o diretorio de configuracao:

```bash
mkdir -p ~/.grok
```

Crie o arquivo `~/.grok/config.toml`:

```toml
[cli]
installer = "internal"

[models]
default = "grok-4.5"
web_search = "grok-4.5"

[endpoints]
models_base_url = "https://api.apipass.dev/grok-build/v1"

[model."grok-4.5"]
model = "grok-4.5"
name = "Grok 4.5"
description = "Grok 4.5 ApiPass"
api_key = "SUA_API_KEY_AQUI"
api_backend = "responses"
context_window = 1000000
```

Substitua `SUA_API_KEY_AQUI` pela sua chave real do ApiPass.

Proteja o arquivo:

```bash
chmod 600 ~/.grok/config.toml
```

## Verificação

```bash
grok inspect
grok -p "Reply with exactly: ApiPass connected" -m grok-4.5
```

## Uso

**Sessao interativa:**
```bash
grok
```

**Comando unico:**
```bash
grok -p "Review this repo" -m grok-4.5
```

## Custo

ApiPass deduz creditos por requisicao. Consulte:
- [Pricing](https://api.apipass.dev/pricing)
- [API Logs](https://api.apipass.dev/logs)

## Troubleshooting

| Erro | Solucao |
|------|---------|
| `grok: command not found` | Feche e reabra o terminal |
| `Authentication Fails` | Confirme a `api_key` em `~/.grok/config.toml` |
| `404 Not Found` | `models_base_url` deve terminar em `/grok-build/v1` |
| `model refresh failed` | Teste com `grok -p ok -m grok-4.5` |
