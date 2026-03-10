# 🛡️ Pipeline Sentinel

> **Framework de Qualidade de Dados** com Great Expectations + dbt + Airflow + Slack Alerts

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-1.11-FF694B?style=flat-square&logo=dbt&logoColor=white)](https://getdbt.com)
[![Airflow](https://img.shields.io/badge/Airflow-3.1-017CEE?style=flat-square&logo=apacheairflow&logoColor=white)](https://airflow.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Great Expectations](https://img.shields.io/badge/Great_Expectations-1.14-FF6B6B?style=flat-square)](https://greatexpectations.io)

---

## 📌 O Problema

A maioria dos pipelines de dados falha silenciosamente. Dados chegam incompletos, duplicados ou fora do padrão — e ninguém fica sabendo até o problema chegar na tomada de decisão.

O **Pipeline Sentinel** resolve isso implementando um sistema completo de vigilância da qualidade dos dados, com alertas automáticos no Slack quando algo dá errado.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Apache Airflow                        │
│                                                          │
│  [Ingestão] → [dbt run] → [dbt test] → [GE Validate]   │
│      ↓             ↓           ↓             ↓          │
│   IBGE API     Staging      Schema       5 Checks        │
│               + Marts       Tests        Quality         │
│                                              ↓           │
│                                        Slack Alert       │
└─────────────────────────────────────────────────────────┘
         ↓                ↓                   ↓
    PostgreSQL         dbt docs          GE Reports
```

---

## ⚙️ Stack

| Camada | Ferramenta | Função |
|--------|-----------|--------|
| Ingestão | Python + Requests | Consome API SIDRA/IBGE |
| Armazenamento | PostgreSQL 15 | Banco de dados principal |
| Transformação | dbt Core 1.11 | Modelos em camadas (staging → marts) |
| Qualidade | Great Expectations 1.14 | 5 tipos de checks de qualidade |
| Testes de schema | dbt tests + dbt_utils | Validação de constraints |
| Orquestração | Apache Airflow 3.1 | Agendamento e monitoramento |
| Alertas | Slack Webhooks | Notificações em tempo real |

---

## ✅ Checks de Qualidade Implementados

| Tipo | Descrição | Implementação |
|------|-----------|---------------|
| **Completude** | Campos obrigatórios sem NULL | `ExpectColumnValuesToNotBeNull` |
| **Unicidade** | Chave composta sem duplicatas | `dbt_utils.unique_combination_of_columns` |
| **Validade** | Código de município com 7 dígitos | `ExpectColumnValueLengthsToEqual` |
| **Contagem** | Entre 5.000 e 50.000 municípios | `ExpectTableRowCountToBeBetween` |
| **Domínio** | Nível territorial = "Município" | `ExpectColumnValuesToBeInSet` |

---

## 📁 Estrutura do Projeto

```
pipeline-sentinel/
├── ingestion/
│   └── ibge_ingestion.py          # Ingestão da API SIDRA/IBGE
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_ibge_population.sql
│   │   │   ├── stg_ibge_population.yml
│   │   │   └── sources.yml
│   │   └── marts/
│   │       └── mart_populacao_estados.sql
│   └── packages.yml
├── great_expectations/
│   └── validate.py                # Expectation suites e checkpoints
├── dags/
│   └── data_quality_pipeline.py   # DAG principal do Airflow
├── notifications/
│   └── slack_notifier.py          # Módulo de alertas
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Como Rodar

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- Git

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/renantorres0/pipeline-sentinel.git
cd pipeline-sentinel

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

### Configurar banco de dados

```bash
sudo -u postgres psql
```
```sql
CREATE USER dquser WITH PASSWORD 'dqpassword';
CREATE DATABASE dqdb OWNER dquser;
GRANT ALL PRIVILEGES ON DATABASE dqdb TO dquser;
\q
```

### Rodar o pipeline

```bash
# 1. Ingestão
python ingestion/ibge_ingestion.py

# 2. Transformação
cd dbt_project && dbt run && dbt test

# 3. Validação de qualidade
cd .. && python great_expectations/validate.py

# 4. Iniciar Airflow (roda tudo automaticamente todo dia às 6h)
export AIRFLOW_HOME=$(pwd)/airflow
airflow db migrate
airflow standalone
```

---

## 📊 Modelos dbt

### Camada Staging
`stg_ibge_population` — Dados brutos do IBGE limpos e padronizados
- Renomeação de colunas para nomes legíveis
- Filtragem de linhas inválidas
- Tipagem correta dos campos

### Camada Marts
`mart_populacao_estados` — Agregação por estado
- Total de municípios por estado
- Soma, média e máximo de valores
- Ordenado por relevância

---

## 🔔 Alertas no Slack

O bot **PipelineSentinelBot** notifica automaticamente:

- ✅ Pipeline concluído com sucesso (com resumo de cada etapa)
- ❌ Falha em qualquer task (com stack trace do erro)

---

## 🗂️ Fonte de Dados

| API | Dados | URL |
|-----|-------|-----|
| SIDRA/IBGE | Indicadores municipais brasileiros | [apisidra.ibge.gov.br](https://apisidra.ibge.gov.br/) |

---

## 👤 Autor

**Renan Torres**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Renan_Torres-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/renan-torres-121a06106/)
[![GitHub](https://img.shields.io/badge/GitHub-renantorres0-181717?style=flat-square&logo=github)](https://github.com/renantorres0)

---

## 📄 Licença

MIT License — sinta-se livre para usar, adaptar e contribuir.
