.PHONY: dev test install setup-supabase

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