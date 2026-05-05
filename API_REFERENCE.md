# Fontspell API — Integration Reference

A complete technical reference for integrating the Fontspell backend into a client application (web, mobile, or desktop). Hand this file to your coding agent and it will have everything it needs to build a working client.

---

## 1. Base URL & Conventions

- **Base URL:** `<host>/api`  (e.g. `https://api.fontspell.example.com/api` or `http://localhost:8000/api` in development)
- **Content-Type:** All request and response bodies are JSON. Send `Content-Type: application/json` on `POST`/`PUT`/`PATCH`.
- **Trailing slash:** All paths end with a trailing `/`. Do **not** strip it — the routes are registered with the slash.
- **Auth:** All endpoints except `POST /auth/login/`, `POST /auth/refresh/`, and `POST /auth/create-superadmin/` require a Bearer access token.
- **Interactive docs:** Swagger UI is available at `<host>/api/docs` and the OpenAPI schema at `<host>/api/openapi.json`.

---

## 2. Universal Response Envelope

**Every response — success or error — has the same shape:**

```json
{
  "status": true,
  "message": "Human readable message",
  "data": <any | null>
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `boolean` | `true` on success, `false` on any error (auth, validation, not found, server error). |
| `message` | `string` | Short human-readable message. Use it for toasts/snackbars. |
| `data` | `object \| array \| null` | The actual payload on success; `null` (or validation details) on error. |

**Client integration rule:** Always read `status` first. If `false`, surface `message` to the user and skip `data` parsing.

### Error examples

```json
// 401 unauthenticated
{ "status": false, "message": "Not authenticated", "data": null }

// 401 invalid creds
{ "status": false, "message": "Incorrect email or password", "data": null }

// 404 not found
{ "status": false, "message": "Customer not found", "data": null }

// 422 validation error — `data` carries field details
{
  "status": false,
  "message": "Validation error",
  "data": [
    { "type": "value_error", "loc": ["body", "email"], "msg": "value is not a valid email address", "input": "not-an-email" }
  ]
}

