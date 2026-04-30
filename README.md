# Fontspell FastAPI Backend

This is the fully rebuilt FastAPI backend system for the Fontspell app, replacing Firebase Auth and Firestore dependencies. It uses PostgreSQL natively through asynchronous SQLAlchemy execution alongside JWT-based authentication.

## Getting Started

### 1. Requirements

- Python 3.10+
- PostgreSQL Server

### 2. Installation Setup

1. **Activate the virtual environment**:
   ```bash
   cd backend
   source venv/bin/activate
   ```
2. **Install remaining environment dependencies (if needed)**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Database Configuration

You need to establish a local PostgreSQL database structure for the endpoints.

1. Ensure PostgreSQL is running. Open your terminal and create a database named `fontspell`.
   ```bash
   createdb fontspell
   ```
   *(Or just create it inside pgAdmin / DBeaver).*
2. Configure `.env` file credentials. By default, it looks for `postgresql+asyncpg://postgres:postgres@localhost:5432/fontspell`. Adjust the user / password as per your local postgres configuration:
   ```env
   DATABASE_URL="postgresql+asyncpg://yourusername:yourpassword@localhost:5432/fontspell"
   ```
3. Run Alembic migrations to generate the database tables:
   ```bash
   alembic revision --autogenerate -m "Initial Schema"
   alembic upgrade head
   ```

### 4. Running the Server

Start the interactive server locally leveraging Uvicorn running on port 8000.
```bash
uvicorn app.main:app --reload
```

---

## Interactive Swagger Documentation
FastAPI natively comes with an interactive SwaggerUI that allows you to directly interface and test the application securely.
Access it by visiting: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

---

## API Documentation Detail

Below are the detailed payload schemas and behavior outlines. For protected routes, provide the token in the `Authorization` header as a Bearer Token: `Authorization: Bearer <access_token>`.

### 1. Auth APIs
*Public endpoints (except `/api/auth/me/`).*

#### **POST /api/auth/login/**
Logs in an active user matching the exact email/password and issues access/refresh tokens.
**Request JSON:**
```json
{
  "email": "admin@fontspell.com",
  "password": "Admin@123"
}
```
**Response JSON (Success - 200 OK):**
```json
{
  "access": "eyJhbG... (jwt_access_token)",
  "refresh": "eyJhbG... (jwt_refresh_token)",
  "user": {
    "id": 1,
    "email": "admin@fontspell.com"
  }
}
```

#### **POST /api/auth/refresh/**
Returns a new access token given a valid refresh token.
**Request JSON:**
```json
{
  "refresh": "jwt_refresh_token"
}
```
**Response JSON (Success - 200 OK):**
```json
{
  "access": "new_eyJhb... (new_access_token)"
}
```

#### **GET /api/auth/me/** *(Protected)*
Returns the currently authenticated user mapping properties.
**Response JSON:**
```json
{
  "id": 1,
  "email": "admin@fontspell.com"
}
```

---

### 2. Fonts APIs
*(Protected Routes)*

#### **GET /api/fonts/**
Lists all available fonts.
**Response JSON:**
```json
[
  {
    "name": "Arial Pro",
    "price": 1200.0,
    "weight": 400.0,
    "id": 1,
    "created_at": "2026-04-14T12:00:00Z"
  }
]
```

#### **POST /api/fonts/**
Create a new font. Rejects requests with existing names.
**Request JSON:**
```json
{
  "name": "Arial Pro",
  "price": 1200.0,
  "weight": 400.0
}
```

#### **GET /api/fonts/{id}/**
Returns a specific font object identical directly via its database ID.

#### **PATCH /api/fonts/{id}/**
Partially update an existing font.
**Request JSON:**
```json
{
  "price": 1500.0
}
```

#### **GET /api/fonts/{id}/customers/**
Returns a list of `CustomerOut` format objects indicating which customers have purchased this exact font.

---

### 3. Customers APIs
*(Protected Routes)*

#### **GET /api/customers/**
Configured with query parameters enabling advanced lookups: `search`, `phone`, `email`, `exclude_font_id`.
**Example Queries:**
- `/api/customers/?search=john`
- `/api/customers/?phone=9999999999`
- `/api/customers/?exclude_font_id=5`

#### **POST /api/customers/**
Create a new customer. Rejects duplicates of `email`, `phone`, or `phone2` (if populated).
**Request JSON:**
```json
{
  "name": "John",
  "phone": "9999999999",
  "phone2": "8888888888",
  "email": "john@test.com",
  "address": "Dubai"
}
```

#### **GET /api/customers/by-phone/?phone=...**
Unique fetch returning all standard customer data plus a `fonts` nested object mapping identifying their existing associations.
**Response JSON:**
```json
{
  "name": "John",
  "phone": "9999999999",
  "phone2": "8888888888",
  "email": "john@test.com",
  "address": "Dubai",
  "id": 10,
  "created_at": "2026-04-14T12:00:00Z",
  "fonts": [
    {
      "name": "Arial Pro",
      "price": 1200.0,
      "weight": 400.0,
      "id": 1,
      "created_at": "2026-04-14T12:00:00Z"
    }
  ]
}
```

#### **POST /api/customers/{id}/assign-fonts/**
Assigns fonts safely skipping pre-assigned entries and establishing relational `Sale` tracking history matching the current market font value implicitly.
**Request JSON:**
```json
{
  "font_ids": [1, 2, 3]
}
```
**Response JSON:**
```json
{
  "message": "Fonts assigned successfully"
}
```

---

### 4. Sales & Dashboard APIs
*(Protected Routes)*

#### **GET /api/dashboard/summary/**
Calculates high-level statistical counts bridging multiple tables concurrently.
**Response JSON:**
```json
{
  "today_sales_count": 4,
  "total_sales_count": 120,
  "total_customers": 32,
  "total_fonts": 15
}
```

#### **GET /api/dashboard/trending-fonts/**
Returns the 10 top-selling Font mappings dynamically nested tracking total purchase histories.
**Response JSON:**
```json
[
  {
    "id": 1,
    "name": "Arial Pro",
    "price": 1200.0,
    "weight": 400.0,
    "created_at": "2026-04-14T12:00:00Z",
    "sales_count": 18
  }
]
```
# fontnext
