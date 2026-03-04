# Changelog

All notable changes to SmartCommerce Kenya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- JWT authentication system with login and refresh tokens
- User registration with password validation
- Email verification workflow (tokens generated, email sending in Phase 6)
- Password reset request and confirmation endpoints
- User profile management (view and update)
- Password change functionality
- Address book CRUD with Kenyan county validation
- 47 Kenyan counties constants and validators
- Phone number validation and normalization for Kenyan formats
- Frontend authentication store using Zustand with persistence
- Login and registration pages with form validation
- Protected routes and authentication state management
- Comprehensive test coverage for authentication APIs

## [0.0.1-alpha] - 2026-03-04

### Added
- Repository initialization with README, LICENSE, and .gitignore
- Contributing guidelines and CODEOWNERS
- Pre-commit hooks for code quality (black, isort, flake8, prettier)
- GitHub Actions CI pipelines for backend and frontend
- Git workflow and branching strategy documentation
- Conventional commit standards
- Django project scaffolding with multi-environment settings (dev/staging/prod/test)
- Core service apps: users, products, orders, payments, vendors, recommendations, analytics, notifications
- Custom User model with Kenya-specific fields (phone, county)
- Address model with Kenyan location fields
- React + Vite frontend scaffolding
- Basic routing and API service setup
- Docker Compose configuration with PostgreSQL, Redis, and Meilisearch
- Celery configuration for background tasks
- DRF and JWT authentication setup
- OpenAPI documentation with drf-spectacular