// 500 internal
{ "status": false, "message": "Internal server error", "data": null }
```

### HTTP status codes

The HTTP status code still reflects the result (`200`, `201`, `400`, `401`, `404`, `422`, `500`). Treat `2xx` as success and any other range as failure, but rely on the envelope's `status` for branching logic.

---

## 3. Authentication

### Token model

- Login returns two tokens: `access` and `refresh`. Both are JWTs (`HS256`).
- Access token is sent on every protected request as `Authorization: Bearer <access>`.
- Refresh token is exchanged for a new access token via `POST /auth/refresh/`.
- Tokens currently have a very long lifetime; treat them as opaque and refresh on `401`.

### Header format

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Recommended client flow

1. On app start, read the saved tokens (Keychain / Keystore / secure storage).
2. If no tokens, route to login screen.
3. Attach `Authorization` header to every API call.
4. On any `401` from a protected route, call `POST /auth/refresh/` with the refresh token.
   - On success, retry the original request with the new access token.
   - On failure, clear tokens and route to login.
5. On `POST /auth/logout/`, clear local tokens (the server is stateless).

---

## 4. Endpoint Index

| # | Method | Path | Auth | Purpose |
|---|---|---|---|---|
| 1 | POST | `/auth/login/` | — | Email + password login |
| 2 | POST | `/auth/refresh/` | — | Exchange refresh for new access token |
| 3 | GET | `/auth/me/` | yes | Current user profile |
| 4 | POST | `/auth/logout/` | yes | Stateless logout |
| 5 | POST | `/auth/create-superadmin/` | — | Bootstrap a superadmin user |
| 6 | GET | `/fonts/` | yes | List all fonts |
| 7 | POST | `/fonts/` | yes | Create a font |
| 8 | GET | `/fonts/{font_id}/` | yes | Get a font by id |
| 9 | PUT | `/fonts/{font_id}/` | yes | Replace a font |
| 10 | PATCH | `/fonts/{font_id}/` | yes | Partially update a font |
| 11 | DELETE | `/fonts/{font_id}/` | yes | Delete a font |
| 12 | GET | `/fonts/{font_id}/customers/` | yes | Customers who bought a font |
| 13 | GET | `/customers/` | yes | List/search customers |
| 14 | GET | `/customers/by-phone/` | yes | Lookup customer by phone (with fonts) |
| 15 | POST | `/customers/` | yes | Create a customer |
| 16 | GET | `/customers/{customer_id}/` | yes | Get a customer |
| 17 | GET | `/customers/{customer_id}/fonts/` | yes | Fonts owned by a customer |
| 18 | PATCH | `/customers/{customer_id}/` | yes | Partially update a customer |
| 19 | PUT | `/customers/{customer_id}/` | yes | Replace a customer |
| 20 | DELETE | `/customers/{customer_id}/` | yes | Delete a customer |
| 21 | POST | `/customers/{customer_id}/assign-fonts/` | yes | Assign fonts to a customer (creates sales) |
| 22 | GET | `/sales/` | yes | List all sales |
| 23 | POST | `/sales/` | yes | Create a sale |
| 24 | GET | `/sales/{sale_id}/` | yes | Get a sale |
| 25 | GET | `/sales/today/count/` | yes | Sales count for today |
| 26 | GET | `/sales/total/count/` | yes | Total sales count |
| 27 | GET | `/dashboard/summary/` | yes | Dashboard counters |
| 28 | GET | `/dashboard/trending-fonts/` | yes | Top 10 fonts by sales |

---

## 5. Data Models

These are the shapes that appear inside `data`. All timestamps are ISO 8601 UTC strings.

### User
```json
{ "id": 1, "email": "admin@example.com" }
```

### Font
```json
{
  "id": 1,
  "name": "Helvetica Neue",
  "price": 49.99,
  "weight": 400.0,
  "created_at": "2026-05-01T10:30:00Z"
}
```

### Customer
```json
{
  "id": 10,
  "name": "Jane Doe",
  "phone": "+15551234567",
  "phone2": "+15557654321",
  "email": "jane@example.com",
  "address": "123 Main St",
  "created_at": "2026-05-01T10:30:00Z"
}
```

`phone2` and `address` may be `null`.

### CustomerDetail (Customer + owned fonts)
```json
{
  "id": 10,
  "name": "Jane Doe",
  "phone": "+15551234567",
  "phone2": null,
  "email": "jane@example.com",
  "address": null,
  "created_at": "2026-05-01T10:30:00Z",
  "fonts": [ /* Font objects */ ]
}
```

### Sale
```json
{
  "id": 100,
  "customer_id": 10,
  "font_id": 1,
  "quantity": 1,
  "price_at_sale": 49.99,
  "sale_date": "2026-05-05T08:00:00Z"
}
```

### TrendingFont (Font + sales_count)
```json
{
  "id": 1,
  "name": "Helvetica Neue",
  "price": 49.99,
  "weight": 400.0,
  "created_at": "2026-05-01T10:30:00Z",
  "sales_count": 42
}
```

### DashboardSummary
```json
{
  "today_sales_count": 5,
  "total_sales_count": 1234,
  "total_customers": 567,
  "total_fonts": 89
}
```

---

## 6. Endpoints — Detailed Reference

> Every response below is wrapped in the universal envelope `{ status, message, data }`. To save space, examples show the value of `data` only; the surrounding envelope is implicit.

---

### 6.1 Auth

#### `POST /auth/login/`

Authenticate and receive tokens.

- **Auth:** none
- **Body:**
```json
{ "email": "admin@example.com", "password": "secret123" }
```
- **Success (200):**
```json
{
  "status": true,
  "message": "Login successful",
  "data": {
    "access": "<jwt>",
    "refresh": "<jwt>",
    "user": { "id": 1, "email": "admin@example.com" }
  }
}
```
- **Errors:**
  - `401` — `Incorrect email or password`
  - `400` — `Inactive user`
  - `422` — Validation error

---

#### `POST /auth/refresh/`

Exchange a refresh token for a new access token.

- **Auth:** none (the refresh token IS the credential)
- **Body:**
```json
{ "refresh": "<jwt>" }
```
- **Success (200):**
```json
{ "status": true, "message": "Token refreshed successfully", "data": { "access": "<jwt>" } }
```
- **Errors:** `401 Invalid token type` / `Invalid token` / `Could not validate credentials` / `Invalid user`

---

#### `GET /auth/me/`

Returns the currently authenticated user.

- **Auth:** Bearer
- **Success (200):** `data = { "id": 1, "email": "admin@example.com" }`

---

#### `POST /auth/logout/`

Stateless logout. Clears nothing server-side; the client should drop tokens locally.

- **Auth:** Bearer
- **Body:** none
- **Success (200):** `data = null`, `message = "Successfully logged out"`

---

#### `POST /auth/create-superadmin/`

Bootstrap a superadmin. **Open endpoint** — protect/disable in production once first admin is created.

- **Auth:** none
- **Body:**
```json
{ "email": "admin@example.com", "password": "secret123" }
```
- **Success (200):** `data = { "id": 1, "email": "admin@example.com" }`
- **Errors:** `400 A user with this email already exists.`

---

### 6.2 Fonts

#### `GET /fonts/`

List all fonts.

- **Auth:** Bearer
- **Success (200):** `data = [ Font, Font, ... ]`

---

#### `POST /fonts/`

Create a font.

- **Auth:** Bearer
- **Body:**
```json
{ "name": "Helvetica Neue", "price": 49.99, "weight": 400 }
```
| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Must be unique |
| `price` | number | yes | |
| `weight` | number | yes | e.g. 400, 700 |

- **Success (201):** `data = Font`
- **Errors:** `400 Font with this name already exists`

---

#### `GET /fonts/{font_id}/`

Get a single font.

- **Auth:** Bearer
- **Success (200):** `data = Font`
- **Errors:** `404 Font not found`

---

#### `PUT /fonts/{font_id}/`

Replace a font (all fields required).

- **Auth:** Bearer
- **Body:** same as `POST /fonts/`
- **Success (200):** `data = Font`
- **Errors:** `404 Font not found`, `400 Font with this name already exists`

---

#### `PATCH /fonts/{font_id}/`

Partial update — send only the fields you want to change.

- **Auth:** Bearer
- **Body (any subset):**
```json
{ "name": "Helvetica Neue", "price": 59.99, "weight": 500 }
```
- **Success (200):** `data = Font`
- **Errors:** `404 Font not found`, `400 Font with this name already exists`

---

#### `DELETE /fonts/{font_id}/`

Delete a font.

- **Auth:** Bearer
- **Success (200):** `data = null`, `message = "Font deleted successfully"`
- **Errors:** `404 Font not found`

---

#### `GET /fonts/{font_id}/customers/`

List customers who have purchased this font (distinct).

- **Auth:** Bearer
- **Success (200):** `data = [ Customer, Customer, ... ]`

---

### 6.3 Customers

#### `GET /customers/`

List customers, with optional filtering.

- **Auth:** Bearer
- **Query params (all optional):**

| Param | Type | Behavior |
|---|---|---|
| `search` | string | Case-insensitive `name` contains |
| `phone` | string | Matches `phone` OR `phone2` exactly |
| `email` | string | Exact match |
| `exclude_font_id` | integer | Exclude customers who already own the given font (useful for "assign fonts" pickers) |

- **Success (200):** `data = [ Customer, Customer, ... ]`

---

#### `GET /customers/by-phone/`

Lookup a single customer by phone number AND return the fonts they own.

- **Auth:** Bearer
- **Query params:**
  - `phone` (required) — matches `phone` OR `phone2`
- **Success (200):** `data = CustomerDetail`
- **Errors:** `404 Customer not found`

---

#### `POST /customers/`

Create a customer.

- **Auth:** Bearer
- **Body:**
```json
{
  "name": "Jane Doe",
  "phone": "+15551234567",
  "phone2": "+15557654321",
  "email": "jane@example.com",
  "address": "123 Main St"
}
```
| Field | Type | Required |
|---|---|---|
| `name` | string | yes |
| `phone` | string | yes (unique) |
| `phone2` | string \| null | no (unique if present) |
| `email` | string (email) | yes (unique) |
| `address` | string \| null | no |

- **Success (201):** `data = Customer`
- **Errors:** `400 Customer with this email/phone/phone2 already exists`

---

#### `GET /customers/{customer_id}/`

Get one customer.

- **Auth:** Bearer
- **Success (200):** `data = Customer`
- **Errors:** `404 Customer not found`

---

#### `GET /customers/{customer_id}/fonts/`

Fonts owned by this customer.

- **Auth:** Bearer
- **Success (200):** `data = [ Font, Font, ... ]`

---

#### `PATCH /customers/{customer_id}/`

Partial update.

- **Auth:** Bearer
- **Body (any subset):** same fields as create. All optional.
- **Success (200):** `data = Customer`
- **Errors:** `404`, `400 Customer with this email/phone/phone2 already exists`

---

#### `PUT /customers/{customer_id}/`

Full replace — send all create fields.

- **Auth:** Bearer
- **Body:** same as `POST /customers/`
- **Success (200):** `data = Customer`
- **Errors:** `404`, `400` (duplicate)

---

#### `DELETE /customers/{customer_id}/`

Delete a customer.

- **Auth:** Bearer
- **Success (200):** `data = null`, `message = "Customer deleted successfully"`
- **Errors:** `404 Customer not found`

---

#### `POST /customers/{customer_id}/assign-fonts/`

Assign one or more fonts to a customer. Internally creates a `Sale` row per new font with `quantity = 1` and `price_at_sale = font.price`. Fonts already owned by the customer are silently skipped.

- **Auth:** Bearer
- **Body:**
```json
{ "font_ids": [1, 2, 5] }
```
- **Success (200):**
  - When new fonts are assigned: `data = null`, `message = "Fonts assigned successfully"`
  - When all are duplicates: `data = null`, `message = "All fonts are already assigned to this customer"`
- **Errors:** `404 Customer not found`

---

### 6.4 Sales

#### `GET /sales/`

List all sales.

- **Auth:** Bearer
- **Success (200):** `data = [ Sale, Sale, ... ]`

---

#### `POST /sales/`

Record a sale. `price_at_sale` is captured from the font's current price server-side — clients do not send price.

- **Auth:** Bearer
- **Body:**
```json
{ "customer": 10, "font": 1, "quantity": 1 }
```
| Field | Type | Required | Notes |
|---|---|---|---|
| `customer` | integer | yes | Customer id |
| `font` | integer | yes | Font id |
| `quantity` | integer | yes | |

- **Success (201):** `data = Sale`
- **Errors:** `404 Customer not found`, `404 Font not found`

---

#### `GET /sales/{sale_id}/`

Get a single sale.

- **Auth:** Bearer
- **Success (200):** `data = Sale`
- **Errors:** `404 Sale not found`

---

#### `GET /sales/today/count/`

Count of sales recorded today (UTC).

- **Auth:** Bearer
- **Success (200):** `data = { "count": 5 }`

---

#### `GET /sales/total/count/`

Total sales count, all time.

- **Auth:** Bearer
- **Success (200):** `data = { "count": 1234 }`

---

### 6.5 Dashboard

#### `GET /dashboard/summary/`

Aggregate counters for the home screen.

- **Auth:** Bearer
- **Success (200):**
```json
{
  "status": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "today_sales_count": 5,
    "total_sales_count": 1234,
    "total_customers": 567,
    "total_fonts": 89
  }
}
```

---

#### `GET /dashboard/trending-fonts/`

Top 10 fonts by number of sales (descending).

- **Auth:** Bearer
- **Success (200):** `data = [ TrendingFont, TrendingFont, ... ]` (max 10)

---

## 7. Client Integration Recipes

### 7.1 `cURL` examples

```bash
# Login
curl -X POST https://api.fontspell.example.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret123"}'

