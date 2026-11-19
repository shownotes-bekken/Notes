# Bekken – shownotes

Statisk shownotes-side for den daglige nyhetspodkasten Bekken. GitHub Pages publiserer rotmappa fra branchen `main`:

https://shownotes-bekken.github.io/Notes/

`index.html` genereres av `python3 build.py`. Skriptet bruker bare Python 3 sitt standardbibliotek. Ikke rediger `index.html` for hånd.

## Ny episode

1. Lag `episodes/ÅÅÅÅ-MM-DD.json`. Filnavnet og feltet `date` skal være samme dato.
2. Kjør `python3 build.py`.
3. Commit både datafilen og den nye `index.html`.

Ett tema per avsnitt i tidskartet, i den rekkefølgen de sendes. Hopp over velkomst og avslutning. «Stortinget i går» er én sak, og `start` er starten på det første stortingsavsnittet. Skriv en kort, nøktern tittel på norsk. Legg kildene inn som navn og URL, i den rekkefølgen de står i kildelista. Ta med alle kildelenker, også X-innlegg. Ta ikke med interne arbeidsnotater (utelatte saker, filstier, likes-tall, valutakurs og liknende).

## Oppdatere lenker

Når Spotify, YouTube eller X-innlegget kommer, legg URL-en i `links` i episodens JSON-fil. Utelat feltet, eller sett det til `null`, så lenge lenken ikke finnes. Kjør `python3 build.py` på nytt, og commit JSON-filen og `index.html`.

Finnes `links.youtube`, blir hver tidskode en lenke til videoen. Videoen har 12,333 sekunder intro før podkastlyden, så skriptet setter `?t=` til `floor(start + 12,333)`. Uten YouTube-lenke vises tidskoden som vanlig tekst. `start` er sekunder i podkastlyden, ikke YouTube-tiden.

## Format

```json
{
  "date": "2026-11-19",
  "title": "Bekken – torsdag 19. november 2026",
  "description": "Kort beskrivelse fra episode.json.",
  "links": {
    "spotify": "https://open.spotify.com/episode/…",
    "youtube": "https://youtu.be/…"
  },
  "topics": [
    {
      "title": "Støres privatfly til COP31",
      "start": 5.0,
      "sources": [
        {"name": "Panorama Nyheter", "url": "https://…"},
        {"name": "Regjeringen", "url": "https://…"}
      ]
    }
  ]
}
```

`links.x` er X-innlegget, og tas med på samme måte når det finnes.
