<div align="center">
  <img src="logo-KubeDeck.svg" alt="KubeDeck Logo" width="200"/>
  <h1>KubeDeck</h1>
  <p><b>O Canivete Suíço Definitivo para DevSecOps & Kubernetes Operacional</b></p>

  <p>
    <a href="https://github.com/SeuUsuario/KubeDeck/releases"><img src="https://img.shields.io/github/v/release/SeuUsuario/KubeDeck?style=for-the-badge&color=007AFF" alt="Release"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge" alt="License"></a>
    <a href="#"><img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey?style=for-the-badge" alt="Platform"></a>
  </p>
</div>

---

## 🚀 A Filosofia do KubeDeck
O **KubeDeck** não quer substituir ferramentas gigantes de administração de cluster como Rancher ou Lens. Nós resolvemos uma dor muito mais específica: a **dor do desenvolvedor e do engenheiro de resposta rápida**. 

Enquanto outras ferramentas exigem +1GB de RAM e instalações complexas, o KubeDeck é projetado para operar como um **Único Binário Executável Standalone**. Sem dependências. Sem instaladores. Ideal para ambientes restritos (air-gapped), jump-hosts ou uso rápido no dia a dia.

## 🎯 Por que o KubeDeck? (USPs - Unique Selling Propositions)

### 1. Zero Fricção, Zero Dependência (Standalone)
Baixe o binário para Linux ou Windows, dê permissão de execução e pronto. O KubeDeck carrega sua própria mini-engine web (via PyInstaller e Streamlit) e expõe o painel sem precisar que o Python ou o kubectl estejam configurados no ambiente local.

### 2. Gestão de Túneis (Port-Forwarding) de Elite
Port-Forwarding no terminal costuma deixar processos zumbis ou travar portas no seu computador local. O KubeDeck possui um **Gerenciador de Túneis Dedicado**.
- **Anti-Duplicação:** Impede o mapeamento de dois serviços para a mesma porta.
- **Derrubada Limpa:** Encerra os túneis com segurança e mata os subprocessos.
- **Visibilidade:** Você sabe exatamente o que está exposto e onde. Fundamental para auditoria de segurança (DevSecOps).

### 3. Laser-Focused UX (Sem Ruído)
Mostramos apenas o que importa para depuração diária de aplicações, ocultando os 80% da infraestrutura que apenas as equipes de plataforma deveriam acessar (como CRDs avançados).
- **Workloads:** Deployments, StatefulSets e DaemonSets com estado de réplicas.
- **Redes:** Services e Ingress (descubra facilmente como sua aplicação está exposta).
- **Configurações:** ConfigMaps e Secrets (base64 decodificado automaticamente).
- **Logs:** Logs em tempo real de seus Pods.

### 4. Nativamente Internacionalizado (i18n)
Desenvolvimento não tem fronteiras. O KubeDeck vem nativamente com suporte a:
- 🇺🇸 English (EN)
- 🇧🇷 Português (PT)
- 🇪🇸 Español (ES)
- 🇨🇳 中文 (ZH)

---

## 📦 Como Usar

### Usando o Executável Pré-Compilado (Recomendado)
Vá até a página de [Releases](https://github.com/SeuUsuario/KubeDeck/releases) e faça o download da última versão para o seu Sistema Operacional (Windows `.exe` ou Linux).

**No Linux:**
```bash
chmod +x KubeDeck-linux
./KubeDeck-linux
```

**No Windows:**
Apenas dê um duplo clique em `KubeDeck.exe`.

### Rodando a partir do Código-Fonte (Desenvolvedores)
Se você quer estender a ferramenta ou auditar o código:

1. Clone o repositório:
```bash
git clone https://github.com/SeuUsuario/KubeDeck.git
cd KubeDeck
```
2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```
3. Instale as dependências e rode o ambiente dev:
```bash
make install
make run
```

---

## 🛠️ Compilando seus Próprios Binários (Build)

O KubeDeck usa `PyInstaller` para empacotar o Python, as bibliotecas, e os assets estáticos (i18n e Logo) num único executável.
Para compilar:

**Gerar binário Linux:**
```bash
make build-linux
```
**Gerar binário Windows:**
```bash
make build-windows
```
*Atenção: A compilação cruzada (fazer build de Windows estando no Linux) tem limitações severas via PyInstaller. Recomendamos executar `make build-windows` diretamente num ambiente nativo do Windows para evitar erros de C++ Runtime (VCRUNTIME).*

---

## 🛡️ O Modelo de Negócio (Open Core)
O KubeDeck que você vê aqui é e sempre será **100% Open Source** sob a licença [Apache 2.0](LICENSE). 
Acreditamos em democratizar a operação de Kubernetes para todos os desenvolvedores.

Se você representa uma corporação com requisitos rígidos de **Governança, Compliance e Auditoria Centralizada** (SSO corporativo, RBAC avançado, relatórios de SOC 2 para Túneis abertos), fique de olho no futuro **KubeDeck Enterprise**.

## ☕ Apoie o Projeto (Doações)
O desenvolvimento do **KubeDeck** é movido a café e noites em claro. Se essa ferramenta salvou o seu dia ou poupou horas da sua equipe, considere pagar um café para o desenvolvedor manter o projeto livre e atualizado! Aceitamos contribuições globais:

- **Pix (Brasil):** `pixrailsonsilva@gmail.com`
- **PayPal (Internacional):** [Doe via PayPal](https://paypal.me/SEU_LINK_AQUI)
- **Crypto (USDT - TRC20/ERC20):** `sua_carteira_usdt_aqui`

*(Qualquer valor é imensamente apreciado e ajuda a manter a pesquisa e os testes de segurança!)*

## 🤝 Contribuindo
Sinta-se à vontade para abrir Issues para reportar bugs e Pull Requests para sugerir melhorias.

---
*Construído para Engenheiros que valorizam o próprio tempo.*
