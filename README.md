# Staff Management System

A comprehensive FastAPI backend for managing staff, payments, and business settings.

## Features

- **Staff Management**: Create, read, update, and delete staff members
- **Payment Management**: Track staff payments with detailed records
- **Role-Based Access Control**: Admin and staff roles with different permissions
- **Settings Management**: Manage suppliers, items, packaging types, and overhead costs
- **Supply Expense Management**: Track supply expenses with detailed calculations
- **JWT Authentication**: Secure token-based authentication
- **RESTful API**: Clean, documented API endpoints

## Project Structure

```
Backend_Laila/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── database.py          # Database configuration
│   ├── auth.py              # Authentication utilities
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Authentication endpoints
│       ├── staff.py         # Staff management
│       ├── payments.py      # Payment management
│       ├── suppliers.py     # Supplier management
│       ├── items.py         # Item management
│       ├── packaging_types.py # Packaging type management
│       ├── overhead_cost_types.py # Overhead cost type management
│       └── supply_expenses.py # Supply expense management
├── tests/
│   └── test_main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py
└── setup_admin.py
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./test.db
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3. Run the Application

```bash
python run.py
```

Or directly with uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup Admin Account

```bash
python setup_admin.py
```

This creates the initial admin account:
- Username: `admin`
- Password: `admin123`

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/login` | Staff login | No |
| POST | `/api/v1/auth/setup-admin` | Create admin account | No |

### Staff Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/staff/` | Create staff member | Admin |
| GET | `/api/v1/staff/` | Get all staff | Admin |
| GET | `/api/v1/staff/search` | Search staff by name | Admin |
| GET | `/api/v1/staff/me` | Get current staff info | Staff |
| GET | `/api/v1/staff/{staff_id}` | Get staff by ID | Admin |
| PATCH | `/api/v1/staff/{staff_id}` | Update staff | Admin |
| PATCH | `/api/v1/staff/{staff_id}/toggle-status` | Toggle staff status | Admin |
| DELETE | `/api/v1/staff/{staff_id}` | Delete staff | Admin |

### Payment Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/payments/` | Create payment | Admin |
| GET | `/api/v1/payments/` | Get all payments (paginated) | Admin |
| GET | `/api/v1/payments/staff/{staff_id}` | Get payments by staff | Admin |
| GET | `/api/v1/payments/{payment_id}` | Get payment by ID | Admin |
| PUT | `/api/v1/payments/{payment_id}` | Update payment | Admin |
| DELETE | `/api/v1/payments/{payment_id}` | Delete payment | Admin |
| GET | `/api/v1/payments/summary` | Get payment summary | Admin |

### Settings Management

#### Suppliers

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/suppliers/` | Create supplier | Admin |
| GET | `/api/v1/suppliers/` | Get all suppliers | No |
| GET | `/api/v1/suppliers/{supplier_id}` | Get supplier by ID | No |
| PATCH | `/api/v1/suppliers/{supplier_id}` | Update supplier | Admin |
| DELETE | `/api/v1/suppliers/{supplier_id}` | Delete supplier | Admin |

#### Items

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/items/` | Create item | Admin |
| GET | `/api/v1/items/` | Get all items | No |
| GET | `/api/v1/items/{item_id}` | Get item by ID | No |
| PATCH | `/api/v1/items/{item_id}` | Update item | Admin |
| DELETE | `/api/v1/items/{item_id}` | Delete item | Admin |

#### Packaging Types

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/packaging-types/` | Create packaging type | Admin |
| GET | `/api/v1/packaging-types/` | Get all packaging types | No |
| GET | `/api/v1/packaging-types/{packaging_type_id}` | Get packaging type by ID | No |
| PATCH | `/api/v1/packaging-types/{packaging_type_id}` | Update packaging type | Admin |
| DELETE | `/api/v1/packaging-types/{packaging_type_id}` | Delete packaging type | Admin |

#### Overhead Cost Types

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/overhead-cost-types/` | Create overhead cost type | Admin |
| GET | `/api/v1/overhead-cost-types/` | Get all overhead cost types | No |
| GET | `/api/v1/overhead-cost-types/{overhead_cost_type_id}` | Get overhead cost type by ID | No |
| PATCH | `/api/v1/overhead-cost-types/{overhead_cost_type_id}` | Update overhead cost type | Admin |
| DELETE | `/api/v1/overhead-cost-types/{overhead_cost_type_id}` | Delete overhead cost type | Admin |

