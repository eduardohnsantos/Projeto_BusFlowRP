Markdown
# 🚌 BusFlow RP — Painel Analítico & Engenharia de Dados

> **Status do Projeto:** Concluído 🚀

O **BusFlow RP** é uma plataforma de Engenharia de Dados ponta a ponta desenvolvida para monitorar, auditar e otimizar a eficiência do transporte público urbano de Ribeirão Preto em tempo real. A aplicação consome dados brutos de telemetria veicular, processa regras de negócio diretamente na base de dados e transforma sinais de GPS em indicadores logísticos estratégicos.

---

## 📸 Demonstração do Painel

### Tela Inicial (Onboarding)
Aqui está a tela inicial de boas-vindas do sistema, projetada com cartões nativos estáveis para introduzir o ecossistema e os recursos ao usuário:
![Uploading Mapa.png…]()

[Tela Inicial do BusFlow RP](docs/<img width="1908" height="926" alt="BusFlow RP" src="https://github.com/user-attachments/assets/a351236b-25e9-488b-a0f2-98de1f68ebb8" />
home.png)

### Monitoramento de Linha e Cerca Virtual em Tempo Real
Ao selecionar uma linha operacional no painel de controle, o sistema calcula os indicadores instantaneamente e plota o mapa dinâmico de telemetria ativa:

[Monitoramento Live e KPIs](docs/mapa.png)

---

## 🎯 O Problema & Solução

Garantir a qualidade do transporte público exige visibilidade contínua. Sem uma auditoria eficiente, atrasos sistemáticos e desvios de rota passam despercebidos pelos órgãos gestores. 

O **BusFlow RP** resolve esse problema integrando três camadas críticas de análise de dados:
1. **Pontualidade (OTP - On-Time Performance):** Calcula em tempo real o desvio em minutos entre o horário planejado na malha horária e a transmissão real do GPS de telemetria.
2. **Cerca Virtual (Geofencing):** Valida algoritmos geográficos diretamente na base de dados para detectar instantaneamente desvios de itinerário.
3. **Telemetria Live:** Renderiza um mapa interativo com ciclos automatizados de atualização a cada 4 segundos, isolando ruídos de sinal de rede do dispositivo embarcado.

---

## 🛠️ Tecnologias & Arquitetura

O ecossistema foi projetado pensando em escalabilidade e separação de conceitos (Ingestão, Armazenamento e Consumo):

* **Linguagem Principal:** Python 3.x
* **Interface e Dashboard:** Streamlit (com componentes dinâmicos de autorefresh)
* **Visualização Geoespacial:** Folium & Streamlit Folium
* **Banco de Dados Relacional:** PostgreSQL (Hospedado em Nuvem)
* **Mapeamento Objeto-Relacional (ORM):** SQLAlchemy

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
Antes de começar, certifique-se de ter instalado em sua máquina:
* Git
* Python (versão 3.8 ou superior)
* Um banco de dados PostgreSQL ativo (ou credenciais de nuvem)

### 1. Clonar o Repositório
```bash
git clone [https://github.com/SEU_USUARIO/busflow-rp.git](https://github.com/SEU_USUARIO/busflow-rp.git)
cd busflow-rp
2. Configurar Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto (este arquivo está listado no .gitignore e não deve ser exposto publicamente) e adicione suas credenciais de conexão do banco de dados:

Snippet de código
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=seu_host_postgresql
DB_PORT=5432
DB_NAME=seu_banco_de_dados
3. Instalar as Dependências
Recomenda-se o uso de um ambiente virtual (venv):

Bash
# Criar e ativar o ambiente virtual (Opcional)
python -m venv venv
source venv/bin/activate  # No Linux/Mac
venv\Scripts\activate     # No Windows

# Instalar pacotes necessários
pip install -r requirements.txt
4. Executar a Aplicação Streamlit
Bash
streamlit run src/app/main.py
O painel abrirá automaticamente no seu navegador padrão (geralmente em http://localhost:8501).

🛠️ Infraestrutura de Dados (Detalhes do Pipeline)
Ingestão: Pipelines estruturados para limpeza, tipagem de dados e tratamento de cenários de exceção de horários (ex: jornadas operacionais de madrugada).

Camada de Banco: Tabelas normalizadas relacionando a malha_horaria estática com a tabela de telemetria_onibus atualizada continuamente via banco.


### 💡 Dica extra de ouro para as imagens do GitHub:
Para que os prints apareçam certinhos no seu perfil, basta criar uma pasta chamada `docs` na raiz do seu repositório local e salvar lá dentro duas capturas de tela:
1. Uma da sua tela inicial de boas-vindas com o nome `home.png`.
2. Outra com a aba do mapa geoespacial carregada e os KPIs visíveis com o nome `mapa.png`.

Assim que você der o `git push`, os links no markdown encontrarão as imagens automaticamente!
