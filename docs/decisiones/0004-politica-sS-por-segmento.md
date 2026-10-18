# ADR 0004: Política de reposición (s, S) con nivel de servicio por segmento

- **Fecha:** 15/01/2026
- **Estado:** Aceptada

## Contexto

La política actual (revisión semanal, media móvil de 4 semanas y días de seguridad fijos)
no distingue entre productos de alta y baja rotación, ni entre demanda estable e intermitente.
Eso produce quiebres en productos A y exceso de inventario en productos C.

## Decisión

Adoptar una política **(s, S)** de revisión periódica con parámetros calculados por segmento ABC:

- `s = d̄·L + SS` (punto de reposición), con `SS = z · sqrt(L·σd² + d̄²·σL²)`.
- `S = s + EOQ` acotado por vida útil en perecederos.
- `z` según nivel de servicio objetivo: A = 97,5%, B = 95%, C = 92%.
- En perecederos, `S` se limita a la demanda esperada durante la vida útil para controlar merma.

## Consecuencias

- Menos quiebres donde el margen es alto y menos capital donde la rotación es baja.
- La política es explicable a los jefes de sucursal (dos números por producto) y auditable.
- Requiere recalcular parámetros mensualmente con el pronóstico vigente.
