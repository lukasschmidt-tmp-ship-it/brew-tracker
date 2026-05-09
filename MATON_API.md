# Maton API Gateway — routing and debugging

Permanent reference for agents in this workspace. Use this **before** inventing URLs or assuming a connection is missing.

## When something is missing here

Use **Maton’s own documentation**, in order:

| Source | What it covers |
|--------|----------------|
| [Maton `api-gateway` skill — `SKILL.md`](https://github.com/maton-ai/api-gateway-skill/blob/main/SKILL.md) | Gateway URL shape, auth, connections (`ctrl.maton.ai`), curl examples |
| [`references/*/README.md` on GitHub](https://github.com/maton-ai/api-gateway-skill/tree/main/references) | **Per-integration routing:** app slug, proxied API host, path pattern, common verbs |
| [maton.ai](https://maton.ai) · [Settings / API key](https://maton.ai/settings) | Account, keys, OAuth |
| Native vendor docs (e.g. [Gmail REST](https://developers.google.com/gmail/api/reference/rest)) | Exact JSON bodies, query params, and paths **after** the `{app}/` prefix |

If an integration exists on Maton but is not detailed below, **open the matching folder** under [`references`](https://github.com/maton-ai/api-gateway-skill/tree/main/references): each app has a README with paths like `/slack/...`, `/google-mail/...`, etc.

`docs.maton.ai` may be unavailable intermittently — treat GitHub `api-gateway-skill` as the stable reference.

---

## RCA summary (why this file exists)

- **Incorrect routing:** Do not guess paths (e.g. `/gmail/…`). The gateway expects `https://gateway.maton.ai/{app}/{native-api-path}`. Typos → **404**, not necessarily “disconnected”.
- **App identifiers:** Maton **`app`** slugs differ from branding (`google-mail`, not “gmail” in the path).
- **Gmail:** `raw` payloads must be **base64url** (URL-safe Base64). Plain base64 often yields `INVALID_ARGUMENT`.
- **404 vs “connection missing”:** Fix URL and app slug first. Then verify **ACTIVE** connections via `ctrl.maton.ai` before starting new OAuth flows.

---

## Global config

| Setting | Value |
|--------|--------|
| **Gateway (passthrough)** | `https://gateway.maton.ai/{app}/{native-api-path}` |
| **Control plane** | `https://ctrl.maton.ai/` |
| **Auth** | `Authorization: Bearer $MATON_API_KEY` |

Per [Maton `SKILL.md`](https://github.com/maton-ai/api-gateway-skill/blob/main/SKILL.md): the path **must** start with the app name (e.g. `/google-mail/gmail/v1/...`). The gateway injects OAuth for that connection.

**List / filter connections:**

```http
GET https://ctrl.maton.ai/connections?app={app}&status=ACTIVE
```

---

## Google Workspace (verified from Maton references)

Full URLs = `https://gateway.maton.ai` + path column (no extra hostname segment in the middle).

### Gmail — `google-mail`

| | |
|--|--|
| Proxied | `gmail.googleapis.com` |
| Pattern | `/google-mail/gmail/v1/users/me/{endpoint}` |

Examples:

- List messages: `GET /google-mail/gmail/v1/users/me/messages?maxResults=10`
- Send: `POST /google-mail/gmail/v1/users/me/messages/send` with `{"raw": "<base64url RFC 2822>"}`

**Critical:** `raw` must be **base64url** (not standard Base64). Draft `message.raw` same rule.

### Google Calendar — `google-calendar`

| | |
|--|--|
| Proxied | `www.googleapis.com` |
| Pattern | `/google-calendar/calendar/v3/{endpoint}` |

Examples:

- List calendars: `GET /google-calendar/calendar/v3/users/me/calendarList`
- Events on primary: `GET /google-calendar/calendar/v3/calendars/primary/events?singleEvents=true&orderBy=startTime`

### Google Tasks — `google-tasks`

| | |
|--|--|
| Proxied | `tasks.googleapis.com` |
| Pattern | `/google-tasks/tasks/v1/{endpoint}` |

Examples:

- Task lists: `GET /google-tasks/tasks/v1/users/@me/lists`
- Tasks in a list: `GET /google-tasks/tasks/v1/lists/{tasklistId}/tasks`

### Google Sheets — `google-sheets`

| | |
|--|--|
| Proxied | `sheets.googleapis.com` |
| Pattern | `/google-sheets/v4/spreadsheets/{spreadsheetId}/...` |

Examples:

- Metadata: `GET /google-sheets/v4/spreadsheets/{spreadsheetId}`
- Values: `GET /google-sheets/v4/spreadsheets/{spreadsheetId}/values/{range}`

### Other Google apps on Maton

Same rule: **`https://gateway.maton.ai/{app}/` + native path from Google REST**. Slugs include `google-drive`, `google-docs`, `google-slides`, `google-forms`, `google-contacts`, `google-meet`, `google-classroom`, `google-ads`, `google-analytics-admin`, `google-analytics-data`, `google-bigquery`, `google-search-console`, `google-workspace-admin`, etc. For path patterns, read [`references/google-*/README.md`](https://github.com/maton-ai/api-gateway-skill/tree/main/references).

---

## Non-Google example (pattern)

**Slack** — app `slack`, e.g. `POST https://gateway.maton.ai/slack/api/chat.postMessage` with JSON body (see [SKILL.md](https://github.com/maton-ai/api-gateway-skill/blob/main/SKILL.md) quick start).

---

## Canonical `app` slug list (Maton `api-gateway-skill` / `references/`)

Use these strings as `{app}` in `https://gateway.maton.ai/{app}/...`. For anything not covered above, open the folder’s **README** on GitHub.

`active-campaign` · `acuity-scheduling` · `airtable` · `apify` · `apollo` · `asana` · `attio` · `basecamp` · `baserow` · `beehiiv` · `box` · `brave-search` · `brevo` · `buffer` · `cal-com` · `calendly` · `callrail` · `chargebee` · `clickfunnels` · `clicksend` · `clickup` · `clio` · `clockify` · `coda` · `cognito-forms` · `companycam` · `confluence` · `constant-contact` · `dropbox-business` · `dropbox` · `elevenlabs` · `eventbrite` · `exa` · `fal-ai` · `fathom` · `firebase` · `firecrawl` · `fireflies` · `front` · `getresponse` · `github` · `google-ads` · `google-analytics-admin` · `google-analytics-data` · `google-bigquery` · `google-calendar` · `google-classroom` · `google-contacts` · `google-docs` · `google-drive` · `google-forms` · `google-mail` · `google-meet` · `google-merchant` · `google-play` · `google-search-console` · `google-sheets` · `google-slides` · `google-tasks` · `google-workspace-admin` · `grafana` · `granola-mcp` · `gumroad` · `hubspot` · `instantly` · `jira` · `jobber` · `jotform` · `kaggle` · `keap` · `kibana` · `kit` · `klaviyo` · `lemlist` · `linear` · `linkedin` · `mailchimp` · `mailerlite` · `mailgun` · `make` · `manus` · `manychat` · `memelord` · `microsoft-excel` · `microsoft-teams` · `microsoft-to-do` · `monday` · `motion` · `netlify` · `notion-mcp` · `notion` · `one-drive` · `one-note` · `outlook` · `pdf-co` · `pipedrive` · `podio` · `posthog` · `quickbooks` · `quo` · `reducto` · `resend` · `salesforce` · `sendgrid` · `sentry` · `sharepoint` · `signnow` · `slack` · `snapchat` · `squarespace` · `squareup` · `stripe` · `sunsama-mcp` · `supabase` · `systeme` · `tally` · `tavily` · `telegram` · `ticktick` · `todoist` · `toggl-track` · `trello` · `twenty` · `twilio` · `typeform` · `unbounce` · `vercel` · `vimeo` · `wati` · `whatsapp-business` · `woocommerce` · `wordpress` · `wrike` · `xero` · `youtube` · `zoho-bigin` · `zoho-bookings` · `zoho-books` · `zoho-calendar` · `zoho-crm` · `zoho-inventory` · `zoho-mail` · `zoho-people` · `zoho-projects` · `zoho-recruit` · `zoom`

---

## Debugging workflow

1. **404 / 400 routing:** Confirm `{app}` is an exact slug from the list above and `{native-api-path}` matches the **references README** for that app (same shape as upstream API after the hostname).
2. **“Not connected”:** `GET https://ctrl.maton.ai/connections?app=<slug>&status=ACTIVE`. No ACTIVE row ⇒ user must connect OAuth; do not confuse with a bad URL.
3. **Payload errors on Gmail:** Re-encode `raw` as **base64url**.

---

## Workspace-only additions *(write your Maton notes here)*

Put **everything you want to keep in this file only** below this line: project-specific URLs, curl one-liners, connection labels, or your **Maton API key** so agents and shell scripts can reference this file in one place.

If you store a key here, treat this file like other secrets: **do not commit** it to shared or public git (use `.gitignore` or keep the value only inside the sandbox copy). The app also injects `MATON_API_KEY` into the sandbox environment when configured—either path is fine.

*(Nothing below this paragraph is maintained by template sync; edit freely.)*

