# Servizio: scambio token OAuth + licenze

Il Worker fa due cose, per lo stesso motivo di fondo: sono le due cose che
un'app installata sul computer del cliente **non può fare da sola**.

| | Perché non può stare nell'app |
|---|---|
| Scambio token OAuth | Il client secret sarebbe leggibile decomprimendo l'eseguibile |
| Licenze | Il database dei piani sarebbe sul PC di chi deve pagare |

## Licenze

Flusso completo:

1. l'app chiede `POST /checkout` → riceve l'URL di pagamento Stripe
2. il cliente paga sulla pagina di Stripe
3. Stripe chiama `POST /stripe/webhook` → qui nasce la chiave di licenza
4. il cliente atterra su `GET /license/claim` → legge e copia la sua chiave
5. la incolla nell'app → `POST /license/verify` → il piano si sblocca

**Gli importi stanno nel Worker**, non nell'app: se li decidesse il client,
chi modifica l'eseguibile potrebbe farsi generare un abbonamento da zero euro.
La firma del webhook viene verificata (HMAC, confronto a tempo costante,
finestra di 5 minuti): senza quel controllo chiunque potrebbe farsi emettere
licenze gratis.

### Configurare Stripe

```bash
python deploy_proxy.py --stripe
```

Chiede le due chiavi e le carica sul Worker senza salvarle su disco. Poi, su
[dashboard.stripe.com](https://dashboard.stripe.com) → Developers → Webhooks,
aggiungi un endpoint che punta a:

```
https://<il-tuo-worker>.workers.dev/stripe/webhook
```

con gli eventi `checkout.session.completed`, `customer.subscription.deleted`
e `invoice.payment_failed`.

### Configurare l'email della chiave

La pagina `/license/claim` è raggiunta solo se il browser del cliente resta
aperto fino al redirect di Stripe: senza una copia via email, chiudere la
scheda un attimo troppo presto significa perdere la chiave per sempre. Con
[Resend](https://resend.com) (gratis fino a 3.000 email/mese):

1. crea un account su resend.com
2. in **Domains**, aggiungi il sottodominio mittente (qui:
   `mail.getcertsprint.com`) e aggiungi su quel dominio i record DNS che
   Resend mostra (SPF, DKIM, DMARC) — senza quelli le email finiscono in spam
3. in **API Keys**, crea una chiave
4. caricala sul Worker:

```bash
python deploy_proxy.py --resend
```

Senza questa chiave l'app funziona lo stesso: la chiave resta comunque
raggiungibile dalla pagina di atterraggio, semplicemente senza una copia di
riserva via email.

### Revoca

Un rimborso o una disdetta arrivano via webhook e la licenza passa a
`inactive`. L'app se ne accorge al controllo successivo (entro 24 ore) e
**toglie il piano subito**: il periodo di tolleranza di 7 giorni copre solo i
problemi di rete, non un abbonamento che non è più pagato.

## Perché serve il proxy OAuth

Instagram e TikTok richiedono il **client secret** per trasformare il `code`
OAuth in un token d'accesso.

In un'app desktop distribuita non esiste un posto sicuro dove metterlo: se è
compilato dentro l'eseguibile, chiunque scarichi l'app può rileggerlo. Non è
un rischio teorico — decomprimendo il binario le stringhe si leggono in
chiaro. Meta lo dice esplicitamente nella propria documentazione: l'app
secret non va mai inserito in codice distribuito.

Questo proxy sposta i segreti su un server. L'app manda il `code` e riceve
indietro il token; il secret non lascia mai il Worker e nella build non ce
n'è traccia.

> Il client secret di Google fa eccezione: per le "installed app" Google lo
> documenta come non confidenziale, quindi resta nell'eseguibile senza
> problemi e non passa da qui.

## Deploy (Cloudflare Workers, piano gratuito)

Due comandi in tutto:

```bash
npx wrangler login       # una volta sola: apre il browser sul tuo account
python deploy_proxy.py   # dalla cartella del progetto
```

`deploy_proxy.py` fa il resto da solo: pubblica il Worker, ci carica i quattro
segreti leggendoli da `brand.py`, scrive l'URL del Worker in `brand.py` e
**svuota** `INSTAGRAM_APP_SECRET` e `TIKTOK_CLIENT_SECRET`, così non finiscono
più nella build. Se qualcosa fallisce si ferma senza toccare `brand.py`.

Il login è l'unico passo che non può essere automatizzato: autentica il tuo
account Cloudflare.

Poi ricompila l'app e verifica:

```bash
python check_release.py --dist
```

<details>
<summary>Farlo a mano, se preferisci</summary>

```bash
cd oauth-proxy
npx wrangler deploy
npx wrangler secret put INSTAGRAM_APP_ID
npx wrangler secret put INSTAGRAM_APP_SECRET
npx wrangler secret put TIKTOK_CLIENT_KEY
npx wrangler secret put TIKTOK_CLIENT_SECRET
```

Poi in `brand.py`: metti l'URL del Worker in `OAUTH_PROXY_URL` e svuota i due
`*_SECRET`.
</details>

## Verificare che funzioni

```bash
curl -X POST https://<il-tuo-worker>/exchange \
  -H 'content-type: application/json' \
  -d '{"platform":"tiktok","code":"non-valido","redirect_uri":"https://esempio"}'
```

Deve rispondere `{"error":"TikTok ha rifiutato la richiesta."}`: significa che
il Worker è raggiungibile, ha i segreti e sta parlando con TikTok. Un errore
diverso (404, 500) indica che qualcosa nel deploy non è a posto.

## Rotazione delle credenziali

Se un secret è già finito in una build distribuita va considerato compromesso
e **rigenerato**:

- Instagram: Meta for Developers → l'app → Configurazione dell'API con
  Instagram Login → *Chiave segreta di Instagram* → rigenera
- TikTok: TikTok for Developers → l'app → Credentials → rigenera il client
  secret

Dopo la rotazione aggiorna i segreti del Worker con `wrangler secret put`.
Le connessioni già attive continuano a funzionare: usano i token, non il
secret.
