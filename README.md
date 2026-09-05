# Wallbit — Growth Challenge

Experimento A/B sobre la pantalla de ingreso de dinero: variante A muestra
la lista completa de métodos, variante B muestra un método recomendado
según el país del usuario con el resto colapsado detrás de "ver otras
opciones". Incluye la asignación a variante, el tracking del funnel, la
recepción idempotente de los webhooks del proveedor de pagos, y la lectura
del resultado.

Las decisiones detrás de cada pieza (por qué el diseño es así, qué quedó
afuera y por qué, cómo se lee el resultado) están en
[`ENTREGA.md`](ENTREGA.md).

## Stack

- **Backend:** Django + Django REST Framework + Postgres
- **Frontend:** Next.js
- Todo corre con **Docker Compose** — no hace falta instalar Python ni
  Node localmente, salvo para correr el simulador del proveedor de pagos.

## Requisitos

- Docker (con Docker Compose)
- Python 3.8+ (solo para `simulator/simulate_provider.py`, que corre fuera
  de Docker)

## Cómo correrlo

Desde un clon limpio del repo:

```bash
# 1. Variables de entorno del backend (el valor de ejemplo ya alcanza para correr local)
cp backend/.env.example backend/.env

# 2. Levantar todo: Postgres, backend (Django) y frontend (Next.js)
#    El backend migra, carga data/*.json y backdatea visitas simuladas
#    (simulate_visits) automáticamente en cada arranque — no hace falta
#    correr nada a mano.
docker compose up -d --build

# 3. Simular los webhooks del proveedor de pagos (fuera de Docker, tal
#    como lo corre el enunciado original). Con esto se completan los
#    depósitos y el resultado del experimento deja de estar vacío.
python3 simulator/simulate_provider.py --url http://localhost:8000
```

Con eso arriba:

| URL | Qué es |
|---|---|
| `http://localhost:3000` | Home — para elegir un usuario |
| `http://localhost:3000/users` | Lista buscable de usuarios (para no tener que abrir `data/users.json` a mano) |
| `http://localhost:3000/funding-screen?user_id=usr_000001` | La pantalla de fondeo (variante A o B según el usuario) |
| `http://localhost:3000/results` | El resultado del experimento |

Para bajar todo: `docker compose down` (agregá `-v` si además querés
borrar los datos de Postgres y arrancar de cero).

El simulador se puede correr las veces que haga falta — todo el
procesamiento de webhooks es idempotente, así que correrlo dos veces no
duplica ni cambia el resultado.

Para inspeccionar los datos crudos desde el admin de Django (opcional, no
viene con usuario creado):

```bash
docker compose exec backend python manage.py createsuperuser
```

y entrar a `http://localhost:8000/admin`.

## Estructura del repo

```
backend/        Django + DRF — modelos, endpoints, management commands
frontend/       Next.js — pantalla de fondeo, resultados, lista de usuarios
data/           Datasets del challenge (users, funding_methods, depósitos históricos)
simulator/      Simulador del proveedor de pagos (provisto por el challenge)
ENTREGA.md      Decisiones, resultado del experimento, qué quedó afuera
PLAN.md         Notas de diseño y verificaciones más profundas
```
