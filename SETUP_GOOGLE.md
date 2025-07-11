# 🔧 Configuração Google Cloud Console

## ⚠️ IMPORTANTE: OAuth 2.0 vs API Key

Para acessar Google Drive e Sheets com permissões de leitura/escrita, você precisa de:
- **OAuth 2.0 (credentials.json)** - OBRIGATÓRIO para este projeto
- **API Key** - NÃO é suficiente para as operações necessárias

A API Key (KEY) foi adicionada ao .env, mas você ainda precisa seguir os passos abaixo para obter o credentials.json.

## Passo a Passo para Obter credentials.json

### 1. Acesse o Google Cloud Console
- Vá para: https://console.cloud.google.com

### 2. Crie ou Selecione um Projeto
- Clique no seletor de projetos no topo
- Crie um novo projeto ou selecione um existente

### 3. Ative as APIs Necessárias
No menu lateral, vá para "APIs e Serviços" > "Biblioteca" e ative:
- **Google Drive API**
- **Google Sheets API**

### 4. Crie as Credenciais OAuth 2.0

1. Vá para "APIs e Serviços" > "Credenciais"
2. Clique em "+ CRIAR CREDENCIAIS" > "ID do cliente OAuth"
3. Configure a tela de consentimento OAuth (se necessário):
   - Escolha "Externo" para uso pessoal
   - Preencha apenas os campos obrigatórios
   - Adicione seu email nos usuários de teste

4. Volte para criar o ID do cliente OAuth:
   - Tipo de aplicativo: **Aplicativo para desktop**
   - Nome: "Vinyl Instagram Bot" (ou qualquer nome)
   - Clique em "CRIAR"

5. Baixe o arquivo JSON:
   - Clique no botão de download ⬇️
   - Salve como `credentials/credentials.json` no projeto

### 5. Estrutura de Pastas
```
script-post-instagram/
└── credentials/
    └── credentials.json  ← Arquivo baixado aqui
```

### 6. Primeira Execução
```bash
python main.py setup
```

- Na primeira vez, abrirá o navegador para autorização
- Faça login com sua conta Google
- Autorize o acesso ao Drive e Sheets
- O token será salvo automaticamente

## ⚠️ Notas Importantes

- **Mantenha credentials.json seguro** - não compartilhe este arquivo
- O arquivo está no .gitignore para não ser enviado ao Git
- Após autorizar, um arquivo `token.json` será criado
- Se mudar os escopos, delete `token.json` e autorize novamente

## 🔒 Permissões Necessárias

O bot precisa de:
- **Leitura do Google Drive** - para baixar fotos
- **Leitura/Escrita do Google Sheets** - para gerenciar catálogo

## 🆘 Problemas Comuns

### "Arquivo de credenciais não encontrado"
- Certifique-se que salvou em `credentials/credentials.json`
- Verifique se o diretório `credentials/` existe

### "Acesso negado" ou "Escopo inválido"
- Delete `credentials/token.json`
- Execute `python main.py setup` novamente
- Reautorize o aplicativo

### "Este app não foi verificado"
- Normal para apps em desenvolvimento
- Clique em "Avançado" > "Ir para [nome do app] (não seguro)"
- É seguro pois é seu próprio aplicativo