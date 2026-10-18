-- Capa nucleo: modelo en estrella materializado como Parquet.
-- Hechos con clave de fecha entera y dimensiones con claves naturales.

CREATE OR REPLACE VIEW dim_fecha AS
SELECT * FROM stg_dim_fecha;

CREATE OR REPLACE VIEW dim_producto AS
SELECT * FROM stg_dim_producto;

CREATE OR REPLACE VIEW dim_sucursal AS
SELECT * FROM stg_dim_sucursal;

CREATE OR REPLACE VIEW dim_proveedor AS
SELECT * FROM stg_dim_proveedor;

CREATE OR REPLACE VIEW dim_promociones AS
SELECT * FROM stg_promociones;

CREATE OR REPLACE VIEW nucleo_hechos_ventas AS
SELECT
    v.fecha,
    v.fecha_id,
    v.sucursal_id,
    v.producto_id,
    v.venta_unidades,
    v.precio_unitario,
    v.venta_valorizada,
    v.costo_total,
    v.margen_bruto,
    v.en_promocion,
    v.indicador_quiebre
FROM stg_ventas v
JOIN dim_fecha f USING (fecha)
JOIN dim_sucursal s USING (sucursal_id)
JOIN dim_producto p USING (producto_id);

CREATE OR REPLACE VIEW nucleo_hechos_inventario AS
SELECT
    i.fecha,
    i.fecha_id,
    i.sucursal_id,
    i.producto_id,
    i.stock_cierre_unidades,
    i.stock_valorizado,
    i.merma_unidades,
    i.merma_valorizada
FROM stg_inventario i
JOIN dim_fecha f USING (fecha)
JOIN dim_sucursal s USING (sucursal_id)
JOIN dim_producto p USING (producto_id);

CREATE OR REPLACE VIEW nucleo_hechos_compras AS
SELECT
    c.fecha_pedido,
    c.fecha_pedido_id,
    c.sucursal_id,
    c.producto_id,
    c.proveedor_id,
    c.unidades_pedido,
    c.lead_time_dias,
    c.fecha_recepcion,
    c.estado,
    c.unidades_recibidas,
    c.lead_time_imputado
FROM stg_compras c
JOIN dim_fecha f ON f.fecha = c.fecha_pedido
JOIN dim_sucursal s USING (sucursal_id)
JOIN dim_proveedor prv USING (proveedor_id);
