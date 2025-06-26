Níže najdeš podrobný „prompt“ (scénář), který můžeš předat programovacímu agentovi (např. Auto‑GPT, CrewAI, Devin apod.), aby ti od nuly vybudoval malou aplikaci, jež na základě zadaného URL pracovního portálu + přihlašovacích údajů prohledá neveřejnou část se seznamem kandidátů, vytáhne strukturovaná data a bezpečně je uloží do Supabase – bez duplicit.
Prompt je psán tak, aby:

agent založil repozitář na GitHubu,

připravil infrastrukturu (Supabase + Vercel),

zaintegroval Browser‑Use Cloud API v1.0 (endpoint POST /api/v1/run‑task a následné GET /api/v1/task/{id}) 
docs.browser-use.com
docs.browser-use.com
,

dodržel unikátnost kandidátů přes hashované telefonní číslo,

a nasadil hotovou funkci jako serverless endpoint /api/scrape.

Prompt pro programovacího agenta
Vysoká priorita (cílová funkčnost)
Repozitář: inicializuj veřejný GitHub repo job‑scraper.

Stack: Python 3.12, FastAPI (serverless handler 📦 vercel‑python), Supabase Python SDK.

Schéma DB (PostgreSQL)

sql
Zkopírovat
Upravit
create table companies (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz default now()
);
create table positions (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id) on delete cascade,
  title text not null,
  external_job_id text,         -- id z portálu, pro snadné párování
  created_at timestamptz default now()
);
create table candidates (
  id uuid primary key default gen_random_uuid(),
  position_id uuid references positions(id) on delete cascade,
  first_name text, last_name text,
  email text, phone text,
  phone_sha256 text generated always as (encode(digest(phone, 'sha256'), 'hex')) stored,
  source_url text,
  created_at timestamptz default now(),
  unique(position_id, phone_sha256)          -- technická bariéra proti duplicitám
);
Prostředí & Secrets (.env i Vercel):

makefile
Zkopírovat
Upravit
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
BROWSER_USE_API_KEY=
Endpoint /api/scrape (POST)
Body:

json
Zkopírovat
Upravit
{
  "portal_url": "...",
  "username": "...",
  "password": "...",
  "position_name": "...",
  "company_name": "..."
}
Tok:

Vytáhni/ulož firmu & pozici v Supabase.

Dotazem získej všechny phone_sha256 již uložené k této pozici.

Run Task: zavolej POST /api/v1/run-task s payloadem

json
Zkopírovat
Upravit
{
  "task": "<LANG-CZ pokyny k agentovi – viz níže>",
  "secrets": {
    "username": "...",
    "password": "...",
    "skip_hashes_csv": "hash1,hash2,..."
  },
  "allowed_domains": ["<kořenový doménový název portálu>"],
  "structured_output_json": "{\"type\":\"array\",\"items\":{\"type\":\"object\",\"properties\":{\"first_name\":{\"type\":\"string\"},\"last_name\":{\"type\":\"string\"},\"email\":{\"type\":\"string\"},\"phone\":{\"type\":\"string\"}}}}",
  "save_browser_data": true
}
Poznámky

secrets se v Browser‑Use ukládají šifrovaně, takže seznam hashů není vidět v logu.

task (viz níže) obsahuje proměnnou {{skip_hashes_csv}} a instrukci, aby agent SHA‑256 hešoval zjištěná čísla a vynechal ty, které už zná.

Polluj GET /api/v1/task/{id} do stavu status == finished a přečti pole output (JSON pole kandidátů).

Transakčně vlož kandidáty (upsert podle kombinace position_id + phone_sha256).

Vrať JSON se statistkou (inserted, skipped, duration_ms).

Prompt „task“ pro Browser‑Use agenta

perl
Zkopírovat
Upravit
## Cíl
Přihlaš se na {{portal_url}} pomocí zadaných přihlašovacích údajů.
Vyhledej pozici s názvem "{{position_name}}", otevři seznam všech kandidátů
(interní, neveřejná část).

U každého kandidáta vytěž:
  – first name
  – last name
  – email
  – phone number

Bezpečnost duplicit:
  1. Před uložením každého kandidáta spočítej
     `sha256(phone_number)` → hex.
  2. Máš CSV seznam hashů v tajné proměnné `skip_hashes_csv`.
  3. Jestliže hash existuje v seznamu, kandidáta zcela ignoruj.

