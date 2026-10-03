# Mat & Vin

Receptbok med vinförslag, och senare matchning mot den egna vinkällaren. Webbplats och iPhone-app (PWA).

A personal recipe notebook with wine pairing suggestions, later matched against your own wine cellar. Django + HTMX, Swedish UI, installable on iPhone via "Lägg till på hemskärmen".

## Kom igång lokalt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Öppna http://127.0.0.1:8000 och logga in. Admin finns på `/admin/`.

## Tester

```bash
python manage.py test
```

## Inställningar (miljövariabler)

| Variabel | Standard | Beskrivning |
|---|---|---|
| `DJANGO_DEBUG` | `1` | Sätt till `0` i produktion |
| `DJANGO_SECRET_KEY` | (dev-nyckel) | Krävs när DEBUG är av |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Kommaseparerade värdnamn |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | | T.ex. `https://matochvin.example.com` |
| `DATABASE_URL` | SQLite i projektmappen | T.ex. `postgres://...` |
| `DJANGO_MEDIA_ROOT` | `./media` | Var uppladdade bilder sparas |
| `ALLOW_SIGNUP` | `0` | `1` öppnar `/konto/registrera/` |
| `ANTHROPIC_API_KEY` | | Nyckel från console.anthropic.com. Utan nyckel används bara de inbyggda reglerna |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Claude-modell för vinförslag |

## Struktur

- `config/` inställningar och URL:er
- `core/` start, inloggning, PWA (manifest, service worker, offlinesida)
- `recipes/` recept, taggar, sök
- `wine/` vinstilar, receptprofil, pairingregler (`rules.py`) och Claude (`ai.py`)

## Vinförslag

1. Claude läser receptet och fyller i en profil: huvudingrediens, tillagning, sås, tyngd och smaker. Utan API-nyckel fyller du i den själv ("Beskriv rätten").
2. Reglerna i `wine/rules.py` poängsätter alla vinstilar mot profilen och dina tidigare tumme upp/ner.
3. Claude väljer de tre bästa bland reglernas åtta toppkandidater och motiverar dem.

Vinstilarna finns i `wine/styles_data.py`. Efter ändringar där: `python manage.py sync_wine_styles`.
- `templates/`, `static/` HTML, CSS, JS (HTMX och Pico CSS ligger under `static/vendor/`)
