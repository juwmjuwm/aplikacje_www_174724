# The Timetabler

API JSON do tygodniowych planów zajęć, lekcji, sal, przedmiotów, grup uczniów i kont nauczycieli. Wykorzystuje Django, SQLite i tokeny JWT. Nie ma osobnego interfejsu użytkownika; korzystaj z interaktywnej strony API lub klienta HTTP.

## Uruchomienie lokalnego serwera

- Python **3.12 lub nowszy** oraz pip. Sprawdź wersję poleceniem `python --version`.
- Nie jest potrzebna zewnętrzna bazy danych: Django tworzy lokalną bazę SQLite podczas migracji.

Aby utworzyć nową bazę danych, uruchom te polecenia:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Jeśli PowerShell blokuje aktywację, w pozostałych poleceniach użyj `.\.venv\Scripts\python.exe` zamiast `python`. Środowisko wirtualne oddziela pakiety tego projektu od pakietów innych projektów Pythona.

Otwórz `.env` i przed kontynuowaniem zastąp przykładowe wartości:

```dotenv
DJANGO_SECRET_KEY=replace-with-your-own-long-random-secret
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=replace-with-your-own-strong-password
```

`DJANGO_SECRET_KEY` jest wymagany do uruchomienia Django i podpisywania tokenów JWT. Początkowe dane logowania administratora są potrzebne przy tworzeniu pierwszego administratora. Użyj unikalnego hasła mającego co najmniej osiem znaków, w tym małe i wielkie litery, cyfrę oraz znak interpunkcyjny lub symbol; Django odrzuca także hasła popularne lub łatwe do odgadnięcia.

Utwórz tabele, początkowe role i konto, a następnie uruchom serwer za pomocą komend:

```sh
python manage.py migrate
python manage.py bootstrap_accounts
python manage.py runserver
```

Polecenie `bootstrap_accounts` tworzy grupy (role) `PLANNER` i `TEACHER` oraz tworzy administratora tylko wtedy, gdy jeszcze żaden nie istnieje; ponowne uruchomienie nie resetuje hasła istniejącego administratora.

## Dokumentacja

- `http://127.0.0.1:8000/api/docs/` - aby skorzystać z interaktywnego API Swagger UI
- `http://127.0.0.1:8000/api/schema/` - aby zobaczyć schemat OpenAPI
- `http://127.0.0.1:8000/admin/` - aby skorzystać z panelu administracyjnego Django.


## Instrukcja obsługi

### Rejestracja i pobranie tokenów dostępu

W interfejsie Swagger UI (`/api/docs/`):

1. Otwórz `POST /api/register/`, kliknij **Try it out** i wyślij poniższy przykład, aby utworzyć konto `VIEWER`. Możesz też zalogować się danymi administratora z pliku `.env`.
2. Otwórz `POST /api/token/` i wyślij nazwę użytkownika oraz hasło. Skopiuj wartość `access` z odpowiedzi.
3. Kliknij **Authorize**, wklej token dostępu w polu `jwtAuth` i potwierdź. Swagger wysyła nagłówek `Authorization: Bearer <access token>` przy żądaniach wymagających uwierzytelnienia.
4. Wypróbuj `GET /api/rooms/`. Aby tworzyć lub edytować dane planowania zajęć, zaloguj się jako `ADMIN` lub poproś administratora o przypisanie konta do grupy `PLANNER`.

Treść żądania rejestracji:

```json
{"username":"john","password":"Strong-unique-pass-123!","first_name":"John","last_name":"Doe"}
```

Treść żądania pobrania tokenu dla `POST /api/token/`:

```json
{"username":"john","password":"Strong-unique-pass-123!"}
```

Odpowiedź z tokenami zawiera `access` i `refresh`. Access token traci ważność po 10 minutach, a refresh token po 1 tygodniu; wyślij `{"refresh":"<refresh token>"}` do `POST /api/token/refresh/`, aby otrzymać nowy token dostępu. Klient HTTP może wysłać:

```http
GET /api/rooms/ HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <access token>
```

### Konta i uprawnienia

