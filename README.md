# Sistema Transaccional de Colas - Tanqueada de Automoviles

Aplicacion web en Python y SQLite para simular la atencion de vehiculos en una estacion de servicio. El sistema registra la llegada de automoviles, los agrega a una cola, asigna bombas disponibles y calcula tiempos de espera y servicio para cada transaccion.

## Caracteristicas

- Registro de vehiculos con placa, capacidad, nivel actual y cantidad solicitada.
- Cola de espera con estados `esperando`, `en servicio` y `finalizado`.
- Varias bombas de gasolina funcionando como servidores del sistema.
- Calculo automatico del tiempo de servicio con la formula:


