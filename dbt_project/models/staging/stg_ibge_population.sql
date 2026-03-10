{{ config(materialized='view') }}

SELECT
    municipio_codigo,
    municipio_nome,
    variavel,
    ano,
    CASE
        WHEN valor = '..' OR valor IS NULL THEN NULL
        ELSE CAST(valor AS FLOAT)
    END                             AS valor,
    unidade_medida,
    ingested_at,
    source
FROM {{ source('raw', 'ibge_population_raw') }}
WHERE municipio_codigo IS NOT NULL
    AND municipio_codigo != ''