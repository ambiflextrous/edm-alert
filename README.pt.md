*Read this in [English](README.md).*

# Alertas de Cortes de Energia — EDM Cabo Delgado

Envia-te um email sempre que a EDM publicar um novo corte programado ("Corte Programado") para **Cabo Delgado** em https://www.edm.co.mz/manutencao.

Corre gratuitamente no GitHub Actions, a cada 4 horas. O script lembra-se de quais códigos de referência (ex: `PEM260705-0092`) já alertou, por isso só recebes um email por corte.

## Configuração (cerca de 10 minutos)

### 1. Cria uma Senha de Aplicação do Gmail
Precisas de uma conta Gmail para *enviar* o alerta (pode enviar para qualquer endereço, incluindo o próprio).

1. Vai a https://myaccount.google.com/security e activa a **Verificação em 2 Passos**, se ainda não estiver activa.
2. Vai a https://myaccount.google.com/apppasswords
3. Cria uma senha de aplicação com o nome "EDM alert" e copia o código de 16 caracteres.

### 2. Cria o repositório no GitHub
1. Inicia sessão em https://github.com (a conta gratuita serve).
2. Cria um repositório **privado**, por exemplo `edm-alert`.
3. Carrega estes ficheiros mantendo a estrutura de pastas:
   - `check_edm.py`
   - `README.md`
   - `README.pt.md`
   - `.github/workflows/edm-alert.yml`

   Forma mais fácil: na página do repositório, **Add file → Upload files**, e arrasta o conteúdo da pasta. (Para criar a pasta `.github/workflows` pela interface web, usa **Add file → Create new file** e escreve `.github/workflows/edm-alert.yml` como nome do ficheiro, depois cola o conteúdo do workflow.)

### 3. Adiciona os teus secrets
No repositório: **Settings → Secrets and variables → Actions → New repository secret**. Adiciona três:

| Nome | Valor |
|---|---|
| `SMTP_USER` | o teu endereço Gmail |
| `SMTP_PASS` | a senha de aplicação de 16 caracteres |
| `ALERT_TO` | o email para onde queres receber os alertas |

### 4. Testa
Vai ao separador **Actions** → "EDM Cabo Delgado outage alert" → **Run workflow**. Como o corte actual de Cabo Delgado ainda é novo para o script, deves receber um email dentro de um a dois minutos.

## Notas
- Para monitorizar outra província, adiciona um secret ou edita o valor padrão de `PROVINCE` no script.
- Para mudar a frequência, edita a linha `cron` no workflow (`0 */2 * * *` = a cada 2 horas).
- O GitHub pode pausar workflows agendados em repositórios sem actividade há 60 dias — os commits do próprio bot em `seen_ids.json` normalmente mantêm o repositório activo, mas se os alertas pararem, verifica se há um botão "re-enable" no separador Actions.
