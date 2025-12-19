# Jobs App - Sistema de Ofertas y Pujas

## Descripción General

La app `jobs` implementa un sistema completo de ofertas de trabajo con sistema de pujas y votación, diseñado para conectar clientes (PERSONA/CONSORCIO) con profesionales (OFICIO).

## Modelos

### 1. JobOffer (Oferta de Trabajo)

Representa una oferta de trabajo publicada por un cliente.

**Campos:**
- `creator` (FK a UserProfile): Usuario que crea la oferta
- `title` (CharField): Título descriptivo
- `description` (TextField): Descripción detallada del trabajo
- `budget_base_ars` (DecimalField): Presupuesto base en ARS
- `status` (CharField): Estado (OPEN, IN_PROGRESS, CLOSED)
- `is_consorcio` (BooleanField): Indica si es de un consorcio
- `created_at` / `updated_at`: Timestamps

**Properties:**
- `budget_base_usdc`: Convierte el presupuesto a USDC (1 USDC = 1200 ARS)

**Métodos:**
- `get_active_bids()`: Retorna pujas activas
- `get_winning_bid()`: Retorna la puja ganadora
- `can_receive_bids()`: Verifica si puede recibir nuevas pujas

**Ejemplo de uso:**
```python
from jobs.models import JobOffer
from usuarios.models import UserProfile

# Crear oferta
profile = UserProfile.objects.get(user__username='cliente1')
offer = JobOffer.objects.create(
    creator=profile,
    title='Reparación de cañerías',
    description='Se necesita plomero para reparar cañería principal',
    budget_base_ars=50000.00,
    is_consorcio=True
)

# Consultar presupuesto en USDC
print(f"Presupuesto: ${offer.budget_base_ars} ARS = ${offer.budget_base_usdc} USDC")
# Output: Presupuesto: $50000.00 ARS = $41.67 USDC
```

### 2. Bid (Puja)

Representa una oferta de un profesional para realizar el trabajo.

**Campos:**
- `job_offer` (FK a JobOffer): Oferta relacionada
- `professional` (FK a UserProfile): Profesional que puja
- `amount_ars` (DecimalField): Monto ofrecido en ARS
- `estimated_days` (PositiveIntegerField): Días estimados
- `pitch_text` (TextField): Propuesta del profesional
- `is_active` (BooleanField): Si la puja está activa
- `is_winner` (BooleanField): Si fue seleccionada como ganadora
- `created_at` / `updated_at`: Timestamps

**Properties:**
- `amount_usdc`: Convierte el monto a USDC (1 USDC = 1200 ARS)
- `total_votes`: Total de votos recibidos

**Métodos:**
- `mark_as_winner()`: Marca como ganadora y actualiza estado de la oferta
- `can_be_voted()`: Verifica si puede recibir votos

**Constraints:**
- Un profesional solo puede hacer una puja activa por oferta

**Ejemplo de uso:**
```python
from jobs.models import Bid

# Crear puja
professional = UserProfile.objects.get(user__username='plomero1')
bid = Bid.objects.create(
    job_offer=offer,
    professional=professional,
    amount_ars=45000.00,
    estimated_days=3,
    pitch_text='Tengo 10 años de experiencia. Puedo empezar mañana.'
)

# Consultar monto en USDC
print(f"Puja: ${bid.amount_ars} ARS = ${bid.amount_usdc} USDC")
# Output: Puja: $45000.00 ARS = $37.50 USDC

# Marcar como ganadora
bid.mark_as_winner()
# Esto automáticamente:
# - Desmarca otras pujas ganadoras de la misma oferta
# - Actualiza el estado de la oferta a IN_PROGRESS
```

### 3. Vote (Voto)

Sistema de votación para ayudar a seleccionar la mejor puja.

**Campos:**
- `user` (FK a User): Usuario que vota
- `bid` (FK a Bid): Puja votada
- `created_at`: Timestamp

**Constraints:**
- Un usuario solo puede votar una vez por puja

**Métodos de clase:**
- `toggle_vote(user, bid)`: Alterna el voto (crea o elimina)
- `user_has_voted(user, bid)`: Verifica si un usuario ya votó
- `get_user_votes_for_job(user, job_offer)`: Votos de un usuario en una oferta

