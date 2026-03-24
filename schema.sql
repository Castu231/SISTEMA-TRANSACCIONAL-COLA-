PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS vehiculos (
    id_vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT NOT NULL UNIQUE,
    capacidad_tanque REAL NOT NULL,
    nivel_actual REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cola (
    id_cola INTEGER PRIMARY KEY AUTOINCREMENT,
    id_vehiculo INTEGER NOT NULL,
    hora_llegada TEXT NOT NULL,
    cantidad_solicitada REAL NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('esperando', 'en servicio', 'finalizado')),
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo)
);

CREATE TABLE IF NOT EXISTS bombas (
    id_bomba INTEGER PRIMARY KEY AUTOINCREMENT,
    estado TEXT NOT NULL CHECK (estado IN ('libre', 'ocupada')),
    velocidad_litro_segundo REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_vehiculo INTEGER NOT NULL,
    id_bomba INTEGER NOT NULL,
    litros_suministrados REAL NOT NULL,
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT NOT NULL,
    tiempo_espera INTEGER NOT NULL,
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
    FOREIGN KEY (id_bomba) REFERENCES bombas(id_bomba)
);

INSERT INTO bombas (estado, velocidad_litro_segundo)
SELECT 'libre', 0.5
WHERE NOT EXISTS (SELECT 1 FROM bombas WHERE id_bomba = 1);

INSERT INTO bombas (estado, velocidad_litro_segundo)
SELECT 'libre', 0.5
WHERE NOT EXISTS (SELECT 1 FROM bombas WHERE id_bomba = 2);

INSERT INTO bombas (estado, velocidad_litro_segundo)
SELECT 'libre', 0.5
WHERE NOT EXISTS (SELECT 1 FROM bombas WHERE id_bomba = 3);

INSERT INTO bombas (estado, velocidad_litro_segundo)
SELECT 'libre', 0.5
WHERE NOT EXISTS (SELECT 1 FROM bombas WHERE id_bomba = 4);

INSERT INTO bombas (estado, velocidad_litro_segundo)
SELECT 'libre', 0.5
WHERE NOT EXISTS (SELECT 1 FROM bombas WHERE id_bomba = 5);