| Rola lub przynależność do grupy | Dostępne działania |
| --- | --- |
| `VIEWER` | Odczyt danych planowania zajęć i zarządzanie własnym profilem. Jest to domyślna rola po rejestracji. |
| `TEACHER` | Uprawnienia roli VIEWER + możliwość przypisywania użytkownika do lekcji + użytkownik wyświetla się po wylistowaniu wszystkich nauczycieli. |
| `PLANNER` | Odczyt oraz tworzenie, aktualizowanie i usuwanie danych planowania zajęć. |
| `ADMIN` | Wszystkie działania dotyczące planowania zajęć, wyświetlanie listy użytkowników i zmiana ról; dostęp do panelu administracyjnego Django. |

Konto może jednocześnie należeć do grup `PLANNER` i `TEACHER`. Administratorzy również mogą należeć do grupy `TEACHER`. Dane planowania zajęć są współdzielone: każdy planista lub administrator może edytować dowolny plan zajęć. Uprawnienia odzwierciedlają aktualne role także w przypadku wcześniej wydanych tokenów dostępu.

| Punkt końcowy | Kto może korzystać | Cel i przykład |
| --- | --- | --- |
| `POST /api/register/` | Każdy | Utworzenie konta użytkownika `VIEWER`; użyj przedstawionej wyżej treści żądania rejestracji. |
| `POST /api/token/` | Każdy | Uzyskanie tokenów dostępu i odświeżania na podstawie nazwy użytkownika i hasła. |
| `POST /api/token/refresh/` | Każdy posiadacz tokenu odświeżania | Uzyskanie nowego tokenu dostępu. |
| `GET /api/users/` | Administrator | Wyświetlenie listy kont z podziałem na strony. |
| `GET /api/users/{id}/` | Dany użytkownik lub administrator | Odczyt danych konta. |
| `PATCH /api/users/{id}/` | Dany użytkownik lub administrator | Edycja `username`, `first_name` lub `last_name`; na przykład `{"first_name":"Alicja"}`. |
| `POST /api/users/me/password/` | Zalogowany użytkownik | Zmiana własnego hasła; wyślij `{"current_password":"Strong-unique-pass-123!","new_password":"Another-strong-pass-456!"}`. Zwraca 204; zaloguj się ponownie przy użyciu nowego hasła. |
| `PATCH /api/users/{id}/role/` | Administrator | Zastąpienie przynależności do grup; na przykład `{"roles":["PLANNER","TEACHER"]}`. |
| `DELETE /api/users/{id}/` | Dany użytkownik lub administrator | Usunięcie konta; zwraca 204. |

Żądanie zmiany ról musi zawierać pole `roles` z tablicą przynależności do grup. `{"roles":[]}` ustawia rolę `VIEWER`, a odpowiedź zawiera `"roles":["VIEWER"]`. `{"roles":["TEACHER"]}` i `{"roles":["PLANNER"]}` przyznają przynależność do jednej grupy; `{"roles":["PLANNER","TEACHER"]}` przyznaje obie. Odpowiedzi użytkowników i nauczycieli zawierają tylko pole `roles` opisujące role; starsze pole `role` w żądaniu jest odrzucane z kodem 400. Nie można przypisać ani usunąć roli `ADMIN` przez ten punkt końcowy ani usunąć roli `TEACHER` użytkownikowi z przypisanymi lekcjami. Najpierw przypisz te lekcje komuś innemu lub je usuń. Usunięcie administratora lub nauczyciela z przypisanymi lekcjami również zwraca 409.

Nazwy użytkowników zawierają tylko litery, cyfry dziesiętne i znaki podkreślenia (maksymalnie 150 znaków). Są normalizowane i porównywane bez rozróżniania wielkości liter, więc `Alice` i `alice` odnoszą się do tego samego konta. Imię i nazwisko są wymagane przy rejestracji, zawierają wyłącznie litery i są zapisywane z wielką pierwszą literą. Nowe hasła muszą spełniać wymagania z sekcji dotyczącej konfiguracji. Żądania dotyczące kont nie przyjmują adresu e-mail; odpowiedzi nie zawierają adresu e-mail ani haseł. Edycja profilu nie pozwala zmieniać haseł ani ról.

