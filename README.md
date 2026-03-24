# Sistema Transaccional de Colas - Tanqueada de Automoviles

Aplicacion web en Python y SQLite para simular la atencion de vehiculos en una estacion de servicio. El sistema registra la llegada de automoviles, los agrega a una cola, asigna bombas disponibles y calcula tiempos de espera, servicio y costo total para cada transaccion.

## Caracteristicas

- Registro de vehiculos con placa, capacidad, nivel actual y cantidad solicitada en galones.
- Seleccion de combustible entre `Corriente` y `Extra`.
- Cola de espera con estados `esperando`, `en servicio` y `finalizado`.
- Varias bombas de gasolina funcionando como servidores del sistema.
- Consulta de precios actualizados por galon desde una fuente en linea de Colombia.
- Calculo automatico del tiempo de servicio con la formula:

```text
tiempo de servicio = (galones solicitados x 3.78541) / velocidad de la bomba
```

- Historial completo de transacciones.
- API interna para consultar precios: `/api/precios-combustible`

## Modelo de Base de Datos

### Tabla `vehiculos`

| Campo | Tipo | Descripcion |
|---|---|---|
| `id_vehiculo` | INTEGER | Identificador unico |
| `placa` | TEXT | Placa del automovil |
| `capacidad_tanque` | REAL | Capacidad total en litros |
| `nivel_actual` | REAL | Nivel actual antes del servicio |

### Tabla `cola`

| Campo | Tipo | Descripcion |
|---|---|---|
| `id_cola` | INTEGER | Identificador del turno |
| `id_vehiculo` | INTEGER | Relacion con el vehiculo |
| `hora_llegada` | TEXT | Fecha y hora de llegada |
| `cantidad_solicitada` | REAL | Campo legado compatible |
| `galones_solicitados` | REAL | Galones requeridos |
| `tipo_combustible` | TEXT | `Corriente` o `Extra` |
| `precio_galon` | REAL | Precio tomado al crear la solicitud |
| `costo_estimado` | REAL | Valor esperado de la tanqueada |
| `estado` | TEXT | `esperando`, `en servicio`, `finalizado` |

### Tabla `bombas`

| Campo | Tipo | Descripcion |
|---|---|---|
| `id_bomba` | INTEGER | Identificador de la bomba |
| `estado` | TEXT | `libre` u `ocupada` |
| `velocidad_litro_segundo` | REAL | Litros suministrados por segundo |

### Tabla `transacciones`

| Campo | Tipo | Descripcion |
|---|---|---|
| `id_transaccion` | INTEGER | Identificador del evento |
| `id_vehiculo` | INTEGER | Vehiculo atendido |
| `id_bomba` | INTEGER | Bomba asignada |
| `litros_suministrados` | REAL | Cantidad servida convertida a litros |
| `galones_suministrados` | REAL | Cantidad servida en galones |
| `combustible` | TEXT | Tipo de gasolina |
| `precio_galon` | REAL | Precio aplicado por galon |
| `costo_total` | REAL | Valor total cobrado |
| `fuente_precio` | TEXT | URL de consulta del precio |
| `fecha_precio` | TEXT | Momento de consulta del precio |
| `hora_inicio` | TEXT | Inicio del tanqueo |
| `hora_fin` | TEXT | Fin del tanqueo |
| `tiempo_espera` | INTEGER | Espera en segundos |

### Tabla `precios_combustible`

| Campo | Tipo | Descripcion |
|---|---|---|
| `tipo_combustible` | TEXT | `Corriente` o `Extra` |
| `precio_galon` | REAL | Precio actual por galon |
| `fuente` | TEXT | Origen del dato |
| `actualizado_en` | TEXT | Fecha y hora de cache |

## Algoritmo del Sistema

1. Llega un vehiculo y se valida que la cantidad solicitada en galones no supere el espacio disponible.
2. El vehiculo se registra o actualiza en la tabla `vehiculos`.
3. El sistema consulta el precio actual del combustible seleccionado.
4. Se agrega un nuevo turno a la tabla `cola`.
5. El sistema sincroniza estados:
   - Marca transacciones terminadas.
   - Libera bombas disponibles.
   - Toma los vehiculos en espera por orden FIFO.
   - Asigna una bomba libre.
   - Convierte galones a litros para calcular el tiempo de servicio.
   - Calcula el costo total de la transaccion.
   - Crea la transaccion.
6. La interfaz muestra cola, bombas, precios y transacciones.

## Ejecucion

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicacion:

```bash
python app.py
```

3. Abrir en el navegador:

```text
http://127.0.0.1:5000
```

## Preparado para GitHub y despliegue

El proyecto ya incluye archivos para subirlo a GitHub y desplegarlo en Render:

- `.gitignore`
- `Procfile`
- `render.yaml`
- `gunicorn` en `requirements.txt`

### Pasos sugeridos

1. Crear un repositorio en GitHub.
2. Subir el contenido del proyecto.
3. En Render, crear un nuevo `Web Service` o `Blueprint` desde el repositorio.
4. Usar:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

### Nota importante sobre la base de datos

Actualmente el proyecto usa SQLite con `gasolinera.db`. Esto funciona bien para pruebas y demostracion, pero en un despliegue web los datos pueden no ser permanentes entre reinicios del servicio. Para una version mas robusta en produccion, lo recomendable es migrar a PostgreSQL.

## Configuracion inicial de la simulacion

- Se crean 3 bombas automaticamente.
- Se crean 5 bombas automaticamente.
- Cada bomba arranca con velocidad `0.5` litros por segundo.
- Esa velocidad equivale a `1 litro cada 2 segundos`, igual al ejemplo del enunciado.
- Los precios se consultan desde `https://petroilsa.com/precios/` y se cachean localmente.

## Criterios cubiertos

- Diseno de base de datos.
- Implementacion de la cola.
- Calculo de tiempos de espera y servicio.
- Interfaz funcional.
- Documentacion del sistema.