### Supply Expense Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/supply-expenses/` | Create supply expense | Admin |
| GET | `/api/v1/supply-expenses/` | Get all supply expenses (with filters) | No |
| GET | `/api/v1/supply-expenses/{expense_id}` | Get supply expense by ID | No |
| GET | `/api/v1/supply-expenses/by-date/{date}` | Get expenses by date | No |
| GET | `/api/v1/supply-expenses/by-supplier/{supplier_name}` | Get expenses by supplier | No |
| PATCH | `/api/v1/supply-expenses/{expense_id}` | Update supply expense | Admin |
| DELETE | `/api/v1/supply-expenses/{expense_id}` | Delete supply expense | Admin |
| GET | `/api/v1/supply-expenses/summary/total` | Get expense summary | Admin |

## Usage Examples

### 1. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 2. Create Staff Member

```bash
curl -X POST "http://localhost:8000/api/v1/staff/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "John Doe",
    "username": "johndoe",
    "password": "password123",
    "role": "staff"
  }'
```

### 3. Create Supplier

```bash
curl -X POST "http://localhost:8000/api/v1/suppliers/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ABC Supplies",
    "contact": "+233 20 123 4567",
    "address": "123 Main St, Accra"
  }'
```

### 4. Create Item

```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rice",
    "unit": "kg"
  }'
```

### 5. Create Packaging Type

```bash
curl -X POST "http://localhost:8000/api/v1/packaging-types/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Boxes",
    "description": "Cardboard boxes for packaging",
    "price": 5.50
  }'
```

### 6. Create Overhead Cost Type

```bash
curl -X POST "http://localhost:8000/api/v1/overhead-cost-types/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rent"
  }'
```

### 7. Create Supply Expense

```bash
curl -X POST "http://localhost:8000/api/v1/supply-expenses/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "supplier": "ABC Supplies",
    "items": "Rice",
    "quantity": 10,
    "costPerItem": 25.50,
    "category": "Supply",
    "purchaseUnit": "kg",
    "packageSize": 5.0
  }'
```

## Authentication

The system uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Token Structure

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Data Models

### Staff

```json
{
  "id": "uuid",
  "fullName": "John Doe",
  "username": "johndoe",
  "role": "staff",
  "isActive": true,
  "createdAt": "2024-01-01T00:00:00"
}
```

### Payment

```json
{
  "id": "uuid",
  "staffId": "staff_uuid",
  "amount": 1000.00,
  "paymentDate": "2024-01-01",
  "staffName": "John Doe",
  "createdAt": "2024-01-01T00:00:00"
}
```

### Supplier

```json
{
  "id": "uuid",
  "name": "ABC Supplies",
  "contact": "+233 20 123 4567",
  "address": "123 Main St, Accra"
}
```

### Item

```json
{
  "id": "uuid",
  "name": "Rice",
  "unit": "kg"
}
```

### Packaging Type

```json
{
  "id": "uuid",
  "name": "Boxes",
  "description": "Cardboard boxes for packaging",
  "price": 5.50
}
```

### Overhead Cost Type

```json
{
  "id": "uuid",
  "name": "Rent"
}
```

### Supply Expense

```json
{
  "id": "EXP-123456",
  "date": "2024-01-15",
  "supplier": "ABC Supplies",
  "items": "Rice",
  "quantity": 10,
  "costPerItem": 25.50,
  "category": "Supply",
  "purchaseUnit": "kg",
  "packageSize": 5.0,
  "total": 255.00,
  "pricePerUnit": 5.10,
  "createdAt": "2024-01-15T10:30:00"
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
 black app/ tests/
```

### Linting

```bash
flake8 app/ tests/
```

## Deployment

### Production Considerations

1. **Database**: Replace in-memory storage with PostgreSQL/MySQL
2. **Environment Variables**: Set proper production values
3. **CORS**: Configure allowed origins properly
4. **HTTPS**: Use SSL/TLS in production
5. **Rate Limiting**: Implement API rate limiting
6. **Logging**: Add proper logging and monitoring

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
