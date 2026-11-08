# hejnumbers-auto

Jeden Tag ein Top-4-Post auf Instagram, TikTok und LinkedIn – voll automatisch.

**Ablauf täglich (ca. 15–16 Uhr):** Claude wählt ein Thema, recherchiert im Web und prüft jede Zahl mit mindestens 2 Quellen. Ein zweiter, unabhängiger Faktencheck muss zustimmen. Fällt ein Thema durch, versucht es das Skript mit einem neuen (max. 3 Versuche, sonst kein Post und du bekommst eine Mail von GitHub). Danach werden Reel, Einzelbild und an Karusselltagen 4 Slides gerendert und an Buffer übergeben. Buffer veröffentlicht um 17:00.

**Formate:**
- TikTok: jeden Tag das Reel
- Instagram: Mo/Mi/Fr/So Reel, Di/Sa Karussell, Do Einzelbild
- LinkedIn: Karussell an Karusselltagen, sonst das Einzelbild

**Kommentare:** Freigabe in Buffer → „Community“ (Web oder App). Dort gibt es Antwortvorschläge, du wählst, passt an und sendest.

---

## Einrichtung (einmalig, ca. 1 Stunde)

### 1. Konten
1. Instagram auf Business-Konto umstellen (Profil → ☰ → Konto-Typ und Tools).
2. TikTok-Konto auf Business-Konto umstellen.
3. LinkedIn-Unternehmensseite „hejnumbers“ anlegen (LinkedIn → Für Unternehmen → Unternehmensseite erstellen).
4. Buffer-Konto anlegen und alle drei Kanäle verbinden (bei LinkedIn die **Seite** wählen, nicht dein Profil).

### 2. Schlüssel holen
1. **Buffer:** publish.buffer.com/settings/api → „Generate API key“. Sofort kopieren, er wird nur einmal angezeigt.
2. **Anthropic:** console.anthropic.com → API Keys → neuen Key anlegen, 10–20 € Guthaben aufladen.

### 3. GitHub-Repo
1. Auf github.com ein neues Repo `hejnumbers-auto` anlegen, **Public** (Buffer muss die Bilder über einen öffentlichen Link abrufen).
2. Alle Dateien aus diesem Ordner hochladen („Add file“ → „Upload files“, auch den Ordner `.github`).
3. Settings → Secrets and variables → Actions → „New repository secret“:
   - `ANTHROPIC_API_KEY`
   - `BUFFER_API_KEY`

### 4. Kanal-IDs eintragen
1. Im Repo: Actions → „Buffer-Kanäle anzeigen“ → „Run workflow“.
2. Im Protokoll stehen deine Kanäle mit ID.
3. Die IDs in `config.json` unter `channels` eintragen (im Repo auf die Datei klicken → Stift-Symbol → speichern).

### 5. Testen
1. Actions → „Täglicher Post“ → „Run workflow“ mit **draft = an** und **sample = an**. Das kostet nichts und legt in Buffer drei Entwürfe an. Prüfe dort Bild, Video und Text.
2. Danach noch einmal mit **draft = an**, **sample = aus**. Jetzt läuft die echte Recherche. Im Protokoll siehst du Thema und Faktencheck.
3. Wenn beides passt: Entwürfe in Buffer löschen. Ab jetzt läuft alles täglich von selbst.

Hinweis: Jeder Lauf speichert die Dateien unter `media/<datum>/` im Repo. Das ist gewollt, sonst kann Buffer sie nicht abrufen.

---

## Anpassen

- **Uhrzeit:** `post_time_berlin` in `config.json`. Der Lauf startet 14:00 UTC, also immer vor 17 Uhr Berliner Zeit.
- **Formate pro Wochentag:** `weekly_formats` (`reel`, `carousel`, `image`).
- **Themenbereiche:** `categories`.
- **Modell:** `model` (aktuelles Claude-Modell).
- **Pause:** Actions → „Täglicher Post“ → „…“ → „Disable workflow“.

## Wenn etwas schiefgeht

GitHub schickt dir bei einem Fehler eine Mail. Häufige Ursachen:
- **„Datei nicht öffentlich erreichbar“:** Das Repo ist privat. Auf Public stellen.
- **Buffer-Fehler bei einem Kanal:** Kanal in Buffer neu verbinden. Die anderen Kanäle werden trotzdem gepostet.
- **„Kein Thema hat den Faktencheck bestanden“:** Kommt selten vor. Am nächsten Tag geht es normal weiter.

## Grenzen

- Die Reels haben keine Musik. Wenn du Ton willst, ergänze ihn in Buffer im Entwurf oder später direkt in der App.
- Der Faktencheck senkt das Fehlerrisiko stark, schließt es aber nicht aus. Schau in der ersten Woche jeden Post kurz an.
