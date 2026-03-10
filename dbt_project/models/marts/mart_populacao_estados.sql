{{ config(materialized='table') }}

SELECT
    LEFT(municipio_codigo, 2)           AS estado_codigo,
    COUNT(DISTINCT municipio_codigo)    AS qtd_municipios,
    SUM(valor)                          AS valor_total,
    AVG(valor)                          AS valor_medio,
    MAX(valor)                          AS valor_maximo,
    variavel,
    ano
FROM {{ ref('stg_ibge_population') }}
WHERE valor IS NOT NULL
GROUP BY 1, 6, 7
ORDER BY valor_total DESC