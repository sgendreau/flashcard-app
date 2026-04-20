# ============================================
#  Quikko — Makefile
# ============================================

.PHONY: help install backend frontend dev seed test lint clean logs

# ---------- Aide ----------
help: ## Afficher cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------- Installation ----------
install: install-backend install-frontend ## Installer toutes les dépendances

install-backend: ## Installer les dépendances Python
	cd backend && pip install -r requirements.txt

install-frontend: ## Installer les dépendances Node (yarn)
	cd frontend && yarn install

# ---------- Lancement ----------
backend: ## Lancer le backend FastAPI (port 8001)
	cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

frontend: ## Lancer le frontend Expo (port 3000)
	cd frontend && npx expo start --port 3000

frontend-tunnel: ## Lancer le frontend Expo avec tunnel
	cd frontend && npx expo start --tunnel --port 3000

dev: ## Lancer backend + frontend en parallèle
	@echo "Lancement du backend..."
	cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
	@echo "Lancement du frontend..."
	cd frontend && npx expo start --port 3000

# ---------- Base de données ----------
seed: ## Relancer le seeding (redémarrer le backend)
	@echo "Le seed s'exécute automatiquement au démarrage du backend."
	@echo "Redémarrage..."
	@pkill -f "uvicorn server:app" 2>/dev/null || true
	cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload &

mongo-shell: ## Ouvrir le shell MongoDB
	mongosh mongodb://localhost:27017/test_database

mongo-reset: ## Supprimer toutes les données et re-seeder
	mongosh mongodb://localhost:27017/test_database --eval "db.dropDatabase()"
	@echo "Base de données vidée. Redémarrez le backend pour re-seeder."

# ---------- Tests ----------
test: ## Lancer les tests backend (pytest)
	cd backend && python -m pytest tests/ -v

test-api: ## Tester les endpoints principaux avec curl
	@echo "=== Login ==="
	@curl -s -X POST http://localhost:8001/api/auth/login \
		-H "Content-Type: application/json" \
		-d '{"email":"admin@flashcards.com","password":"admin123"}' | python3 -m json.tool
	@echo "\n=== Subjects ==="
	@TOKEN=$$(curl -s -X POST http://localhost:8001/api/auth/login \
		-H "Content-Type: application/json" \
		-d '{"email":"admin@flashcards.com","password":"admin123"}' | \
		python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	curl -s http://localhost:8001/api/subjects -H "Authorization: Bearer $$TOKEN" | python3 -m json.tool

# ---------- Qualité de code ----------
lint: lint-backend lint-frontend ## Linter backend + frontend

lint-backend: ## Linter le code Python
	cd backend && python -m flake8 server.py --max-line-length 150 --ignore E402,E501,W503,E302,E303,W291

lint-frontend: ## Linter le code TypeScript/React
	cd frontend && npx eslint app/ src/ --ext .ts,.tsx

format: ## Formater le code Python
	cd backend && python -m black server.py --line-length 150
	cd backend && python -m isort server.py

# ---------- Logs ----------
logs: ## Afficher les logs backend + frontend
	@echo "=== Backend ==="
	@tail -20 /var/log/supervisor/backend.err.log 2>/dev/null || echo "Pas de logs backend"
	@echo "\n=== Frontend ==="
	@tail -20 /var/log/supervisor/expo.out.log 2>/dev/null || echo "Pas de logs frontend"

logs-backend: ## Suivre les logs backend en direct
	tail -f /var/log/supervisor/backend.err.log /var/log/supervisor/backend.out.log

logs-frontend: ## Suivre les logs frontend en direct
	tail -f /var/log/supervisor/expo.out.log /var/log/supervisor/expo.err.log

# ---------- Nettoyage ----------
clean: ## Nettoyer les caches et fichiers temporaires
	rm -rf frontend/node_modules/.cache
	rm -rf frontend/.metro-cache
	rm -rf frontend/.expo
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Caches nettoyés."

# ---------- Environnement ----------
env-setup: ## Créer les fichiers .env à partir des .env.example
	@test -f backend/.env || (cp backend/.env.example backend/.env && echo "backend/.env créé")
	@test -f frontend/.env || (cp frontend/.env.example frontend/.env && echo "frontend/.env créé")
	@test -f backend/.env && echo "backend/.env existe déjà" || true
	@test -f frontend/.env && echo "frontend/.env existe déjà" || true

jwt-secret: ## Générer une nouvelle clé JWT
	@python3 -c "import secrets; print(secrets.token_hex(32))"
