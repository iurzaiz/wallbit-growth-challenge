# Entrega

---

## Cómo correrlo

Ver [`README.md`](README.md).
---

## Qué construí y qué dejé afuera

**Construí:**

- Backend Django + DRF: modelos (`User`, `FundingMethod`, `Deposit`,
  `ExperimentAssignment`, `WebhookEvent`, `TrackingEvent`), carga
  idempotente de los fixtures, asignación de variante determinística por
  hash, el endpoint de la pantalla de fondeo, el webhook idempotente y
  tolerante a desorden, el endpoint de tracking, el de resultado del
  experimento y uno de usuarios (paginado y buscable, para no tener que
  abrir el JSON a mano).
- `simulate_visits`: backdatea una visita a la pantalla para cada usuario
  del escenario, para que `assigned_at` refleje una exposición real y no
  el arranque del depósito (ver "El resultado" para el detalle).
- Frontend Next.js: la pantalla de fondeo en sus dos variantes (A: lista
  completa; B: recomendado + "ver otras opciones"), con datos mock de
  cuenta al elegir un método; la página de resultados; la página de
  usuarios buscable; manejo de errores en las tres (nada se queda colgado
  si el backend no responde).
- Docker Compose: para levantar con `docker compose up`. Migra, carga los
  datos y backdatea las visitas en cada arranque, sin pasos manuales.
  Deje solamente el comando de webhook aparte para respetar el enunciado.
  Esto lo agregue solamente para que sea simple levantar el proyecto.

**Dejé afuera, y por qué:**

El enunciado ya avisa que estas cuatro "casi seguro no entran" (y tuvo razon),
y que decidir qué queda afuera es parte de lo que evalúan. 
Las cuatro son features reales y buenas. Pero pesan más de lo que parece:

- **Significancia estadística**: sin esto, reportar "B convirtió mejor"
  sobre una muestra de 285 usuarios es tan confiable como tirar una
  moneda. Implementarlo bien (elegir el test correcto, manejar el caso de
  muestras chicas) es un tema en sí mismo.
  Esta es la que hubiese agregado.
- **Corte por país/método**: con 1200 usuarios repartidos en 10 países,
  cortar por país te deja con muestras de 100-150 personas cada una, por lo tanto,
  mucho más ruido todavía. Útil, pero necesitarías mucho más volumen para
  que signifique algo.
- **Kill switch**: es una feature operacional (poder apagar una variante
  en producción sin esperar un deploy), no algo que haga falta para ver
  el resultado de este experimento puntual. Esta es la que ultima que hubiese agregado.
- **Segundo experimento en paralelo**: podria haber sido util pero no
  me parecio algo que este experimento necesite para funcionar solo.

