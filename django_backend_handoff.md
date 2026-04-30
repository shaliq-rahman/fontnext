# Fontspell Django Backend Handoff

## Project Summary
Fontspell currently uses Firebase Authentication and Cloud Firestore directly from the Flutter client. This causes platform-specific issues, especially on Windows. The backend needs to be moved to Django so Flutter becomes a client-only application for Android, iOS, macOS, and Windows.

This document is the backend scope and API handoff for the Django developer.

## Objective
Build a Django REST API backend that fully replaces Firebase usage in the Flutter app.

The Django backend will handle:
- authentication
- fonts management
- customers management
- sales management
- dashboard statistics
- customer-font relationships
- validation and business rules

The Flutter app will:
- send HTTP requests to Django
- store JWT tokens locally
- stop using Firebase Auth and Firestore

## Recommended Backend Stack
- Django
- Django REST Framework
- PostgreSQL
- djangorestframework-simplejwt
- django-cors-headers if needed
- drf-spectacular optional for OpenAPI/Swagger

## Suggested Django Apps
- `accounts`
- `fonts`
- `customers`
- `sales`
- `dashboard`

## Core Data Model

### 1. User
Use Django `User` or a custom user model.

Required fields:
- `id`
- `email`
- `password`
- `is_active`
- `is_staff`

Notes:
- email-based login
- only authenticated users can access protected APIs

### 2. Font
Fields:
- `id`
- `name`
- `price`
- `weight`
- `created_at`

Rules:
- `name` must be unique

### 3. Customer
Fields:
- `id`
- `name`
- `phone`
- `phone2`
- `email`
- `address`
- `created_at`

Rules:
- `email` must be unique
- `phone` must be unique
- `phone2` must be unique if provided

### 4. Sale
Fields:
- `id`
- `customer` as ForeignKey to customer
- `font` as ForeignKey to font
- `quantity`
- `price_at_sale`
- `sale_date`

Rules:
- each sale represents a font purchase/assignment for a customer
- `price_at_sale` must be copied from the font price at time of sale

## Important Design Note
Do not make `fontIds` inside customer the source of truth.

Use the `Sale` table as the real relationship between customer and font. This will make dashboard, reporting, and history much easier and more reliable.

## Authentication Requirements
Use JWT authentication.

Recommended package:
- `djangorestframework-simplejwt`

Required behavior:
- login with email and password
- return access and refresh tokens
- authenticated endpoint to fetch current user
- token refresh endpoint

## API Specification

### Auth APIs

#### `POST /api/auth/login/`
Purpose:
- log in user with email and password

Request:
```json
{
  "email": "admin@fontspell.com",
  "password": "Admin@123"
}
```

Response:
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 1,
    "email": "admin@fontspell.com"
  }
}
```

#### `POST /api/auth/refresh/`
Request:
```json
{
  "refresh": "jwt_refresh_token"
}
```

Response:
```json
{
  "access": "new_access_token"
}
```

#### `GET /api/auth/me/`
Purpose:
- return currently authenticated user

Response:
```json
{
  "id": 1,
  "email": "admin@fontspell.com"
}
```

#### `POST /api/auth/logout/`
Optional:
- only if refresh token blacklisting is implemented

## Font APIs

#### `GET /api/fonts/`
Purpose:
- list all fonts

Response:
```json
[
  {
    "id": 1,
    "name": "Arial Pro",
    "price": 1200.0,
    "weight": 400.0,
    "created_at": "2026-04-13T10:00:00Z"
  }
]
```

#### `POST /api/fonts/`
Purpose:
- create a new font

Request:
```json
{
  "name": "Arial Pro",
  "price": 1200.0,
  "weight": 400.0
}
```

Validation:
- reject duplicate `name`

#### `GET /api/fonts/{id}/`
Purpose:
- get font detail

#### `PUT /api/fonts/{id}/`
Purpose:
- full update

#### `PATCH /api/fonts/{id}/`
Purpose:
- partial update

#### `DELETE /api/fonts/{id}/`
Optional:
- only if delete is required by business

## Customer APIs

#### `GET /api/customers/`
Purpose:
- list all customers

Optional query params:
- `search`
- `phone`
- `email`
- `exclude_font_id`

Examples:
- `/api/customers/?search=john`
- `/api/customers/?phone=9999999999`
- `/api/customers/?exclude_font_id=5`

#### `POST /api/customers/`
Purpose:
- create customer

Request:
```json
{
  "name": "John",
  "phone": "9999999999",
  "phone2": "8888888888",
  "email": "john@test.com",
  "address": "Dubai"
}
```

Validation:
- reject duplicate `email`
- reject duplicate `phone`
- reject duplicate `phone2` if provided

#### `GET /api/customers/{id}/`
Purpose:
- get customer detail

#### `PUT /api/customers/{id}/`
Purpose:
- full update

#### `PATCH /api/customers/{id}/`
Purpose:
- partial update

#### `DELETE /api/customers/{id}/`
Optional:
- only if delete is required

## Customer Lookup APIs

#### `GET /api/customers/by-phone/?phone=9999999999`
Purpose:
- find customer using `phone` or `phone2`
- return customer plus fonts purchased

Response:
```json
{
  "id": 10,
  "name": "John",
  "phone": "9999999999",
  "phone2": "8888888888",
  "email": "john@test.com",
  "address": "Dubai",
  "fonts": [
    {
      "id": 1,
      "name": "Arial Pro",
      "price": 1200.0,
      "weight": 400.0
    }
  ]
}
```

#### `GET /api/customers/{id}/fonts/`
Purpose:
- return fonts purchased/assigned to customer

## Customer Font Assignment API

#### `POST /api/customers/{id}/assign-fonts/`
Purpose:
- assign one or more fonts to a customer
- create `Sale` rows automatically for newly assigned fonts

Request:
```json
{
  "font_ids": [1, 2, 3]
}
```

Behavior:
- create sales only for newly assigned fonts
- do not duplicate an existing customer-font assignment unless business explicitly needs repeat purchases
- set `price_at_sale` from current font price

Response:
```json
{
  "message": "Fonts assigned successfully"
}
```

## Sales APIs

#### `GET /api/sales/`
Purpose:
- list sales

#### `POST /api/sales/`
Optional:
- manual sale creation if needed

Request:
```json
{
  "customer": 10,
  "font": 1,
  "quantity": 1
}
```

#### `GET /api/sales/{id}/`
Purpose:
- get sale detail

#### `GET /api/sales/today/count/`
Response:
```json
{
  "count": 4
}
```

#### `GET /api/sales/total/count/`
Response:
```json
{
  "count": 120
}
```

## Dashboard APIs

#### `GET /api/dashboard/summary/`
Purpose:
- return high-level dashboard data for home screen

Response:
```json
{
  "today_sales_count": 4,
  "total_sales_count": 120,
  "total_customers": 32,
  "total_fonts": 15
}
```

#### `GET /api/dashboard/trending-fonts/`
Purpose:
- return top-selling fonts

Response:
```json
[
  {
    "id": 1,
    "name": "Arial Pro",
    "price": 1200.0,
    "weight": 400.0,
    "sales_count": 18
  }
]
```

## Font Customer APIs

#### `GET /api/fonts/{id}/customers/`
Purpose:
- return customers who purchased a specific font

Response:
```json
[
  {
    "id": 10,
    "name": "John",
    "phone": "9999999999",
    "email": "john@test.com"
  }
]
```

## Validation Rules
Django must enforce the following:
- font name must be unique
- customer email must be unique
- customer phone must be unique
- customer phone2 must be unique if present
- phone lookup should search `phone` and `phone2`
- assigning new fonts should create sales
- `price_at_sale` should be stored in sale record

## Permissions
Public endpoints:
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`

