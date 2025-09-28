# Lista de Verificación de Pruebas

Este documento proporciona una lista de verificación para validar la funcionalidad del módulo de Órdenes de Servicio.

## Pruebas de Orden de Servicio

- [ ] Crear una orden de servicio
  - [ ] Con campos obligatorios únicamente
  - [ ] Con todos los campos
  - [ ] Con líneas de refacción
  - [ ] Con equipo
  - [ ] Sin equipo (si no es requerido)
  - [ ] Con técnico
  - [ ] Sin técnico (si no es requerido)

- [ ] Flujo de trabajo de orden de servicio
  - [ ] Borrador a Programada
  - [ ] Programada a En Progreso
  - [ ] En Progreso a Completada
  - [ ] Cancelar en cualquier estado

- [ ] Acciones de orden de servicio
  - [ ] Programar
  - [ ] Iniciar
  - [ ] Completar (con asistente)
  - [ ] Cancelar
  - [ ] Reprogramar (con asistente)
  - [ ] Crear factura
  - [ ] Imprimir orden de servicio
  - [ ] Imprimir certificado de servicio

## Pruebas de Equipo

- [ ] Crear equipo
  - [ ] Con campos obligatorios únicamente
  - [ ] Con todos los campos
  - [ ] Con información de garantía
  - [ ] Con intervalo de servicio

- [ ] Acciones de equipo
  - [ ] Programar servicio
  - [ ] Ver historial de servicio
  - [ ] Imprimir historial de equipo

- [ ] Código QR de equipo
  - [ ] Generar código QR
  - [ ] Escanear código QR

## Pruebas de Tipo de Servicio

- [ ] Crear tipo de servicio
  - [ ] Con campos obligatorios únicamente
  - [ ] Con todos los campos
  - [ ] Con producto relacionado

- [ ] Acciones de tipo de servicio
  - [ ] Ver órdenes de servicio

## Pruebas de Integración

- [ ] Integración contable
  - [ ] Crear factura desde orden de servicio
  - [ ] Crear factura de proveedor para línea de refacción

- [ ] Integración de RRHH
  - [ ] Asignar técnico a orden de servicio
  - [ ] Verificar disponibilidad de técnico
  - [ ] Programar orden de servicio
  - [ ] Encontrar siguiente espacio disponible

- [ ] Integración de inventario
  - [ ] Verificar disponibilidad de producto
  - [ ] Reservar producto para servicio
  - [ ] Consumir producto para servicio
  - [ ] Devolver producto desde servicio

## Pruebas de Lógica de Negocio

- [ ] Validar orden de servicio
  - [ ] Orden de servicio válida
  - [ ] Campos obligatorios faltantes
  - [ ] Desajuste de propietario de equipo

- [ ] Calcular duración de servicio
  - [ ] Duración base
  - [ ] Con líneas de refacción
  - [ ] Con factor de prioridad

- [ ] Verificar conflictos de orden de servicio
  - [ ] Conflicto de técnico
  - [ ] Conflicto de equipo

## Pruebas de Portal

- [ ] Portal de cliente
  - [ ] Ver órdenes de servicio
  - [ ] Ver detalles de orden de servicio
  - [ ] Aceptar orden de servicio
  - [ ] Cancelar orden de servicio

## Pruebas de API

- [ ] API de estado de orden de servicio
  - [ ] Obtener estado de orden de servicio
  - [ ] Actualizar estado de orden de servicio

## Pruebas de Rendimiento

- [ ] Rendimiento de creación de orden de servicio
- [ ] Rendimiento de flujo de trabajo de orden de servicio
- [ ] Rendimiento de lista de órdenes de servicio
