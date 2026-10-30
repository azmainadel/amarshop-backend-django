# amarshop-backend

Django REST API for the AmarShop e-commerce app: users, products, cart, checkout with a mock payment, and admin reports.

## Requirements

- Python 3.10–3.13
- Docker with Docker Compose, for the local Postgres database

## Run locally

Run these from the project root unless noted.

1. Create and activate a virtual environment, then install the packages:

   `python -m venv .venv && source .venv/bin/activate`

   `pip install -r requirements.txt`

2. Start the database (from the `docker` folder):

   `docker compose up -d`

3. Create the tables:

   `python manage.py migrate`

4. Create an admin user. Staff users can call `/api/admin/` and log in to `/admin/`:

   `python manage.py createsuperuser`

5. Start the server at http://127.0.0.1:8000:

   `python manage.py runserver`

Run the tests with `python manage.py test`.

## Configuration

Settings are read from environment variables or a `.env` file in the project root. The defaults match the Docker database, so local runs need no setup.

| Variable | Default |
| --- | --- |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | `amarshop_db`, `db_admin`, `123456` |
| `DB_HOST`, `DB_PORT` | `localhost`, `5432` |
| `EMAIL_BACKEND` | console (emails print to the server log) |
| `DEFAULT_FROM_EMAIL` | `no-reply@amarshop.local` |
| `PASSWORD_RESET_URL` | `http://localhost:3000/reset-password` |

## APIs

All endpoints except register, login and password reset need an `Authorization: Bearer <access_token>` header. You get the token from login or register.

| Area | Base path | Endpoints |
| --- | --- | --- |
| Users | `/api/users/` | `register/`, `login/`, `logout/`, `profile/`, `addresses/`, `password-reset/`, `password-reset/confirm/` |
| Products | `/api/products/` | `products/`, `products/{id}/`, `products/search/`, `products/filter/`, `categories/`, `brands/` |
| Cart | `/api/cart/` | `cart/`, `cart/add_item/`, `cart/update-item/{id}/`, `cart/remove-item/{id}/`, `saved_item/`, `saved_item/save-for-later/`, `saved_item/{id}/move_to_cart/` |
| Orders | `/api/order/` | `orders/`, `orders/{id}/`, `orders/checkout/`, `orders/payment/mock/` |
| Admin (staff only) | `/api/admin/` | `users/`, `products/`, `transactions/`, `reports/?type=sales\|users\|inventory` |

Placing an order takes two calls. `checkout/` with an `address_id` creates a pending order from the cart. `payment/mock/` with the `order_id` pays it. Send `"payment_info": {"simulate": "fail"}` to test a declined payment.