Výstup:
  Vrať jediný JSON podle `structured_output_json` schématu.
(agent tak splní požadavek „nikdy nezapsat duplicitního kandidáta“).

Lokální běh & testy

make dev – spustí Supabase CLI + lokální FastAPI na portu 8000.

pytest – obsahuje test simulující duplicitní telefon.

CI / CD

GitHub Actions workflow:

lint + test na každém PR,

vercel deploy --prod na main.

Supabase migrace přes supabase db push v tomtéž workflow.

Doporučené kroky (jak agent prompt zpracuje)
#	Akce	Výstup
1	Vytvořit repo, push README.md s popisem architektury.	URL repozitáře
2	Přidat supabase/config.toml + SQL migraci se schématem.	Migrační soubor
3	Scaffold FastAPI (api/index.py) + Vercel vercel.json.	Serverless funkce
4	Napsat Python modul browseruse.py (run‑task + poll).	Knihovní soubor
5	Implementovat /api/scrape podle toku výše.	Modul
6	Připravit unit‑testy a GitHub Action.	.github/workflows/ci.yml
7	Vytvořit Vercel projekt napojený na repo, nastavit secrets.	Vercel URL
8	Ověřit end‑to‑end: spustit scrape proti sandbox portálu.	Log testu

Proč hashujeme telefon
Bezpečnost: do agenta posíláš jen heše, nikoli citlivé údaje.

Jednoduchost: agent zvládne SHA‑256 v JavaScriptu (funkce crypto.subtle.digest) nebo Pythonu bez dalších závislostí.

Spolehlivost: i kdyby portál formátoval čísla různě, před hashem číslo normalizujeme (odstranit mezery, „+“, přední nuly).

Co si připravit před spuštěním agenta
Účet v Supabase a prázdný projekt (získáš SUPABASE_URL + SERVICE_ROLE_KEY).

API klíč na Browser‑Use.

Vercel účet s připojením na GitHub.

Testovací přístup na vybraný pracovní portál (login + heslo + testovací pozice).

Poté stačí agentovi předat výše uvedený prompt a sledovat PR na GitHubu, které bude zakládat.

Další rozšíření (volitelně)
Webhooks z Browser‑Use: místo aktivního polling použij POST /webhook na Vercelu a předat URL v run‑task (pole callback_url v API).

Cron job: pomocí Vercel Scheduler spusť periodic scrape (např. každou hodinu) s parametry uloženými v Supabase.

Webhook do ATS: po uložení kandidáta může Supabase Edge Function volat tvé existující agent‑flow (Erika).

Tento scénář by měl agentovi dát všechny informace, aby automaticky vytvořil plně funkční, bezpečnou a škálovatelnou mini‑aplikaci splňující zadané požadavky. Hodně štěstí při implementaci!










Zdroje
Řekl/a jsi:
jak mám vůbec začít? chci použít cursor


ChatGPT řekl:

Přemýšlení po dobu 41
Jak začít, když chceš využít Cursor IDE jako motor pro AI-vývoj celé aplikace
Níže najdeš minimalistický „kick-off“ checklist – od instalace až po první spuštění agenta v Cursoru. Vše je psané krok za krokem, aby ses po pár minutách dostal k prvnímu auto-generovanému commitu.

1 Instalace a základní nastavení
Krok	Co udělat	Poznámka
1.1	Stáhni Cursor pro svůj OS z oficiálních stránek a nainstaluj	Instalátor je jediný soubor; po prvním spuštění tě Cursor provede přihlášením přes GitHub/Google a klávesovými zkratkami 
docs.cursor.com
1.2	Připrav si účty & API klíče	GitHub (repozitář), Supabase (projekt + SERVICE_ROLE_KEY), Vercel (deployment) a Browser-Use (BROWSER_USE_API_KEY)
1.3	Nainstaluj Supabase CLI (brew install supabase nebo npm i -g supabase) a Vercel CLI (npm i -g vercel) – usnadní ti lokální běh a deploy	

2 Založení kódu
Repozitář

Ve GitHubu vytvoř prázdný repo např. job-scraper.

