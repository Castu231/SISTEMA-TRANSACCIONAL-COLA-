# Entrega del Taller

## Tema

Diseno de un sistema transaccional de colas para simular la tanqueada de automoviles en una estacion de servicio.

## Objetivo cumplido

El proyecto permite:

- Registrar la llegada de vehiculos.
- Agregarlos a una cola de espera.
- Asignar automaticamente una bomba disponible.
- Calcular el tiempo de espera.
- Calcular el tiempo de servicio segun la cantidad solicitada.
- Mostrar el historial de transacciones.

## Componentes entregados

- Aplicacion web funcional en Flask.
- Base de datos SQLite.
- Script SQL del modelo relacional.
- Interfaz web para operacion del sistema.
- Documentacion tecnica y de ejecucion.
- Archivos de preparacion para despliegue en GitHub y Render.

## Logica aplicada

La simulacion usa una cola FIFO. Cuando llega un vehiculo:

1. Se valida la informacion del tanque.
2. Se registra el vehiculo.
3. Se crea un turno en la tabla `cola`.
4. El sistema revisa si existe una bomba libre.
5. Si hay una bomba libre, crea la transaccion y cambia el estado a `en servicio`.
6. Si no hay bomba libre, el vehiculo permanece `esperando`.
7. Cuando el tiempo de servicio termina, la bomba se libera y el turno pasa a `finalizado`.

## Formula utilizada

```text
Tiempo de servicio = litros solicitados / velocidad de la bomba
```

Ejemplo del sistema:

```text
20 litros / 0.5 litros por segundo = 40 segundos
```

