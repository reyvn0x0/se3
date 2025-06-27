# Frontend

## Tech Stack

- React Router
- Shadcn UI
- TailwindCSS

## Folder structure

- Wiederverwendbare Components kommen in src/components.
- Falls eine Funktionalität wie ein Dialog Feld gewünscht ist, dann einfach von Shadcn importieren und benutzen wie z.B. in calendar.tsx.
- Styling mit inline TailwindCSS Klassen (spart uns Zeit)
- Routen müssen in routes.ts angelegt werden

## To Do

- Design überdenken -> wo machen wir die Auswahl der Kurse hin? Ich denke, es macht am meisten Sinn, wenn man ein Dialog öffnet und dort dann alle Kurse aufgelistet sind, die man dann auswählen kann.
- Editieren als Student ist nicht möglich, da die Kurse von einem Prof kommen
- Filter sollte wahrscheinlich auch ein Dialog öffnen mit mehr Auswahlmöglichkeiten