Protected endpoints:
- all fonts APIs
- all customer APIs
- all sales APIs
- all dashboard APIs
- `GET /api/auth/me/`

## Recommended Serializers
- `UserSerializer`
- `LoginSerializer`
- `FontSerializer`
- `CustomerSerializer`
- `CustomerDetailSerializer`
- `SaleSerializer`
- `DashboardSummarySerializer`
- `TrendingFontSerializer`

## Recommended Views or ViewSets
- auth login view
- auth me view
- token refresh view
- font CRUD viewset
- customer CRUD viewset
- customer by-phone lookup view
- customer assign-fonts action
- sales list/detail views
- dashboard summary view
- dashboard trending fonts view
- font customers view

## Database Recommendations
Use PostgreSQL.

Recommended indexes:
- `font.name`
- `customer.email`
- `customer.phone`
- `customer.phone2`
- `sale.sale_date`
- `sale.customer_id`
- `sale.font_id`

## Performance Notes
Use:
- `select_related`
- `prefetch_related`

Avoid N+1 queries in:
- customer detail with fonts
- dashboard trending fonts
- customers by font

## Test Requirements
Create tests for:
- login success
- login failure
- font creation
- duplicate font name rejection
- customer creation
- duplicate email rejection
- duplicate phone rejection
- customer lookup by phone
- font assignment to customer
- sale creation during font assignment
- dashboard summary
- trending font calculation

## Expected Delivery From Django Developer
- Django project with app structure
- models
- migrations
- serializers
- views
- urls
- JWT auth setup
- PostgreSQL configuration
- API tests
- API documentation or Swagger if enabled

## High Priority Endpoints To Build First
1. `POST /api/auth/login/`
2. `GET /api/auth/me/`
3. `POST /api/auth/refresh/`
4. `GET /api/fonts/`
5. `POST /api/fonts/`
6. `GET /api/customers/by-phone/`
7. `POST /api/customers/`
8. `PATCH /api/customers/{id}/`
9. `POST /api/customers/{id}/assign-fonts/`
10. `GET /api/dashboard/summary/`
11. `GET /api/dashboard/trending-fonts/`
12. `GET /api/fonts/{id}/customers/`

## Flutter Areas This Backend Will Replace
Current Firebase-dependent Flutter files:
- `/Users/fahad/freelances/fontspell/lib/main.dart`
- `/Users/fahad/freelances/fontspell/lib/firebase_options.dart`
- `/Users/fahad/freelances/fontspell/lib/provider/auth_provider.dart`
- `/Users/fahad/freelances/fontspell/lib/provider/font_provider.dart`
- `/Users/fahad/freelances/fontspell/lib/provider/customer_provider.dart`
- `/Users/fahad/freelances/fontspell/lib/provider/home_provider.dart`
- `/Users/fahad/freelances/fontspell/lib/provider/font_customer_provider.dart`
- `/Users/fahad/freelances/fontspell/lib/view/splash_screen.dart`
- `/Users/fahad/freelances/fontspell/lib/view/logout_dialog.dart`

## Final Instruction To Backend Developer
Build the Django backend so Flutter no longer depends on Firebase Auth or Firestore for any production feature. All business logic should be owned by Django APIs and PostgreSQL.
