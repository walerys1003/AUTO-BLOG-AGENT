# Naprawa Uprawnień WordPress dla API

## Problem
Błąd: `rest_cannot_create` - Brak uprawnień do tworzenia wpisów jako zalogowany użytkownik.

## Rozwiązanie Krok Po Kroku

### 1. Zaloguj się do WordPress Admin
```
URL: https://mamatestuje.com/wp-admin
Użytkownik: TomaszKotlinski
Hasło: [hasło administratora]
```

### 2. Sprawdź Rolę Użytkownika
1. Przejdź do: **Użytkownicy → Wszyscy użytkownicy**
2. Znajdź użytkownika: **TomaszKotlinski**
3. Sprawdź rolę - powinna być: **Administrator** lub **Redaktor**
4. Jeśli ma rolę **Autor** lub **Współpracownik** - zmień na **Redaktor**

### 3. Sprawdź Application Password
1. Przejdź do: **Użytkownicy → Profil**
2. Przewiń na dół do sekcji: **Hasła aplikacji**
3. Sprawdź czy istnieje aktywne hasło aplikacji
4. Jeśli nie ma - utwórz nowe:
   - Nazwa: "MASTER AGENT AI"
   - Kliknij: **Dodaj nowe hasło aplikacji**
   - Zapisz wygenerowane hasło

### 4. Aktualizuj System
Po utworzeniu nowego Application Password, zaktualizuj dane w systemie:

```python
# Nowe dane logowania
username = "TomaszKotlinski"
new_app_password = "[NOWE_HASŁO_APLIKACJI]"
```

### 5. Sprawdź Ustawienia REST API
1. Przejdź do: **Ustawienia → Ogólne**
2. Sprawdź czy opcja **"Dostęp do REST API"** jest włączona
3. Jeśli nie ma tej opcji, sprawdź wtyczki

### 6. Alternatywne Rozwiązanie - Nowy Użytkownik
Jeśli problem nie zniknie, utwórz dedykowanego użytkownika API:

1. **Użytkownicy → Dodaj nowego**
2. **Login:** `masteragent_api`
3. **Email:** `api@mamatestuje.com`
4. **Rola:** `Administrator`
5. **Utwórz Application Password** dla tego użytkownika

### 7. Test Uprawnień
Po wprowadzeniu zmian, przetestuj API:

```bash
curl -X GET "https://mamatestuje.com/wp-json/wp/v2/posts" \
  -u "USERNAME:APPLICATION_PASSWORD" \
  -H "Content-Type: application/json"
```

## Typowe Przyczyny Problemów

1. **Rola Użytkownika** - Autor/Współpracownik nie może tworzyć przez API
2. **Application Password** - Wygasł lub został usunięty
3. **Wtyczki Bezpieczeństwa** - Blokują dostęp REST API
4. **Ustawienia Serwera** - mod_security blokuje API calls

## Sprawdzenie Po Naprawie

```python
# Test autoryzacji
response = requests.get(
    "https://mamatestuje.com/wp-json/wp/v2/users/me",
    headers={"Authorization": f"Basic {token}"}
)

if response.status_code == 200:
    user_data = response.json()
    print(f"Użytkownik: {user_data['name']}")
    print(f"Rola: {user_data['roles']}")
    print(f"Uprawnienia: {user_data['capabilities']}")
```

## Kontakt z Administratorem
Jeśli problem nadal występuje, skontaktuj się z administratorem mamatestuje.com z prośbą o:
1. Sprawdzenie uprawnień użytkownika TomaszKotlinski
2. Włączenie dostępu REST API
3. Utworzenie dedykowanego konta API