**Ejemplo de uso:**
```python
from jobs.models import Vote
from django.contrib.auth.models import User

# Votar por una puja
user = User.objects.get(username='votante1')
voted, vote = Vote.toggle_vote(user, bid)

if voted:
    print(f"Voto registrado. Total de votos: {bid.total_votes}")
else:
    print("Voto eliminado")

# Verificar si ya votó
if Vote.user_has_voted(user, bid):
    print("Ya votaste por esta puja")

# Ver todas las pujas votadas en una oferta
user_votes = Vote.get_user_votes_for_job(user, offer)
print(f"Has votado {user_votes.count()} pujas en esta oferta")
```

## Conversión ARS → USDC

Todos los montos en ARS tienen una property que los convierte a USDC usando una cotización mockeada:

**Tasa de conversión: 1 USDC = 1200 ARS**

Esta conversión usa `Decimal` con redondeo `ROUND_HALF_UP` para precisión financiera.

**Ejemplo:**
```python
# Presupuesto
budget_ars = 120000.00
budget_usdc = budget_ars / 1200.00  # = 100.00 USDC

# Puja
bid_ars = 96000.00
bid_usdc = bid_ars / 1200.00  # = 80.00 USDC
```

## Admin Panel

Los tres modelos están registrados en el admin panel con interfaces completas:

### JobOfferAdmin
- Vista de lista con presupuesto en ARS y USDC
- Filtros por estado y tipo de consorcio
- Búsqueda por título y creador
- Campos agrupados por secciones

### BidAdmin
- Vista de lista con montos en ARS y USDC
- Total de votos por puja
- Acciones bulk:
  - "Marcar como ganadora"
  - "Marcar como inactiva"
- Filtros por estado activo/ganador

### VoteAdmin
- Vista de solo lectura (no permite crear/editar)
- Muestra usuario, puja y oferta relacionada
- Filtros por fecha

## Flujo de Trabajo Típico

1. **Cliente crea oferta:**
```python
offer = JobOffer.objects.create(
    creator=cliente_profile,
    title='Pintura de edificio',
    description='Pintar fachada completa',
    budget_base_ars=200000.00,
    is_consorcio=True
)
```

2. **Profesionales envían pujas:**
```python
bid1 = Bid.objects.create(
    job_offer=offer,
    professional=pintor1_profile,
    amount_ars=180000.00,
    estimated_days=7,
    pitch_text='Equipo de 5 personas, referencias verificables'
)

bid2 = Bid.objects.create(
    job_offer=offer,
    professional=pintor2_profile,
    amount_ars=190000.00,
    estimated_days=5,
    pitch_text='Trabajo express con garantía'
)
```

3. **Usuarios votan:**
```python
Vote.toggle_vote(user1, bid1)  # +1 voto
Vote.toggle_vote(user2, bid1)  # +1 voto
Vote.toggle_vote(user3, bid2)  # +1 voto
```

4. **Cliente selecciona ganador:**
```python
winning_bid = offer.get_active_bids().annotate(
    vote_count=Count('votes')
).order_by('-vote_count').first()

winning_bid.mark_as_winner()
# Estado de la oferta cambia a IN_PROGRESS
```

## Índices de Base de Datos

Para optimizar el rendimiento, se crearon los siguientes índices:

**JobOffer:**
- `(status, -created_at)`: Para listar ofertas por estado y fecha
- `(creator, status)`: Para ver ofertas de un creador por estado

**Bid:**
- `(job_offer, -created_at)`: Para listar pujas de una oferta
- `(professional, -created_at)`: Para ver pujas de un profesional
- `(is_winner)`: Para encontrar pujas ganadoras rápidamente

**Vote:**
- `(bid, -created_at)`: Para listar votos de una puja
- `(user, -created_at)`: Para ver votos de un usuario

## Validaciones

- Montos y presupuestos deben ser > 0.01
- Días estimados deben ser >= 1
- Un profesional solo puede tener una puja activa por oferta
- Un usuario solo puede votar una vez por puja
- Solo puede haber una puja ganadora por oferta

## Integración con app usuarios

Los modelos dependen de `UserProfile` de la app `usuarios`:
- `JobOffer.creator` → usuarios.UserProfile
- `Bid.professional` → usuarios.UserProfile

Asegúrate de que los perfiles existan antes de crear ofertas o pujas.

## Próximos Pasos Sugeridos

1. Crear vistas para CRUD de ofertas y pujas
2. Implementar endpoints API REST
3. Crear templates para frontend
4. Agregar notificaciones cuando una puja recibe votos
5. Sistema de mensajería entre cliente y profesional
6. Integración con sistema de transacciones de la wallet