# Authenticated request
curl https://api.fontspell.example.com/api/fonts/ \
  -H "Authorization: Bearer <access_token>"

# Create customer
curl -X POST https://api.fontspell.example.com/api/customers/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","phone":"+15551234567","email":"jane@example.com"}'
```

### 7.2 JavaScript / TypeScript (`fetch`)

```ts
type ApiResponse<T> = { status: boolean; message: string; data: T | null };

const BASE_URL = "https://api.fontspell.example.com/api";

async function api<T>(path: string, init: RequestInit = {}): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("access_token");
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });
  return res.json();
}

// Login
const login = (email: string, password: string) =>
  api<{ access: string; refresh: string; user: { id: number; email: string } }>(
    "/auth/login/",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );

// List fonts
const listFonts = () => api<Array<{ id: number; name: string; price: number; weight: number; created_at: string }>>("/fonts/");
```

### 7.3 Dart / Flutter (`http`)

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  static const baseUrl = 'https://api.fontspell.example.com/api';
  String? accessToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (accessToken != null) 'Authorization': 'Bearer $accessToken',
      };

  Future<Map<String, dynamic>> request(String path, {String method = 'GET', Object? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final res = await (switch (method) {
      'GET' => http.get(uri, headers: _headers),
      'DELETE' => http.delete(uri, headers: _headers),
      _ => http.Request(method, uri).let((r) {
            r.headers.addAll(_headers);
            if (body != null) r.body = jsonEncode(body);
            return http.Response.fromStream(r.send());
          }) as Future<http.Response>,
    });
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
```

