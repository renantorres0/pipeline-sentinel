from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/home/renantorres/projetos/pipeline_sentinel')
os.environ.setdefault('AIRFLOW_HOME', '/home/renantorres/projetos/pipeline_sentinel/airflow')

from ingestion.ibge_ingestion import fetch_ibge_population, save_to_database
from notifications.slack_notifier import send_slack_alert

def on_failure_callback(context):
    task_id = context['task_instance'].task_id
    exception = context.get('exception')
    send_slack_alert(
        f"❌ FALHA na task: *{task_id}*",
        level='ERROR',
        exception=exception
    )

default_args = {
    'owner': 'pipeline_sentinel',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': on_failure_callback,
}

def ingest_data():
    df = fetch_ibge_population()
    save_to_database(df, 'ibge_population_raw')
    return f"Ingestão concluída: {len(df)} linhas"

def run_ge_validation():
    import great_expectations as gx
    from dotenv import load_dotenv
    load_dotenv('/home/renantorres/projetos/pipeline_sentinel/.env')

    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_postgres(
        name="postgres_datasource",
        connection_string=os.getenv("DATABASE_URL")
    )
    asset = datasource.add_table_asset(
        name="ibge_population_raw",
        table_name="ibge_population_raw",
        schema_name="raw"
    )
    batch_definition = asset.add_batch_definition_whole_table("full_table")
    suite = context.suites.add(gx.ExpectationSuite(name="ibge_suite"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="municipio_codigo"))
    suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=5000, max_value=50000))
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToEqual(column="municipio_codigo", value=7))

    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(name="ibge_validation", data=batch_definition, suite=suite)
    )
    results = validation_definition.run()

    if not results.success:
        raise ValueError("Validação GE falhou!")

    print(f"✅ Validação OK — {results.statistics['successful_expectations']}/{results.statistics['evaluated_expectations']} checks passaram")

def notify_success():
    send_slack_alert(
        "✅ Pipeline Sentinel concluído com sucesso!\n"
        "• Ingestão IBGE: OK\n"
        "• dbt run: OK\n"
        "• dbt test: OK\n"
        "• Great Expectations: OK",
        level='SUCCESS'
    )

with DAG(
    dag_id='data_quality_pipeline',
    default_args=default_args,
    schedule='0 6 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['quality', 'ibge'],
    description='Pipeline completo: ingestão → dbt → Great Expectations → Slack'
) as dag:

    ingest = PythonOperator(
        task_id='ingest_ibge_data',
        python_callable=ingest_data
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /home/renantorres/projetos/pipeline_sentinel/dbt_project && /home/renantorres/projetos/pipeline_sentinel/venv/bin/dbt run'
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /home/renantorres/projetos/pipeline_sentinel/dbt_project && /home/renantorres/projetos/pipeline_sentinel/venv/bin/dbt test'
    )

    ge_validate = PythonOperator(
        task_id='great_expectations_validate',
        python_callable=run_ge_validation
    )

    notify = PythonOperator(
        task_id='notify_success',
        python_callable=notify_success
    )

    ingest >> dbt_run >> dbt_test >> ge_validate >> notify