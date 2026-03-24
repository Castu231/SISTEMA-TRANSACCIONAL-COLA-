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
- Escoger entre gasolina `Corriente` y `Extra`.
- Calcular el costo total de la tanqueada segun el precio actualizado por galon.
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
3. Se consulta el precio actual del combustible elegido.
4. Se crea un turno en la tabla `cola`.
5. El sistema revisa si existe una bomba libre.
6. Si hay una bomba libre, crea la transaccion y cambia el estado a `en servicio`.
7. Si no hay bomba libre, el vehiculo permanece `esperando`.
8. Cuando el tiempo de servicio termina, la bomba se libera y el turno pasa a `finalizado`.

## Formula utilizada

```text
Tiempo de servicio = (galones solicitados x 3.78541) / velocidad de la bomba
```

Ejemplo del sistema:

```text
10 galones x 3.78541 = 37.8541 litros
37.8541 / 0.5 = 75.7 segundos
```

