# Job Recommender

Plateforme de recommandation d'offres d'emploi et de stages basée sur des agents IA.

[![CI](https://github.com/RouaBenTiba/DEPOT/actions/workflows/ci.yml/badge.svg)](https://github.com/RouaBenTiba/DEPOT/actions/workflows/ci.yml)

## Structure

- backend/ : API FastAPI et agent LangGraph
- frontend/ : interface React + TypeScript
- evaluation/ : jeu annoté et métriques
- infra/ : Docker et Terraform
- docs/ : cahier des charges, architecture

  ## Démarrage rapide

  docker compose up --build
  - API : http://localhost:8000/health
  - Interface : http://localhost:3000

## Base de données

```bash
docker compose up -d postgres
cd backend
alembic upgrade head      # applique les migrations
alembic revision --autogenerate -m "message"   # crée une migration après un changement de modèle
```