### 7.4 Token refresh interceptor (pseudocode)

```text
function callApi(req):
    res = send(req with access token)
    if res.http_status == 401:
        refresh_res = POST /auth/refresh/ { refresh: stored_refresh }
        if refresh_res.status == true:
            store(refresh_res.data.access)
            res = send(req with NEW access token)
        else:
            clearTokens(); navigateToLogin()
    return res
```

---

## 8. Error Handling Cheatsheet

| HTTP | Envelope `message` (typical) | When |
|---|---|---|
| 400 | "Inactive user" / "...already exists" | Business-rule violation |
| 401 | "Not authenticated" / "Incorrect email or password" / "Could not validate credentials" / "Invalid token type" | Missing or invalid token |
| 404 | "Customer not found" / "Font not found" / "Sale not found" / "Not Found" | Resource missing |
| 422 | "Validation error" (`data` is an array of field errors) | Body failed Pydantic validation |
| 500 | "Internal server error" | Unhandled server bug |

**Idiomatic client check:**

```ts
const r = await api("/customers/", { ... });
if (!r.status) {
  showToast(r.message);
  return;
}
useData(r.data);
```

---

## 9. Notes & Gotchas

- **Trailing slashes are mandatory** on every path.
- **Uniqueness** is enforced on: `Font.name`, `Customer.email`, `Customer.phone`, `Customer.phone2`. Plan UI validation accordingly.
- **`assign-fonts`** is idempotent for already-owned fonts — duplicates are silently skipped, you'll get a different `message`.
- **`price_at_sale`** is server-captured; never trust a client-submitted price.
- **Dates** in input bodies aren't required anywhere — `created_at` and `sale_date` are server-set.
- **Pagination** is not implemented — list endpoints return all rows. If you expect large datasets, request a pagination feature.
- **CORS** is currently `*` — anything goes in dev. Tighten before production.
- **Token expiry** is effectively infinite today, but you should still implement the refresh flow so the client survives a future tightening of expiry.

---

## 10. Quick Smoke Test (after wiring up)

1. `POST /auth/create-superadmin/` with a fresh email/password.
2. `POST /auth/login/` → save `data.access` and `data.refresh`.
3. `GET /auth/me/` with `Authorization: Bearer <access>` → expect your email back inside `data`.
4. `POST /fonts/` with a unique name, price, weight → expect `Font` back.
5. `POST /customers/` with unique phone/email → expect `Customer` back.
6. `POST /customers/{id}/assign-fonts/` with `{ font_ids: [<font_id>] }` → expect success message.
7. `GET /dashboard/summary/` → counters reflect your inserts.

If all seven pass, the integration is healthy.