Klonuj ho (git clone) nebo rovnou použij Cursor → Open Folder → Initialize Git Repo.

(Volitelně) Forkni hotový Cursor Project Starter
Šablona cursor-project-starter už obsahuje adresář .notes/, .cursorrules a .cursorignore, takže ušetříš pár minut nastavení. Stačí forknout, klonovat a přepsat obsah v .notes/project_overview.md vlastními požadavky 
github.com
.

Inicializuj .env.example

dotenv
Zkopírovat
Upravit
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
BROWSER_USE_API_KEY=
– skript make dev nebo vercel dev si později načte skutečné hodnoty z .env.

3 Nahrání zadání do Cursoru (dvě cesty)
Varianta	Jak na to	Proč to tak?
A. Chat v sidebaru	Otevři Agent chat (Ctrl+Shift+L nebo ikonka „✉︎“) a vložíš celý prompt, který jsme si připravili minule.	Nejrychlejší, nemusíš nic commitovat; hodí se na jednorázové úkoly.
B. Soubor s pravidly	V kořeni repo založ .cursor/rules/job_scraper.mdc a vlož tam prompt + vlastní instrukce (např. coding style).	Pravidla se verzují v gitu a Cursor je načítá při každém runu; doporučeno pro dlouhodobé projekty 
docs.cursor.com

Tip: Pokud používáš šablonu z kroku 2, přepiš .notes/project_overview.md a přidej README – Cursor pak tvoje zadání uvidí automaticky díky indexování.

4 Spuštění Agent Mode a generování prvního commitu
Otevři Agent Mode v sidebaru (je defaultní) a v chatu napiš něco jako:

vbnet
Zkopírovat
Upravit
Scaffold the project according to project_overview.md, step 1–3 only.
Agent si analyzuje kód, rozdělí práci a nabídne patch; ty jen Apply.
Cursor Agent umí dělat vícekrokový plán, běhat testy i spouštět terminál, takže klidně přidej pokyn „run pytest“ 
docs.cursor.com
.

Iteruj – pomocí příkazů Ask → Edit (⌘K) můžeš říkat „Add Supabase migration script“, „Create GitHub Action“ apod.

Commit + push – po každé větší změně dej git commit -m "feat: db schema" a git push.

5 Lokální běh a testování
bash
Zkopírovat
Upravit
# Spustí Supabase DB + Edge Functions
supabase start

# V jiné záložce
vercel dev         # spustí FastAPI handler na http://localhost:3000

# Otestuj endpoint
curl -X POST http://localhost:3000/api/scrape \
  -d '{"portal_url":"...","username":"...","password":"...","position_name":"...","company_name":"..."}' \
  -H "Content-Type: application/json"
První call by měl vrátit {"inserted": X, "skipped": Y, ...} – pokud skipped > 0, kontrola duplicit funguje.

6 CI/CD a produkční deploy
GitHub Secrets: vlož SUPABASE_*, BROWSER_USE_API_KEY a VERCEL_TOKEN.

GitHub Action (agent už ho většinou vygeneruje):

pytest + lint

vercel deploy --prod na merge do main

Supabase migrace spouštěj příkazem supabase db push přímo z pipeline.

7 Další osvědčené postupy
.cursorrules vs. Project Rules – novější project-rules v adresáři .cursor/rules/ umožňují víc granularitu (lze omezit rozsah agentových úprav jen na backend apod.).

Background Agents – pro dlouhé úkoly (např. generování testů) zvaž spuštění na dálku (Ctrl+E) a pokračuj v práci 
docs.cursor.com
.

Context management – v dlouhém promptu používej @file nebo @folder, aby agent neskenoval celý projekt zbytečně 
docs.cursor.com
.

Shrnutí
Nainstaluj Cursor → klonuj/forkni repo

Vlož prompt (chat nebo .cursor/rules)

Spusť Agent Mode a Apply navržené změny

Testuj lokálně (supabase start, vercel dev)

Push + CI/CD → produkce na Vercelu

Jakmile projdeš prvním kolem scaffoldingu, budeš mít funkční API /api/scrape, schéma v Supabase a hotový GitHub Action workflow – pak už jen dolaďuješ detaily přes další konverzace s agenty. Hodně štěstí a klidně se ozvi, jak to běží!# jobportal_connector