### API planowania zajęć

Uwierzytelnieni użytkownicy mogą odczytywać wszystkie kolekcje i poszczególne rekordy. Użytkownicy `PLANNER` i `ADMIN` mogą tworzyć rekordy, całkowicie je zastępować (`PUT`), częściowo aktualizować (`PATCH`) i usuwać, z wyjątkiem nauczycieli. Lista nauczycieli służy wyłącznie do odczytu; przypisz rolę `TEACHER` przez opisany wyżej punkt końcowy ról. Ścieżka kolekcji kończy się znakiem `/`; aby wskazać jeden element, dodaj jego ID, na przykład `GET /api/rooms/1/`. ID w odpowiedziach są tylko do odczytu.

| Kolekcja | Co przechowuje | Przykładowa treść żądania `POST` |
| --- | --- | --- |
| `/api/timetables/` | Plan zajęć z nazwą i opcjonalnym opisem. | `{"name":"Autumn","description":"Term 1"}` |
| `/api/student-groups/` | Grupę uczniów i jej dodatnią liczebność `size`. | `{"name":"Class 1A","size":25}` |
| `/api/subjects/` | Przedmiot z opcjonalnym opisem. | `{"name":"Biology","description":"Lab and theory"}` |
| `/api/rooms/` | Salę i jej dodatnią pojemność `capacity`. | `{"name":"Room 101","capacity":30}` |
| `/api/teachers/` | Użytkowników należących do grupy `TEACHER`, w tym nauczycieli z połączonymi rolami oraz administratorów będących nauczycielami. | Tylko odczyt: `GET /api/teachers/` lub `/api/teachers/{id}/`. |
| `/api/lessons/` | Cotygodniową lekcję łączącą powyższe rekordy z nauczycielem, dniem i godziną. | Zobacz przykład poniżej. |

Na przykład utwórz plan zajęć za pomocą `POST /api/timetables/` i `{"name":"Autumn"}`, a następnie użyj zwróconego `id` w lekcji. Najpierw utwórz grupę uczniów, przedmiot i salę oraz poproś administratora o przypisanie użytkownikowi roli `TEACHER`. `GET /api/teachers/` pokazuje ID nauczycieli, których można przypisać. Gdy te rekordy już istnieją, wyślij poniższą treść do `POST /api/lessons/`:

```json
{
  "timetable": 1,
  "student_group": 1,
  "subject": 1,
  "teacher": 7,
  "room": 1,
  "weekday": "MON",
  "start_time": "09:00:00",
  "end_time": "10:00:00"
}
```

Zastąp przykładowe ID wartościami z własnych odpowiedzi. Dozwolone dni tygodnia to `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT` i `SUN`. Godzina zakończenia musi być późniejsza niż godzina rozpoczęcia. Lekcje nie mogą nakładać się w tym samym dniu dla tej samej sali, tego samego nauczyciela lub tej samej grupy uczniów, nawet w różnych planach zajęć. Zaktualizuj lekcję za pomocą `PATCH /api/lessons/{id}/`, na przykład `{"room":2}`, albo usuń ją za pomocą `DELETE /api/lessons/{id}/`.

### Listowanie i wyszukiwanie

Odpowiedzi dla wszystkich kolekcji, w tym lista użytkowników dostępna administratorowi, są dzielone na strony:

```json
{
  "count":12,
  "next":"http://127.0.0.1:8000/api/rooms/?page=2",
  "previous":null,
  "results":[
    { "id":1, "name":"Room 101", "capacity":30 }
  ]
}
```

Rekordy odczytujemy z pola `results`. Domyślnie strony zawierają 10 rekordów. Użyj `?page=2&size=5`; `size` musi być dodatnie i nie może przekraczać 100. Użyj `search` do wyszukiwania częściowych dopasowań bez rozróżniania wielkości liter: w nazwach planów zajęć, grup uczniów i sal; w nazwie lub opisie przedmiotu; oraz w imionach lub nazwiskach nauczycieli. Na przykład `GET /api/subjects/?search=biology&size=5`. Lekcje i użytkownicy nie mają filtra wyszukiwania.