De las cuatro, la significancia estadística es la que más analicé,
justamente porque el resultado (A y B casi idénticos) me generó dudas y
quise entender si estaba bien medido antes de darlo por bueno (ver "El
resultado"). Lo hice de forma informal, sin ponerle el nombre técnico:
cuando comparé las dos formas de medir la ventana de conversión, la
alternativa que descarté (ventana anclada a una fecha fija para todos: 
todos los usuarios "entran" el mismo día, el 2026-08-01, fecha de arranque
del experimento, sin importar cuándo depositen después. 
Los 7 días se cuentan desde esa fecha única para todos) daba una diferencia
de 9 puntos entre A y B que resultó ser puro ruido de muestreo (lo verifiqué
razonando sobre el hash de asignación, no con un test formal). Eso es exactamente lo que un test
de significancia formalizaría con un número: esa diferencia de 9 puntos
tendría un p-valor alto, así que no habría que confiar en ella. Con 142 vs
143 usuarios y menos de un punto de diferencia, un test formal casi seguro
daría "no significativo" coincidiendo con lo que ya había concluido a ojo.
Aun así no lo formalicé (no corrí un z-test de proporciones de verdad): el
análisis razonado me alcanzaba para la duda puntual que tenía, y para hacerlo
formal me hubiera excedido en cuanto al tiempo. 
Aclaracion: por mi parte no hubiese tenido ningun problema en tomarme mas tiempo
de lo debido para realizar el challenge solo que me parecio mas correcto obedecer
el enunciado.

- Firma HMAC del webhook: el doc del proveedor dice que es opcional y no
  cambia el resultado del experimento. Pero es obligatorio en produccion.
- Un framework genérico para "varios experimentos": solo hay uno corriendo,
  armar algo configurable para eso me pareció sobreingeniería.
- Login/autenticación real: el enunciado dice que asumamos que ya sabemos
  quién es el usuario.
- Un gráfico en la página de resultados: lo agregué y después lo saqué.
  con solo dos barras casi idénticas no sumaba nada sobre la tabla.

**Si tuviera 4 horas más, lo próximo que haría:**

- Una vista que cruce `TrackingEvent` para mostrar el funnel completo
  (cuántos llegaron a cada escalón, por variante). El modelo ya está
  armado, falta la lectura.
- Tests automatizados para el estado del webhook (duplicado, desorden,
  fallback). Es la pieza más delicada de todo el sistema y hoy solo está
  verificada a mano y corriendo el simulador real.
- Algún criterio para filtrar quién entra al experimento según
  `kyc_status`. Hoy entra cualquiera, sin importar si el KYC está
  aprobado, pendiente o rechazado.

---

## Asignación de variantes

**Cómo se decide la variante:** `sha256(user_id)` par o impar → A o B. Es
determinística — el mismo `user_id` siempre da la misma variante, sin
necesidad de guardar nada para saber a qué grupo *le tocaría* ir. Evita
además cualquier condición de carrera si dos requests del mismo usuario
llegan casi al mismo tiempo (no hay un "tirar la moneda" que pueda dar
resultados distintos según cuál request gane la carrera).

**Cómo se vuelve pegajosa (sticky):** lo que sí se persiste es la fila
`ExperimentAssignment` (`user`, `variant`, `assigned_at`), creada la
primera vez que el usuario entra al experimento. No guarda la variante
porque haga falta para decidirla (eso ya lo resuelve el hash), la guarda
para saber **quién** está en el experimento y **desde cuándo**, que es lo
que necesita la ventana de conversión de 7 días.

**Cuándo se dispara la asignación:** en la primera visita real a
`GET /funding-screen?user_id=X`, no en un batch previo. Así se comporta
un experimento real: se asigna en el momento de exposición. Como
acá no hay login ni un frontend real generando tráfico orgánico, hay dos
caminos adicionales que terminan en la misma fila `ExperimentAssignment`:

- **Fallback del webhook:** si llega un `deposit.received`/`completed` de
  un usuario que nunca visitó la pantalla, se lo asigna ahí mismo, con
  `assigned_at = occurred_at` del evento. En producción real esto no
  debería pasar (no hay datos de cuenta para depositar sin haber pasado
  antes por la pantalla), pero cubre el caso de que el dataset de prueba
  incluya depósitos de usuarios que nunca "visitamos".
- **`simulate_visits`:** backdatea una visita simulada un rato antes (5 a
  180 minutos) del primer evento de cada usuario del escenario, para que
  la asignación refleje una exposición real y no el arranque del depósito,
  el detalle de por qué hace falta está en "El resultado".

Las tres rutas llaman al mismo `get_or_create`, así que da lo mismo por
cuál entre un usuario: la variante sale del mismo hash, y la fila solo se
crea una vez.

---

## Modelo de eventos

Un `TrackingEvent` por paso del funnel, con `user`, `event_name`, `variant`
(desnormalizado del lado del servidor al momento de guardar, evita un
join para cualquier corte por variante), `metadata` (JSON libre, para datos
puntuales del evento) y `occurred_at`.

| Evento | Quién lo dispara | Campos propios | Para qué sirve |
|---|---|---|---|
| `experiment_assigned` | Servidor, al crear la asignación (primera visita real, fallback del webhook, o `simulate_visits`) | — | Marca el punto de partida de cada usuario en el experimento; de acá sale la ventana de 7 días para leer conversión. |
| `funding_screen_viewed` | Servidor, en cada `GET /funding-screen` | — | Cuánta gente llega efectivamente a ver la pantalla. |
| `other_methods_expanded` | Cliente, en la práctica, solo aplica a variante B | — | Si el recorte de opciones molesta: ¿necesitan abrir "otras opciones" para encontrar lo que buscaban? |
| `method_selected` | Cliente, al elegir un método | `metadata.method_id` | Qué método termina eligiendo cada uno. Compara la elección "espontánea" (A) contra la "guiada" (B). |

**Por qué este esquema:** con solo el resultado final (convirtió o no) se
puede decir que una variante anda peor, pero no *por qué*. Con estos
cuatro eventos se reconstruye el funnel completo: asignado → vio la
pantalla → (en B: exploró otras opciones o no) → eligió un método →
depositó. y se puede ver en qué escalón se cae la gente. Preguntas que
quedan respondidas: ¿la pantalla siquiera se ve? ¿en B, la gente confía en
el recomendado o casi todos terminan abriendo "otras opciones" (lo que
diría que la recomendación no convence)? ¿empuja B a la gente hacia un
método que no habría elegido por su cuenta?

La conversión (`deposit.completed`) se lee de `Deposit`, no de un evento de
tracking aparte, una sola fuente de verdad sobre si alguien depositó, en
vez de arriesgarse a que las dos se desincronicen.

`experiment_assigned` y `funding_screen_viewed` se generan del lado del
servidor a propósito, nunca del cliente. El primero define a qué grupo
pertenece cada usuario para todo el análisis, y no puede depender de que el
frontend dispare algo correctamente.

Aparte de estos cuatro hay un `WebhookEvent`, pero no es tracking de
usuario: es el log crudo de cada webhook del proveedor que llega, para
poder auditar la idempotencia si algo se ve raro. No se usa en ningún
cálculo del experimento.

---

## El resultado

**¿Cuántos usuarios convirtieron en cada variante?**

| Variante | Usuarios en el experimento | Convertidos | Tasa |
|---|---|---|---|
| A (control) | 142 | 127 | 89.4% |
| B (recomendado) | 143 | 127 | 88.8% |

**¿Cómo definiste "convertido"?** Primer depósito acreditado
(`Deposit.status = completed`) dentro de los 7 días desde que el usuario fue
asignado a su variante (primera visita a la pantalla de fondeo), no desde
su fecha de alta; el porqué está en "Supuestos y decisiones de criterio".
Lo que dejé afuera del conteo: los `deposit.failed` no restan ni bloquean
nada, si el usuario reintentó y esa segunda transferencia se completó
dentro de la ventana, cuenta igual (un reintento genera un `deposit_id`
nuevo, según `PROVIDER.md`).

**Por qué dudé del resultado, y cómo lo verifiqué de otra forma**

A y B dan casi idénticos (89.4% vs 88.8%, menos de un punto de diferencia)
y eso me generó sospecha, es el tipo de resultado que uno espera cuando
algo está mal medido, no cuando el experimento simplemente no encontró
efecto. Antes de asumir que era la conclusión correcta, hice dos
verificaciones:

1. **¿Es un bug en el cómputo?** Recalculé el resultado con una query SQL
   cruda contra la base, por fuera del código de `results.py`, y comparé
   número por número contra lo que devuelve `GET /experiment/results`.
   Coincidieron exacto en ambos lados, entonces se descarta un
   error de cómputo.

2. **¿Es un artefacto de cómo elegí medir la ventana de conversión?**
    **Qué hubiera pasado con la otra opción (asignar a todos el 2026-08-01 fijo)**

    La probe para comparar. Da esto:

    | Variante | Asignados | Convertidos | Tasa |
    |---|---|---|---|
    | A | 142 | 42 | 29.6% |
    | B | 143 | 29 | 20.3% |

    Parece un hallazgo: "B convierte 9 puntos menos", pero es un espejismo. Con
    fecha fija, solo 71 de los 254 depósitos completados caen dentro de los
    primeros 7 días de agosto; los otros 183 son gente que si depositó,
    pero más tarde en el mes, y quedan contados como "no convertido" solo
    porque el calendario los agarra tarde, no porque la pantalla les haya
    fallado. 
  
   Como ya sabía que "medir distinto" puede inventar una
   diferencia falsa, que la medición correcta no muestre ninguna es más
   convincente, no menos: probé que mi forma de medir es capaz de mostrar
   una diferencia cuando aparece, y con la medición
   correcta no aparece ninguna.

   Conclusión: `scenario.json` es un dataset fijo, generado de antemano,
   que no sabe qué variante le tocó a cada usuario. No hay ningún mecanismo
   en los datos que haga que alguien deposite distinto según lo que vio en
   la pantalla. Con este dataset, la respuesta correcta es "no hay
   evidencia de que la variante cambie el comportamiento", forzarle una
   lectura distinta hubiera sido el error real acá, no el resultado en sí.

**Por qué agregué `simulate_visits`**

La asignación a variante ocurre en la primera visita a `/funding-screen`.
Corriendo el experimento de punta a punta sin ese comando, encontré que si
nadie visita la pantalla antes de que lleguen los webhooks (que es lo que
pasa en una corrida de prueba sin frontend real detrás), el 100% de las
asignaciones terminan pasando por el fallback del webhook, y ahí
`assigned_at` queda pegado al momento del primer webhook, casi en
simultáneo con el arranque del depósito. La ventana de "7 días desde la
asignación" empieza cuando el depósito ya estaba en curso, así que casi
cualquiera que depositó "convierte": eso no mide el efecto de la variante,
mide si la gente que ya estaba depositando siguió depositando.

`simulate_visits` backdatea una visita a la pantalla para cada usuario del
escenario, un rato antes (5 a 180 minutos) de su primer evento, simulando
que vio la pantalla, copió los datos y después transfirió, así
`assigned_at` refleja una exposición real, no el arranque del depósito. Un
detalle honesto: agregarlo no cambió los números finales en este dataset
puntual (el margen real entre depósito recibido y liquidado nunca supera
las 40 horas, muy por debajo de la
ventana de 7 días), pero sigue siendo la forma correcta de anclar la
ventana, y sin él no podría defender que `assigned_at` significa lo que
dice significar.

**¿Lanzarías la variante B a todos los usuarios? ¿Por qué?**

No, con este resultado no. No hay evidencia de que B convierta mejor (ni
peor) que A, la diferencia observada (1.2 puntos) es perfectamente
consistente con ruido de muestreo sobre ~288 usuarios, no con un efecto
real. Lanzar B a todos en base a esto sería una decisión sin sustento, lo
que corresponde es seguir corriendo el experimento con usuarios reales
(no con datos sintéticos que no tienen el efecto codificado) hasta juntar
señal suficiente o revisar el diseño de B si hay motivos para creer que el
recorte de opciones ayuda pero este dataset de prueba no lo puede mostrar.

---

## Supuestos y decisiones de criterio

Todo lo que el enunciado no aclaraba y resolviste vos.

- **Stack:** Django + DRF (backend), Next.js (frontend), Postgres, Docker
  Compose para levantar todo local. El enunciado no lo evalúa, pero se eligió
  para que el código se lea parecido al stack real de Wallbit (Laravel/RN).

- **Población del experimento:** entra cualquier usuario que llegue a la
  pantalla de fondeo durante la ventana del experimento (agosto 2026), sin
  importar su fecha de alta. Por qué la mayoría de los usuarios que
  efectivamente depositan en agosto (285 de los referenciados en
  `scenario.json`) se registraron antes del 2026-08-01. Excluirlos por fecha
  de alta vacía el experimento de datos reales.

- **Disparador de asignación:** la asignación a variante ocurre en la primera
  visita a la pantalla de fondeo (`GET /funding-screen?user_id=X`), no en un
  batch previo. Por qué: así se comporta un experimento real, se asigna en
  el momento de exposición, no antes. Como no hay login real, un script
  aparte simula esas visitas para los usuarios que el escenario referencia,
  para que exista una asignación antes de que llegue su primer webhook de
  depósito.

- **Definición de "convertido" (para leer el resultado del experimento):**
  primer depósito acreditado dentro de los 7 días de la **asignación a
  variante** (primera visita a la pantalla de fondeo), no de `created_at`.

  Esto se aparta a propósito de la definición literal de activación de la
  empresa ("7 días desde el alta"), y lo hacemos conscientes de eso. La razón es porque
  la mayoría de los usuarios que depositan en agosto se habían registrado
  meses antes. Con la ventana atada al alta, esos usuarios llegan a la
  pantalla con los 7 días ya vencidos, no importa qué tan rápido depositen
  después de ver la variante, nunca podrían contar como convertidos. Eso no
  favorece a A por sobre B (la asignación es al azar e independiente de la
  fecha de alta), pero sí ensucia la métrica con una razón que no tiene nada
  que ver con lo que el experimento prueba: si la variante cambia el
  comportamiento de depósito, el efecto solo puede medirse desde el momento
  en que la persona la vio, no desde una fecha de alta que en muchos casos es
  anterior a que el experimento existiera.

  Dicho de otra forma: la definición de la empresa mide activación general,
  y sigue siendo la correcta para el dashboard de negocio. La definición que
  usamos acá mide el efecto causal de la variante, que es la pregunta que
  este experimento puntualmente busca responder. Son cosas distintas y no
  compiten, pero para "¿A o B convierte mejor?", atarla al alta hubiera dado
  una respuesta contaminada por ruido de timing, no por el diseño de la
  pantalla.

-

---

## Lo que sé que está flojo

Qué le falta a tu entrega para ir a producción. Ser explícito acá suma, no
resta.

- **La recomendación de la variante B no está validada con datos reales, y
  eso puede estar jugando en contra de B en el resultado.** Hoy el método
  "recomendado" sale de una heurística mía (local > regional > el más
  barato/rápido), no de un análisis de qué método usa o prefiere en la
  práctica la gente de cada país. Si esa heurística elige mal, por
  ejemplo, recomienda cripto en un país donde históricamente casi nadie
  deposita así, B no está compitiendo con su mejor versión posible contra
  A, sino con una adivinanza sin validar. Antes de sacar una conclusión
  real de "A vs B" haría falta cruzar `deposits_historicos.json` con el
  país de cada usuario para ver qué método es realmente el más usado (o el
  que mejor convierte) por país, y usar eso como recomendación. Recién ahí
  B sería un candidato digno para el versus.

---

## Uso de IA

Utilice Claude code desde la terminal. 99% del codigo fue hecho por claude
Toda la arquitectura, orquestacion, analisis y reportes fue hecha por mi,
además de estandares y buenas practicas de codigo (hago bastante hincapie en cuanto a eso).

---

## Tiempo

Traté de no excederme en el tiempo estipulado aun asi siendo sincero me excedi un poco.
En cuanto al codigo puro estuvo bien (gracias ia), pero me excedi en cuanto al 
analisis y completado de esta planilla. Aproximadamente una hora y media más.
La razon fue la explicada mas arriba: la sospecha del resultado y la validacion extra que
tuve que hacer mas toda la explicación para comunicar el resultado.