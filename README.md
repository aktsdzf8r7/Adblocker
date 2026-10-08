# Schild Adblocker

Browser-Erweiterung (Manifest V3), die **Werbung, Tracker, Pop-ups und YouTube-Werbung** blockiert –
für **Chrome, Edge, Brave, Opera, Vivaldi** und **Firefox (ab Version 128)**.

Schild nutzt die bewährten Filterlisten **EasyList**, **EasyPrivacy** und **EasyList Germany**
(rund 140.000 Filter) und wandelt sie in native Browser-Blockregeln um. Das Blockieren
übernimmt der Browser selbst – dadurch ist es sehr schnell und braucht kaum Speicher.
Schild sammelt keine Daten und sendet nichts ins Internet.

## Funktionen

- **Netzwerk-Blocker:** Werbe- und Tracking-Anfragen werden gar nicht erst geladen.
- **Element-Ausblendung:** leere Werbeflächen und Banner werden ausgeblendet (die Seite kann das nicht rückgängig machen).
- **Pop-up-/Pop-under-Blocker:** Werbefenster, die Seiten ungefragt öffnen, werden sofort geschlossen.
- **YouTube:** Video-Werbung wird aus den Player-Daten entfernt; durchrutschende Werbeclips werden stumm geschaltet und übersprungen.
- **Zähler** der blockierten Anfragen pro Tab direkt am Symbol.
- **Pro Seite abschaltbar** (Ausnahmeliste) und **global pausierbar** – mit einem Klick im Popup.
- **Element-Picker:** beliebiges Element anklicken → wird künftig immer ausgeblendet (auch per Rechtsklick-Menü).
- **Eigene Filter** in Adblock-Plus-Syntax.
- Optionale Listen: **Cookie-Hinweise** und **störende Elemente** (Newsletter-Pop-ups, Social-Leisten …).
- Einstellungen exportieren/importieren.

## Installation

### Chrome, Edge, Brave, Opera, Vivaldi

1. Dieses Repository herunterladen (grüner Button **Code → Download ZIP**) und entpacken
   – oder `git clone`.
2. `chrome://extensions` öffnen (Edge: `edge://extensions`, Brave: `brave://extensions`).
3. Oben rechts den **Entwicklermodus** einschalten.
4. **„Entpackte Erweiterung laden“** klicken und den Ordner **`extension`** auswählen.
5. Fertig – das rote Schild erscheint in der Symbolleiste (ggf. über das Puzzle-Symbol anheften).

### Firefox

1. Paket bauen: `npm install && npm run build` (erzeugt `dist/schild-firefox.xpi`).
2. `about:debugging#/runtime/this-firefox` öffnen → **„Temporäres Add-on laden …“** →
   `dist/firefox/manifest.json` auswählen.
3. Beim ersten Start öffnet sich die Einstellungsseite: auf **„Zugriff erlauben“** klicken
   (Firefox fragt die Berechtigung für alle Webseiten separat ab).

> Temporäre Add-ons entfernt Firefox beim Neustart. Für eine dauerhafte Installation muss das
> Paket von Mozilla signiert werden (kostenlos über [addons.mozilla.org](https://addons.mozilla.org/developers/)).

## Bedienung

- **Klick auf das Schild:** zeigt die blockierten Anfragen auf der aktuellen Seite.
  - **„Auf dieser Seite deaktivieren“** – die Seite kommt auf die Ausnahmeliste.
  - **Schalter oben rechts** – Schild überall pausieren.
  - **„Element ausblenden“** – Element anklicken, das verschwinden soll (Esc bricht ab).
- **Einstellungen:** Filterlisten an/aus, Ausnahmen, eigene Filter, YouTube- und Pop-up-Blocker.

## Entwicklung

```bash
npm install
npm run build:rules   # Filterlisten neu herunterladen und in Regeln umwandeln
npm test              # Unit-Tests (Filter-Parser, Gültigkeit aller Regeln)
npm run test:e2e      # Ende-zu-Ende-Test in echtem Chromium mit geladener Erweiterung
npm run build         # dist/schild-chrome.zip und dist/schild-firefox.xpi
```

Aufbau:

| Pfad | Inhalt |
| --- | --- |
| `extension/manifest.json` | Manifest V3 |
| `extension/background.js` | Service Worker: Regeln, Ausnahmen, Pop-up-Blocker, Element-Ausblendung |
| `extension/lib/filter-parser.js` | Wandelt Adblock-Plus-Filter in `declarativeNetRequest`-Regeln und CSS um |
| `extension/rules/*.json` | Generierte Netzwerkregeln (eine Datei pro Filterliste) |
| `extension/cosmetic/*.json` | Generierte Ausblend-Selektoren und Pop-up-Filter |
| `extension/content/` | Content-Skripte (Ausblendung, Element-Picker, YouTube) |
| `extension/popup/`, `extension/options/` | Oberfläche |
| `tools/` | Build-Skripte (Listen, Icons, Pakete) |

Der E2E-Test lädt die Erweiterung in Chromium, leitet echte Werbe-Domains
(z. B. `pagead2.googlesyndication.com`, `google-analytics.com`, `popads.net`) auf einen lokalen
Testserver um und prüft, dass sie blockiert werden, normale Inhalte weiter laden, Werbeelemente
ausgeblendet und Werbe-Pop-ups geschlossen werden – sowie Ausnahmeliste, Pause und eigene Filter.

## Grenzen (ehrlich gesagt)

Kein Adblocker erwischt 100 % aller Werbung auf jeder Seite – auch uBlock Origin nicht.
Schild deckt den Großteil ab, aber:

- **Manifest V3:** Chrome erlaubt keine Skript-Eingriffe aus Filterlisten („Scriptlets“) und keine
  prozeduralen Filter wie `:has-text()`. Rund 300 solcher Spezialfilter aus EasyList werden daher
  nicht angewendet; alle normalen Filter (> 99 %) schon.
- **YouTube** ändert regelmäßig seine Technik und testet serverseitig eingebettete Werbung. Schild
  entfernt Werbung aus den Player-Daten und überspringt verbliebene Clips, aber zeitweise kann
  trotzdem etwas durchrutschen.
- **Filterlisten-Updates:** Die Listen sind in die Erweiterung eingebaut. Für den neuesten Stand
  `npm run build:rules` ausführen und die Erweiterung neu laden.
- **Anti-Adblock-Sperren** mancher Seiten können anschlagen – dann die Seite per Klick auf
  „Auf dieser Seite deaktivieren“ freigeben.
- In **Firefox** wird der Zähler der blockierten Anfragen je nach Version nicht angezeigt;
  das Blockieren selbst funktioniert.

## Lizenzen

Filterlisten: EasyList/EasyPrivacy/Fanboy © The EasyList authors, lizenziert unter
GPLv3 / CC BY-SA 3.0 (https://easylist.to).
