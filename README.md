# SmartCommerce Kenya

A production-ready AI-assisted e-commerce platform optimized for African payments and logistics, with a focus on the Kenyan market.

## Project Vision

SmartCommerce Kenya is a full-stack Django + React e-commerce system designed to look and behave like a real startup product:

- **Payments**: M-Pesa Daraja STK Push + Stripe Checkout (sandbox)
- **Currency**: Kenyan Shillings (KES) with optional USD/EUR conversion
- **Multi-Vendor Marketplace**: Vendor onboarding, product management, commissions, payouts
- **AI & Automation**:
  - Product recommendations
  - Real-time stock updates (WebSockets)
  - Smart cart recovery (email + coupons)
  - Basic fraud detection
- **Search & Performance**:
  - Meilisearch/Elasticsearch for advanced search
  - Redis caching, Celery background tasks, pagination
- **Dashboards**:
  - Admin, Vendor, and Customer dashboards
  - Revenue and growth analytics

## Tech Stack

- **Backend**: Django, Django REST Framework, PostgreSQL, Redis, Celery, Django Channels
- **Frontend**: React (Vite/SPA), React Query or Redux Toolkit, TailwindCSS or similar
- **Search**: Meilisearch or Elasticsearch
- **Payments**: Stripe (sandbox), M-Pesa Daraja API
- **Storage**: AWS S3 or Cloudinary
- **Infrastructure**: Docker, Docker Compose, GitHub Actions CI/CD

## High-Level Features

- Product catalog with variants, categories, inventory tracking, CSV bulk upload
- Customer accounts with JWT auth, address book, order history
- Cart, wishlist, save-for-later, checkout flow
- Orders with statuses, invoices, and email notifications
- Multi-vendor marketplace with commissions and payouts
- AI-based recommendations and smart cart recovery
- Real-time stock updates to prevent overselling
- Advanced search with filters and typo tolerance
- Delivery cost calculator based on Kenyan counties and distance
- Fraud detection rules with admin review tools

## Development Workflow

- Default branches:
  - `main` – production-ready
  - `develop` – integration branch
- Feature branches: `feature/<short-desc>-<id>`  
  Example: `feature/auth-jwt-001`
- Commit style: **Conventional Commits**, e.g.:
  - `feat(auth): add JWT login and refresh endpoints`
  - `fix(payment): handle failed M-Pesa callback`
- Releases use semantic versioning tags:
  - `v0.1.0`, `v0.2.0`, ..., `v1.0.0`

## Getting Started (dev)

> These steps will be refined as the project evolves.

1. **Clone**
   ```bash
   git clone https://github.com/franklineXonguti/smartcommerce-kenya.git
   cd smartcommerce-kenya
   ```

2. **Backend setup (Django)**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # then configure DB, Redis, Stripe, M-Pesa, etc.
   python manage.py migrate
   python manage.py runserver
   ```

3. **Frontend setup (React)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Visit**
   - API: http://localhost:8000/
   - Frontend: http://localhost:5173/ (or Vite default)

## License

This project is licensed under the MIT License – see the LICENSE file for details.
