.PHONY: dev test install setup-supabase format lint

# Load environment variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

install:
	pip install -r requirements.txt

setup-supabase:
	supabase init
	supabase start
	supabase db reset

dev: install
	supabase start &
	uvicorn api.index:app --reload --port 8000

test:
	pytest -v

stop:
	supabase stop

clean:
	supabase stop
	docker system prune -f

migrate:
	supabase db push

reset-db:
	supabase db reset

logs:
	supabase logs

status:
	supabase status

format:
	python3 -m pip install black isort flake8
	python3 -m black .
	python3 -m isort .

lint:
	python3 -m pip install black isort flake8
	python3 -m black --check .
	python3 -m isort --check-only .
	python3 -m flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501

fix-all:
	python3 fix_formatting.py 