# Inmoser Service Order - Documentación técnica

## Alcance
Módulo Odoo 17 CE para gestión de órdenes de servicio técnico: equipos, técnicos, refacciones, aprobación cliente y generación de factura.

## Modelos principales
| Modelo | Descripción |
|--------|-------------|
| `inmoser.service.order` | Cabecera de la orden |
| `inmoser.service.equipment` | Equipos de cliente |
| `inmoser.service.type` | Tipos de servicio |
| `inmoser.service.order.refaction.line` | Líneas de refacción |

## Estados de la orden
1. **Borrador** → 2. **Asignado** → 3. **En proceso** → 4. **Pendiente aprobación** → 5. **Aceptado** → 6. **Realizado** / **Cancelado**

## Dependencias Odoo
`base`, `mail`, `portal`, `website`, `hr`, `account`, `stock`, `sale`, `purchase`, `project`, `crm`

## Instalación rápida (Docker)
Ver script `run-docker.sh` en raíz del proyecto.

## Tests
`./odoo-bin -c odoo.conf -d testdb --test-enable --stop-after-init -i inmoser_service_order`
