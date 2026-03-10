import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

def fetch_ibge_population(table_id: str = '1301') -> pd.DataFrame:
    print(f"Buscando dados da tabela IBGE {table_id}...")
    url = f'https://apisidra.ibge.gov.br/values/t/{table_id}/n6/all/v/all/p/last%201'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Dados já vêm com chaves curtas (D1C, D1N, V, etc.)
    df = pd.DataFrame(data[1:])

    print(f"Total de linhas: {len(df)}")
    print(f"Colunas: {list(df.columns)}")

    # Renomear para nomes legíveis
    df = df.rename(columns={
        'NC': 'nivel_territorial_codigo',
        'NN': 'nivel_territorial',
        'MC': 'unidade_medida_codigo',
        'MN': 'unidade_medida',
        'V':  'valor',
        'D1C': 'municipio_codigo',
        'D1N': 'municipio_nome',
        'D2C': 'variavel_codigo',
        'D2N': 'variavel',
        'D3C': 'ano_codigo',
        'D3N': 'ano'
    })

    # Filtrar linhas válidas
    df = df[df['municipio_codigo'].notna()]
    df = df[df['municipio_codigo'].astype(str).str.strip() != '']

    df['ingested_at'] = datetime.now(timezone.utc)
    df['source'] = 'ibge_sidra'
    print(f"Linhas válidas: {len(df)}")
    return df

def save_to_database(df: pd.DataFrame, table_name: str):
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text(f"DROP TABLE IF EXISTS raw.{table_name} CASCADE"))
        conn.commit()
    df.to_sql(table_name, engine, schema='raw', if_exists='replace', index=False)
    print(f"Salvo: {len(df)} linhas em raw.{table_name}")

if __name__ == '__main__':
    df = fetch_ibge_population()
    save_to_database(df, 'ibge_population_raw')
    print("Ingestão concluída!")