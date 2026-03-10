import great_expectations as gx
import os
from dotenv import load_dotenv

load_dotenv()

def run_validation():
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

    suite = context.suites.add(
        gx.ExpectationSuite(name="ibge_population_suite")
    )

    # 1. Completude
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="municipio_codigo")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="valor")
    )

    # 2. Contagem de linhas esperada
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=5000, max_value=50000)
    )

    # 3. Valores esperados na coluna nivel_territorial
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="nivel_territorial",
            value_set=["Município"]
        )
    )

    # 4. Coluna municipio_codigo deve ter 7 caracteres
    suite.add_expectation(
        gx.expectations.ExpectColumnValueLengthsToEqual(
            column="municipio_codigo",
            value=7
        )
    )

    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="ibge_validation",
            data=batch_definition,
            suite=suite
        )
    )

    results = validation_definition.run()

    print("\n=== RESULTADO DA VALIDAÇÃO ===")
    print(f"Status: {'✅ SUCESSO' if results.success else '❌ FALHA'}")
    for result in results.results:
        status = "✅" if result.success else "❌"
        print(f"  {status} {result.expectation_config.type}")

    return results.success

if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)