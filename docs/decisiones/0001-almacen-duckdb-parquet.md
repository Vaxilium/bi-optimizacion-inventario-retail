# ADR 0001: DuckDB + Parquet como almacén analítico local

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

El proyecto corre en un equipo con recursos limitados (16 GB de RAM) y necesita procesar
~3 millones de filas de ventas diarias más inventario, compras y dimensiones. Un motor
cliente-servidor tradicional (PostgreSQL, SQL Server) agrega instalación, administración
y consumo de memoria que no aportan al objetivo analítico.

## Decisión

Usar **DuckDB** como motor SQL embebido y **Parquet** como formato columnar de persistencia
para las capas crudo, staging, núcleo y marts. Las consultas analíticas se ejecutan en SQL
sobre DuckDB; los scripts Python solo orquestan y generan los datos sintéticos.

## Consecuencias

- Cero administración de servidor; todo corre en proceso.
- Lectura columnar rápida con proyección y filtros pushdown sobre Parquet.
- El repositorio se mantiene liviano: los Parquet se ignoran en git y se regeneran con `make todo`.
- Limitación: sin concurrencia multiusuario; aceptable para un proyecto de portafolio reproducible.
