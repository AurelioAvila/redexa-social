/**
 * Interfaccia di Social Dashboard.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 */
const PLATFORM_LABELS = {
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
  x: "X",
  certsprint: "CertSprint",
};
/** Un'icona dello sprite definito in index.html. Unica definizione per icona,
 *  quindi la sidebar, la command palette e i modali non possono piu' divergere
 *  come era successo ai marchi delle piattaforme. */
const icon = (name) => `<svg class="ico" aria-hidden="true"><use href="#i-${name}"/></svg>`;

// Marchi semplificati, non le icone ufficiali pixel-per-pixel (licenza) ma
// riconoscibili a colpo d'occhio - molto meglio dei simboli geometrici
// generici (▶ ◈ ♪ ✕) che non dicevano nulla del brand a prima vista.
const PLATFORM_ICONS = {
  youtube: icon("youtube"),
  instagram: icon("instagram"),
  tiktok: icon("tiktok"),
  x: icon("x"),
  certsprint: icon("certsprint"),
};

// ---------- Lingua ----------
const LANGS = [
  { code: "it", name: "Italiano", locale: "it-IT" },
  { code: "en", name: "English", locale: "en-US" },
  { code: "es", name: "Español", locale: "es-ES" },
  { code: "fr", name: "Français", locale: "fr-FR" },
  { code: "de", name: "Deutsch", locale: "de-DE" },
  { code: "ja", name: "日本語", locale: "ja-JP" },
];

const I18N = {
  it: {

    // --- Aggiornamento automatico ---
    update_available_title: "È disponibile la versione {version}",
    update_now: "Aggiorna ora",
    update_later: "Ricordamelo più tardi",
    update_skip: "Salta questa versione",
    update_mandatory: "Aggiornamento necessario",
    update_downloading: "Scaricamento e verifica in corso…",
    update_restarting: "L'app si chiude e si riapre da sola con la nuova versione.",
    update_failed: "Aggiornamento non riuscito. La versione attuale è rimasta intatta.",
    update_managed_by_winget: "Questa copia è stata installata con winget: aggiornala con «winget upgrade».",
    update_running_from_source: "Stai eseguendo l'app dai sorgenti: l'aggiornamento automatico non si applica.",
    update_up_to_date: "L'app è aggiornata.",
    update_check_now: "Controlla aggiornamenti",
    update_channel_beta: "Ricevi le versioni di prova",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "Questa chiave ha già raggiunto il numero massimo di dispositivi attivi. Disattivala su un altro dispositivo prima di riprovare qui.",
    license_reactivate_needed: "Inserisci di nuovo la chiave su questo dispositivo per riattivarla qui.",

    // --- state OAuth non valido ---
    connect_state_missing: "Nessun collegamento in attesa. Riparti premendo di nuovo Collega.",
    connect_state_mismatch: "Questo indirizzo non corrisponde al collegamento che hai avviato. Incolla l'indirizzo completo della pagina su cui sei atterrato, e se non è tuo non usarlo.",

    // --- Dati in cache ---
    cache_title: "Dati in cache",
    cache_hint: "Se un numero sembra sbagliato anche dopo aver aggiornato, svuotare la cache locale forza la dashboard a ricalcolare tutto da zero. Gli account collegati e la licenza restano intatti.",
    cache_clear_btn: "Svuota cache", app_footer_rights: "Tutti i diritti riservati.", app_footer_license: "Licenza",
    cache_confirm: "Le statistiche e lo storico salvati verranno ricalcolati dal prossimo aggiornamento. Continuare?",
    cache_cleared: "Cache svuotata.",

    // --- Controllo aggiornamenti ---
    update_available: "Aggiornamento disponibile",
    update_available_v: "Versione {v} disponibile",
    update_hint: "Apre la pagina di download della versione {v}.",
    um_size: "{size}",
    um_release_notes: "Note di rilascio",
    um_installing: "Installazione in corso…",
    um_later: "Ricordamelo più tardi",
    um_skip: "Salta questa versione",
    um_install: "Installa e riavvia",
    um_error: "Installazione non riuscita. Riprova, oppure scarica la nuova versione manualmente.",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "Collega {p} con la tua app",
    sw_step_of: "Passo {n} di {tot}",
    sw_back: "Indietro",
    sw_next: "Avanti",
    sw_finish: "Salva e collega",
    sw_saving: "Verifica in corso…",
    sw_open: "Apri la pagina",
    sw_copy: "Copia",
    sw_copied: "Copiato ✓",
    sw_copy_failed: "Non riesco a copiare: seleziona l'indirizzo e copialo a mano.",
    sw_saved: "Fatto: ora accedi al tuo account.",
    sw_removed: "La tua app è stata rimossa.",
    sw_offer: "Non vuoi aspettare? Puoi collegarlo subito registrando una tua app: ti guidiamo passo passo, servono circa 10 minuti.",
    sw_offer_btn: "Collegalo adesso →",
    sw_own_active: "Stai usando la tua app ({id}).",
    sw_own_remove: "Rimuovi",
    sw_id_label_ig: "ID app Instagram",
    sw_secret_label_ig: "Chiave segreta app Instagram",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32 caratteri",
    sw_id_label_tt: "Client key",
    sw_secret_label_tt: "Client secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "incolla il segreto",
    sw_ig1_t: "Cosa serve",
    sw_ig1_d: "Registrerai una tua app Instagram: circa 10 minuti, una volta sola.\nServono un account Instagram Professionale (Business o Creator) e un account Facebook per entrare nel pannello sviluppatori.\nLe credenziali restano su questo computer.",
    sw_ig2_t: "Crea l'app",
    sw_ig2_d: "Apri il pannello sviluppatori di Meta e premi «Crea app».\nQuando chiede il caso d'uso scegli «Altro», poi come tipo scegli «Business».\nIl nome è libero.",
    sw_ig3_t: "Aggiungi Instagram",
    sw_ig3_d: "Nella tua nuova app apri «Aggiungi prodotti», trova «Instagram» e premi «Configura».\nPoi scegli «Configura l'API con il login di Instagram business».",
    sw_ig4_t: "Incolla l'indirizzo di ritorno",
    sw_ig4_d: "Nella stessa pagina apri «Impostazioni di login business».\nCopia l'indirizzo qui sotto e incollalo nel campo «URI di reindirizzamento OAuth», poi salva.\nÈ una pagina che esiste già: non devi pubblicare nessun sito.",
    sw_ig5_t: "Copia le due credenziali",
    sw_ig5_d: "Sempre in quella pagina, nella sezione delle impostazioni dell'app, trovi «ID app Instagram» e «Chiave segreta app Instagram».\nCopiali qui sotto: è l'ultimo passaggio.",
    sw_tt1_t: "Cosa serve",
    sw_tt1_d: "Registrerai una tua app TikTok: circa 10 minuti, una volta sola.\nServe solo il tuo account TikTok.\nLe credenziali restano su questo computer.",
    sw_tt2_t: "Crea l'app",
    sw_tt2_d: "Apri il portale sviluppatori di TikTok, accedi con il tuo account e registra una nuova app.\nDalle un nome e conferma.",
    sw_tt3_t: "Attiva login e permessi",
    sw_tt3_d: "Nella tua app apri «Add products» e aggiungi «Login Kit».\nTra gli ambiti attiva user.info.basic, user.info.stats e video.list.\nSono di sola lettura: servono a leggere follower e statistiche dei video.",
    sw_tt4_t: "Crea la sandbox",
    sw_tt4_d: "Apri «Sandbox» e creane una.\nDentro la sandbox aggiungi il tuo account TikTok come «target user»: è questo che ti permette di leggere i tuoi dati senza attendere la revisione di TikTok.",
    sw_tt5_t: "Incolla l'indirizzo di ritorno",
    sw_tt5_d: "Nelle impostazioni del Login Kit copia l'indirizzo qui sotto e incollalo tra i «Redirect URI», poi salva.\nÈ una pagina che esiste già: non devi pubblicare nessun sito.",
    sw_tt6_t: "Copia le due credenziali",
    sw_tt6_d: "Nei dettagli dell'app trovi «Client key» e «Client secret» della sandbox.\nCopiali qui sotto: è l'ultimo passaggio.",
    ownapp_missing: "Compila entrambi i campi.",
    ownapp_unsupported: "Piattaforma non supportata.",
    ownapp_bad_ig_id: "L'ID app Instagram è fatto solo di cifre. Controlla di non aver invertito i due campi.",
    ownapp_bad_ig_secret: "La chiave segreta non sembra completa: copiala per intero, senza spazi.",
    ownapp_bad_tt_key: "La Client key di TikTok inizia con «aw» o «sbaw». Controlla di non aver invertito i due campi.",
    ownapp_bad_tt_secret: "Il Client secret non sembra completo: copialo per intero, senza spazi.",
    ownapp_tt_refused: "TikTok non riconosce queste credenziali. Verifica di aver copiato Client key e Client secret della stessa app.",
    overview_by_platform: "Per piattaforma",
    overview_top_content: "Contenuto migliore", platform_status_green: "Connesso e sincronizzato", platform_status_yellow: "Richiede attenzione", platform_status_red: "Errore", platform_status_grey: "Non ancora configurato",
    tile_followers: "Pubblico totale", tile_recent_views: "Views recenti", tile_recent_views_foot: "sugli ultimi contenuti",
    tile_engagement: "Interazioni", tile_engagement_foot: "like + commenti recenti",
    tile_health: "Salute", tile_accounts_foot: "account attivi",
    tile_analyzed: "Contenuti analizzati", tile_analyzed_foot: "post e video con dati",
    tile_avg_per_post: "Media per contenuto", tile_avg_per_post_foot: "views medie",
    tile_avg_per_post_foot_n: "views medie su {n} contenuti con dati", tile_best_hour_insufficient: "servono più contenuti",
    analytics_hours_insufficient: "Dati ancora insufficienti per indicare una fascia oraria affidabile: servono almeno {n} contenuti in più con visualizzazioni.",
    tile_best_hour: "Ora migliore", tile_best_hour_foot: "{v} views medie",
    tile_best_platform: "Piattaforma top", tile_best_platform_foot: "{v} views totali",
    analytics_hours_hint: "Media di views per fascia oraria di pubblicazione (UTC). Le barre piene sono le ore in cui i tuoi contenuti rendono di piu'.",
    hours_tooltip: "{h}:00 - {v} views medie su {n} contenuti",
    guided_step1: "Autorizza l'account nella scheda che si e' aperta.",
    guided_step2: "Poi copia l'indirizzo della pagina su cui atterri e incollalo qui sotto.",
    guided_placeholder: "Incolla qui l'URL completo", guided_cancel: "Annulla", guided_finish: "Completa",
    guided_paste_needed: "Incolla prima l'URL di ritorno.",
    btn_link_account: "Collega", btn_link_account_full: "Collega un account",
    cm_auto_text: "Si aprira' il browser: accedi e autorizza l'accesso in sola lettura. Tutto il resto lo fa la dashboard.",
    cm_step1: "Autorizza l'account nella scheda che si apre.", cm_open: "Apri autorizzazione",
    cm_step2: "Incolla qui l'indirizzo della pagina su cui atterri.", cm_finish: "Completa collegamento",
    group_connections: "Account collegati", nav_connections: "Collega account",
    connections_subtitle: "Accedi con il tuo account e la dashboard fa il resto. Nessun token da copiare.",
    connections_privacy: "Le autorizzazioni restano salvate solo sul tuo computer, in locale. Non passano da nessun server.",
    connect_now: "Collega {p}", connect_add_another: "Collega un altro account", connect_soon: "In arrivo",
    generic_error: "Si è verificato un errore.", connect_timeout: "Tempo scaduto: il collegamento non è stato completato.",
    connect_already_running: "C'è già un collegamento in corso.",
    connect_platform_unsupported: "Questa piattaforma non è ancora supportata.",
    connect_guided_unavailable: "Il collegamento guidato non è disponibile per questa piattaforma.",
    connect_window_closed: "Collegamento annullato: la finestra è stata chiusa prima di completare l'accesso.",
    connect_denied: "Autorizzazione negata dalla piattaforma.",
    connect_code_not_found: "Non sono riuscito a trovare il codice nell'URL incollato.",
    connect_instagram_rejected: "Instagram ha rifiutato il codice di autorizzazione. Riprova a collegare l'account.",
    connect_token_exchange_failed: "Scambio del token non riuscito. Riprova a collegare l'account.",
    connect_tiktok_rejected: "TikTok ha rifiutato il codice di autorizzazione. Riprova a collegare l'account.",
    connect_tiktok_unexpected: "Risposta inattesa da TikTok. Riprova più tardi.",
    connect_proxy_http_error: "Il servizio di autorizzazione non ha risposto correttamente. Riprova tra poco.",
    connect_proxy_rejected: "Il servizio di autorizzazione ha rifiutato la richiesta.",
    connect_no_google_app: "Nessuna app OAuth Google configurata.",
    connect_coming_soon: "In arrivo",
    cm_coming_soon_text: "Il collegamento a questa piattaforma è quasi pronto: stiamo completando l'approvazione richiesta dalla piattaforma stessa. Torna a provare tra qualche giorno.",
    proxy_not_configured: "Il servizio di autorizzazione non è configurato in questa build.",
    unavail_not_configured: "Collegamento non ancora disponibile in questa versione dell'app.",
    unavail_x_no_read_api: "X non espone le statistiche di lettura sul piano gratuito.",
    connect_not_linked: "Non collegato", connect_linked_n: "{n} collegato/i", connect_unlink: "Scollega",
    connect_reauth_badge: "Da ricollegare",
    connect_reauth_hint: "L'accesso è scaduto o è stato revocato dalla piattaforma: ricollega l'account per tornare a leggere le statistiche.",
    connect_locked_hint: "Le credenziali di questo account non sono leggibili su questo computer: ricollegalo per continuare.",
    connect_desc: "Accedi con {p} per vedere qui le tue statistiche.",
    connect_waiting: "In attesa del browser...", connect_browser_opened: "Ho aperto il browser: completa l'accesso.",
    connect_success: "{n} collegato!", connect_unlinked: "Account scollegato.",
    diag_problems: "problemi", diag_warnings: "avvisi", diag_ok: "a posto",
    diag_filter_all: "Tutto", diag_filter_problems: "Da sistemare", diag_filter_ok: "A posto",
    diag_filter_empty: "Niente da mostrare con questo filtro.", diag_go_connect: "Vai a Collega account",
    diag_group_strategy: "Strategia",
    health_part_technical: "Tecnica", health_part_engagement: "Engagement",
    health_part_consistency: "Costanza", health_part_coverage: "Copertura",
    health_detail_technical: "{n} problemi bloccano la raccolta dati", health_detail_engagement: "confrontato con {n} benchmark di piattaforma", health_detail_engagement_none: "dati sui follower insufficienti per il confronto", health_detail_consistency: "ultimo post {days} giorni fa", health_detail_consistency_none: "nessun contenuto datato", health_detail_coverage: "{active} di {total} piattaforme con contenuti recenti",
    health_nodata_title: "Nessun account collegato", health_nodata_sub: "Collega un account per vedere il punteggio di salute.",
    health_bad_title: "Ci sono cose da sistemare", health_bad_sub: "{n} tra problemi e avvisi richiedono la tua attenzione.",
    health_warn_title: "Quasi tutto a posto", health_warn_sub: "{n} avvisi da tenere d'occhio.",
    health_good_title: "Tutto in ordine", health_good_sub: "Nessun problema rilevato sui tuoi account.",
    group_general: "Generale", group_platforms: "Piattaforme", group_insights: "Insight",
    group_account: "Account", group_settings: "Impostazioni",
    nav_overview: "Panoramica", nav_analytics: "Analitiche", nav_diagnostics: "Diagnostica",
    nav_themes: "Temi", nav_language: "Lingua", nav_account: "Il tuo account", nav_pricing: "Piani e prezzi",
    btn_refresh: "Aggiorna", btn_analyze: "Analizza", btn_export: "Esporta CSV", palette_hint: "Cerca",
    analytics_subtitle: "Calcolate dal codice sui dati raccolti — post migliori e fasce orarie più performanti, zero costo AI.",
    analytics_top_posts: "Top post/video (per views)", analytics_outliers: "Sopra/sotto la tua media", analytics_outliers_hint: "Confrontati con la tua media di {v} views a contenuto — non con un settore che non conosce il tuo pubblico.", analytics_outliers_empty: "Non ci sono ancora abbastanza contenuti per un confronto affidabile.", analytics_best_hours: "Fasce orarie migliori (media views)",
    diagnostics_subtitle: "Calcolata istantaneamente dal codice, zero costo — segnala errori ed è aggiornata a ogni Refresh.",
    themes_subtitle: "Scegli l'aspetto della dashboard — resta salvato anche alla prossima apertura.",
    language_subtitle: "Scegli la lingua dell'interfaccia — resta salvata anche alla prossima apertura.",
    empty_no_data: "Nessun dato — premi Refresh.", waiting_for_data: "In attesa di dati", empty_configure_yt: "Collega un canale YouTube per vedere qui le tue statistiche.",
    empty_configure_ig: "Collega un account Instagram per vedere qui le tue statistiche.", empty_configure_tt: "Collega un account TikTok per vedere qui le tue statistiche.",
    empty_not_configured: "Non configurato.",
    label_subscribers_total: "Iscritti totali", label_channels: "Canali", label_followers_total: "Follower totali",
    label_accounts: "Account", label_accounts_configured: "Account configurati", label_credentials: "Credenziali",
    val_ok: "OK", val_missing: "Mancanti", label_site: "Sito", val_online: "Online", val_down: "Down",
    label_subscribers: "Iscritti", label_total_views: "Views totali", label_videos_published: "Video pubblicati",
    label_recent_views: "Views ultimi 10 video", label_last_publish: "Ultima pubblicazione", label_never_published: "Mai pubblicato",
    label_followers: "Follower", label_views_recent: "Views (ultimi post)", label_likes: "Like", label_comments: "Commenti",
    label_views: "Views", label_likes_comments_shares: "Like / Commenti / Share",
    val_online_latency: "Online ({ms}ms)", val_down_error: "Down / errore", label_npm_vulns: "Vulnerabilità npm",
    label_eslint: "ESLint", val_not_configured: "non configurato", val_errors_warnings: "{e} errori, {w} warning",
    insight_loading: "Analisi in corso…", insight_error: "Errore durante l'analisi: ",
    ins_no_items: "{name}: nessun contenuto recente da analizzare.",
    locked_title: "Funzione del piano Pro",
    locked_cta: "Vedi i piani",
    locked_best_hours: "Le fasce orarie consigliate sono incluse nel piano Pro.",
    locked_history: "Lo storico e i grafici di trend sono inclusi nel piano Pro.",
    plan_feature_locked: "Questa funzione è inclusa nel piano Pro.",
    plan_account_limit: "Il tuo piano include {n} account collegati. Passa a un piano superiore per aggiungerne altri.",
    plan_account_limit_one: "Il tuo piano include 1 solo account collegato. Passa a un piano superiore per aggiungerne altri.",
    plan_free_tagline: "Per iniziare e capire i tuoi numeri.",
    plan_free_accounts: "1 account collegato",
    plan_pro_tagline: "Per chi pubblica ogni giorno e vuole crescere.",
    plan_pro_accounts: "3 account collegati",
    plan_studio_tagline: "Per agenzie e chi gestisce più brand.",
    plan_studio_accounts: "10 account collegati",
    plan_feat_all_socials: "Statistiche di tutti i social supportati",
    plan_feat_manual_refresh: "Refresh manuale on-demand",
    plan_feat_analytics: "Analitiche: top post e fasce orarie",
    plan_feat_diagnostics: "Diagnostica automatica degli errori",
    plan_feat_insights: "Osservazioni automatiche sui tuoi contenuti",
    plan_feat_history: "Storico completo con grafici di trend",
    plan_feat_reports: "Report automatici",
    plan_feat_all_free: "Tutto quello che c'è nel Free",
    plan_feat_compare: "Confronto tra periodi e alert sui cali",
    plan_feat_hours: "Suggerimenti sugli orari di pubblicazione",
    plan_feat_csv: "Esportazione dei dati in CSV",
    plan_feat_all_pro: "Tutto quello che c'è nel Pro",
    plan_feat_workspaces: "Spazi di lavoro separati per cliente",
    plan_feat_whitelabel: "Report PDF white-label automatici",
    plan_feat_multiuser: "Accesso multi-utente al team",
    plan_feat_priority: "Supporto prioritario",
    aria_toggle_password: "Mostra password",
    aria_close: "Chiudi",
    ins_some_zero: "{name}: {n} degli ultimi {tot} contenuti sono ancora a zero visualizzazioni.",
    ins_some_zero_one: "{name}: 1 degli ultimi {tot} contenuti è ancora a zero visualizzazioni.",
    ins_all_zero_one: "{name}: l'unico contenuto recente non ha ancora visualizzazioni.",
    ins_flop_one: "{name}: 1 contenuto sotto il 40% della media: «{title}» con {v} views.",
    ins_cadence_daily: "{name}: pubblichi circa {n} volte al giorno.",
    ins_cadence_broken_daily: "{name}: di solito pubblichi più volte al giorno, ma l'ultimo contenuto risale a {d} giorni fa.",
    ins_all_zero: "{name}: nessuno degli ultimi {n} contenuti ha ancora visualizzazioni.",
    ins_star: "{name}: «{title}» ha fatto {v} views, {x}x la media dell'account. Guarda cosa lo distingue e replicalo.",
    ins_flop: "{name}: {n} contenuti sotto il 40% della media; il più debole è «{title}» con {v} views.",
    ins_engagement: "{name}: {rate}% di engagement sugli ultimi contenuti ({i} interazioni su {v} views).",
    ins_cadence_broken: "{name}: di solito pubblichi ogni {gap} giorni, ma l'ultimo contenuto risale a {d} giorni fa.",
    ins_cadence: "{name}: pubblichi in media ogni {gap} giorni.",
    ins_best_account: "{best} è l'account che rende di più: {bv} views contro le {wv} di {worst}.",
    ins_x_free_plan: "X non espone le statistiche di lettura sul piano gratuito: non c'è nulla da analizzare.",
    ins_no_data: "Nessun dato da analizzare: collega un account e premi Refresh.",
    ins_nothing_notable: "Nessuna criticità rilevata sugli ultimi contenuti.",
    analytics_empty: "Non ci sono ancora abbastanza post/video con dati per un'analisi — premi Refresh.",
    analytics_engagement: "Engagement",
    analytics_engagement_hint: "Quanti, fra chi ti ha visto, hanno messo like, commentato, condiviso o salvato. Confrontato con la media degli account della tua dimensione.",
    analytics_heatmap: "Giorno e ora",
    analytics_heatmap_hint: "Dove i tuoi contenuti hanno funzionato davvero. Più scuro significa più visualizzazioni medie per i post pubblicati in quella fascia.",
    eng_above: "Sopra la media ({e}%)", eng_below: "Sotto la media ({e}%)",
    eng_inline: "In linea con la media ({e}%)",
    eng_no_benchmark: "Follower non disponibili per il confronto",
    eng_saves: "Salvataggi", eng_shares: "Condivisioni",
    eng_saves_hint: "Percentuale di chi ti ha visto che ha salvato il contenuto: è il segnale più forte che ha valore.",
    eng_shares_hint: "Percentuale di chi ti ha visto che l'ha condiviso: è così che un contenuto esce dal tuo pubblico.",
    heatmap_not_enough: "Servono più contenuti con data e ora per disegnare la mappa.",
    heatmap_cell: "{d} alle {h}:00 — {v} visualizzazioni medie su {n} contenuti",
    weekday_short: "Lun,Mar,Mer,Gio,Ven,Sab,Dom",
    analytics_untitled: "(senza titolo)", analytics_avg_views: "views medie", analytics_bucket_count: "post analizzati in questa fascia",
    analytics_last_refresh: "Ultimo caricamento dati: {t} ({d})", analytics_last_refresh_never: "Ultimo caricamento dati: mai — premi Refresh.",
    footer_last_refresh: "Ultimo aggiornamento: {d}", footer_never: "Mai aggiornato", footer_error: "Errore durante il refresh - riprova.",
    time_never: "mai", time_seconds_ago: "pochi secondi fa", time_min_ago: "{n} min fa", time_hours_ago: "{n} ore fa", time_days_ago: "{n} giorni fa",
    diag_next_step_label: "Prossimo passo:",
    diag_unreachable_title: "{name}: non risponde",
    diagerr_scope_denied_cat: "Permesso non concesso", diagerr_scope_denied_step: "Serve l'approvazione del permesso di lettura statistiche sul portale sviluppatori della piattaforma: non è risolvibile dall'app.",
    diagerr_expired_cat: "Accesso scaduto", diagerr_expired_step: "Ricollega questo account: l'autorizzazione è scaduta o è stata revocata.",
    diagerr_scope_mismatch_cat: "Permessi non allineati", diagerr_scope_mismatch_step: "I permessi richiesti non coincidono con quelli concessi in origine: ricollega l'account per riallinearli.",
    diagerr_permission_cat: "Permesso mancante", diagerr_permission_step: "L'account non ha concesso il permesso richiesto: ricollegalo accettando tutte le richieste.",
    diagerr_rate_cat: "Troppe richieste", diagerr_rate_step: "Attendi qualche minuto prima del prossimo aggiornamento: il limite della piattaforma è stato raggiunto.",
    diagerr_auth_cat: "Credenziali non valide", diagerr_auth_step: "Ricollega l'account per rigenerare l'accesso.",
    diagerr_notfound_cat: "Account non trovato", diagerr_notfound_step: "L'account collegato non risulta più raggiungibile: potrebbe essere stato rimosso o rinominato.",
    diagerr_network_cat: "Problema di rete", diagerr_network_step: "Riprova l'aggiornamento: sembra un problema temporaneo di connessione.",
    diagerr_unknown_cat: "Errore non classificato", diagerr_unknown_step: "Riprova l'aggiornamento; se persiste, ricollega l'account.",
    diag_no_account_cat: "Da collegare", diag_no_account_title: "Nessun account {p}", diag_no_account_text: "Non hai ancora collegato nessun account {p}.", diag_no_account_step: "Premi Collega e accedi: bastano pochi secondi.",
    diag_no_data_cat: "Dati mancanti", diag_no_data_title: "{p} senza dati", diag_no_data_text: "Nessun dato ancora caricato.", diag_no_data_step: "Premi Refresh per caricare i dati.",
    diag_all_ok_title_one: "{p}: 1 account in regola", diag_all_ok_cat_one: "Tutto a posto", diag_all_ok_text_one: "L'account risponde e pubblica con costanza.", diag_all_ok_step_one: "Nessuna azione richiesta.",
    diag_all_ok_cat: "Tutto a posto", diag_all_ok_title: "{p}: {n} account in regola", diag_all_ok_text: "Tutti gli account rispondono e pubblicano con costanza.", diag_all_ok_step: "Nessuna azione richiesta.",
    diag_stale_bad_cat: "Contenuto fermo", diag_stale_bad_title: "{name}: fermo da {d} giorni", diag_stale_bad_text: "L'ultimo contenuto su {p} risale a {d} giorni fa.", diag_stale_bad_step: "Pubblica qualcosa: le piattaforme premiano la costanza e la copertura cala in fretta con i profili inattivi.",
    diag_stale_warn_cat: "Ritmo in calo", diag_stale_warn_title: "{name}: ultimo post {d} giorni fa", diag_stale_warn_text: "Su {p} non esce nulla da {d} giorni.", diag_stale_warn_step: "Torna al ritmo abituale prima che la copertura inizi a scendere.",
    diag_zero_views_cat: "Nessuna visualizzazione", diag_zero_views_title: "{name}: 0 views sugli ultimi video", diag_zero_views_text: "Gli ultimi video pubblicati non hanno ancora nessuna visualizzazione.", diag_zero_views_step: "Se sono appena usciti è normale; se hanno qualche giorno, rivedi titolo, miniatura e primi secondi.",
    diag_not_configured_cat: "Da configurare", diag_not_configured_title: "{name}: non configurato", diag_not_configured_text: "L'account è elencato ma non ha credenziali associate.", diag_not_configured_step: "Collega l'account, oppure rimuovilo dall'elenco se non ti serve.",
    diag_x_not_linked_cat: "Non collegato", diag_x_not_linked_title: "X non collegato", diag_x_not_linked_text: "Nessuna credenziale X configurata.", diag_x_not_linked_step: "X non espone le statistiche di lettura sul piano gratuito: al momento la sezione resta informativa.",
    diag_x_linked_cat: "Collegato", diag_x_linked_title: "X collegato", diag_x_linked_text: "Credenziali presenti. Le statistiche di lettura non sono disponibili sul piano gratuito di X.", diag_x_linked_step: "Nessuna azione richiesta.",
    yt_total_views_lag_note: "YouTube a volte impiega ore/giorni ad aggiornare il totale storico su canali piccoli/nuovi — non è un errore del dashboard.",
    overview_sub: "{n} account monitorati su {p} piattaforme.", overview_sub_empty: "Premi Refresh per caricare i tuoi dati.",
    trend_since: "dal precedente", trend_no_history: "Serve un altro refresh per vedere il trend.",
    account_guest: "Ospite", account_signin_hint: "Accedi per salvare",
    auth_tab_login: "Accedi", auth_tab_register: "Registrati",
    auth_title_login: "Bentornato", auth_title_register: "Crea il tuo account",
    auth_sub_login: "Accedi per sincronizzare piani e preferenze.", auth_sub_register: "Bastano trenta secondi. Nessuna carta richiesta.",
    auth_name: "Come ti chiami", auth_first_name: "Nome", auth_last_name: "Cognome", auth_birth_date: "Data di nascita",
    auth_first_name_ph: "Mario", auth_last_name_ph: "Rossi", auth_email_ph: "tu@esempio.com",
    auth_email: "Email", auth_password: "Password", auth_password_confirm: "Conferma password",
    auth_switch_to_register: "Non hai un account?", auth_switch_to_login: "Hai già un account?",
    auth_aside_badge: "Tutto in un posto solo",
    auth_aside_title: "Smetti di aprire sei app per capire come stai andando.",
    auth_aside_1: "Tutti i tuoi account, un solo colpo d'occhio",
    auth_aside_2: "Ti dice quando un numero scende, non solo quanto vale",
    auth_aside_3: "Trova gli orari in cui i tuoi post rendono di più",
    auth_aside_4: "I token restano sul tuo computer, non su un server",
    auth_aside_foot: "Nessuna carta richiesta per iniziare.",
    auth_logout: "Esci", account_upgrade: "Passa a Pro", account_upgrade_studio: "Passa a Studio", account_since: "Account creato il {d}",
    err_email_invalid: "Inserisci un indirizzo email valido.", err_password_short: "Almeno 8 caratteri.",
    err_required: "Campo obbligatorio.", err_birth_date_future: "La data non può essere nel futuro.",
    err_birth_invalid: "Inserisci una data di nascita valida.", err_birth_too_young: "Devi avere almeno 13 anni per registrarti.",
    err_first_name_required: "Inserisci il tuo nome.", err_last_name_required: "Inserisci il tuo cognome.",
    err_email_taken: "Esiste già un account con questa email.", err_bad_credentials: "Email o password non corretti.",
    err_session_expired: "Sessione non valida o scaduta.", err_login_required_for_plan: "Devi accedere prima di acquistare un piano.",
    err_age_min: "Devi avere almeno {n} anni.", err_password_mismatch: "Le due password non coincidono.",
    auth_forgot_password: "Password dimenticata?", reset_title: "Reimposta la password", reset_step1_sub: "Inserisci la tua email: ti mandiamo un codice a 6 cifre.", reset_step2_sub: "Codice inviato a {email}. Controlla anche lo spam.", reset_send_code: "Invia codice", reset_code_label: "Codice a 6 cifre", reset_new_password: "Nuova password", reset_confirm: "Reimposta password", reset_resend: "Invia di nuovo il codice", reset_err_code_format: "Il codice deve avere 6 cifre.", reset_success: "Password reimpostata. Hai effettuato l'accesso.", err_reset_invalid: "Codice non valido.", err_reset_expired: "Il codice è scaduto, richiedine uno nuovo.", err_reset_too_many: "Troppi tentativi con questo codice. Richiedine uno nuovo.",
    toast_welcome: "Benvenuto, {n}!", toast_logged_in: "Bentornato, {n}!", toast_logged_out: "Sei uscito dall'account.",
    toast_refresh_done: "Dati aggiornati.", toast_export_done: "CSV esportato.",
    toast_login_required: "Accedi prima di scegliere un piano.",
    pricing_title: "Scegli quanto vuoi vedere", pricing_sub: "Inizia gratis. Passa a Pro quando i numeri iniziano a contare davvero.",
    pricing_monthly: "Mensile", pricing_yearly: "Annuale", pricing_save: "2 mesi gratis",
    plan_popular: "Il più scelto", plan_free_cta: "Inizia gratis", plan_cta: "Scegli {p}",
    plan_current: "Piano attuale", plan_period_month: "/mese", plan_period_year: "/anno",
    plan_billed_yearly: "{a}€ fatturati una volta l'anno", plan_billed_free: "Per sempre, senza scadenza",
    pricing_note_ready: "Pagamento sicuro tramite Stripe. Puoi disdire quando vuoi.",
    pricing_note_setup: "I pagamenti non sono al momento disponibili. Riprova più tardi.",
    checkout_unavailable: "Il servizio di pagamento non è raggiungibile. Riprova tra poco.",
    plan_unknown: "Piano non valido.",
    checkout_opened: "Ho aperto la pagina di pagamento nel browser.",
    licence_title: "Licenza",
    licence_hint: "Hai acquistato Pro o Studio? Incolla qui la chiave che hai ricevuto dopo il pagamento.",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "Attiva", licence_manage: "Gestisci abbonamento", licence_remove: "Rimuovi da questo computer",
    licence_state_free: "Piano Free", licence_state_active: "{p} attivo",
    licence_state_expired: "Licenza da verificare",
    licence_state_revoked: "Licenza non attiva",
    licence_revoked_note: "Questo abbonamento non risulta più attivo. Se pensi sia un errore, contatta l'assistenza.",
    licence_active_on: "Licenza attiva ({k})",
    licence_recheck_failed: "Non riusciamo a verificare la licenza. Controlla la connessione: il piano resta attivo ancora per qualche giorno.",
    licence_enter_key: "Inserisci la chiave di licenza.",
    licence_activated: "{p} attivato!", licence_removed: "Licenza rimossa da questo computer.",
    license_missing: "Inserisci la chiave di licenza.",
    license_not_found: "Chiave non valida. Controlla di averla copiata per intero.",
    license_inactive: "Questa licenza non è più attiva. Se l'abbonamento è in corso, contatta l'assistenza.",
    license_service_unavailable: "Non riusciamo a raggiungere il servizio di verifica. Controlla la connessione e riprova.",
    palette_placeholder: "Vai a…", palette_empty: "Nessun risultato.",
    strength_labels: "debole,debole,media,buona,ottima",
  },
  en: {

    // --- Aggiornamento automatico ---
    update_available_title: "Version {version} is available",
    update_now: "Update now",
    update_later: "Remind me later",
    update_skip: "Skip this version",
    update_mandatory: "Required update",
    update_downloading: "Downloading and verifying…",
    update_restarting: "The app will close and reopen itself on the new version.",
    update_failed: "The update did not go through. Your current version is untouched.",
    update_managed_by_winget: "This copy was installed with winget: update it with \"winget upgrade\".",
    update_running_from_source: "You are running from source: automatic updates do not apply.",
    update_up_to_date: "You're up to date.",
    update_check_now: "Check for updates",
    update_channel_beta: "Receive test versions",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "This key has already reached its device limit. Deactivate it on another device before trying again here.",
    license_reactivate_needed: "Enter the key again on this device to reactivate it here.",

    // --- state OAuth non valido ---
    connect_state_missing: "No connection is waiting to be completed. Start again by pressing Link.",
    connect_state_mismatch: "This address doesn't match the connection you started. Paste the full address of the page you landed on — and if it isn't yours, don't use it.",

    // --- Dati in cache ---
    cache_title: "Cached data",
    cache_hint: "If a number looks wrong even after Refresh, clearing the local cache forces the dashboard to recompute everything from scratch. Your linked accounts and license stay untouched.",
    cache_clear_btn: "Clear cached data", app_footer_rights: "All rights reserved.", app_footer_license: "License",
    cache_confirm: "Saved stats and history will be recomputed from the next refresh. Continue?",
    cache_cleared: "Cache cleared.",

    // --- Controllo aggiornamenti ---
    update_available: "Update available",
    update_available_v: "Version {v} available",
    update_hint: "Opens the download page for version {v}.",
    um_size: "{size}",
    um_release_notes: "Release notes",
    um_installing: "Installing…",
    um_later: "Remind me later",
    um_skip: "Skip this version",
    um_install: "Install and restart",
    um_error: "Installation failed. Try again, or download the new version manually.",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "Connect {p} with your own app",
    sw_step_of: "Step {n} of {tot}",
    sw_back: "Back",
    sw_next: "Next",
    sw_finish: "Save and connect",
    sw_saving: "Checking…",
    sw_open: "Open the page",
    sw_copy: "Copy",
    sw_copied: "Copied ✓",
    sw_copy_failed: "Couldn't copy: select the address and copy it manually.",
    sw_saved: "Done — now sign in to your account.",
    sw_removed: "Your own app has been removed.",
    sw_offer: "Don't want to wait? You can connect it right away by registering your own app — we'll guide you step by step, it takes about 10 minutes.",
    sw_offer_btn: "Connect it now →",
    sw_own_active: "You're using your own app ({id}).",
    sw_own_remove: "Remove",
    sw_id_label_ig: "Instagram app ID",
    sw_secret_label_ig: "Instagram app secret",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32 characters",
    sw_id_label_tt: "Client key",
    sw_secret_label_tt: "Client secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "paste the secret",
    sw_ig1_t: "What you'll need",
    sw_ig1_d: "You'll register your own Instagram app: about 10 minutes, once only.\nYou need an Instagram Professional account (Business or Creator) and a Facebook account to access the developer dashboard.\nThe credentials stay on this computer.",
    sw_ig2_t: "Create the app",
    sw_ig2_d: "Open the Meta developer dashboard and click «Create app».\nWhen asked for the use case pick «Other», then choose «Business» as the type.\nThe name is up to you.",
    sw_ig3_t: "Add Instagram",
    sw_ig3_d: "In your new app open «Add products», find «Instagram» and click «Set up».\nThen choose «API setup with Instagram business login».",
    sw_ig4_t: "Paste the redirect address",
    sw_ig4_d: "On the same page open «Business login settings».\nCopy the address below and paste it into the «OAuth redirect URI» field, then save.\nThat page already exists — you don't have to publish any website.",
    sw_ig5_t: "Copy the two credentials",
    sw_ig5_d: "Still on that page, in the app settings section, you'll find «Instagram app ID» and «Instagram app secret».\nCopy them below — this is the last step.",
    sw_tt1_t: "What you'll need",
    sw_tt1_d: "You'll register your own TikTok app: about 10 minutes, once only.\nAll you need is your TikTok account.\nThe credentials stay on this computer.",
    sw_tt2_t: "Create the app",
    sw_tt2_d: "Open the TikTok developer portal, sign in with your account and register a new app.\nGive it a name and confirm.",
    sw_tt3_t: "Enable login and permissions",
    sw_tt3_d: "In your app open «Add products» and add «Login Kit».\nAmong the scopes enable user.info.basic, user.info.stats and video.list.\nThey are read-only: they let the dashboard read followers and video stats.",
    sw_tt4_t: "Create the sandbox",
    sw_tt4_d: "Open «Sandbox» and create one.\nInside it, add your TikTok account as a «target user» — this is what lets you read your own data without waiting for TikTok's review.",
    sw_tt5_t: "Paste the redirect address",
    sw_tt5_d: "In the Login Kit settings, copy the address below and paste it among the «Redirect URI» entries, then save.\nThat page already exists — you don't have to publish any website.",
    sw_tt6_t: "Copy the two credentials",
    sw_tt6_d: "In the app details you'll find the sandbox «Client key» and «Client secret».\nCopy them below — this is the last step.",
    ownapp_missing: "Fill in both fields.",
    ownapp_unsupported: "Platform not supported.",
    ownapp_bad_ig_id: "The Instagram app ID is digits only. Check you haven't swapped the two fields.",
    ownapp_bad_ig_secret: "The app secret doesn't look complete: copy all of it, without spaces.",
    ownapp_bad_tt_key: "The TikTok client key starts with «aw» or «sbaw». Check you haven't swapped the two fields.",
    ownapp_bad_tt_secret: "The client secret doesn't look complete: copy all of it, without spaces.",
    ownapp_tt_refused: "TikTok doesn't recognize these credentials. Check that the client key and client secret come from the same app.",
    overview_by_platform: "By platform",
    overview_top_content: "Top content", platform_status_green: "Connected and synced", platform_status_yellow: "Needs attention", platform_status_red: "Error", platform_status_grey: "Not configured yet",
    tile_followers: "Total audience", tile_recent_views: "Recent views", tile_recent_views_foot: "on latest content",
    tile_engagement: "Interactions", tile_engagement_foot: "recent likes + comments",
    tile_health: "Health", tile_accounts_foot: "active accounts",
    tile_analyzed: "Content analyzed", tile_analyzed_foot: "posts and videos with data",
    tile_avg_per_post: "Average per post", tile_avg_per_post_foot: "average views",
    tile_avg_per_post_foot_n: "average views across {n} posts with data", tile_best_hour_insufficient: "needs more content",
    analytics_hours_insufficient: "Not enough data yet for a reliable time slot: {n} more posts with views are needed.",
    tile_best_hour: "Best hour", tile_best_hour_foot: "{v} average views",
    tile_best_platform: "Top platform", tile_best_platform_foot: "{v} total views",
    analytics_hours_hint: "Average views by publishing hour (UTC). The filled bars are the hours when your content performs best.",
    hours_tooltip: "{h}:00 - {v} average views across {n} posts",
    guided_step1: "Authorize the account in the tab that just opened.",
    guided_step2: "Then copy the address of the page you land on and paste it below.",
    guided_placeholder: "Paste the full URL here", guided_cancel: "Cancel", guided_finish: "Finish",
    guided_paste_needed: "Paste the return URL first.",
    btn_link_account: "Link", btn_link_account_full: "Link an account",
    cm_auto_text: "Your browser will open: sign in and grant read-only access. The dashboard handles the rest.",
    cm_step1: "Authorize the account in the tab that opens.", cm_open: "Open authorization",
    cm_step2: "Paste the address of the page you land on here.", cm_finish: "Finish linking",
    group_connections: "Linked accounts", nav_connections: "Link account",
    connections_subtitle: "Sign in with your account and the dashboard does the rest. No tokens to copy.",
    connections_privacy: "Authorizations are stored only on your computer, locally. They never pass through any server.",
    connect_now: "Link {p}", connect_add_another: "Link another account", connect_soon: "Coming soon",
    generic_error: "Something went wrong.", connect_timeout: "Timed out: the link was not completed.",
    connect_already_running: "A connection is already in progress.",
    connect_platform_unsupported: "This platform isn't supported yet.",
    connect_guided_unavailable: "Guided connection isn't available for this platform.",
    connect_window_closed: "Connection canceled: the window was closed before finishing sign-in.",
    connect_denied: "Authorization was denied by the platform.",
    connect_code_not_found: "Couldn't find the code in the pasted URL.",
    connect_instagram_rejected: "Instagram rejected the authorization code. Try connecting the account again.",
    connect_token_exchange_failed: "Token exchange failed. Try connecting the account again.",
    connect_tiktok_rejected: "TikTok rejected the authorization code. Try connecting the account again.",
    connect_tiktok_unexpected: "Unexpected response from TikTok. Try again later.",
    connect_proxy_http_error: "The authorization service didn't respond correctly. Try again shortly.",
    connect_proxy_rejected: "The authorization service rejected the request.",
    connect_no_google_app: "No Google OAuth app configured.",
    connect_coming_soon: "Coming soon",
    cm_coming_soon_text: "This platform's connection is almost ready: we're completing the approval required by the platform itself. Check back in a few days.",
    proxy_not_configured: "The authorization service isn't configured in this build.",
    unavail_not_configured: "Linking is not available yet in this version of the app.",
    unavail_x_no_read_api: "X does not expose read analytics on the free plan.",
    connect_not_linked: "Not linked", connect_linked_n: "{n} linked", connect_unlink: "Unlink",
    connect_reauth_badge: "Needs relinking",
    connect_reauth_hint: "Access expired or was revoked by the platform: link this account again to keep reading its stats.",
    connect_locked_hint: "This account's credentials can't be read on this computer: link it again to continue.",
    connect_desc: "Sign in with {p} to see your stats here.",
    connect_waiting: "Waiting for browser...", connect_browser_opened: "Browser opened: complete the sign-in.",
    connect_success: "{n} linked!", connect_unlinked: "Account unlinked.",
    diag_problems: "problems", diag_warnings: "warnings", diag_ok: "fine",
    diag_filter_all: "All", diag_filter_problems: "Needs fixing", diag_filter_ok: "Fine",
    diag_filter_empty: "Nothing to show with this filter.", diag_go_connect: "Go to Link account",
    diag_group_strategy: "Strategy",
    health_part_technical: "Technical", health_part_engagement: "Engagement",
    health_part_consistency: "Consistency", health_part_coverage: "Coverage",
    health_detail_technical: "{n} problem(s) blocking data collection", health_detail_engagement: "compared against {n} platform benchmark(s)", health_detail_engagement_none: "not enough follower data to compare", health_detail_consistency: "last post {days} day(s) ago", health_detail_consistency_none: "no dated content yet", health_detail_coverage: "{active} of {total} platform(s) with recent content",
    health_nodata_title: "No account linked", health_nodata_sub: "Link an account to see your health score.",
    health_bad_title: "Some things need fixing", health_bad_sub: "{n} problems and warnings need your attention.",
    health_warn_title: "Almost all good", health_warn_sub: "{n} warnings to keep an eye on.",
    health_good_title: "All good", health_good_sub: "No problems found on your accounts.",
    group_general: "General", group_platforms: "Platforms", group_insights: "Insights",
    group_account: "Account", group_settings: "Settings",
    nav_overview: "Overview", nav_analytics: "Analytics", nav_diagnostics: "Diagnostics",
    nav_themes: "Themes", nav_language: "Language", nav_account: "Your account", nav_pricing: "Plans & pricing",
    btn_refresh: "Refresh", btn_analyze: "Analyze", btn_export: "Export CSV", palette_hint: "Search",
    analytics_subtitle: "Computed locally from collected data — top posts and best posting hours, zero AI cost.",
    analytics_top_posts: "Top posts/videos (by views)", analytics_outliers: "Above/below your average", analytics_outliers_hint: "Compared against your own average of {v} views per post — not an industry benchmark that knows nothing about your audience.", analytics_outliers_empty: "Not enough content yet for a reliable comparison.", analytics_best_hours: "Best posting hours (avg views)",
    diagnostics_subtitle: "Computed instantly from code, zero cost — flags errors and updates on every Refresh.",
    themes_subtitle: "Choose the dashboard's look — saved for next time too.",
    language_subtitle: "Choose the interface language — saved for next time too.",
    empty_no_data: "No data — press Refresh.", waiting_for_data: "Waiting for data", empty_configure_yt: "Connect a YouTube channel to see your stats here.",
    empty_configure_ig: "Connect an Instagram account to see your stats here.", empty_configure_tt: "Connect a TikTok account to see your stats here.",
    empty_not_configured: "Not configured.",
    label_subscribers_total: "Total subscribers", label_channels: "Channels", label_followers_total: "Total followers",
    label_accounts: "Accounts", label_accounts_configured: "Configured accounts", label_credentials: "Credentials",
    val_ok: "OK", val_missing: "Missing", label_site: "Site", val_online: "Online", val_down: "Down",
    label_subscribers: "Subscribers", label_total_views: "Total views", label_videos_published: "Published videos",
    label_recent_views: "Views (last 10 videos)", label_last_publish: "Last published", label_never_published: "Never published",
    label_followers: "Followers", label_views_recent: "Views (recent posts)", label_likes: "Likes", label_comments: "Comments",
    label_views: "Views", label_likes_comments_shares: "Likes / Comments / Shares",
    val_online_latency: "Online ({ms}ms)", val_down_error: "Down / error", label_npm_vulns: "npm vulnerabilities",
    label_eslint: "ESLint", val_not_configured: "not configured", val_errors_warnings: "{e} errors, {w} warnings",
    insight_loading: "Analyzing…", insight_error: "Error during analysis: ",
    ins_no_items: "{name}: no recent content to analyze.",
    locked_title: "Pro plan feature",
    locked_cta: "See plans",
    locked_best_hours: "Recommended time slots are included in the Pro plan.",
    locked_history: "History and trend charts are included in the Pro plan.",
    plan_feature_locked: "This feature is included in the Pro plan.",
    plan_account_limit: "Your plan includes {n} linked accounts. Move up a plan to add more.",
    plan_account_limit_one: "Your plan includes only 1 linked account. Move up a plan to add more.",
    plan_free_tagline: "To get started and understand your numbers.",
    plan_free_accounts: "1 linked account",
    plan_pro_tagline: "For those posting daily who want to grow.",
    plan_pro_accounts: "3 linked accounts",
    plan_studio_tagline: "For agencies and multi-brand managers.",
    plan_studio_accounts: "10 linked accounts",
    plan_feat_all_socials: "Stats for every supported social network",
    plan_feat_manual_refresh: "Manual on-demand refresh",
    plan_feat_analytics: "Analytics: top posts and time slots",
    plan_feat_diagnostics: "Automatic error diagnostics",
    plan_feat_insights: "Automatic observations on your content",
    plan_feat_history: "Full history with trend charts",
    plan_feat_reports: "Automated reports",
    plan_feat_all_free: "Everything in Free",
    plan_feat_compare: "Period comparison and drop alerts",
    plan_feat_hours: "Publishing time suggestions",
    plan_feat_csv: "CSV data export",
    plan_feat_all_pro: "Everything in Pro",
    plan_feat_workspaces: "Separate workspaces per client",
    plan_feat_whitelabel: "Automated white-label PDF reports",
    plan_feat_multiuser: "Multi-user team access",
    plan_feat_priority: "Priority support",
    aria_toggle_password: "Show password",
    aria_close: "Close",
    ins_some_zero: "{name}: {n} of the last {tot} posts still have zero views.",
    ins_some_zero_one: "{name}: 1 of the last {tot} posts still has zero views.",
    ins_all_zero_one: "{name}: the only recent post has no views yet.",
    ins_flop_one: "{name}: 1 post below 40% of the average: “{title}” with {v} views.",
    ins_cadence_daily: "{name}: you post about {n} times a day.",
    ins_cadence_broken_daily: "{name}: you usually post several times a day, but the latest content is {d} days old.",
    ins_all_zero: "{name}: none of the last {n} posts has any views yet.",
    ins_star: "{name}: “{title}” hit {v} views, {x}x the account average. Look at what sets it apart and repeat it.",
    ins_flop: "{name}: {n} posts below 40% of the average; the weakest is “{title}” with {v} views.",
    ins_engagement: "{name}: {rate}% engagement on recent content ({i} interactions across {v} views).",
    ins_cadence_broken: "{name}: you usually post every {gap} days, but the latest content is {d} days old.",
    ins_cadence: "{name}: you post every {gap} days on average.",
    ins_best_account: "{best} is your best performing account: {bv} views versus {wv} for {worst}.",
    ins_x_free_plan: "X doesn't expose read analytics on the free plan: there's nothing to analyze.",
    ins_no_data: "Nothing to analyze yet: link an account and press Refresh.",
    ins_nothing_notable: "No issues found in your recent content.",
    analytics_empty: "Not enough posts/videos with data yet for an analysis — press Refresh.",
    analytics_engagement: "Engagement",
    analytics_engagement_hint: "Share of the people you reached who liked, commented, shared or saved. Compared against the average for accounts of your size.",
    analytics_heatmap: "Day and hour",
    analytics_heatmap_hint: "Where your content actually landed. Darker means more average views for the posts published in that slot.",
    eng_above: "Above average ({e}%)", eng_below: "Below average ({e}%)",
    eng_inline: "In line with average ({e}%)",
    eng_no_benchmark: "Follower count unavailable for comparison",
    eng_saves: "Saves", eng_shares: "Shares",
    eng_saves_hint: "Share of the people you reached who saved the post: the strongest signal that it was worth keeping.",
    eng_shares_hint: "Share of the people you reached who sent it on: this is how content escapes your own audience.",
    heatmap_not_enough: "More content with a date and time is needed to draw the map.",
    heatmap_cell: "{d} at {h}:00 — {v} average views across {n} posts",
    weekday_short: "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    analytics_untitled: "(untitled)", analytics_avg_views: "avg views", analytics_bucket_count: "posts analyzed in this slot",
    analytics_last_refresh: "Last data load: {t} ({d})", analytics_last_refresh_never: "Last data load: never — press Refresh.",
    footer_last_refresh: "Last updated: {d}", footer_never: "Never updated", footer_error: "Error during refresh - try again.",
    time_never: "never", time_seconds_ago: "a few seconds ago", time_min_ago: "{n} min ago", time_hours_ago: "{n} hours ago", time_days_ago: "{n} days ago",
    diag_next_step_label: "Next step:",
    diag_unreachable_title: "{name}: not responding",
    diagerr_scope_denied_cat: "Permission not granted", diagerr_scope_denied_step: "The stats-read permission must be approved on the platform's developer portal — this can't be fixed from the app.",
    diagerr_expired_cat: "Access expired", diagerr_expired_step: "Relink this account: the authorization expired or was revoked.",
    diagerr_scope_mismatch_cat: "Permissions out of sync", diagerr_scope_mismatch_step: "The requested permissions don't match the ones originally granted: relink the account to realign them.",
    diagerr_permission_cat: "Missing permission", diagerr_permission_step: "The account didn't grant the required permission: relink it and accept every request.",
    diagerr_rate_cat: "Too many requests", diagerr_rate_step: "Wait a few minutes before refreshing again: the platform's rate limit was reached.",
    diagerr_auth_cat: "Invalid credentials", diagerr_auth_step: "Relink the account to regenerate access.",
    diagerr_notfound_cat: "Account not found", diagerr_notfound_step: "The linked account is no longer reachable: it may have been removed or renamed.",
    diagerr_network_cat: "Network problem", diagerr_network_step: "Try refreshing again: this looks like a temporary connection issue.",
    diagerr_unknown_cat: "Unclassified error", diagerr_unknown_step: "Try refreshing again; if it persists, relink the account.",
    diag_no_account_cat: "To link", diag_no_account_title: "No {p} account", diag_no_account_text: "You haven't linked any {p} account yet.", diag_no_account_step: "Press Link and sign in: it only takes a few seconds.",
    diag_no_data_cat: "Missing data", diag_no_data_title: "{p} has no data", diag_no_data_text: "No data loaded yet.", diag_no_data_step: "Press Refresh to load the data.",
    diag_all_ok_title_one: "{p}: 1 account healthy", diag_all_ok_cat_one: "All good", diag_all_ok_text_one: "The account responds and posts consistently.", diag_all_ok_step_one: "No action needed.",
    diag_all_ok_cat: "All good", diag_all_ok_title: "{p}: {n} accounts healthy", diag_all_ok_text: "Every account responds and posts consistently.", diag_all_ok_step: "No action needed.",
    diag_stale_bad_cat: "Content stalled", diag_stale_bad_title: "{name}: idle for {d} days", diag_stale_bad_text: "The latest content on {p} is {d} days old.", diag_stale_bad_step: "Post something: platforms reward consistency and reach drops fast on inactive profiles.",
    diag_stale_warn_cat: "Slowing down", diag_stale_warn_title: "{name}: last post {d} days ago", diag_stale_warn_text: "Nothing new on {p} for {d} days.", diag_stale_warn_step: "Get back to your usual pace before reach starts to fall.",
    diag_zero_views_cat: "No views", diag_zero_views_title: "{name}: 0 views on latest videos", diag_zero_views_text: "The latest published videos have no views yet.", diag_zero_views_step: "If they just went live that's normal; if they're a few days old, revisit title, thumbnail and first seconds.",
    diag_not_configured_cat: "To configure", diag_not_configured_title: "{name}: not configured", diag_not_configured_text: "The account is listed but has no credentials attached.", diag_not_configured_step: "Link the account, or remove it from the list if you don't need it.",
    diag_x_not_linked_cat: "Not linked", diag_x_not_linked_title: "X not linked", diag_x_not_linked_text: "No X credentials configured.", diag_x_not_linked_step: "X doesn't expose read analytics on the free plan: for now this section stays informational.",
    diag_x_linked_cat: "Linked", diag_x_linked_title: "X linked", diag_x_linked_text: "Credentials present. Read analytics aren't available on X's free plan.", diag_x_linked_step: "No action needed.",
    yt_total_views_lag_note: "YouTube can take hours/days to update the historical total on small/new channels — this isn't a dashboard bug.",
    overview_sub: "{n} accounts tracked across {p} platforms.", overview_sub_empty: "Press Refresh to load your data.",
    trend_since: "since last", trend_no_history: "One more refresh and the trend shows up here.",
    account_guest: "Guest", account_signin_hint: "Sign in to save",
    auth_tab_login: "Sign in", auth_tab_register: "Sign up",
    auth_title_login: "Welcome back", auth_title_register: "Create your account",
    auth_sub_login: "Sign in to sync plans and preferences.", auth_sub_register: "Takes thirty seconds. No card required.",
    auth_name: "Your name", auth_first_name: "First name", auth_last_name: "Last name", auth_birth_date: "Date of birth",
    auth_first_name_ph: "Jane", auth_last_name_ph: "Smith", auth_email_ph: "you@example.com",
    auth_email: "Email", auth_password: "Password", auth_password_confirm: "Confirm password",
    auth_switch_to_register: "No account yet?", auth_switch_to_login: "Already have an account?",
    auth_aside_badge: "All in one place",
    auth_aside_title: "Stop opening six apps to find out how you're doing.",
    auth_aside_1: "Every account you run, in a single glance",
    auth_aside_2: "Tells you when a number drops, not just what it is",
    auth_aside_3: "Finds the hours your posts actually perform",
    auth_aside_4: "Your tokens stay on your machine, not on a server",
    auth_aside_foot: "No card required to start.",
    auth_logout: "Sign out", account_upgrade: "Upgrade to Pro", account_upgrade_studio: "Upgrade to Studio", account_since: "Account created on {d}",
    err_email_invalid: "Enter a valid email address.", err_password_short: "At least 8 characters.",
    err_required: "This field is required.", err_birth_date_future: "The date can't be in the future.",
    err_birth_invalid: "Enter a valid date of birth.", err_birth_too_young: "You must be at least 13 to sign up.",
    err_first_name_required: "Enter your first name.", err_last_name_required: "Enter your last name.",
    err_email_taken: "An account with this email already exists.", err_bad_credentials: "Incorrect email or password.",
    err_session_expired: "Session invalid or expired.", err_login_required_for_plan: "Sign in before purchasing a plan.",
    err_age_min: "You must be at least {n} years old.", err_password_mismatch: "The two passwords don't match.",
    auth_forgot_password: "Forgot password?", reset_title: "Reset your password", reset_step1_sub: "Enter your email and we'll send you a 6-digit code.", reset_step2_sub: "Code sent to {email}. Check your spam folder too.", reset_send_code: "Send code", reset_code_label: "6-digit code", reset_new_password: "New password", reset_confirm: "Reset password", reset_resend: "Resend code", reset_err_code_format: "The code must be 6 digits.", reset_success: "Password reset. You're signed in.", err_reset_invalid: "Invalid code.", err_reset_expired: "This code has expired — request a new one.", err_reset_too_many: "Too many attempts with this code. Request a new one.",
    toast_welcome: "Welcome, {n}!", toast_logged_in: "Welcome back, {n}!", toast_logged_out: "You've been signed out.",
    toast_refresh_done: "Data updated.", toast_export_done: "CSV exported.",
    toast_login_required: "Sign in before choosing a plan.",
    pricing_title: "Choose how much you want to see", pricing_sub: "Start free. Move to Pro when the numbers start to matter.",
    pricing_monthly: "Monthly", pricing_yearly: "Yearly", pricing_save: "2 months free",
    plan_popular: "Most popular", plan_free_cta: "Start free", plan_cta: "Choose {p}",
    plan_current: "Current plan", plan_period_month: "/mo", plan_period_year: "/yr",
    plan_billed_yearly: "€{a} billed once a year", plan_billed_free: "Free forever, no expiry",
    pricing_note_ready: "Secure payment via Stripe. Cancel anytime.",
    pricing_note_setup: "Payments are currently unavailable. Please try again later.",
    checkout_unavailable: "The payment service can't be reached. Try again shortly.",
    plan_unknown: "Invalid plan.",
    checkout_opened: "I've opened the payment page in your browser.",
    licence_title: "License",
    licence_hint: "Bought Pro or Studio? Paste the key you received after payment.",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "Activate", licence_manage: "Manage subscription", licence_remove: "Remove from this computer",
    licence_state_free: "Free plan", licence_state_active: "{p} active",
    licence_state_expired: "License needs checking",
    licence_state_revoked: "License inactive",
    licence_revoked_note: "This subscription is no longer active. If you think this is a mistake, contact support.",
    licence_active_on: "License active ({k})",
    licence_recheck_failed: "We can't verify your license right now. Check your connection — your plan stays active for a few more days.",
    licence_enter_key: "Enter your license key.",
    licence_activated: "{p} activated!", licence_removed: "License removed from this computer.",
    license_missing: "Enter your license key.",
    license_not_found: "Invalid key. Check that you copied all of it.",
    license_inactive: "This license is no longer active. If your subscription is current, contact support.",
    license_service_unavailable: "We can't reach the verification service. Check your connection and try again.",
    palette_placeholder: "Go to…", palette_empty: "No results.",
    strength_labels: "weak,weak,fair,good,strong",
  },
  es: {

    // --- Aggiornamento automatico ---
    update_available_title: "La versión {version} está disponible",
    update_now: "Actualizar ahora",
    update_later: "Recordármelo más tarde",
    update_skip: "Omitir esta versión",
    update_mandatory: "Actualización necesaria",
    update_downloading: "Descargando y verificando…",
    update_restarting: "La aplicación se cerrará y volverá a abrirse en la nueva versión.",
    update_failed: "La actualización no se completó. Tu versión actual sigue intacta.",
    update_managed_by_winget: "Esta copia se instaló con winget: actualízala con «winget upgrade».",
    update_running_from_source: "Estás ejecutando desde el código fuente: la actualización automática no se aplica.",
    update_up_to_date: "La aplicación está actualizada.",
    update_check_now: "Buscar actualizaciones",
    update_channel_beta: "Recibir versiones de prueba",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "Esta clave ya ha alcanzado el número máximo de dispositivos activos. Desactívala en otro dispositivo antes de volver a intentarlo aquí.",
    license_reactivate_needed: "Vuelve a introducir la clave en este dispositivo para reactivarla aquí.",

    // --- state OAuth non valido ---
    connect_state_missing: "No hay ninguna conexión pendiente. Vuelve a empezar pulsando Vincular.",
    connect_state_mismatch: "Esta dirección no coincide con la conexión que iniciaste. Pega la dirección completa de la página a la que llegaste; si no es tuya, no la uses.",

    // --- Dati in cache ---
    cache_title: "Datos en caché",
    cache_hint: "Si un número parece incorrecto incluso después de actualizar, vaciar la caché local obliga al panel a recalcular todo desde cero. Tus cuentas vinculadas y tu licencia no se ven afectadas.",
    cache_clear_btn: "Vaciar caché", app_footer_rights: "Todos los derechos reservados.", app_footer_license: "Licencia",
    cache_confirm: "Las estadísticas y el historial guardados se recalcularán en la próxima actualización. ¿Continuar?",
    cache_cleared: "Caché vaciada.",

    // --- Controllo aggiornamenti ---
    update_available: "Actualización disponible",
    update_available_v: "Versión {v} disponible",
    update_hint: "Abre la página de descarga de la versión {v}.",
    um_size: "{size}",
    um_release_notes: "Notas de la versión",
    um_installing: "Instalando…",
    um_later: "Recuérdamelo más tarde",
    um_skip: "Omitir esta versión",
    um_install: "Instalar y reiniciar",
    um_error: "La instalación falló. Inténtalo de nuevo o descarga la nueva versión manualmente.",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "Conecta {p} con tu propia app",
    sw_step_of: "Paso {n} de {tot}",
    sw_back: "Atrás",
    sw_next: "Siguiente",
    sw_finish: "Guardar y conectar",
    sw_saving: "Comprobando…",
    sw_open: "Abrir la página",
    sw_copy: "Copiar",
    sw_copied: "Copiado ✓",
    sw_copy_failed: "No se pudo copiar: selecciona la dirección y cópiala a mano.",
    sw_saved: "Listo: ahora inicia sesión en tu cuenta.",
    sw_removed: "Se ha quitado tu propia app.",
    sw_offer: "¿No quieres esperar? Puedes conectarlo ya registrando tu propia app: te guiamos paso a paso, son unos 10 minutos.",
    sw_offer_btn: "Conectarlo ahora →",
    sw_own_active: "Estás usando tu propia app ({id}).",
    sw_own_remove: "Quitar",
    sw_id_label_ig: "ID de la app de Instagram",
    sw_secret_label_ig: "Clave secreta de la app de Instagram",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32 caracteres",
    sw_id_label_tt: "Client key",
    sw_secret_label_tt: "Client secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "pega el secreto",
    sw_ig1_t: "Qué necesitas",
    sw_ig1_d: "Registrarás tu propia app de Instagram: unos 10 minutos, una sola vez.\nNecesitas una cuenta profesional de Instagram (Business o Creator) y una cuenta de Facebook para entrar en el panel de desarrolladores.\nLas credenciales se quedan en este ordenador.",
    sw_ig2_t: "Crea la app",
    sw_ig2_d: "Abre el panel de desarrolladores de Meta y pulsa «Crear app».\nCuando pregunte el caso de uso elige «Otro» y luego «Negocios» como tipo.\nEl nombre es libre.",
    sw_ig3_t: "Añade Instagram",
    sw_ig3_d: "En tu nueva app abre «Añadir productos», busca «Instagram» y pulsa «Configurar».\nLuego elige «Configurar la API con el inicio de sesión de Instagram business».",
    sw_ig4_t: "Pega la dirección de retorno",
    sw_ig4_d: "En la misma página abre «Configuración de inicio de sesión de negocios».\nCopia la dirección de abajo y pégala en el campo «URI de redireccionamiento de OAuth», luego guarda.\nEsa página ya existe: no tienes que publicar ningún sitio.",
    sw_ig5_t: "Copia las dos credenciales",
    sw_ig5_d: "En esa misma página, en la sección de ajustes de la app, encontrarás «ID de la app de Instagram» y «Clave secreta de la app de Instagram».\nCópialos abajo: es el último paso.",
    sw_tt1_t: "Qué necesitas",
    sw_tt1_d: "Registrarás tu propia app de TikTok: unos 10 minutos, una sola vez.\nSolo necesitas tu cuenta de TikTok.\nLas credenciales se quedan en este ordenador.",
    sw_tt2_t: "Crea la app",
    sw_tt2_d: "Abre el portal de desarrolladores de TikTok, inicia sesión con tu cuenta y registra una nueva app.\nPonle un nombre y confirma.",
    sw_tt3_t: "Activa el login y los permisos",
    sw_tt3_d: "En tu app abre «Add products» y añade «Login Kit».\nEntre los ámbitos activa user.info.basic, user.info.stats y video.list.\nSon de solo lectura: sirven para leer seguidores y estadísticas de los vídeos.",
    sw_tt4_t: "Crea la sandbox",
    sw_tt4_d: "Abre «Sandbox» y crea una.\nDentro añade tu cuenta de TikTok como «target user»: esto es lo que te permite leer tus datos sin esperar la revisión de TikTok.",
    sw_tt5_t: "Pega la dirección de retorno",
    sw_tt5_d: "En los ajustes del Login Kit copia la dirección de abajo y pégala entre los «Redirect URI», luego guarda.\nEsa página ya existe: no tienes que publicar ningún sitio.",
    sw_tt6_t: "Copia las dos credenciales",
    sw_tt6_d: "En los detalles de la app encontrarás «Client key» y «Client secret» de la sandbox.\nCópialos abajo: es el último paso.",
    ownapp_missing: "Rellena ambos campos.",
    ownapp_unsupported: "Plataforma no compatible.",
    ownapp_bad_ig_id: "El ID de la app de Instagram son solo dígitos. Comprueba que no hayas invertido los dos campos.",
    ownapp_bad_ig_secret: "La clave secreta no parece completa: cópiala entera, sin espacios.",
    ownapp_bad_tt_key: "La client key de TikTok empieza por «aw» o «sbaw». Comprueba que no hayas invertido los dos campos.",
    ownapp_bad_tt_secret: "El client secret no parece completo: cópialo entero, sin espacios.",
    ownapp_tt_refused: "TikTok no reconoce estas credenciales. Comprueba que la client key y el client secret sean de la misma app.",
    overview_by_platform: "Por plataforma",
    overview_top_content: "Mejor contenido", platform_status_green: "Conectado y sincronizado", platform_status_yellow: "Requiere atención", platform_status_red: "Error", platform_status_grey: "Aún no configurado",
    tile_followers: "Audiencia total", tile_recent_views: "Vistas recientes", tile_recent_views_foot: "en el contenido reciente",
    tile_engagement: "Interacciones", tile_engagement_foot: "me gusta + comentarios recientes",
    tile_health: "Salud", tile_accounts_foot: "cuentas activas",
    tile_analyzed: "Contenido analizado", tile_analyzed_foot: "publicaciones y videos con datos",
    tile_avg_per_post: "Media por contenido", tile_avg_per_post_foot: "vistas medias",
    tile_avg_per_post_foot_n: "vistas medias en {n} contenidos con datos", tile_best_hour_insufficient: "faltan contenidos",
    analytics_hours_insufficient: "Datos aún insuficientes para indicar una franja horaria fiable: faltan al menos {n} contenidos con visualizaciones.",
    tile_best_hour: "Mejor hora", tile_best_hour_foot: "{v} vistas medias",
    tile_best_platform: "Plataforma top", tile_best_platform_foot: "{v} vistas totales",
    analytics_hours_hint: "Media de vistas por franja horaria de publicacion (UTC). Las barras llenas son las horas en que tu contenido rinde mas.",
    hours_tooltip: "{h}:00 - {v} vistas medias en {n} contenidos",
    guided_step1: "Autoriza la cuenta en la pestana que se ha abierto.",
    guided_step2: "Luego copia la direccion de la pagina en la que aterrizas y pegala abajo.",
    guided_placeholder: "Pega aqui la URL completa", guided_cancel: "Cancelar", guided_finish: "Completar",
    guided_paste_needed: "Pega antes la URL de retorno.",
    btn_link_account: "Vincular", btn_link_account_full: "Vincular una cuenta",
    cm_auto_text: "Se abrira el navegador: accede y autoriza el acceso de solo lectura. El panel hace el resto.",
    cm_step1: "Autoriza la cuenta en la pestana que se abre.", cm_open: "Abrir autorizacion",
    cm_step2: "Pega aqui la direccion de la pagina en la que aterrizas.", cm_finish: "Completar vinculacion",
    group_connections: "Cuentas vinculadas", nav_connections: "Vincular cuenta",
    connections_subtitle: "Accede con tu cuenta y el panel hace el resto. Sin tokens que copiar.",
    connections_privacy: "Las autorizaciones se guardan solo en tu ordenador, en local. No pasan por ningun servidor.",
    connect_now: "Vincular {p}", connect_add_another: "Vincular otra cuenta", connect_soon: "Proximamente",
    generic_error: "Se ha producido un error.", connect_timeout: "Tiempo agotado: la vinculación no se completó.",
    connect_already_running: "Ya hay una vinculación en curso.",
    connect_platform_unsupported: "Esta plataforma aún no es compatible.",
    connect_guided_unavailable: "La vinculación guiada no está disponible para esta plataforma.",
    connect_window_closed: "Vinculación cancelada: la ventana se cerró antes de completar el acceso.",
    connect_denied: "La plataforma denegó la autorización.",
    connect_code_not_found: "No se encontró el código en la URL pegada.",
    connect_instagram_rejected: "Instagram rechazó el código de autorización. Vuelve a intentar la vinculación.",
    connect_token_exchange_failed: "Error al intercambiar el token. Vuelve a intentar la vinculación.",
    connect_tiktok_rejected: "TikTok rechazó el código de autorización. Vuelve a intentar la vinculación.",
    connect_tiktok_unexpected: "Respuesta inesperada de TikTok. Inténtalo más tarde.",
    connect_proxy_http_error: "El servicio de autorización no respondió correctamente. Inténtalo en unos minutos.",
    connect_proxy_rejected: "El servicio de autorización rechazó la solicitud.",
    connect_no_google_app: "No hay ninguna app de OAuth de Google configurada.",
    connect_coming_soon: "Próximamente",
    cm_coming_soon_text: "La conexión con esta plataforma está casi lista: estamos completando la aprobación que exige la propia plataforma. Vuelve a intentarlo en unos días.",
    proxy_not_configured: "El servicio de autorización no está configurado en esta build.",
    unavail_not_configured: "La vinculación aún no está disponible en esta versión de la app.",
    unavail_x_no_read_api: "X no ofrece estadísticas de lectura en el plan gratuito.",
    connect_not_linked: "No vinculado", connect_linked_n: "{n} vinculada(s)", connect_unlink: "Desvincular",
    connect_reauth_badge: "Volver a vincular",
    connect_reauth_hint: "El acceso caducó o fue revocado por la plataforma: vuelve a vincular la cuenta para seguir leyendo sus estadísticas.",
    connect_locked_hint: "Las credenciales de esta cuenta no se pueden leer en este equipo: vuelve a vincularla para continuar.",
    connect_desc: "Accede con {p} para ver aqui tus estadisticas.",
    connect_waiting: "Esperando al navegador...", connect_browser_opened: "He abierto el navegador: completa el acceso.",
    connect_success: "\u00a1{n} vinculada!", connect_unlinked: "Cuenta desvinculada.",
    diag_problems: "problemas", diag_warnings: "avisos", diag_ok: "correcto",
    diag_filter_all: "Todo", diag_filter_problems: "Por arreglar", diag_filter_ok: "Correcto",
    diag_filter_empty: "Nada que mostrar con este filtro.", diag_go_connect: "Ir a Vincular cuenta",
    diag_group_strategy: "Estrategia",
    health_part_technical: "Técnica", health_part_engagement: "Engagement",
    health_part_consistency: "Constancia", health_part_coverage: "Cobertura",
    health_detail_technical: "{n} problema(s) bloqueando la recopilación de datos", health_detail_engagement: "comparado con {n} referencia(s) de plataforma", health_detail_engagement_none: "faltan datos de seguidores para comparar", health_detail_consistency: "última publicación hace {days} día(s)", health_detail_consistency_none: "aún no hay contenido con fecha", health_detail_coverage: "{active} de {total} plataforma(s) con contenido reciente",
    health_nodata_title: "Ninguna cuenta vinculada", health_nodata_sub: "Vincula una cuenta para ver tu puntuacion de salud.",
    health_bad_title: "Hay cosas que arreglar", health_bad_sub: "{n} entre problemas y avisos requieren tu atencion.",
    health_warn_title: "Casi todo correcto", health_warn_sub: "{n} avisos a vigilar.",
    health_good_title: "Todo en orden", health_good_sub: "Ningun problema detectado en tus cuentas.",
    group_general: "General", group_platforms: "Plataformas", group_insights: "Análisis",
    group_account: "Cuenta", group_settings: "Ajustes",
    nav_overview: "Resumen", nav_analytics: "Analíticas", nav_diagnostics: "Diagnóstico",
    nav_themes: "Temas", nav_language: "Idioma", nav_account: "Tu cuenta", nav_pricing: "Planes y precios",
    btn_refresh: "Actualizar", btn_analyze: "Analizar", btn_export: "Exportar CSV", palette_hint: "Buscar",
    analytics_subtitle: "Calculadas localmente a partir de los datos recogidos — mejores publicaciones y franjas horarias, sin coste de IA.",
    analytics_top_posts: "Mejores publicaciones/vídeos (por vistas)", analytics_outliers: "Por encima/debajo de tu media", analytics_outliers_hint: "Comparado con tu propia media de {v} vistas por publicación, no con un sector que no conoce tu audiencia.", analytics_outliers_empty: "Aún no hay suficiente contenido para una comparación fiable.", analytics_best_hours: "Mejores franjas horarias (vistas medias)",
    diagnostics_subtitle: "Calculado al instante por el código, sin coste — señala errores y se actualiza en cada Refresh.",
    themes_subtitle: "Elige el aspecto del panel — se guarda para la próxima vez.",
    language_subtitle: "Elige el idioma de la interfaz — se guarda para la próxima vez.",
    empty_no_data: "Sin datos — pulsa Refresh.", waiting_for_data: "Esperando datos", empty_configure_yt: "Vincula un canal de YouTube para ver aquí tus estadísticas.",
    empty_configure_ig: "Vincula una cuenta de Instagram para ver aquí tus estadísticas.", empty_configure_tt: "Vincula una cuenta de TikTok para ver aquí tus estadísticas.",
    empty_not_configured: "No configurado.",
    label_subscribers_total: "Suscriptores totales", label_channels: "Canales", label_followers_total: "Seguidores totales",
    label_accounts: "Cuentas", label_accounts_configured: "Cuentas configuradas", label_credentials: "Credenciales",
    val_ok: "OK", val_missing: "Faltan", label_site: "Sitio", val_online: "En línea", val_down: "Caído",
    label_subscribers: "Suscriptores", label_total_views: "Vistas totales", label_videos_published: "Vídeos publicados",
    label_recent_views: "Vistas (últimos 10 vídeos)", label_last_publish: "Última publicación", label_never_published: "Nunca publicado",
    label_followers: "Seguidores", label_views_recent: "Vistas (publicaciones recientes)", label_likes: "Me gusta", label_comments: "Comentarios",
    label_views: "Vistas", label_likes_comments_shares: "Me gusta / Comentarios / Compartidos",
    val_online_latency: "En línea ({ms}ms)", val_down_error: "Caído / error", label_npm_vulns: "Vulnerabilidades npm",
    label_eslint: "ESLint", val_not_configured: "no configurado", val_errors_warnings: "{e} errores, {w} avisos",
    insight_loading: "Analizando…", insight_error: "Error durante el análisis: ",
    ins_no_items: "{name}: no hay contenido reciente que analizar.",
    locked_title: "Función del plan Pro",
    locked_cta: "Ver planes",
    locked_best_hours: "Las franjas horarias recomendadas se incluyen en el plan Pro.",
    locked_history: "El historial y los gráficos de tendencia se incluyen en el plan Pro.",
    plan_feature_locked: "Esta función se incluye en el plan Pro.",
    plan_account_limit: "Tu plan incluye {n} cuentas vinculadas. Cambia a un plan superior para añadir más.",
    plan_account_limit_one: "Tu plan incluye solo 1 cuenta vinculada. Cambia a un plan superior para añadir más.",
    plan_free_tagline: "Para empezar y entender tus números.",
    plan_free_accounts: "1 cuenta vinculada",
    plan_pro_tagline: "Para quien publica a diario y quiere crecer.",
    plan_pro_accounts: "3 cuentas vinculadas",
    plan_studio_tagline: "Para agencias y quien gestiona varias marcas.",
    plan_studio_accounts: "10 cuentas vinculadas",
    plan_feat_all_socials: "Estadísticas de todas las redes compatibles",
    plan_feat_manual_refresh: "Actualización manual bajo demanda",
    plan_feat_analytics: "Analíticas: mejores publicaciones y franjas",
    plan_feat_diagnostics: "Diagnóstico automático de errores",
    plan_feat_insights: "Observaciones automáticas sobre tu contenido",
    plan_feat_history: "Historial completo con gráficos de tendencia",
    plan_feat_reports: "Informes automáticos",
    plan_feat_all_free: "Todo lo del plan Free",
    plan_feat_compare: "Comparación de periodos y alertas de caída",
    plan_feat_hours: "Sugerencias de horarios de publicación",
    plan_feat_csv: "Exportación de datos en CSV",
    plan_feat_all_pro: "Todo lo del plan Pro",
    plan_feat_workspaces: "Espacios de trabajo separados por cliente",
    plan_feat_whitelabel: "Informes PDF de marca blanca automáticos",
    plan_feat_multiuser: "Acceso multiusuario para el equipo",
    plan_feat_priority: "Soporte prioritario",
    aria_toggle_password: "Mostrar contraseña",
    aria_close: "Cerrar",
    ins_some_zero: "{name}: {n} de las últimas {tot} publicaciones siguen con cero visualizaciones.",
    ins_some_zero_one: "{name}: 1 de las últimas {tot} publicaciones sigue con cero visualizaciones.",
    ins_all_zero_one: "{name}: la única publicación reciente no tiene visualizaciones todavía.",
    ins_flop_one: "{name}: 1 publicación por debajo del 40% de la media: «{title}» con {v} vistas.",
    ins_cadence_daily: "{name}: publicas unas {n} veces al día.",
    ins_cadence_broken_daily: "{name}: sueles publicar varias veces al día, pero el último contenido es de hace {d} días.",
    ins_all_zero: "{name}: ninguna de las últimas {n} publicaciones tiene visualizaciones todavía.",
    ins_star: "{name}: «{title}» alcanzó {v} vistas, {x}x la media de la cuenta. Mira qué lo diferencia y repítelo.",
    ins_flop: "{name}: {n} publicaciones por debajo del 40% de la media; la más floja es «{title}» con {v} vistas.",
    ins_engagement: "{name}: {rate}% de engagement en el contenido reciente ({i} interacciones sobre {v} vistas).",
    ins_cadence_broken: "{name}: sueles publicar cada {gap} días, pero el último contenido es de hace {d} días.",
    ins_cadence: "{name}: publicas de media cada {gap} días.",
    ins_best_account: "{best} es la cuenta que mejor rinde: {bv} vistas frente a las {wv} de {worst}.",
    ins_x_free_plan: "X no ofrece estadísticas de lectura en el plan gratuito: no hay nada que analizar.",
    ins_no_data: "Nada que analizar aún: vincula una cuenta y pulsa Actualizar.",
    ins_nothing_notable: "No se han detectado problemas en tu contenido reciente.",
    analytics_empty: "Aún no hay suficientes publicaciones/vídeos con datos para un análisis — pulsa Refresh.",
    analytics_engagement: "Engagement",
    analytics_engagement_hint: "Porcentaje de las personas que alcanzaste que dieron me gusta, comentaron, compartieron o guardaron. Comparado con la media de cuentas de tu tamaño.",
    analytics_heatmap: "Día y hora",
    analytics_heatmap_hint: "Dónde funcionó realmente tu contenido. Más oscuro significa más visualizaciones medias para las publicaciones de esa franja.",
    eng_above: "Por encima de la media ({e}%)", eng_below: "Por debajo de la media ({e}%)",
    eng_inline: "En línea con la media ({e}%)",
    eng_no_benchmark: "Seguidores no disponibles para la comparación",
    eng_saves: "Guardados", eng_shares: "Compartidos",
    eng_saves_hint: "Porcentaje de quienes te vieron y guardaron la publicación: la señal más fuerte de que aporta valor.",
    eng_shares_hint: "Porcentaje de quienes te vieron y la compartieron: así es como el contenido sale de tu propia audiencia.",
    heatmap_not_enough: "Se necesita más contenido con fecha y hora para dibujar el mapa.",
    heatmap_cell: "{d} a las {h}:00 — {v} visualizaciones medias en {n} publicaciones",
    weekday_short: "Lun,Mar,Mié,Jue,Vie,Sáb,Dom",
    analytics_untitled: "(sin título)", analytics_avg_views: "vistas medias", analytics_bucket_count: "publicaciones analizadas en esta franja",
    analytics_last_refresh: "Última carga de datos: {t} ({d})", analytics_last_refresh_never: "Última carga de datos: nunca — pulsa Refresh.",
    footer_last_refresh: "Última actualización: {d}", footer_never: "Nunca actualizado", footer_error: "Error durante la actualización - inténtalo de nuevo.",
    time_never: "nunca", time_seconds_ago: "hace unos segundos", time_min_ago: "hace {n} min", time_hours_ago: "hace {n} horas", time_days_ago: "hace {n} días",
    diag_next_step_label: "Próximo paso:",
    diag_unreachable_title: "{name}: no responde",
    diagerr_scope_denied_cat: "Permiso no concedido", diagerr_scope_denied_step: "El permiso de lectura de estadísticas debe aprobarse en el portal de desarrolladores de la plataforma: no se puede resolver desde la app.",
    diagerr_expired_cat: "Acceso caducado", diagerr_expired_step: "Vuelve a vincular esta cuenta: la autorización caducó o fue revocada.",
    diagerr_scope_mismatch_cat: "Permisos desalineados", diagerr_scope_mismatch_step: "Los permisos solicitados no coinciden con los concedidos originalmente: vuelve a vincular la cuenta para realinearlos.",
    diagerr_permission_cat: "Falta un permiso", diagerr_permission_step: "La cuenta no concedió el permiso necesario: vuelve a vincularla aceptando todas las solicitudes.",
    diagerr_rate_cat: "Demasiadas solicitudes", diagerr_rate_step: "Espera unos minutos antes de la próxima actualización: se alcanzó el límite de la plataforma.",
    diagerr_auth_cat: "Credenciales no válidas", diagerr_auth_step: "Vuelve a vincular la cuenta para regenerar el acceso.",
    diagerr_notfound_cat: "Cuenta no encontrada", diagerr_notfound_step: "La cuenta vinculada ya no está disponible: puede haber sido eliminada o renombrada.",
    diagerr_network_cat: "Problema de red", diagerr_network_step: "Vuelve a intentar la actualización: parece un problema temporal de conexión.",
    diagerr_unknown_cat: "Error sin clasificar", diagerr_unknown_step: "Vuelve a intentar la actualización; si persiste, vuelve a vincular la cuenta.",
    diag_no_account_cat: "Por vincular", diag_no_account_title: "Ninguna cuenta de {p}", diag_no_account_text: "Aún no has vinculado ninguna cuenta de {p}.", diag_no_account_step: "Pulsa Vincular e inicia sesión: solo tarda unos segundos.",
    diag_no_data_cat: "Faltan datos", diag_no_data_title: "{p} sin datos", diag_no_data_text: "Todavía no se han cargado datos.", diag_no_data_step: "Pulsa Actualizar para cargar los datos.",
    diag_all_ok_title_one: "{p}: 1 cuenta en orden", diag_all_ok_cat_one: "Todo correcto", diag_all_ok_text_one: "La cuenta responde y publica con constancia.", diag_all_ok_step_one: "No se requiere ninguna acción.",
    diag_all_ok_cat: "Todo correcto", diag_all_ok_title: "{p}: {n} cuentas en orden", diag_all_ok_text: "Todas las cuentas responden y publican con constancia.", diag_all_ok_step: "No se requiere ninguna acción.",
    diag_stale_bad_cat: "Contenido detenido", diag_stale_bad_title: "{name}: parado desde hace {d} días", diag_stale_bad_text: "El último contenido en {p} es de hace {d} días.", diag_stale_bad_step: "Publica algo: las plataformas premian la constancia y el alcance cae rápido en perfiles inactivos.",
    diag_stale_warn_cat: "Ritmo a la baja", diag_stale_warn_title: "{name}: última publicación hace {d} días", diag_stale_warn_text: "En {p} no sale nada desde hace {d} días.", diag_stale_warn_step: "Vuelve a tu ritmo habitual antes de que el alcance empiece a bajar.",
    diag_zero_views_cat: "Sin visualizaciones", diag_zero_views_title: "{name}: 0 vistas en los últimos vídeos", diag_zero_views_text: "Los últimos vídeos publicados todavía no tienen visualizaciones.", diag_zero_views_step: "Si acaban de publicarse es normal; si tienen algunos días, revisa título, miniatura y primeros segundos.",
    diag_not_configured_cat: "Por configurar", diag_not_configured_title: "{name}: sin configurar", diag_not_configured_text: "La cuenta aparece en la lista pero no tiene credenciales asociadas.", diag_not_configured_step: "Vincula la cuenta o quítala de la lista si no la necesitas.",
    diag_x_not_linked_cat: "No vinculado", diag_x_not_linked_title: "X no vinculado", diag_x_not_linked_text: "No hay credenciales de X configuradas.", diag_x_not_linked_step: "X no ofrece estadísticas de lectura en el plan gratuito: por ahora esta sección es informativa.",
    diag_x_linked_cat: "Vinculado", diag_x_linked_title: "X vinculado", diag_x_linked_text: "Credenciales presentes. Las estadísticas de lectura no están disponibles en el plan gratuito de X.", diag_x_linked_step: "No se requiere ninguna acción.",
    yt_total_views_lag_note: "YouTube a veces tarda horas/días en actualizar el total histórico en canales pequeños/nuevos — no es un error del panel.",
    overview_sub: "{n} cuentas monitorizadas en {p} plataformas.", overview_sub_empty: "Pulsa Refresh para cargar tus datos.",
    trend_since: "desde la anterior", trend_no_history: "Con otra actualización aparecerá la tendencia.",
    account_guest: "Invitado", account_signin_hint: "Accede para guardar",
    auth_tab_login: "Acceder", auth_tab_register: "Registrarse",
    auth_title_login: "Bienvenido de nuevo", auth_title_register: "Crea tu cuenta",
    auth_sub_login: "Accede para sincronizar planes y preferencias.", auth_sub_register: "Treinta segundos. Sin tarjeta.",
    auth_name: "Tu nombre", auth_first_name: "Nombre", auth_last_name: "Apellidos", auth_birth_date: "Fecha de nacimiento",
    auth_first_name_ph: "María", auth_last_name_ph: "García", auth_email_ph: "tu@ejemplo.com",
    auth_email: "Email", auth_password: "Contraseña", auth_password_confirm: "Confirma la contraseña",
    auth_switch_to_register: "¿Aún no tienes cuenta?", auth_switch_to_login: "¿Ya tienes cuenta?",
    auth_aside_badge: "Todo en un solo sitio",
    auth_aside_title: "Deja de abrir seis apps para saber cómo te va.",
    auth_aside_1: "Todas tus cuentas de un vistazo",
    auth_aside_2: "Te avisa cuando un número baja, no solo cuánto vale",
    auth_aside_3: "Encuentra las horas en que tus posts rinden más",
    auth_aside_4: "Tus tokens se quedan en tu ordenador, no en un servidor",
    auth_aside_foot: "No hace falta tarjeta para empezar.",
    auth_logout: "Salir", account_upgrade: "Pasar a Pro", account_upgrade_studio: "Pasar a Studio", account_since: "Cuenta creada el {d}",
    err_email_invalid: "Introduce un email válido.", err_password_short: "Mínimo 8 caracteres.",
    err_required: "Campo obligatorio.", err_birth_date_future: "La fecha no puede ser futura.",
    err_birth_invalid: "Introduce una fecha de nacimiento válida.", err_birth_too_young: "Debes tener al menos 13 años para registrarte.",
    err_first_name_required: "Introduce tu nombre.", err_last_name_required: "Introduce tus apellidos.",
    err_email_taken: "Ya existe una cuenta con este email.", err_bad_credentials: "Email o contraseña incorrectos.",
    err_session_expired: "Sesión no válida o caducada.", err_login_required_for_plan: "Inicia sesión antes de comprar un plan.",
    err_age_min: "Debes tener al menos {n} años.", err_password_mismatch: "Las contraseñas no coinciden.",
    auth_forgot_password: "¿Olvidaste tu contraseña?", reset_title: "Restablece tu contraseña", reset_step1_sub: "Introduce tu email y te enviaremos un código de 6 dígitos.", reset_step2_sub: "Código enviado a {email}. Revisa también el spam.", reset_send_code: "Enviar código", reset_code_label: "Código de 6 dígitos", reset_new_password: "Nueva contraseña", reset_confirm: "Restablecer contraseña", reset_resend: "Reenviar código", reset_err_code_format: "El código debe tener 6 dígitos.", reset_success: "Contraseña restablecida. Has iniciado sesión.", err_reset_invalid: "Código no válido.", err_reset_expired: "El código ha caducado, solicita uno nuevo.", err_reset_too_many: "Demasiados intentos con este código. Solicita uno nuevo.",
    toast_welcome: "¡Bienvenido, {n}!", toast_logged_in: "¡Bienvenido de nuevo, {n}!", toast_logged_out: "Has cerrado sesión.",
    toast_refresh_done: "Datos actualizados.", toast_export_done: "CSV exportado.",
    toast_login_required: "Accede antes de elegir un plan.",
    pricing_title: "Elige cuánto quieres ver", pricing_sub: "Empieza gratis. Pasa a Pro cuando los números empiecen a importar.",
    pricing_monthly: "Mensual", pricing_yearly: "Anual", pricing_save: "2 meses gratis",
    plan_popular: "El más elegido", plan_free_cta: "Empezar gratis", plan_cta: "Elegir {p}",
    plan_current: "Plan actual", plan_period_month: "/mes", plan_period_year: "/año",
    plan_billed_yearly: "{a}€ facturados una vez al año", plan_billed_free: "Gratis para siempre",
    pricing_note_ready: "Pago seguro con Stripe. Cancela cuando quieras.",
    pricing_note_setup: "Los pagos no están disponibles en este momento. Inténtalo más tarde.",
    checkout_unavailable: "No se puede contactar con el servicio de pago. Inténtalo en unos minutos.",
    plan_unknown: "Plan no válido.",
    checkout_opened: "He abierto la página de pago en el navegador.",
    licence_title: "Licencia",
    licence_hint: "¿Has comprado Pro o Studio? Pega aquí la clave que recibiste tras el pago.",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "Activar", licence_manage: "Gestionar suscripción", licence_remove: "Quitar de este equipo",
    licence_state_free: "Plan Free", licence_state_active: "{p} activo",
    licence_state_expired: "Licencia por verificar",
    licence_state_revoked: "Licencia inactiva",
    licence_revoked_note: "Esta suscripción ya no está activa. Si crees que es un error, contacta con soporte.",
    licence_active_on: "Licencia activa ({k})",
    licence_recheck_failed: "No podemos verificar tu licencia ahora. Revisa la conexión: tu plan sigue activo unos días más.",
    licence_enter_key: "Introduce tu clave de licencia.",
    licence_activated: "¡{p} activado!", licence_removed: "Licencia quitada de este equipo.",
    license_missing: "Introduce tu clave de licencia.",
    license_not_found: "Clave no válida. Comprueba que la copiaste entera.",
    license_inactive: "Esta licencia ya no está activa. Si tu suscripción está vigente, contacta con soporte.",
    license_service_unavailable: "No podemos contactar con el servicio de verificación. Revisa la conexión e inténtalo de nuevo.",
    palette_placeholder: "Ir a…", palette_empty: "Sin resultados.",
    strength_labels: "débil,débil,media,buena,excelente",
  },
  fr: {

    // --- Aggiornamento automatico ---
    update_available_title: "La version {version} est disponible",
    update_now: "Mettre à jour",
    update_later: "Me le rappeler plus tard",
    update_skip: "Ignorer cette version",
    update_mandatory: "Mise à jour requise",
    update_downloading: "Téléchargement et vérification…",
    update_restarting: "L'application va se fermer et se rouvrir sur la nouvelle version.",
    update_failed: "La mise à jour n'a pas abouti. Votre version actuelle est intacte.",
    update_managed_by_winget: "Cette copie a été installée avec winget : mettez-la à jour avec « winget upgrade ».",
    update_running_from_source: "Vous exécutez depuis les sources : la mise à jour automatique ne s'applique pas.",
    update_up_to_date: "L'application est à jour.",
    update_check_now: "Rechercher des mises à jour",
    update_channel_beta: "Recevoir les versions d'essai",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "Cette clé a déjà atteint le nombre maximal d'appareils actifs. Désactivez-la sur un autre appareil avant de réessayer ici.",
    license_reactivate_needed: "Ressaisissez la clé sur cet appareil pour la réactiver ici.",

    // --- state OAuth non valido ---
    connect_state_missing: "Aucune connexion en attente. Recommencez en appuyant sur Lier.",
    connect_state_mismatch: "Cette adresse ne correspond pas à la connexion que vous avez lancée. Collez l'adresse complète de la page où vous êtes arrivé ; si elle n'est pas la vôtre, ne l'utilisez pas.",

    // --- Dati in cache ---
    cache_title: "Données en cache",
    cache_hint: "Si un chiffre semble faux même après actualisation, vider le cache local force le tableau de bord à tout recalculer depuis zéro. Vos comptes liés et votre licence restent intacts.",
    cache_clear_btn: "Vider le cache", app_footer_rights: "Tous droits réservés.", app_footer_license: "Licence",
    cache_confirm: "Les statistiques et l'historique enregistrés seront recalculés à la prochaine actualisation. Continuer ?",
    cache_cleared: "Cache vidé.",

    // --- Controllo aggiornamenti ---
    update_available: "Mise à jour disponible",
    update_available_v: "Version {v} disponible",
    update_hint: "Ouvre la page de téléchargement de la version {v}.",
    um_size: "{size}",
    um_release_notes: "Notes de version",
    um_installing: "Installation en cours…",
    um_later: "Me le rappeler plus tard",
    um_skip: "Ignorer cette version",
    um_install: "Installer et redémarrer",
    um_error: "L'installation a échoué. Réessayez ou téléchargez la nouvelle version manuellement.",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "Connecter {p} avec votre propre app",
    sw_step_of: "Étape {n} sur {tot}",
    sw_back: "Retour",
    sw_next: "Suivant",
    sw_finish: "Enregistrer et connecter",
    sw_saving: "Vérification…",
    sw_open: "Ouvrir la page",
    sw_copy: "Copier",
    sw_copied: "Copié ✓",
    sw_copy_failed: "Copie impossible : sélectionnez l'adresse et copiez-la manuellement.",
    sw_saved: "Terminé : connectez-vous maintenant à votre compte.",
    sw_removed: "Votre app a été retirée.",
    sw_offer: "Vous ne voulez pas attendre ? Vous pouvez le connecter tout de suite en enregistrant votre propre app : nous vous guidons pas à pas, environ 10 minutes.",
    sw_offer_btn: "Le connecter maintenant →",
    sw_own_active: "Vous utilisez votre propre app ({id}).",
    sw_own_remove: "Retirer",
    sw_id_label_ig: "ID de l'app Instagram",
    sw_secret_label_ig: "Clé secrète de l'app Instagram",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32 caractères",
    sw_id_label_tt: "Client key",
    sw_secret_label_tt: "Client secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "collez le secret",
    sw_ig1_t: "Ce qu'il vous faut",
    sw_ig1_d: "Vous allez enregistrer votre propre app Instagram : environ 10 minutes, une seule fois.\nIl vous faut un compte Instagram professionnel (Business ou Créateur) et un compte Facebook pour accéder au tableau de bord développeur.\nLes identifiants restent sur cet ordinateur.",
    sw_ig2_t: "Créez l'app",
    sw_ig2_d: "Ouvrez le tableau de bord développeur Meta et cliquez sur «Créer une app».\nPour le cas d'usage choisissez «Autre», puis «Entreprise» comme type.\nLe nom est libre.",
    sw_ig3_t: "Ajoutez Instagram",
    sw_ig3_d: "Dans votre nouvelle app, ouvrez «Ajouter des produits», trouvez «Instagram» et cliquez sur «Configurer».\nChoisissez ensuite «Configuration de l'API avec la connexion Instagram business».",
    sw_ig4_t: "Collez l'adresse de retour",
    sw_ig4_d: "Sur la même page, ouvrez «Paramètres de connexion business».\nCopiez l'adresse ci-dessous et collez-la dans le champ «URI de redirection OAuth», puis enregistrez.\nCette page existe déjà : vous n'avez aucun site à publier.",
    sw_ig5_t: "Copiez les deux identifiants",
    sw_ig5_d: "Toujours sur cette page, dans la section des paramètres de l'app, vous trouverez «ID de l'app Instagram» et «Clé secrète de l'app Instagram».\nCopiez-les ci-dessous : c'est la dernière étape.",
    sw_tt1_t: "Ce qu'il vous faut",
    sw_tt1_d: "Vous allez enregistrer votre propre app TikTok : environ 10 minutes, une seule fois.\nIl vous suffit de votre compte TikTok.\nLes identifiants restent sur cet ordinateur.",
    sw_tt2_t: "Créez l'app",
    sw_tt2_d: "Ouvrez le portail développeur TikTok, connectez-vous avec votre compte et enregistrez une nouvelle app.\nDonnez-lui un nom et confirmez.",
    sw_tt3_t: "Activez la connexion et les permissions",
    sw_tt3_d: "Dans votre app, ouvrez «Add products» et ajoutez «Login Kit».\nParmi les portées, activez user.info.basic, user.info.stats et video.list.\nElles sont en lecture seule : elles servent à lire les abonnés et les statistiques des vidéos.",
    sw_tt4_t: "Créez la sandbox",
    sw_tt4_d: "Ouvrez «Sandbox» et créez-en une.\nÀ l'intérieur, ajoutez votre compte TikTok comme «target user» : c'est ce qui vous permet de lire vos données sans attendre la revue de TikTok.",
    sw_tt5_t: "Collez l'adresse de retour",
    sw_tt5_d: "Dans les paramètres du Login Kit, copiez l'adresse ci-dessous et collez-la parmi les «Redirect URI», puis enregistrez.\nCette page existe déjà : vous n'avez aucun site à publier.",
    sw_tt6_t: "Copiez les deux identifiants",
    sw_tt6_d: "Dans les détails de l'app, vous trouverez «Client key» et «Client secret» de la sandbox.\nCopiez-les ci-dessous : c'est la dernière étape.",
    ownapp_missing: "Remplissez les deux champs.",
    ownapp_unsupported: "Plateforme non prise en charge.",
    ownapp_bad_ig_id: "L'ID de l'app Instagram ne contient que des chiffres. Vérifiez que vous n'avez pas inversé les deux champs.",
    ownapp_bad_ig_secret: "La clé secrète semble incomplète : copiez-la en entier, sans espaces.",
    ownapp_bad_tt_key: "La client key TikTok commence par «aw» ou «sbaw». Vérifiez que vous n'avez pas inversé les deux champs.",
    ownapp_bad_tt_secret: "Le client secret semble incomplet : copiez-le en entier, sans espaces.",
    ownapp_tt_refused: "TikTok ne reconnaît pas ces identifiants. Vérifiez que la client key et le client secret proviennent de la même app.",
    overview_by_platform: "Par plateforme",
    overview_top_content: "Meilleur contenu", platform_status_green: "Connecté et synchronisé", platform_status_yellow: "Nécessite votre attention", platform_status_red: "Erreur", platform_status_grey: "Pas encore configuré",
    tile_followers: "Audience totale", tile_recent_views: "Vues recentes", tile_recent_views_foot: "sur le contenu recent",
    tile_engagement: "Interactions", tile_engagement_foot: "j'aime + commentaires recents",
    tile_health: "Sante", tile_accounts_foot: "comptes actifs",
    tile_analyzed: "Contenus analyses", tile_analyzed_foot: "posts et videos avec donnees",
    tile_avg_per_post: "Moyenne par contenu", tile_avg_per_post_foot: "vues moyennes",
    tile_avg_per_post_foot_n: "vues moyennes sur {n} contenus avec données", tile_best_hour_insufficient: "plus de contenus requis",
    analytics_hours_insufficient: "Données encore insuffisantes pour indiquer un créneau fiable : il faut au moins {n} contenus de plus avec des vues.",
    tile_best_hour: "Meilleure heure", tile_best_hour_foot: "{v} vues moyennes",
    tile_best_platform: "Plateforme top", tile_best_platform_foot: "{v} vues au total",
    analytics_hours_hint: "Vues moyennes par heure de publication (UTC). Les barres pleines sont les heures ou vos contenus marchent le mieux.",
    hours_tooltip: "{h}:00 - {v} vues moyennes sur {n} contenus",
    guided_step1: "Autorisez le compte dans l'onglet qui vient de s'ouvrir.",
    guided_step2: "Copiez ensuite l'adresse de la page ou vous atterrissez et collez-la ci-dessous.",
    guided_placeholder: "Collez ici l'URL complete", guided_cancel: "Annuler", guided_finish: "Terminer",
    guided_paste_needed: "Collez d'abord l'URL de retour.",
    btn_link_account: "Lier", btn_link_account_full: "Lier un compte",
    cm_auto_text: "Le navigateur va s'ouvrir : connectez-vous et autorisez l'acces en lecture seule. Le tableau de bord fait le reste.",
    cm_step1: "Autorisez le compte dans l'onglet qui s'ouvre.", cm_open: "Ouvrir l'autorisation",
    cm_step2: "Collez ici l'adresse de la page ou vous atterrissez.", cm_finish: "Terminer la liaison",
    group_connections: "Comptes lies", nav_connections: "Lier un compte",
    connections_subtitle: "Connectez-vous avec votre compte, le tableau de bord fait le reste. Aucun jeton a copier.",
    connections_privacy: "Les autorisations sont enregistrees uniquement sur votre ordinateur, en local. Elles ne transitent par aucun serveur.",
    connect_now: "Lier {p}", connect_add_another: "Lier un autre compte", connect_soon: "Bientot",
    generic_error: "Une erreur est survenue.", connect_timeout: "Délai dépassé : la liaison n'a pas abouti.",
    connect_already_running: "Une liaison est déjà en cours.",
    connect_platform_unsupported: "Cette plateforme n'est pas encore prise en charge.",
    connect_guided_unavailable: "La liaison guidée n'est pas disponible pour cette plateforme.",
    connect_window_closed: "Liaison annulée : la fenêtre a été fermée avant la fin de la connexion.",
    connect_denied: "Autorisation refusée par la plateforme.",
    connect_code_not_found: "Impossible de trouver le code dans l'URL collée.",
    connect_instagram_rejected: "Instagram a refusé le code d'autorisation. Réessayez de lier le compte.",
    connect_token_exchange_failed: "Échec de l'échange du jeton. Réessayez de lier le compte.",
    connect_tiktok_rejected: "TikTok a refusé le code d'autorisation. Réessayez de lier le compte.",
    connect_tiktok_unexpected: "Réponse inattendue de TikTok. Réessayez plus tard.",
    connect_proxy_http_error: "Le service d'autorisation n'a pas répondu correctement. Réessayez sous peu.",
    connect_proxy_rejected: "Le service d'autorisation a refusé la demande.",
    connect_no_google_app: "Aucune application OAuth Google configurée.",
    connect_coming_soon: "Bientôt disponible",
    cm_coming_soon_text: "La connexion à cette plateforme est presque prête : nous finalisons l'approbation exigée par la plateforme elle-même. Revenez essayer dans quelques jours.",
    proxy_not_configured: "Le service d'autorisation n'est pas configuré dans cette build.",
    unavail_not_configured: "La liaison n'est pas encore disponible dans cette version de l'app.",
    unavail_x_no_read_api: "X n'expose pas les statistiques de lecture sur l'offre gratuite.",
    connect_not_linked: "Non lie", connect_linked_n: "{n} lie(s)", connect_unlink: "Delier",
    connect_reauth_badge: "À relier",
    connect_reauth_hint: "L'accès a expiré ou a été révoqué par la plateforme : reliez le compte pour continuer à lire ses statistiques.",
    connect_locked_hint: "Les identifiants de ce compte ne sont pas lisibles sur cet ordinateur : reliez-le à nouveau pour continuer.",
    connect_desc: "Connectez-vous avec {p} pour voir vos statistiques ici.",
    connect_waiting: "En attente du navigateur...", connect_browser_opened: "Navigateur ouvert : terminez la connexion.",
    connect_success: "{n} lie !", connect_unlinked: "Compte delie.",
    diag_problems: "problemes", diag_warnings: "avertissements", diag_ok: "OK",
    diag_filter_all: "Tout", diag_filter_problems: "A corriger", diag_filter_ok: "OK",
    diag_filter_empty: "Rien a afficher avec ce filtre.", diag_go_connect: "Aller a Lier un compte",
    diag_group_strategy: "Stratégie",
    health_part_technical: "Technique", health_part_engagement: "Engagement",
    health_part_consistency: "Régularité", health_part_coverage: "Couverture",
    health_detail_technical: "{n} problème(s) bloquant la collecte de données", health_detail_engagement: "comparé à {n} référence(s) de plateforme", health_detail_engagement_none: "pas assez de données d'abonnés pour comparer", health_detail_consistency: "dernière publication il y a {days} jour(s)", health_detail_consistency_none: "aucun contenu daté pour l'instant", health_detail_coverage: "{active} sur {total} plateforme(s) avec du contenu récent",
    health_nodata_title: "Aucun compte lie", health_nodata_sub: "Liez un compte pour voir votre score de sante.",
    health_bad_title: "Des choses a corriger", health_bad_sub: "{n} problemes et avertissements demandent votre attention.",
    health_warn_title: "Presque tout va bien", health_warn_sub: "{n} avertissements a surveiller.",
    health_good_title: "Tout va bien", health_good_sub: "Aucun probleme detecte sur vos comptes.",
    group_general: "Général", group_platforms: "Plateformes", group_insights: "Analyses",
    group_account: "Compte", group_settings: "Réglages",
    nav_overview: "Vue d'ensemble", nav_analytics: "Analytique", nav_diagnostics: "Diagnostic",
    nav_themes: "Thèmes", nav_language: "Langue", nav_account: "Votre compte", nav_pricing: "Offres et tarifs",
    btn_refresh: "Actualiser", btn_analyze: "Analyser", btn_export: "Exporter CSV", palette_hint: "Rechercher",
    analytics_subtitle: "Calculées localement à partir des données collectées — meilleures publications et créneaux horaires, sans coût IA.",
    analytics_top_posts: "Meilleurs posts/vidéos (par vues)", analytics_outliers: "Au-dessus/en dessous de votre moyenne", analytics_outliers_hint: "Comparé à votre propre moyenne de {v} vues par contenu — pas à un secteur qui ne connaît pas votre audience.", analytics_outliers_empty: "Pas encore assez de contenu pour une comparaison fiable.", analytics_best_hours: "Meilleurs créneaux horaires (vues moyennes)",
    diagnostics_subtitle: "Calculé instantanément par le code, sans coût — signale les erreurs et se met à jour à chaque Refresh.",
    themes_subtitle: "Choisissez l'apparence du tableau de bord — sauvegardé pour la prochaine fois.",
    language_subtitle: "Choisissez la langue de l'interface — sauvegardé pour la prochaine fois.",
    empty_no_data: "Aucune donnée — appuyez sur Refresh.", waiting_for_data: "En attente de données", empty_configure_yt: "Liez une chaîne YouTube pour voir vos statistiques ici.",
    empty_configure_ig: "Liez un compte Instagram pour voir vos statistiques ici.", empty_configure_tt: "Liez un compte TikTok pour voir vos statistiques ici.",
    empty_not_configured: "Non configuré.",
    label_subscribers_total: "Abonnés totaux", label_channels: "Chaînes", label_followers_total: "Followers totaux",
    label_accounts: "Comptes", label_accounts_configured: "Comptes configurés", label_credentials: "Identifiants",
    val_ok: "OK", val_missing: "Manquants", label_site: "Site", val_online: "En ligne", val_down: "Hors ligne",
    label_subscribers: "Abonnés", label_total_views: "Vues totales", label_videos_published: "Vidéos publiées",
    label_recent_views: "Vues (10 dernières vidéos)", label_last_publish: "Dernière publication", label_never_published: "Jamais publié",
    label_followers: "Abonnés", label_views_recent: "Vues (posts récents)", label_likes: "J'aime", label_comments: "Commentaires",
    label_views: "Vues", label_likes_comments_shares: "J'aime / Commentaires / Partages",
    val_online_latency: "En ligne ({ms}ms)", val_down_error: "Hors ligne / erreur", label_npm_vulns: "Vulnérabilités npm",
    label_eslint: "ESLint", val_not_configured: "non configuré", val_errors_warnings: "{e} erreurs, {w} avertissements",
    insight_loading: "Analyse en cours…", insight_error: "Erreur pendant l'analyse : ",
    ins_no_items: "{name} : aucun contenu récent à analyser.",
    locked_title: "Fonction de l'offre Pro",
    locked_cta: "Voir les offres",
    locked_best_hours: "Les créneaux recommandés sont inclus dans l'offre Pro.",
    locked_history: "L'historique et les graphiques de tendance sont inclus dans l'offre Pro.",
    plan_feature_locked: "Cette fonction est incluse dans l'offre Pro.",
    plan_account_limit: "Votre offre inclut {n} comptes liés. Passez à une offre supérieure pour en ajouter.",
    plan_account_limit_one: "Votre offre n'inclut qu'1 compte lié. Passez à une offre supérieure pour en ajouter.",
    plan_free_tagline: "Pour débuter et comprendre vos chiffres.",
    plan_free_accounts: "1 compte lié",
    plan_pro_tagline: "Pour ceux qui publient chaque jour et veulent grandir.",
    plan_pro_accounts: "3 comptes liés",
    plan_studio_tagline: "Pour les agences et le multi-marque.",
    plan_studio_accounts: "10 comptes liés",
    plan_feat_all_socials: "Statistiques de tous les réseaux pris en charge",
    plan_feat_manual_refresh: "Actualisation manuelle à la demande",
    plan_feat_analytics: "Analyses : meilleurs contenus et créneaux",
    plan_feat_diagnostics: "Diagnostic automatique des erreurs",
    plan_feat_insights: "Observations automatiques sur vos contenus",
    plan_feat_history: "Historique complet avec graphiques de tendance",
    plan_feat_reports: "Rapports automatiques",
    plan_feat_all_free: "Tout ce qu'il y a dans Free",
    plan_feat_compare: "Comparaison de périodes et alertes de baisse",
    plan_feat_hours: "Suggestions d'horaires de publication",
    plan_feat_csv: "Export des données en CSV",
    plan_feat_all_pro: "Tout ce qu'il y a dans Pro",
    plan_feat_workspaces: "Espaces de travail séparés par client",
    plan_feat_whitelabel: "Rapports PDF en marque blanche automatisés",
    plan_feat_multiuser: "Accès multi-utilisateur pour l'équipe",
    plan_feat_priority: "Support prioritaire",
    aria_toggle_password: "Afficher le mot de passe",
    aria_close: "Fermer",
    ins_some_zero: "{name} : {n} des {tot} derniers contenus sont encore à zéro vue.",
    ins_some_zero_one: "{name} : 1 des {tot} derniers contenus est encore à zéro vue.",
    ins_all_zero_one: "{name} : l'unique contenu récent n'a encore aucune vue.",
    ins_flop_one: "{name} : 1 contenu sous 40% de la moyenne : « {title} » avec {v} vues.",
    ins_cadence_daily: "{name} : vous publiez environ {n} fois par jour.",
    ins_cadence_broken_daily: "{name} : vous publiez d'habitude plusieurs fois par jour, mais le dernier contenu date de {d} jours.",
    ins_all_zero: "{name} : aucun des {n} derniers contenus n'a encore de vues.",
    ins_star: "{name} : « {title} » a fait {v} vues, {x}x la moyenne du compte. Regardez ce qui le distingue et reproduisez-le.",
    ins_flop: "{name} : {n} contenus sous 40% de la moyenne ; le plus faible est « {title} » avec {v} vues.",
    ins_engagement: "{name} : {rate}% d'engagement sur les contenus récents ({i} interactions pour {v} vues).",
    ins_cadence_broken: "{name} : vous publiez d'habitude tous les {gap} jours, mais le dernier contenu date de {d} jours.",
    ins_cadence: "{name} : vous publiez en moyenne tous les {gap} jours.",
    ins_best_account: "{best} est le compte le plus performant : {bv} vues contre {wv} pour {worst}.",
    ins_x_free_plan: "X n'expose pas les statistiques de lecture sur l'offre gratuite : il n'y a rien à analyser.",
    ins_no_data: "Rien à analyser pour l'instant : liez un compte et appuyez sur Actualiser.",
    ins_nothing_notable: "Aucun problème détecté dans vos contenus récents.",
    analytics_empty: "Pas encore assez de posts/vidéos avec des données pour une analyse — appuyez sur Refresh.",
    analytics_engagement: "Engagement",
    analytics_engagement_hint: "Part des personnes atteintes qui ont aimé, commenté, partagé ou enregistré. Comparé à la moyenne des comptes de votre taille.",
    analytics_heatmap: "Jour et heure",
    analytics_heatmap_hint: "Où votre contenu a vraiment fonctionné. Plus c'est foncé, plus les publications de ce créneau ont de vues en moyenne.",
    eng_above: "Au-dessus de la moyenne ({e}%)", eng_below: "En dessous de la moyenne ({e}%)",
    eng_inline: "Dans la moyenne ({e}%)",
    eng_no_benchmark: "Nombre d'abonnés indisponible pour la comparaison",
    eng_saves: "Enregistrements", eng_shares: "Partages",
    eng_saves_hint: "Part des personnes atteintes qui ont enregistré la publication : le signal le plus fort qu'elle valait la peine d'être gardée.",
    eng_shares_hint: "Part des personnes atteintes qui l'ont transmise : c'est ainsi qu'un contenu sort de votre propre audience.",
    heatmap_not_enough: "Il faut plus de contenus datés pour dessiner la carte.",
    heatmap_cell: "{d} à {h}:00 — {v} vues en moyenne sur {n} publications",
    weekday_short: "Lun,Mar,Mer,Jeu,Ven,Sam,Dim",
    analytics_untitled: "(sans titre)", analytics_avg_views: "vues moyennes", analytics_bucket_count: "posts analysés dans ce créneau",
    analytics_last_refresh: "Dernier chargement des données : {t} ({d})", analytics_last_refresh_never: "Dernier chargement des données : jamais — appuyez sur Refresh.",
    footer_last_refresh: "Dernière mise à jour : {d}", footer_never: "Jamais mis à jour", footer_error: "Erreur pendant l'actualisation - réessayez.",
    time_never: "jamais", time_seconds_ago: "il y a quelques secondes", time_min_ago: "il y a {n} min", time_hours_ago: "il y a {n} heures", time_days_ago: "il y a {n} jours",
    diag_next_step_label: "Prochaine étape :",
    diag_unreachable_title: "{name} : ne répond pas",
    diagerr_scope_denied_cat: "Autorisation non accordée", diagerr_scope_denied_step: "L'autorisation de lecture des statistiques doit être approuvée sur le portail développeurs de la plateforme : impossible à régler depuis l'app.",
    diagerr_expired_cat: "Accès expiré", diagerr_expired_step: "Reliez ce compte : l'autorisation a expiré ou a été révoquée.",
    diagerr_scope_mismatch_cat: "Autorisations désalignées", diagerr_scope_mismatch_step: "Les autorisations demandées ne correspondent pas à celles accordées à l'origine : reliez le compte pour les réaligner.",
    diagerr_permission_cat: "Autorisation manquante", diagerr_permission_step: "Le compte n'a pas accordé l'autorisation requise : reliez-le en acceptant toutes les demandes.",
    diagerr_rate_cat: "Trop de requêtes", diagerr_rate_step: "Attendez quelques minutes avant la prochaine actualisation : la limite de la plateforme est atteinte.",
    diagerr_auth_cat: "Identifiants invalides", diagerr_auth_step: "Reliez le compte pour régénérer l'accès.",
    diagerr_notfound_cat: "Compte introuvable", diagerr_notfound_step: "Le compte lié n'est plus joignable : il a peut-être été supprimé ou renommé.",
    diagerr_network_cat: "Problème réseau", diagerr_network_step: "Réessayez l'actualisation : cela ressemble à un souci de connexion temporaire.",
    diagerr_unknown_cat: "Erreur non classée", diagerr_unknown_step: "Réessayez l'actualisation ; si cela persiste, reliez le compte.",
    diag_no_account_cat: "À lier", diag_no_account_title: "Aucun compte {p}", diag_no_account_text: "Vous n'avez encore lié aucun compte {p}.", diag_no_account_step: "Appuyez sur Lier et connectez-vous : quelques secondes suffisent.",
    diag_no_data_cat: "Données manquantes", diag_no_data_title: "{p} sans données", diag_no_data_text: "Aucune donnée chargée pour l'instant.", diag_no_data_step: "Appuyez sur Actualiser pour charger les données.",
    diag_all_ok_title_one: "{p} : 1 compte en règle", diag_all_ok_cat_one: "Tout va bien", diag_all_ok_text_one: "Le compte répond et publie régulièrement.", diag_all_ok_step_one: "Aucune action requise.",
    diag_all_ok_cat: "Tout va bien", diag_all_ok_title: "{p} : {n} comptes en règle", diag_all_ok_text: "Tous les comptes répondent et publient régulièrement.", diag_all_ok_step: "Aucune action requise.",
    diag_stale_bad_cat: "Contenu à l'arrêt", diag_stale_bad_title: "{name} : à l'arrêt depuis {d} jours", diag_stale_bad_text: "Le dernier contenu sur {p} date de {d} jours.", diag_stale_bad_step: "Publiez quelque chose : les plateformes récompensent la régularité et la portée chute vite sur les profils inactifs.",
    diag_stale_warn_cat: "Rythme en baisse", diag_stale_warn_title: "{name} : dernier post il y a {d} jours", diag_stale_warn_text: "Rien de nouveau sur {p} depuis {d} jours.", diag_stale_warn_step: "Revenez à votre rythme habituel avant que la portée ne commence à baisser.",
    diag_zero_views_cat: "Aucune vue", diag_zero_views_title: "{name} : 0 vue sur les dernières vidéos", diag_zero_views_text: "Les dernières vidéos publiées n'ont encore aucune vue.", diag_zero_views_step: "Si elles viennent de sortir c'est normal ; si elles ont quelques jours, revoyez titre, miniature et premières secondes.",
    diag_not_configured_cat: "À configurer", diag_not_configured_title: "{name} : non configuré", diag_not_configured_text: "Le compte est listé mais n'a aucun identifiant associé.", diag_not_configured_step: "Liez le compte, ou retirez-le de la liste si vous n'en avez pas besoin.",
    diag_x_not_linked_cat: "Non lié", diag_x_not_linked_title: "X non lié", diag_x_not_linked_text: "Aucun identifiant X configuré.", diag_x_not_linked_step: "X n'expose pas les statistiques de lecture sur l'offre gratuite : cette section reste informative pour le moment.",
    diag_x_linked_cat: "Lié", diag_x_linked_title: "X lié", diag_x_linked_text: "Identifiants présents. Les statistiques de lecture ne sont pas disponibles sur l'offre gratuite de X.", diag_x_linked_step: "Aucune action requise.",
    yt_total_views_lag_note: "YouTube peut mettre des heures/jours à actualiser le total historique sur les petites/nouvelles chaînes — ce n'est pas un bug du tableau de bord.",
    overview_sub: "{n} comptes suivis sur {p} plateformes.", overview_sub_empty: "Appuyez sur Refresh pour charger vos données.",
    trend_since: "depuis la précédente", trend_no_history: "Encore une actualisation et la tendance apparaît.",
    account_guest: "Invité", account_signin_hint: "Connectez-vous pour sauvegarder",
    auth_tab_login: "Se connecter", auth_tab_register: "S'inscrire",
    auth_title_login: "Content de vous revoir", auth_title_register: "Créez votre compte",
    auth_sub_login: "Connectez-vous pour synchroniser offres et préférences.", auth_sub_register: "Trente secondes. Sans carte bancaire.",
    auth_name: "Votre nom", auth_first_name: "Prénom", auth_last_name: "Nom", auth_birth_date: "Date de naissance",
    auth_first_name_ph: "Camille", auth_last_name_ph: "Martin", auth_email_ph: "vous@exemple.com",
    auth_email: "Email", auth_password: "Mot de passe", auth_password_confirm: "Confirmez le mot de passe",
    auth_switch_to_register: "Pas encore de compte ?", auth_switch_to_login: "Vous avez déjà un compte ?",
    auth_aside_badge: "Tout au même endroit",
    auth_aside_title: "Arrêtez d'ouvrir six applis pour savoir où vous en êtes.",
    auth_aside_1: "Tous vos comptes d'un seul coup d'œil",
    auth_aside_2: "Vous prévient quand un chiffre baisse, pas seulement sa valeur",
    auth_aside_3: "Trouve les heures où vos posts marchent vraiment",
    auth_aside_4: "Vos jetons restent sur votre machine, pas sur un serveur",
    auth_aside_foot: "Aucune carte requise pour commencer.",
    auth_logout: "Déconnexion", account_upgrade: "Passer à Pro", account_upgrade_studio: "Passer à Studio", account_since: "Compte créé le {d}",
    err_email_invalid: "Saisissez une adresse email valide.", err_password_short: "8 caractères minimum.",
    err_required: "Champ obligatoire.", err_birth_date_future: "La date ne peut pas être dans le futur.",
    err_birth_invalid: "Saisissez une date de naissance valide.", err_birth_too_young: "Vous devez avoir au moins 13 ans pour vous inscrire.",
    err_first_name_required: "Saisissez votre prénom.", err_last_name_required: "Saisissez votre nom.",
    err_email_taken: "Un compte existe déjà avec cet email.", err_bad_credentials: "Email ou mot de passe incorrect.",
    err_session_expired: "Session invalide ou expirée.", err_login_required_for_plan: "Connectez-vous avant d'acheter une offre.",
    err_age_min: "Vous devez avoir au moins {n} ans.", err_password_mismatch: "Les deux mots de passe ne correspondent pas.",
    auth_forgot_password: "Mot de passe oublié ?", reset_title: "Réinitialiser votre mot de passe", reset_step1_sub: "Indiquez votre email, nous vous enverrons un code à 6 chiffres.", reset_step2_sub: "Code envoyé à {email}. Vérifiez aussi vos spams.", reset_send_code: "Envoyer le code", reset_code_label: "Code à 6 chiffres", reset_new_password: "Nouveau mot de passe", reset_confirm: "Réinitialiser le mot de passe", reset_resend: "Renvoyer le code", reset_err_code_format: "Le code doit comporter 6 chiffres.", reset_success: "Mot de passe réinitialisé. Vous êtes connecté.", err_reset_invalid: "Code invalide.", err_reset_expired: "Ce code a expiré, demandez-en un nouveau.", err_reset_too_many: "Trop de tentatives avec ce code. Demandez-en un nouveau.",
    toast_welcome: "Bienvenue, {n} !", toast_logged_in: "Content de vous revoir, {n} !", toast_logged_out: "Vous êtes déconnecté.",
    toast_refresh_done: "Données actualisées.", toast_export_done: "CSV exporté.",
    toast_login_required: "Connectez-vous avant de choisir une offre.",
    pricing_title: "Choisissez ce que vous voulez voir", pricing_sub: "Commencez gratuitement. Passez à Pro quand les chiffres comptent vraiment.",
    pricing_monthly: "Mensuel", pricing_yearly: "Annuel", pricing_save: "2 mois offerts",
    plan_popular: "Le plus choisi", plan_free_cta: "Commencer gratuitement", plan_cta: "Choisir {p}",
    plan_current: "Offre actuelle", plan_period_month: "/mois", plan_period_year: "/an",
    plan_billed_yearly: "{a}€ facturés une fois par an", plan_billed_free: "Gratuit pour toujours",
    pricing_note_ready: "Paiement sécurisé via Stripe. Annulable à tout moment.",
    pricing_note_setup: "Les paiements sont indisponibles pour le moment. Réessayez plus tard.",
    checkout_unavailable: "Le service de paiement est injoignable. Réessayez sous peu.",
    plan_unknown: "Offre non valide.",
    checkout_opened: "J'ai ouvert la page de paiement dans le navigateur.",
    licence_title: "Licence",
    licence_hint: "Vous avez acheté Pro ou Studio ? Collez ici la clé reçue après le paiement.",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "Activer", licence_manage: "Gérer l'abonnement", licence_remove: "Retirer de cet ordinateur",
    licence_state_free: "Offre Free", licence_state_active: "{p} actif",
    licence_state_expired: "Licence à vérifier",
    licence_state_revoked: "Licence inactive",
    licence_revoked_note: "Cet abonnement n'est plus actif. Si vous pensez qu'il s'agit d'une erreur, contactez le support.",
    licence_active_on: "Licence active ({k})",
    licence_recheck_failed: "Impossible de vérifier votre licence pour l'instant. Vérifiez la connexion : votre offre reste active encore quelques jours.",
    licence_enter_key: "Saisissez votre clé de licence.",
    licence_activated: "{p} activé !", licence_removed: "Licence retirée de cet ordinateur.",
    license_missing: "Saisissez votre clé de licence.",
    license_not_found: "Clé non valide. Vérifiez que vous l'avez copiée en entier.",
    license_inactive: "Cette licence n'est plus active. Si votre abonnement est en cours, contactez le support.",
    license_service_unavailable: "Impossible de joindre le service de vérification. Vérifiez la connexion et réessayez.",
    palette_placeholder: "Aller à…", palette_empty: "Aucun résultat.",
    strength_labels: "faible,faible,moyen,bon,excellent",
  },
  de: {

    // --- Aggiornamento automatico ---
    update_available_title: "Version {version} ist verfügbar",
    update_now: "Jetzt aktualisieren",
    update_later: "Später erinnern",
    update_skip: "Diese Version überspringen",
    update_mandatory: "Erforderliches Update",
    update_downloading: "Wird heruntergeladen und geprüft…",
    update_restarting: "Die App schließt sich und startet in der neuen Version neu.",
    update_failed: "Das Update ist nicht durchgelaufen. Deine aktuelle Version ist unverändert.",
    update_managed_by_winget: "Diese Kopie wurde mit winget installiert: aktualisiere sie mit \"winget upgrade\".",
    update_running_from_source: "Du führst die App aus dem Quellcode aus: automatische Updates gelten nicht.",
    update_up_to_date: "Die App ist aktuell.",
    update_check_now: "Nach Updates suchen",
    update_channel_beta: "Testversionen erhalten",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "Dieser Schlüssel hat die maximale Anzahl aktiver Geräte bereits erreicht. Deaktiviere ihn auf einem anderen Gerät, bevor du es hier erneut versuchst.",
    license_reactivate_needed: "Gib den Schlüssel auf diesem Gerät erneut ein, um ihn hier zu reaktivieren.",

    // --- state OAuth non valido ---
    connect_state_missing: "Es wartet keine Verknüpfung auf den Abschluss. Starte neu über Verknüpfen.",
    connect_state_mismatch: "Diese Adresse gehört nicht zu der Verknüpfung, die du gestartet hast. Füge die vollständige Adresse der Seite ein, auf der du gelandet bist — und wenn sie nicht deine ist, verwende sie nicht.",

    // --- Dati in cache ---
    cache_title: "Zwischengespeicherte Daten",
    cache_hint: "Wenn eine Zahl auch nach dem Aktualisieren falsch erscheint, erzwingt das Leeren des lokalen Caches eine komplette Neuberechnung. Deine verknüpften Konten und deine Lizenz bleiben unberührt.",
    cache_clear_btn: "Cache leeren", app_footer_rights: "Alle Rechte vorbehalten.", app_footer_license: "Lizenz",
    cache_confirm: "Gespeicherte Statistiken und der Verlauf werden bei der nächsten Aktualisierung neu berechnet. Fortfahren?",
    cache_cleared: "Cache geleert.",

    // --- Controllo aggiornamenti ---
    update_available: "Update verfügbar",
    update_available_v: "Version {v} verfügbar",
    update_hint: "Öffnet die Download-Seite für Version {v}.",
    um_size: "{size}",
    um_release_notes: "Versionshinweise",
    um_installing: "Wird installiert…",
    um_later: "Später erinnern",
    um_skip: "Diese Version überspringen",
    um_install: "Installieren und neu starten",
    um_error: "Installation fehlgeschlagen. Versuche es erneut oder lade die neue Version manuell herunter.",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "{p} mit deiner eigenen App verbinden",
    sw_step_of: "Schritt {n} von {tot}",
    sw_back: "Zurück",
    sw_next: "Weiter",
    sw_finish: "Speichern und verbinden",
    sw_saving: "Wird geprüft…",
    sw_open: "Seite öffnen",
    sw_copy: "Kopieren",
    sw_copied: "Kopiert ✓",
    sw_copy_failed: "Kopieren nicht möglich: Markiere die Adresse und kopiere sie von Hand.",
    sw_saved: "Fertig — melde dich jetzt bei deinem Konto an.",
    sw_removed: "Deine eigene App wurde entfernt.",
    sw_offer: "Du willst nicht warten? Du kannst es sofort verbinden, indem du eine eigene App registrierst — wir führen dich Schritt für Schritt, etwa 10 Minuten.",
    sw_offer_btn: "Jetzt verbinden →",
    sw_own_active: "Du verwendest deine eigene App ({id}).",
    sw_own_remove: "Entfernen",
    sw_id_label_ig: "Instagram-App-ID",
    sw_secret_label_ig: "Instagram-App-Geheimnis",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32 Zeichen",
    sw_id_label_tt: "Client Key",
    sw_secret_label_tt: "Client Secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "Geheimnis einfügen",
    sw_ig1_t: "Was du brauchst",
    sw_ig1_d: "Du registrierst deine eigene Instagram-App: etwa 10 Minuten, nur einmal.\nDu brauchst ein professionelles Instagram-Konto (Business oder Creator) und ein Facebook-Konto für das Entwickler-Dashboard.\nDie Zugangsdaten bleiben auf diesem Computer.",
    sw_ig2_t: "App erstellen",
    sw_ig2_d: "Öffne das Meta-Entwickler-Dashboard und klicke auf «App erstellen».\nWähle beim Anwendungsfall «Sonstiges» und als Typ «Business».\nDer Name ist frei wählbar.",
    sw_ig3_t: "Instagram hinzufügen",
    sw_ig3_d: "Öffne in deiner neuen App «Produkte hinzufügen», suche «Instagram» und klicke auf «Einrichten».\nWähle dann «API-Einrichtung mit Instagram-Business-Login».",
    sw_ig4_t: "Weiterleitungsadresse einfügen",
    sw_ig4_d: "Öffne auf derselben Seite «Business-Login-Einstellungen».\nKopiere die Adresse unten und füge sie in das Feld «OAuth-Weiterleitungs-URI» ein, dann speichern.\nDiese Seite existiert bereits — du musst keine Website veröffentlichen.",
    sw_ig5_t: "Die beiden Zugangsdaten kopieren",
    sw_ig5_d: "Auf derselben Seite findest du im Bereich der App-Einstellungen «Instagram-App-ID» und «Instagram-App-Geheimnis».\nKopiere sie unten — das ist der letzte Schritt.",
    sw_tt1_t: "Was du brauchst",
    sw_tt1_d: "Du registrierst deine eigene TikTok-App: etwa 10 Minuten, nur einmal.\nDu brauchst nur dein TikTok-Konto.\nDie Zugangsdaten bleiben auf diesem Computer.",
    sw_tt2_t: "App erstellen",
    sw_tt2_d: "Öffne das TikTok-Entwicklerportal, melde dich mit deinem Konto an und registriere eine neue App.\nGib ihr einen Namen und bestätige.",
    sw_tt3_t: "Login und Berechtigungen aktivieren",
    sw_tt3_d: "Öffne in deiner App «Add products» und füge «Login Kit» hinzu.\nAktiviere bei den Scopes user.info.basic, user.info.stats und video.list.\nSie sind nur lesend: Sie dienen dazu, Follower und Videostatistiken zu lesen.",
    sw_tt4_t: "Sandbox erstellen",
    sw_tt4_d: "Öffne «Sandbox» und erstelle eine.\nFüge darin dein TikTok-Konto als «target user» hinzu — das erlaubt dir, deine eigenen Daten ohne TikToks Prüfung zu lesen.",
    sw_tt5_t: "Weiterleitungsadresse einfügen",
    sw_tt5_d: "Kopiere in den Login-Kit-Einstellungen die Adresse unten und füge sie bei «Redirect URI» ein, dann speichern.\nDiese Seite existiert bereits — du musst keine Website veröffentlichen.",
    sw_tt6_t: "Die beiden Zugangsdaten kopieren",
    sw_tt6_d: "In den App-Details findest du «Client key» und «Client secret» der Sandbox.\nKopiere sie unten — das ist der letzte Schritt.",
    ownapp_missing: "Fülle beide Felder aus.",
    ownapp_unsupported: "Plattform nicht unterstützt.",
    ownapp_bad_ig_id: "Die Instagram-App-ID besteht nur aus Ziffern. Prüfe, ob du die beiden Felder vertauscht hast.",
    ownapp_bad_ig_secret: "Das App-Geheimnis wirkt unvollständig: Kopiere es vollständig, ohne Leerzeichen.",
    ownapp_bad_tt_key: "Der TikTok-Client-Key beginnt mit «aw» oder «sbaw». Prüfe, ob du die beiden Felder vertauscht hast.",
    ownapp_bad_tt_secret: "Das Client Secret wirkt unvollständig: Kopiere es vollständig, ohne Leerzeichen.",
    ownapp_tt_refused: "TikTok erkennt diese Zugangsdaten nicht. Prüfe, ob Client Key und Client Secret aus derselben App stammen.",
    overview_by_platform: "Nach Plattform",
    overview_top_content: "Bester Beitrag", platform_status_green: "Verbunden und synchron", platform_status_yellow: "Braucht Aufmerksamkeit", platform_status_red: "Fehler", platform_status_grey: "Noch nicht eingerichtet",
    tile_followers: "Gesamtreichweite", tile_recent_views: "Aktuelle Views", tile_recent_views_foot: "auf den letzten Inhalten",
    tile_engagement: "Interaktionen", tile_engagement_foot: "Likes + Kommentare",
    tile_health: "Zustand", tile_accounts_foot: "aktive Konten",
    tile_analyzed: "Analysierte Inhalte", tile_analyzed_foot: "Beitraege und Videos mit Daten",
    tile_avg_per_post: "Schnitt pro Inhalt", tile_avg_per_post_foot: "durchschnittliche Views",
    tile_avg_per_post_foot_n: "durchschnittliche Views über {n} Inhalte mit Daten", tile_best_hour_insufficient: "mehr Inhalte nötig",
    analytics_hours_insufficient: "Noch zu wenig Daten für ein verlässliches Zeitfenster: Es fehlen mindestens {n} weitere Inhalte mit Aufrufen.",
    tile_best_hour: "Beste Stunde", tile_best_hour_foot: "{v} Views im Schnitt",
    tile_best_platform: "Top-Plattform", tile_best_platform_foot: "{v} Views gesamt",
    analytics_hours_hint: "Durchschnittliche Views nach Veroeffentlichungsstunde (UTC). Die gefuellten Balken sind die Stunden, in denen deine Inhalte am besten laufen.",
    hours_tooltip: "{h}:00 - {v} Views im Schnitt bei {n} Inhalten",
    guided_step1: "Autorisiere das Konto im gerade geoeffneten Tab.",
    guided_step2: "Kopiere dann die Adresse der Seite, auf der du landest, und fuege sie unten ein.",
    guided_placeholder: "Vollstaendige URL hier einfuegen", guided_cancel: "Abbrechen", guided_finish: "Fertigstellen",
    guided_paste_needed: "Fuege zuerst die Rueckgabe-URL ein.",
    btn_link_account: "Verkn\u00fcpfen", btn_link_account_full: "Konto verkn\u00fcpfen",
    cm_auto_text: "Der Browser \u00f6ffnet sich: melde dich an und erlaube den Lesezugriff. Den Rest \u00fcbernimmt das Dashboard.",
    cm_step1: "Autorisiere das Konto im Tab, der sich \u00f6ffnet.", cm_open: "Autorisierung \u00f6ffnen",
    cm_step2: "F\u00fcge hier die Adresse der Seite ein, auf der du landest.", cm_finish: "Verkn\u00fcpfung abschlie\u00dfen",
    group_connections: "Verkn\u00fcpfte Konten", nav_connections: "Konto verkn\u00fcpfen",
    connections_subtitle: "Melde dich mit deinem Konto an, den Rest macht das Dashboard. Keine Tokens zum Kopieren.",
    connections_privacy: "Die Autorisierungen werden nur lokal auf deinem Rechner gespeichert. Sie laufen \u00fcber keinen Server.",
    connect_now: "{p} verkn\u00fcpfen", connect_add_another: "Weiteres Konto verkn\u00fcpfen", connect_soon: "Demn\u00e4chst",
    generic_error: "Es ist ein Fehler aufgetreten.", connect_timeout: "Zeit\u00fcberschreitung: Die Verkn\u00fcpfung wurde nicht abgeschlossen.",
    connect_already_running: "Es l\u00e4uft bereits eine Verkn\u00fcpfung.",
    connect_platform_unsupported: "Diese Plattform wird noch nicht unterst\u00fctzt.",
    connect_guided_unavailable: "Die gef\u00fchrte Verkn\u00fcpfung ist f\u00fcr diese Plattform nicht verf\u00fcgbar.",
    connect_window_closed: "Verkn\u00fcpfung abgebrochen: Das Fenster wurde vor Abschluss der Anmeldung geschlossen.",
    connect_denied: "Autorisierung von der Plattform verweigert.",
    connect_code_not_found: "Der Code wurde in der eingef\u00fcgten URL nicht gefunden.",
    connect_instagram_rejected: "Instagram hat den Autorisierungscode abgelehnt. Verkn\u00fcpfung erneut versuchen.",
    connect_token_exchange_failed: "Token-Austausch fehlgeschlagen. Verkn\u00fcpfung erneut versuchen.",
    connect_tiktok_rejected: "TikTok hat den Autorisierungscode abgelehnt. Verkn\u00fcpfung erneut versuchen.",
    connect_tiktok_unexpected: "Unerwartete Antwort von TikTok. Sp\u00e4ter erneut versuchen.",
    connect_proxy_http_error: "Der Autorisierungsdienst hat nicht korrekt geantwortet. In K\u00fcrze erneut versuchen.",
    connect_proxy_rejected: "Der Autorisierungsdienst hat die Anfrage abgelehnt.",
    connect_no_google_app: "Keine Google-OAuth-App konfiguriert.",
    connect_coming_soon: "Demnächst verfügbar",
    cm_coming_soon_text: "Die Verknüpfung mit dieser Plattform ist fast fertig: Wir schließen gerade die von der Plattform selbst geforderte Freigabe ab. Versuch es in ein paar Tagen erneut.",
    proxy_not_configured: "Der Autorisierungsdienst ist in dieser Build nicht konfiguriert.",
    unavail_not_configured: "Das Verkn\u00fcpfen ist in dieser App-Version noch nicht verf\u00fcgbar.",
    unavail_x_no_read_api: "X stellt im kostenlosen Tarif keine Lesestatistiken bereit.",
    connect_not_linked: "Nicht verkn\u00fcpft", connect_linked_n: "{n} verkn\u00fcpft", connect_unlink: "Trennen",
    connect_reauth_badge: "Neu verkn\u00fcpfen",
    connect_reauth_hint: "Der Zugriff ist abgelaufen oder wurde von der Plattform widerrufen: Verkn\u00fcpfe das Konto erneut, um die Statistiken weiter zu lesen.",
    connect_locked_hint: "Die Zugangsdaten dieses Kontos sind auf diesem Computer nicht lesbar: Verkn\u00fcpfe es erneut, um fortzufahren.",
    connect_desc: "Melde dich mit {p} an, um deine Statistiken hier zu sehen.",
    connect_waiting: "Warte auf den Browser...", connect_browser_opened: "Browser ge\u00f6ffnet: schlie\u00dfe die Anmeldung ab.",
    connect_success: "{n} verkn\u00fcpft!", connect_unlinked: "Konto getrennt.",
    diag_problems: "Probleme", diag_warnings: "Hinweise", diag_ok: "in Ordnung",
    diag_filter_all: "Alles", diag_filter_problems: "Zu beheben", diag_filter_ok: "In Ordnung",
    diag_filter_empty: "Mit diesem Filter gibt es nichts anzuzeigen.", diag_go_connect: "Zu Konto verkn\u00fcpfen",
    diag_group_strategy: "Strategie",
    health_part_technical: "Technik", health_part_engagement: "Engagement",
    health_part_consistency: "Best\u00e4ndigkeit", health_part_coverage: "Abdeckung",
    health_detail_technical: "{n} Problem(e) blockieren die Datenerfassung", health_detail_engagement: "verglichen mit {n} Plattform-Benchmark(s)", health_detail_engagement_none: "zu wenig Follower-Daten f\u00fcr einen Vergleich", health_detail_consistency: "letzter Beitrag vor {days} Tag(en)", health_detail_consistency_none: "noch keine datierten Inhalte", health_detail_coverage: "{active} von {total} Plattform(en) mit aktuellem Inhalt",
    health_nodata_title: "Kein Konto verknüpft", health_nodata_sub: "Verknüpfe ein Konto, um deinen Gesundheitswert zu sehen.",
    health_bad_title: "Es gibt etwas zu beheben", health_bad_sub: "{n} Probleme und Hinweise brauchen deine Aufmerksamkeit.",
    health_warn_title: "Fast alles in Ordnung", health_warn_sub: "{n} Hinweise im Auge behalten.",
    health_good_title: "Alles in Ordnung", health_good_sub: "Keine Probleme bei deinen Konten gefunden.",
    group_general: "Allgemein", group_platforms: "Plattformen", group_insights: "Insights",
    group_account: "Konto", group_settings: "Einstellungen",
    nav_overview: "Übersicht", nav_analytics: "Analysen", nav_diagnostics: "Diagnose",
    nav_themes: "Designs", nav_language: "Sprache", nav_account: "Dein Konto", nav_pricing: "Tarife & Preise",
    btn_refresh: "Aktualisieren", btn_analyze: "Analysieren", btn_export: "CSV exportieren", palette_hint: "Suchen",
    analytics_subtitle: "Lokal aus den gesammelten Daten berechnet — beste Beiträge und Uhrzeiten, ohne KI-Kosten.",
    analytics_top_posts: "Top-Beiträge/Videos (nach Views)", analytics_outliers: "Über/unter deinem Durchschnitt", analytics_outliers_hint: "Verglichen mit deinem eigenen Durchschnitt von {v} Views pro Beitrag — nicht mit einer Branche, die dein Publikum nicht kennt.", analytics_outliers_empty: "Noch nicht genug Inhalte für einen zuverlässigen Vergleich.", analytics_best_hours: "Beste Uhrzeiten (Ø Views)",
    diagnostics_subtitle: "Sofort und kostenlos vom Code berechnet — zeigt Fehler an und aktualisiert sich bei jedem Refresh.",
    themes_subtitle: "Wähle das Erscheinungsbild des Dashboards — bleibt auch beim nächsten Öffnen gespeichert.",
    language_subtitle: "Wähle die Sprache der Oberfläche — bleibt auch beim nächsten Öffnen gespeichert.",
    empty_no_data: "Keine Daten — Refresh drücken.", waiting_for_data: "Warten auf Daten", empty_configure_yt: "Verknüpfe einen YouTube-Kanal, um hier deine Statistiken zu sehen.",
    empty_configure_ig: "Verknüpfe ein Instagram-Konto, um hier deine Statistiken zu sehen.", empty_configure_tt: "Verknüpfe ein TikTok-Konto, um hier deine Statistiken zu sehen.",
    empty_not_configured: "Nicht konfiguriert.",
    label_subscribers_total: "Abonnenten gesamt", label_channels: "Kanäle", label_followers_total: "Follower gesamt",
    label_accounts: "Konten", label_accounts_configured: "Konfigurierte Konten", label_credentials: "Zugangsdaten",
    val_ok: "OK", val_missing: "Fehlend", label_site: "Website", val_online: "Online", val_down: "Offline",
    label_subscribers: "Abonnenten", label_total_views: "Views gesamt", label_videos_published: "Veröffentlichte Videos",
    label_recent_views: "Views (letzte 10 Videos)", label_last_publish: "Letzte Veröffentlichung", label_never_published: "Nie veröffentlicht",
    label_followers: "Follower", label_views_recent: "Views (letzte Beiträge)", label_likes: "Likes", label_comments: "Kommentare",
    label_views: "Views", label_likes_comments_shares: "Likes / Kommentare / Shares",
    val_online_latency: "Online ({ms}ms)", val_down_error: "Offline / Fehler", label_npm_vulns: "npm-Schwachstellen",
    label_eslint: "ESLint", val_not_configured: "nicht konfiguriert", val_errors_warnings: "{e} Fehler, {w} Warnungen",
    insight_loading: "Analyse läuft…", insight_error: "Fehler bei der Analyse: ",
    ins_no_items: "{name}: keine aktuellen Inhalte zum Auswerten.",
    locked_title: "Funktion des Pro-Tarifs",
    locked_cta: "Tarife ansehen",
    locked_best_hours: "Empfohlene Zeitfenster sind im Pro-Tarif enthalten.",
    locked_history: "Verlauf und Trenddiagramme sind im Pro-Tarif enthalten.",
    plan_feature_locked: "Diese Funktion ist im Pro-Tarif enthalten.",
    plan_account_limit: "Dein Tarif umfasst {n} verknüpfte Konten. Wechsle in einen höheren Tarif für mehr.",
    plan_account_limit_one: "Dein Tarif umfasst nur 1 verknüpftes Konto. Wechsle in einen höheren Tarif für mehr.",
    plan_free_tagline: "Zum Einstieg und um deine Zahlen zu verstehen.",
    plan_free_accounts: "1 verknüpftes Konto",
    plan_pro_tagline: "Für alle, die täglich posten und wachsen wollen.",
    plan_pro_accounts: "3 verknüpfte Konten",
    plan_studio_tagline: "Für Agenturen und mehrere Marken.",
    plan_studio_accounts: "10 verknüpfte Konten",
    plan_feat_all_socials: "Statistiken aller unterstützten Netzwerke",
    plan_feat_manual_refresh: "Manuelles Aktualisieren bei Bedarf",
    plan_feat_analytics: "Analysen: Top-Beiträge und Zeitfenster",
    plan_feat_diagnostics: "Automatische Fehlerdiagnose",
    plan_feat_insights: "Automatische Beobachtungen zu deinen Inhalten",
    plan_feat_history: "Vollständiger Verlauf mit Trenddiagrammen",
    plan_feat_reports: "Automatische Berichte",
    plan_feat_all_free: "Alles aus Free",
    plan_feat_compare: "Zeitraumvergleich und Warnungen bei Rückgang",
    plan_feat_hours: "Vorschläge für Veröffentlichungszeiten",
    plan_feat_csv: "Datenexport als CSV",
    plan_feat_all_pro: "Alles aus Pro",
    plan_feat_workspaces: "Getrennte Arbeitsbereiche pro Kunde",
    plan_feat_whitelabel: "Automatische White-Label-PDF-Berichte",
    plan_feat_multiuser: "Mehrbenutzerzugang fürs Team",
    plan_feat_priority: "Prioritätssupport",
    aria_toggle_password: "Passwort anzeigen",
    aria_close: "Schließen",
    ins_some_zero: "{name}: {n} der letzten {tot} Beiträge stehen noch bei null Aufrufen.",
    ins_some_zero_one: "{name}: 1 der letzten {tot} Beiträge steht noch bei null Aufrufen.",
    ins_all_zero_one: "{name}: der einzige aktuelle Beitrag hat noch keine Aufrufe.",
    ins_flop_one: "{name}: 1 Beitrag unter 40% des Durchschnitts: „{title}“ mit {v} Aufrufen.",
    ins_cadence_daily: "{name}: du postest etwa {n} Mal pro Tag.",
    ins_cadence_broken_daily: "{name}: normalerweise postest du mehrmals täglich, der letzte Inhalt ist aber {d} Tage alt.",
    ins_all_zero: "{name}: keiner der letzten {n} Beiträge hat bisher Aufrufe.",
    ins_star: "{name}: „{title}“ kam auf {v} Aufrufe, {x}x den Kontodurchschnitt. Schau, was ihn auszeichnet, und wiederhole es.",
    ins_flop: "{name}: {n} Beiträge unter 40% des Durchschnitts; der schwächste ist „{title}“ mit {v} Aufrufen.",
    ins_engagement: "{name}: {rate}% Engagement bei den letzten Inhalten ({i} Interaktionen auf {v} Aufrufe).",
    ins_cadence_broken: "{name}: normalerweise postest du alle {gap} Tage, der letzte Inhalt ist aber {d} Tage alt.",
    ins_cadence: "{name}: du postest im Schnitt alle {gap} Tage.",
    ins_best_account: "{best} ist dein stärkstes Konto: {bv} Aufrufe gegenüber {wv} bei {worst}.",
    ins_x_free_plan: "X stellt im kostenlosen Tarif keine Lesestatistiken bereit: Es gibt nichts auszuwerten.",
    ins_no_data: "Noch nichts auszuwerten: Verknüpfe ein Konto und drücke Refresh.",
    ins_nothing_notable: "Keine Auffälligkeiten in deinen letzten Inhalten.",
    analytics_empty: "Noch nicht genug Beiträge/Videos mit Daten für eine Analyse — Refresh drücken.",
    analytics_engagement: "Engagement",
    analytics_engagement_hint: "Anteil der erreichten Personen, die geliked, kommentiert, geteilt oder gespeichert haben. Verglichen mit dem Durchschnitt für Konten deiner Größe.",
    analytics_heatmap: "Tag und Uhrzeit",
    analytics_heatmap_hint: "Wo deine Inhalte wirklich angekommen sind. Dunkler heißt mehr durchschnittliche Aufrufe für die Beiträge aus diesem Zeitfenster.",
    eng_above: "Über dem Durchschnitt ({e}%)", eng_below: "Unter dem Durchschnitt ({e}%)",
    eng_inline: "Im Durchschnitt ({e}%)",
    eng_no_benchmark: "Followerzahl für den Vergleich nicht verfügbar",
    eng_saves: "Speicherungen", eng_shares: "Geteilt",
    eng_saves_hint: "Anteil der erreichten Personen, die den Beitrag gespeichert haben: das stärkste Zeichen, dass er es wert war.",
    eng_shares_hint: "Anteil der erreichten Personen, die ihn weitergegeben haben: so verlässt ein Inhalt dein eigenes Publikum.",
    heatmap_not_enough: "Für die Karte werden mehr Inhalte mit Datum und Uhrzeit benötigt.",
    heatmap_cell: "{d} um {h}:00 — {v} Aufrufe im Schnitt bei {n} Beiträgen",
    weekday_short: "Mo,Di,Mi,Do,Fr,Sa,So",
    analytics_untitled: "(ohne Titel)", analytics_avg_views: "Ø Views", analytics_bucket_count: "analysierte Beiträge in dieser Zeitspanne",
    analytics_last_refresh: "Letzter Datenabruf: {t} ({d})", analytics_last_refresh_never: "Letzter Datenabruf: nie — Refresh drücken.",
    footer_last_refresh: "Letzte Aktualisierung: {d}", footer_never: "Nie aktualisiert", footer_error: "Fehler beim Refresh - erneut versuchen.",
    time_never: "nie", time_seconds_ago: "vor wenigen Sekunden", time_min_ago: "vor {n} Min.", time_hours_ago: "vor {n} Std.", time_days_ago: "vor {n} Tagen",
    diag_next_step_label: "Nächster Schritt:",
    diag_unreachable_title: "{name}: antwortet nicht",
    diagerr_scope_denied_cat: "Berechtigung nicht erteilt", diagerr_scope_denied_step: "Die Leseberechtigung für Statistiken muss im Entwicklerportal der Plattform freigegeben werden – aus der App heraus nicht lösbar.",
    diagerr_expired_cat: "Zugriff abgelaufen", diagerr_expired_step: "Verknüpfe dieses Konto neu: Die Autorisierung ist abgelaufen oder wurde widerrufen.",
    diagerr_scope_mismatch_cat: "Berechtigungen abweichend", diagerr_scope_mismatch_step: "Die angeforderten Berechtigungen stimmen nicht mit den ursprünglich erteilten überein: Konto neu verknüpfen.",
    diagerr_permission_cat: "Fehlende Berechtigung", diagerr_permission_step: "Das Konto hat die nötige Berechtigung nicht erteilt: neu verknüpfen und alle Anfragen annehmen.",
    diagerr_rate_cat: "Zu viele Anfragen", diagerr_rate_step: "Warte einige Minuten bis zur nächsten Aktualisierung: Das Limit der Plattform wurde erreicht.",
    diagerr_auth_cat: "Ungültige Zugangsdaten", diagerr_auth_step: "Verknüpfe das Konto neu, um den Zugriff zu erneuern.",
    diagerr_notfound_cat: "Konto nicht gefunden", diagerr_notfound_step: "Das verknüpfte Konto ist nicht mehr erreichbar: Es wurde möglicherweise entfernt oder umbenannt.",
    diagerr_network_cat: "Netzwerkproblem", diagerr_network_step: "Versuche die Aktualisierung erneut: Das sieht nach einem vorübergehenden Verbindungsproblem aus.",
    diagerr_unknown_cat: "Nicht klassifizierter Fehler", diagerr_unknown_step: "Aktualisierung erneut versuchen; wenn es bestehen bleibt, Konto neu verknüpfen.",
    diag_no_account_cat: "Zu verknüpfen", diag_no_account_title: "Kein {p}-Konto", diag_no_account_text: "Du hast noch kein {p}-Konto verknüpft.", diag_no_account_step: "Auf Verknüpfen tippen und anmelden: Das dauert nur Sekunden.",
    diag_no_data_cat: "Fehlende Daten", diag_no_data_title: "{p} ohne Daten", diag_no_data_text: "Noch keine Daten geladen.", diag_no_data_step: "Auf Refresh tippen, um die Daten zu laden.",
    diag_all_ok_title_one: "{p}: 1 Konto in Ordnung", diag_all_ok_cat_one: "Alles in Ordnung", diag_all_ok_text_one: "Das Konto antwortet und postet regelmäßig.", diag_all_ok_step_one: "Keine Aktion erforderlich.",
    diag_all_ok_cat: "Alles in Ordnung", diag_all_ok_title: "{p}: {n} Konten in Ordnung", diag_all_ok_text: "Alle Konten antworten und posten regelmäßig.", diag_all_ok_step: "Keine Aktion erforderlich.",
    diag_stale_bad_cat: "Inhalt steht still", diag_stale_bad_title: "{name}: seit {d} Tagen inaktiv", diag_stale_bad_text: "Der letzte Inhalt auf {p} ist {d} Tage alt.", diag_stale_bad_step: "Poste etwas: Plattformen belohnen Beständigkeit und die Reichweite fällt bei inaktiven Profilen schnell.",
    diag_stale_warn_cat: "Nachlassender Rhythmus", diag_stale_warn_title: "{name}: letzter Beitrag vor {d} Tagen", diag_stale_warn_text: "Auf {p} kommt seit {d} Tagen nichts Neues.", diag_stale_warn_step: "Kehre zu deinem üblichen Rhythmus zurück, bevor die Reichweite sinkt.",
    diag_zero_views_cat: "Keine Aufrufe", diag_zero_views_title: "{name}: 0 Aufrufe bei den letzten Videos", diag_zero_views_text: "Die zuletzt veröffentlichten Videos haben noch keine Aufrufe.", diag_zero_views_step: "Frisch veröffentlicht ist das normal; sind sie ein paar Tage alt, überarbeite Titel, Thumbnail und die ersten Sekunden.",
    diag_not_configured_cat: "Zu konfigurieren", diag_not_configured_title: "{name}: nicht konfiguriert", diag_not_configured_text: "Das Konto ist gelistet, hat aber keine Zugangsdaten hinterlegt.", diag_not_configured_step: "Verknüpfe das Konto oder entferne es aus der Liste, wenn du es nicht brauchst.",
    diag_x_not_linked_cat: "Nicht verknüpft", diag_x_not_linked_title: "X nicht verknüpft", diag_x_not_linked_text: "Keine X-Zugangsdaten konfiguriert.", diag_x_not_linked_step: "X stellt im kostenlosen Tarif keine Lesestatistiken bereit: Dieser Bereich bleibt vorerst informativ.",
    diag_x_linked_cat: "Verknüpft", diag_x_linked_title: "X verknüpft", diag_x_linked_text: "Zugangsdaten vorhanden. Lesestatistiken sind im kostenlosen Tarif von X nicht verfügbar.", diag_x_linked_step: "Keine Aktion erforderlich.",
    yt_total_views_lag_note: "YouTube braucht bei kleinen/neuen Kanälen manchmal Stunden/Tage, um die historische Gesamtzahl zu aktualisieren — kein Fehler im Dashboard.",
    overview_sub: "{n} Konten auf {p} Plattformen im Blick.", overview_sub_empty: "Refresh drücken, um deine Daten zu laden.",
    trend_since: "seit dem letzten", trend_no_history: "Noch ein Refresh und der Trend erscheint hier.",
    account_guest: "Gast", account_signin_hint: "Anmelden zum Speichern",
    auth_tab_login: "Anmelden", auth_tab_register: "Registrieren",
    auth_title_login: "Willkommen zurück", auth_title_register: "Konto erstellen",
    auth_sub_login: "Melde dich an, um Tarife und Einstellungen zu synchronisieren.", auth_sub_register: "Dauert dreißig Sekunden. Ohne Karte.",
    auth_name: "Dein Name", auth_first_name: "Vorname", auth_last_name: "Nachname", auth_birth_date: "Geburtsdatum",
    auth_first_name_ph: "Max", auth_last_name_ph: "Mustermann", auth_email_ph: "du@beispiel.de",
    auth_email: "E-Mail", auth_password: "Passwort", auth_password_confirm: "Passwort bestätigen",
    auth_switch_to_register: "Noch kein Konto?", auth_switch_to_login: "Schon ein Konto?",
    auth_aside_badge: "Alles an einem Ort",
    auth_aside_title: "Schluss damit, sechs Apps zu öffnen, um zu sehen, wie es läuft.",
    auth_aside_1: "Alle deine Konten auf einen Blick",
    auth_aside_2: "Sagt dir, wenn eine Zahl fällt — nicht nur, wie hoch sie ist",
    auth_aside_3: "Findet die Uhrzeiten, zu denen deine Posts wirklich laufen",
    auth_aside_4: "Deine Tokens bleiben auf deinem Rechner, nicht auf einem Server",
    auth_aside_foot: "Zum Starten ist keine Karte nötig.",
    auth_logout: "Abmelden", account_upgrade: "Auf Pro wechseln", account_upgrade_studio: "Auf Studio wechseln", account_since: "Konto erstellt am {d}",
    err_email_invalid: "Gib eine gültige E-Mail-Adresse ein.", err_password_short: "Mindestens 8 Zeichen.",
    err_required: "Pflichtfeld.", err_birth_date_future: "Das Datum darf nicht in der Zukunft liegen.",
    err_birth_invalid: "Gib ein gültiges Geburtsdatum ein.", err_birth_too_young: "Du musst mindestens 13 Jahre alt sein, um dich zu registrieren.",
    err_first_name_required: "Gib deinen Vornamen ein.", err_last_name_required: "Gib deinen Nachnamen ein.",
    err_email_taken: "Mit dieser E-Mail existiert bereits ein Konto.", err_bad_credentials: "E-Mail oder Passwort falsch.",
    err_session_expired: "Sitzung ungültig oder abgelaufen.", err_login_required_for_plan: "Melde dich an, bevor du einen Tarif kaufst.",
    err_age_min: "Du musst mindestens {n} Jahre alt sein.", err_password_mismatch: "Die Passwörter stimmen nicht überein.",
    auth_forgot_password: "Passwort vergessen?", reset_title: "Passwort zurücksetzen", reset_step1_sub: "Gib deine E-Mail ein, wir schicken dir einen 6-stelligen Code.", reset_step2_sub: "Code an {email} gesendet. Prüfe auch deinen Spam-Ordner.", reset_send_code: "Code senden", reset_code_label: "6-stelliger Code", reset_new_password: "Neues Passwort", reset_confirm: "Passwort zurücksetzen", reset_resend: "Code erneut senden", reset_err_code_format: "Der Code muss 6 Ziffern haben.", reset_success: "Passwort zurückgesetzt. Du bist angemeldet.", err_reset_invalid: "Ungültiger Code.", err_reset_expired: "Dieser Code ist abgelaufen — fordere einen neuen an.", err_reset_too_many: "Zu viele Versuche mit diesem Code. Fordere einen neuen an.",
    toast_welcome: "Willkommen, {n}!", toast_logged_in: "Willkommen zurück, {n}!", toast_logged_out: "Du wurdest abgemeldet.",
    toast_refresh_done: "Daten aktualisiert.", toast_export_done: "CSV exportiert.",
    toast_login_required: "Melde dich an, bevor du einen Tarif wählst.",
    pricing_title: "Wähle, wie viel du sehen willst", pricing_sub: "Kostenlos starten. Auf Pro wechseln, wenn die Zahlen zählen.",
    pricing_monthly: "Monatlich", pricing_yearly: "Jährlich", pricing_save: "2 Monate gratis",
    plan_popular: "Am beliebtesten", plan_free_cta: "Kostenlos starten", plan_cta: "{p} wählen",
    plan_current: "Aktueller Tarif", plan_period_month: "/Mon.", plan_period_year: "/Jahr",
    plan_billed_yearly: "{a}€ einmal jährlich abgerechnet", plan_billed_free: "Für immer kostenlos",
    pricing_note_ready: "Sichere Zahlung über Stripe. Jederzeit kündbar.",
    pricing_note_setup: "Zahlungen sind derzeit nicht verfügbar. Bitte später erneut versuchen.",
    checkout_unavailable: "Der Zahlungsdienst ist nicht erreichbar. Bitte in Kürze erneut versuchen.",
    plan_unknown: "Ungültiger Tarif.",
    checkout_opened: "Die Zahlungsseite wurde im Browser geöffnet.",
    licence_title: "Lizenz",
    licence_hint: "Pro oder Studio gekauft? Füge hier den Schlüssel ein, den du nach der Zahlung erhalten hast.",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "Aktivieren", licence_manage: "Abo verwalten", licence_remove: "Von diesem Computer entfernen",
    licence_state_free: "Free-Tarif", licence_state_active: "{p} aktiv",
    licence_state_expired: "Lizenz zu prüfen",
    licence_state_revoked: "Lizenz inaktiv",
    licence_revoked_note: "Dieses Abo ist nicht mehr aktiv. Falls das ein Fehler ist, wende dich an den Support.",
    licence_active_on: "Lizenz aktiv ({k})",
    licence_recheck_failed: "Die Lizenz kann gerade nicht geprüft werden. Prüfe die Verbindung – dein Tarif bleibt noch einige Tage aktiv.",
    licence_enter_key: "Gib deinen Lizenzschlüssel ein.",
    licence_activated: "{p} aktiviert!", licence_removed: "Lizenz von diesem Computer entfernt.",
    license_missing: "Gib deinen Lizenzschlüssel ein.",
    license_not_found: "Ungültiger Schlüssel. Prüfe, ob du ihn vollständig kopiert hast.",
    license_inactive: "Diese Lizenz ist nicht mehr aktiv. Falls dein Abo läuft, wende dich an den Support.",
    license_service_unavailable: "Der Prüfdienst ist nicht erreichbar. Prüfe die Verbindung und versuche es erneut.",
    palette_placeholder: "Gehe zu…", palette_empty: "Keine Ergebnisse.",
    strength_labels: "schwach,schwach,mittel,gut,stark",
  },
  ja: {

    // --- Aggiornamento automatico ---
    update_available_title: "バージョン {version} が利用できます",
    update_now: "今すぐ更新",
    update_later: "後で通知",
    update_skip: "このバージョンをスキップ",
    update_mandatory: "必須の更新",
    update_downloading: "ダウンロードと検証中…",
    update_restarting: "アプリが終了し、新しいバージョンで自動的に再起動します。",
    update_failed: "更新は完了しませんでした。現在のバージョンはそのままです。",
    update_managed_by_winget: "このコピーは winget でインストールされています。「winget upgrade」で更新してください。",
    update_running_from_source: "ソースから実行しています。自動更新は適用されません。",
    update_up_to_date: "アプリは最新です。",
    update_check_now: "更新を確認",
    update_channel_beta: "テスト版を受け取る",

    // --- Limite dispositivi per licenza ---
    license_device_limit: "このキーはすでに有効化できる端末の上限に達しています。別の端末で無効化してから、こちらで再度お試しください。",
    license_reactivate_needed: "この端末でキーをもう一度入力して、再有効化してください。",

    // --- state OAuth non valido ---
    connect_state_missing: "完了待ちの連携はありません。「連携」を押してやり直してください。",
    connect_state_mismatch: "このアドレスは開始した連携と一致しません。到達したページの完全なアドレスを貼り付けてください。自分のものでない場合は使用しないでください。",

    // --- Dati in cache ---
    cache_title: "キャッシュデータ",
    cache_hint: "更新しても数値がおかしい場合、ローカルキャッシュを消去するとダッシュボードが最初から再計算します。連携アカウントとライセンスには影響しません。",
    cache_clear_btn: "キャッシュを消去", app_footer_rights: "無断複製・転載を禁じます。", app_footer_license: "ライセンス",
    cache_confirm: "保存された統計と履歴は次回の更新時に再計算されます。続行しますか?",
    cache_cleared: "キャッシュを消去しました。",

    // --- Controllo aggiornamenti ---
    update_available: "アップデートあり",
    update_available_v: "バージョン {v} が利用可能",
    update_hint: "バージョン{v}のダウンロードページを開きます。",
    um_size: "{size}",
    um_release_notes: "リリースノート",
    um_installing: "インストール中…",
    um_later: "後で通知する",
    um_skip: "このバージョンをスキップ",
    um_install: "インストールして再起動",
    um_error: "インストールに失敗しました。もう一度試すか、新しいバージョンを手動でダウンロードしてください。",

    // --- "Usa la tua app": procedura guidata ---
    sw_title: "自分のアプリで{p}を連携",
    sw_step_of: "ステップ {n}/{tot}",
    sw_back: "戻る",
    sw_next: "次へ",
    sw_finish: "保存して連携",
    sw_saving: "確認中…",
    sw_open: "ページを開く",
    sw_copy: "コピー",
    sw_copied: "コピーしました ✓",
    sw_copy_failed: "コピーできません。アドレスを選択して手動でコピーしてください。",
    sw_saved: "完了しました。アカウントにログインしてください。",
    sw_removed: "自分のアプリを解除しました。",
    sw_offer: "待ちたくない場合は、自分のアプリを登録すればすぐに連携できます。手順は画面で案内します（約10分）。",
    sw_offer_btn: "今すぐ連携 →",
    sw_own_active: "自分のアプリを使用中です（{id}）。",
    sw_own_remove: "解除",
    sw_id_label_ig: "Instagram アプリ ID",
    sw_secret_label_ig: "Instagram アプリシークレット",
    sw_id_ph_ig: "1234567890123456",
    sw_secret_ph_ig: "32文字",
    sw_id_label_tt: "Client key",
    sw_secret_label_tt: "Client secret",
    sw_id_ph_tt: "sbawxxxxxxxxxxxxxxxx",
    sw_secret_ph_tt: "シークレットを貼り付け",
    sw_ig1_t: "必要なもの",
    sw_ig1_d: "自分の Instagram アプリを登録します（約10分、初回のみ）。\nInstagram のプロアカウント（ビジネスまたはクリエイター）と、開発者ダッシュボードに入るための Facebook アカウントが必要です。\n認証情報はこのパソコンに保存されます。",
    sw_ig2_t: "アプリを作成",
    sw_ig2_d: "Meta の開発者ダッシュボードを開き、「アプリを作成」を押します。\nユースケースは「その他」、タイプは「ビジネス」を選んでください。\n名前は自由です。",
    sw_ig3_t: "Instagram を追加",
    sw_ig3_d: "新しいアプリで「プロダクトを追加」を開き、「Instagram」を選んで「設定」を押します。\n次に「Instagram ビジネスログインで API を設定」を選びます。",
    sw_ig4_t: "リダイレクト先を貼り付け",
    sw_ig4_d: "同じページで「ビジネスログイン設定」を開きます。\n下のアドレスをコピーして「OAuth リダイレクト URI」欄に貼り付け、保存してください。\nこのページは既に存在します。サイトを公開する必要はありません。",
    sw_ig5_t: "2つの認証情報をコピー",
    sw_ig5_d: "同じページのアプリ設定欄に「Instagram アプリ ID」と「Instagram アプリシークレット」があります。\n下に貼り付けてください。これが最後の手順です。",
    sw_tt1_t: "必要なもの",
    sw_tt1_d: "自分の TikTok アプリを登録します（約10分、初回のみ）。\n必要なのは TikTok アカウントだけです。\n認証情報はこのパソコンに保存されます。",
    sw_tt2_t: "アプリを作成",
    sw_tt2_d: "TikTok の開発者ポータルを開き、アカウントでログインして新しいアプリを登録します。\n名前を付けて確定してください。",
    sw_tt3_t: "ログインと権限を有効化",
    sw_tt3_d: "アプリで「Add products」を開き、「Login Kit」を追加します。\nスコープで user.info.basic、user.info.stats、video.list を有効にします。\nいずれも読み取り専用で、フォロワー数と動画の統計を読むために使います。",
    sw_tt4_t: "サンドボックスを作成",
    sw_tt4_d: "「Sandbox」を開いて1つ作成します。\nその中に自分の TikTok アカウントを「target user」として追加します。これにより、TikTok の審査を待たずに自分のデータを読めます。",
    sw_tt5_t: "リダイレクト先を貼り付け",
    sw_tt5_d: "Login Kit の設定で、下のアドレスをコピーして「Redirect URI」に貼り付け、保存してください。\nこのページは既に存在します。サイトを公開する必要はありません。",
    sw_tt6_t: "2つの認証情報をコピー",
    sw_tt6_d: "アプリ詳細にサンドボックスの「Client key」と「Client secret」があります。\n下に貼り付けてください。これが最後の手順です。",
    ownapp_missing: "両方の項目を入力してください。",
    ownapp_unsupported: "対応していないプラットフォームです。",
    ownapp_bad_ig_id: "Instagram アプリ ID は数字のみです。2つの項目を入れ替えていないか確認してください。",
    ownapp_bad_ig_secret: "シークレットが不完全のようです。空白を含めず全体をコピーしてください。",
    ownapp_bad_tt_key: "TikTok の Client key は「aw」または「sbaw」で始まります。2つの項目を入れ替えていないか確認してください。",
    ownapp_bad_tt_secret: "Client secret が不完全のようです。空白を含めず全体をコピーしてください。",
    ownapp_tt_refused: "TikTok がこの認証情報を認識できません。Client key と Client secret が同じアプリのものか確認してください。",
    overview_by_platform: "\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u5225",
    overview_top_content: "\u4eba\u6c17\u30b3\u30f3\u30c6\u30f3\u30c4", platform_status_green: "\u63a5\u7d9a\u6e08\u307f\u30fb\u540c\u671f\u6e08\u307f", platform_status_yellow: "\u8981\u5bfe\u5fdc", platform_status_red: "\u30a8\u30e9\u30fc", platform_status_grey: "\u672a\u8a2d\u5b9a",
    tile_followers: "\u7dcf\u30d5\u30a9\u30ed\u30ef\u30fc", tile_recent_views: "\u6700\u8fd1\u306e\u518d\u751f\u6570", tile_recent_views_foot: "\u76f4\u8fd1\u306e\u30b3\u30f3\u30c6\u30f3\u30c4",
    tile_engagement: "\u30a8\u30f3\u30b2\u30fc\u30b8\u30e1\u30f3\u30c8", tile_engagement_foot: "\u76f4\u8fd1\u306e\u3044\u3044\u306d\u3068\u30b3\u30e1\u30f3\u30c8",
    tile_health: "\u30d8\u30eb\u30b9", tile_accounts_foot: "\u30a2\u30af\u30c6\u30a3\u30d6\u306a\u30a2\u30ab\u30a6\u30f3\u30c8",
    tile_analyzed: "\u5206\u6790\u3057\u305f\u30b3\u30f3\u30c6\u30f3\u30c4", tile_analyzed_foot: "\u30c7\u30fc\u30bf\u306e\u3042\u308b\u6295\u7a3f\u3068\u52d5\u753b",
    tile_avg_per_post: "1\u4ef6\u3042\u305f\u308a\u5e73\u5747", tile_avg_per_post_foot: "\u5e73\u5747\u518d\u751f\u6570",
    tile_avg_per_post_foot_n: "\u30c7\u30fc\u30bf\u306e\u3042\u308b {n} \u4ef6\u306e\u5e73\u5747\u518d\u751f\u6570", tile_best_hour_insufficient: "\u30b3\u30f3\u30c6\u30f3\u30c4\u304c\u4e0d\u8db3",
    analytics_hours_insufficient: "\u4fe1\u983c\u3067\u304d\u308b\u6642\u9593\u5e2f\u3092\u793a\u3059\u306b\u306f\u30c7\u30fc\u30bf\u304c\u4e0d\u8db3\u3057\u3066\u3044\u307e\u3059\u3002\u518d\u751f\u6570\u306e\u3042\u308b\u30b3\u30f3\u30c6\u30f3\u30c4\u304c\u3042\u3068 {n} \u4ef6\u5fc5\u8981\u3067\u3059\u3002",
    tile_best_hour: "\u6700\u9069\u306a\u6642\u9593", tile_best_hour_foot: "\u5e73\u5747{v}\u518d\u751f",
    tile_best_platform: "\u30c8\u30c3\u30d7\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0", tile_best_platform_foot: "\u5408\u8a08{v}\u518d\u751f",
    analytics_hours_hint: "\u6295\u7a3f\u6642\u9593\u5e2f\uff08UTC\uff09\u3054\u3068\u306e\u5e73\u5747\u518d\u751f\u6570\u3002\u6fc3\u3044\u30d0\u30fc\u304c\u6700\u3082\u4f38\u3073\u308b\u6642\u9593\u5e2f\u3067\u3059\u3002",
    hours_tooltip: "{h}:00 - {n}\u4ef6\u3067\u5e73\u5747{v}\u518d\u751f",
    guided_step1: "\u958b\u3044\u305f\u30bf\u30d6\u3067\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u8a8d\u53ef\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    guided_step2: "\u305d\u306e\u5f8c\u3001\u79fb\u52d5\u5148\u306e\u30da\u30fc\u30b8\u306eURL\u3092\u30b3\u30d4\u30fc\u3057\u3066\u4e0b\u306b\u8cbc\u308a\u4ed8\u3051\u3066\u304f\u3060\u3055\u3044\u3002",
    guided_placeholder: "\u5b8c\u5168\u306aURL\u3092\u8cbc\u308a\u4ed8\u3051", guided_cancel: "\u30ad\u30e3\u30f3\u30bb\u30eb", guided_finish: "\u5b8c\u4e86",
    guided_paste_needed: "\u5148\u306b\u623b\u308aURL\u3092\u8cbc\u308a\u4ed8\u3051\u3066\u304f\u3060\u3055\u3044\u3002",
    btn_link_account: "\u9023\u643a", btn_link_account_full: "\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u9023\u643a",
    cm_auto_text: "\u30d6\u30e9\u30a6\u30b6\u304c\u958b\u304d\u307e\u3059\u3002\u30ed\u30b0\u30a4\u30f3\u3057\u3066\u8aad\u307f\u53d6\u308a\u5c02\u7528\u30a2\u30af\u30bb\u30b9\u3092\u8a31\u53ef\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    cm_step1: "\u958b\u3044\u305f\u30bf\u30d6\u3067\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u8a8d\u53ef\u3057\u3066\u304f\u3060\u3055\u3044\u3002", cm_open: "\u8a8d\u53ef\u3092\u958b\u304f",
    cm_step2: "\u79fb\u52d5\u5148\u306e\u30da\u30fc\u30b8\u306eURL\u3092\u3053\u3053\u306b\u8cbc\u308a\u4ed8\u3051\u3066\u304f\u3060\u3055\u3044\u3002", cm_finish: "\u9023\u643a\u3092\u5b8c\u4e86",
    group_connections: "\u9023\u643a\u6e08\u307f\u30a2\u30ab\u30a6\u30f3\u30c8", nav_connections: "\u30a2\u30ab\u30a6\u30f3\u30c8\u9023\u643a",
    connections_subtitle: "\u30a2\u30ab\u30a6\u30f3\u30c8\u3067\u30ed\u30b0\u30a4\u30f3\u3059\u308b\u3060\u3051\u3002\u30c8\u30fc\u30af\u30f3\u306e\u30b3\u30d4\u30fc\u306f\u4e0d\u8981\u3067\u3059\u3002",
    connections_privacy: "\u8a8d\u8a3c\u60c5\u5831\u306f\u304a\u4f7f\u3044\u306ePC\u5185\u306b\u306e\u307f\u4fdd\u5b58\u3055\u308c\u307e\u3059\u3002\u30b5\u30fc\u30d0\u30fc\u3092\u7d4c\u7531\u3059\u308b\u3053\u3068\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
    connect_now: "{p}\u3092\u9023\u643a", connect_add_another: "\u5225\u306e\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u9023\u643a", connect_soon: "\u8fd1\u65e5\u5bfe\u5fdc",
    generic_error: "\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f\u3002", connect_timeout: "\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8\uff1a\u9023\u643a\u304c\u5b8c\u4e86\u3057\u307e\u305b\u3093\u3067\u3057\u305f\u3002",
    connect_already_running: "\u65e2\u306b\u9023\u643a\u51e6\u7406\u304c\u9032\u884c\u4e2d\u3067\u3059\u3002",
    connect_platform_unsupported: "\u3053\u306e\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u306f\u307e\u3060\u5bfe\u5fdc\u3057\u3066\u3044\u307e\u305b\u3093\u3002",
    connect_guided_unavailable: "\u3053\u306e\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u3067\u306f\u30ac\u30a4\u30c9\u4ed8\u304d\u9023\u643a\u3092\u5229\u7528\u3067\u304d\u307e\u305b\u3093\u3002",
    connect_window_closed: "\u9023\u643a\u304c\u30ad\u30e3\u30f3\u30bb\u30eb\u3055\u308c\u307e\u3057\u305f\uff1a\u30ed\u30b0\u30a4\u30f3\u5b8c\u4e86\u524d\u306b\u30a6\u30a3\u30f3\u30c9\u30a6\u304c\u9589\u3058\u3089\u308c\u307e\u3057\u305f\u3002",
    connect_denied: "\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u306b\u3088\u3063\u3066\u8a8d\u53ef\u304c\u62d2\u5426\u3055\u308c\u307e\u3057\u305f\u3002",
    connect_code_not_found: "\u8cbc\u308a\u4ed8\u3051\u305fURL\u306b\u30b3\u30fc\u30c9\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3067\u3057\u305f\u3002",
    connect_instagram_rejected: "Instagram\u304c\u8a8d\u53ef\u30b3\u30fc\u30c9\u3092\u62d2\u5426\u3057\u307e\u3057\u305f\u3002\u3082\u3046\u4e00\u5ea6\u9023\u643a\u3092\u304a\u8a66\u3057\u304f\u3060\u3055\u3044\u3002",
    connect_token_exchange_failed: "\u30c8\u30fc\u30af\u30f3\u306e\u4ea4\u63db\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002\u3082\u3046\u4e00\u5ea6\u9023\u643a\u3092\u304a\u8a66\u3057\u304f\u3060\u3055\u3044\u3002",
    connect_tiktok_rejected: "TikTok\u304c\u8a8d\u53ef\u30b3\u30fc\u30c9\u3092\u62d2\u5426\u3057\u307e\u3057\u305f\u3002\u3082\u3046\u4e00\u5ea6\u9023\u643a\u3092\u304a\u8a66\u3057\u304f\u3060\u3055\u3044\u3002",
    connect_tiktok_unexpected: "TikTok\u304b\u3089\u4e88\u671f\u3057\u306a\u3044\u5fdc\u7b54\u304c\u3042\u308a\u307e\u3057\u305f\u3002\u3057\u3070\u3089\u304f\u3057\u3066\u304b\u3089\u518d\u8a66\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    connect_proxy_http_error: "\u8a8d\u53ef\u30b5\u30fc\u30d3\u30b9\u304c\u6b63\u3057\u304f\u5fdc\u7b54\u3057\u307e\u305b\u3093\u3067\u3057\u305f\u3002\u3057\u3070\u3089\u304f\u3057\u3066\u304b\u3089\u518d\u8a66\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    connect_proxy_rejected: "\u8a8d\u53ef\u30b5\u30fc\u30d3\u30b9\u304c\u30ea\u30af\u30a8\u30b9\u30c8\u3092\u62d2\u5426\u3057\u307e\u3057\u305f\u3002",
    connect_no_google_app: "Google OAuth\u30a2\u30d7\u30ea\u304c\u8a2d\u5b9a\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002",
    connect_coming_soon: "\u8fd1\u65e5\u516c\u958b",
    cm_coming_soon_text: "\u3053\u306e\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u3068\u306e\u9023\u643a\u306f\u307e\u3082\u306a\u304f\u5229\u7528\u53ef\u80fd\u306b\u306a\u308a\u307e\u3059\u3002\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u5074\u304c\u6c42\u3081\u308b\u627f\u8a8d\u624b\u7d9a\u304d\u3092\u9032\u3081\u3066\u3044\u307e\u3059\u3002\u6570\u65e5\u5f8c\u306b\u3082\u3046\u4e00\u5ea6\u304a\u8a66\u3057\u304f\u3060\u3055\u3044\u3002",
    proxy_not_configured: "\u3053\u306e\u30d3\u30eb\u30c9\u3067\u306f\u8a8d\u53ef\u30b5\u30fc\u30d3\u30b9\u304c\u8a2d\u5b9a\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002",
    unavail_not_configured: "\u3053\u306e\u30d0\u30fc\u30b8\u30e7\u30f3\u306e\u30a2\u30d7\u30ea\u3067\u306f\u307e\u3060\u9023\u643a\u3067\u304d\u307e\u305b\u3093\u3002",
    unavail_x_no_read_api: "X \u306f\u7121\u6599\u30d7\u30e9\u30f3\u3067\u306f\u95b2\u89a7\u7d71\u8a08\u3092\u63d0\u4f9b\u3057\u3066\u3044\u307e\u305b\u3093\u3002",
    connect_not_linked: "\u672a\u9023\u643a", connect_linked_n: "{n}\u4ef6\u9023\u643a\u6e08\u307f", connect_unlink: "\u89e3\u9664",
    connect_reauth_badge: "\u518d\u9023\u643a\u304c\u5fc5\u8981",
    connect_reauth_hint: "\u30a2\u30af\u30bb\u30b9\u6a29\u306e\u6709\u52b9\u671f\u9650\u304c\u5207\u308c\u305f\u304b\u3001\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u5074\u3067\u53d6\u308a\u6d88\u3055\u308c\u307e\u3057\u305f\u3002\u7d71\u8a08\u306e\u53d6\u5f97\u3092\u7d9a\u3051\u308b\u306b\u306f\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u518d\u9023\u643a\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    connect_locked_hint: "\u3053\u306e\u30a2\u30ab\u30a6\u30f3\u30c8\u306e\u8a8d\u8a3c\u60c5\u5831\u306f\u3053\u306e\u30b3\u30f3\u30d4\u30e5\u30fc\u30bf\u30fc\u3067\u306f\u8aad\u307f\u53d6\u308c\u307e\u305b\u3093\u3002\u7d9a\u3051\u308b\u306b\u306f\u518d\u9023\u643a\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    connect_desc: "{p}\u3067\u30ed\u30b0\u30a4\u30f3\u3059\u308b\u3068\u3001\u3053\u3053\u306b\u7d71\u8a08\u304c\u8868\u793a\u3055\u308c\u307e\u3059\u3002",
    connect_waiting: "\u30d6\u30e9\u30a6\u30b6\u3092\u5f85\u6a5f\u4e2d...", connect_browser_opened: "\u30d6\u30e9\u30a6\u30b6\u3092\u958b\u304d\u307e\u3057\u305f\u3002\u30ed\u30b0\u30a4\u30f3\u3092\u5b8c\u4e86\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    connect_success: "{n}\u3092\u9023\u643a\u3057\u307e\u3057\u305f\uff01", connect_unlinked: "\u9023\u643a\u3092\u89e3\u9664\u3057\u307e\u3057\u305f\u3002",
    diag_problems: "\u4ef6\u306e\u554f\u984c", diag_warnings: "\u4ef6\u306e\u8b66\u544a", diag_ok: "\u4ef6\u304c\u826f\u597d",
    diag_filter_all: "\u3059\u3079\u3066", diag_filter_problems: "\u8981\u5bfe\u5fdc", diag_filter_ok: "\u826f\u597d",
    diag_filter_empty: "\u3053\u306e\u30d5\u30a3\u30eb\u30bf\u30fc\u3067\u306f\u8868\u793a\u3059\u308b\u3082\u306e\u304c\u3042\u308a\u307e\u305b\u3093\u3002", diag_go_connect: "\u30a2\u30ab\u30a6\u30f3\u30c8\u9023\u643a\u3078",
    diag_group_strategy: "\u6226\u7565",
    health_part_technical: "\u6280\u8853\u9762", health_part_engagement: "\u30a8\u30f3\u30b2\u30fc\u30b8\u30e1\u30f3\u30c8",
    health_part_consistency: "\u7d99\u7d9a\u6027", health_part_coverage: "\u30ab\u30d0\u30fc\u7bc4\u56f2",
    health_detail_technical: "{n}\u4ef6\u306e\u554f\u984c\u304c\u30c7\u30fc\u30bf\u53ce\u96c6\u3092\u59a8\u3052\u3066\u3044\u307e\u3059", health_detail_engagement: "{n}\u4ef6\u306e\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u57fa\u6e96\u3068\u6bd4\u8f03", health_detail_engagement_none: "\u6bd4\u8f03\u306b\u5341\u5206\u306a\u30d5\u30a9\u30ed\u30ef\u30fc\u30c7\u30fc\u30bf\u304c\u3042\u308a\u307e\u305b\u3093", health_detail_consistency: "\u6700\u7d42\u6295\u7a3f\u304b\u3089{days}\u65e5", health_detail_consistency_none: "\u65e5\u4ed8\u4ed8\u304d\u30b3\u30f3\u30c6\u30f3\u30c4\u304c\u307e\u3060\u3042\u308a\u307e\u305b\u3093", health_detail_coverage: "{total}\u4ef6\u4e2d{active}\u4ef6\u306e\u30d7\u30e9\u30c3\u30c8\u30d5\u30a9\u30fc\u30e0\u3067\u6700\u8fd1\u306e\u6295\u7a3f\u3042\u308a",
    health_nodata_title: "\u30a2\u30ab\u30a6\u30f3\u30c8\u672a\u9023\u643a", health_nodata_sub: "\u30a2\u30ab\u30a6\u30f3\u30c8\u3092\u9023\u643a\u3059\u308b\u3068\u5065\u5eb7\u5ea6\u30b9\u30b3\u30a2\u304c\u8868\u793a\u3055\u308c\u307e\u3059\u3002",
    health_bad_title: "\u5bfe\u5fdc\u304c\u5fc5\u8981\u306a\u9805\u76ee\u304c\u3042\u308a\u307e\u3059", health_bad_sub: "\u554f\u984c\u3068\u8b66\u544a\u304c{n}\u4ef6\u3042\u308a\u307e\u3059\u3002",
    health_warn_title: "\u307b\u307c\u826f\u597d\u3067\u3059", health_warn_sub: "{n}\u4ef6\u306e\u8b66\u544a\u306b\u6ce8\u610f\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    health_good_title: "\u3059\u3079\u3066\u826f\u597d", health_good_sub: "\u30a2\u30ab\u30a6\u30f3\u30c8\u306b\u554f\u984c\u306f\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3067\u3057\u305f\u3002",
    group_general: "一般", group_platforms: "プラットフォーム", group_insights: "インサイト",
    group_account: "アカウント", group_settings: "設定",
    nav_overview: "概要", nav_analytics: "分析", nav_diagnostics: "診断",
    nav_themes: "テーマ", nav_language: "言語", nav_account: "アカウント", nav_pricing: "プランと料金",
    btn_refresh: "更新", btn_analyze: "分析", btn_export: "CSV書き出し", palette_hint: "検索",
    analytics_subtitle: "収集済みデータからコードでローカル計算 — 人気の投稿と最適な投稿時間帯、AIコストなし。",
    analytics_top_posts: "トップ投稿/動画（再生数順）", analytics_outliers: "平均より上/下", analytics_outliers_hint: "自分の平均{v}再生（投稿あたり）との比較 — オーディエンスを知らない業界基準ではありません。", analytics_outliers_empty: "信頼できる比較を行うにはコンテンツがまだ不足しています。", analytics_best_hours: "最適な時間帯（平均再生数）",
    diagnostics_subtitle: "コードによって即座に無料で計算 — エラーを検出し、Refreshのたびに更新されます。",
    themes_subtitle: "ダッシュボードの外観を選択 — 次回起動時も保存されます。",
    language_subtitle: "インターフェースの言語を選択 — 次回起動時も保存されます。",
    empty_no_data: "データがありません — Refreshを押してください。", waiting_for_data: "データ待機中", empty_configure_yt: "YouTubeチャンネルを連携すると、ここに統計が表示されます。",
    empty_configure_ig: "Instagramアカウントを連携すると、ここに統計が表示されます。", empty_configure_tt: "TikTokアカウントを連携すると、ここに統計が表示されます。",
    empty_not_configured: "未設定。",
    label_subscribers_total: "総登録者数", label_channels: "チャンネル数", label_followers_total: "総フォロワー数",
    label_accounts: "アカウント", label_accounts_configured: "設定済みアカウント", label_credentials: "認証情報",
    val_ok: "OK", val_missing: "未設定", label_site: "サイト", val_online: "オンライン", val_down: "ダウン",
    label_subscribers: "登録者数", label_total_views: "総再生回数", label_videos_published: "公開動画数",
    label_recent_views: "再生数（直近10本）", label_last_publish: "最終公開日", label_never_published: "未公開",
    label_followers: "フォロワー", label_views_recent: "再生数（最近の投稿）", label_likes: "いいね", label_comments: "コメント",
    label_views: "再生数", label_likes_comments_shares: "いいね / コメント / シェア",
    val_online_latency: "オンライン（{ms}ms）", val_down_error: "ダウン / エラー", label_npm_vulns: "npmの脆弱性",
    label_eslint: "ESLint", val_not_configured: "未設定", val_errors_warnings: "エラー{e}件、警告{w}件",
    insight_loading: "分析中…", insight_error: "分析中にエラーが発生しました: ",
    ins_no_items: "{name}: 分析できる最近のコンテンツがありません。",
    locked_title: "Pro プランの機能",
    locked_cta: "プランを見る",
    locked_best_hours: "おすすめの時間帯は Pro プランに含まれています。",
    locked_history: "履歴とトレンドグラフは Pro プランに含まれています。",
    plan_feature_locked: "この機能は Pro プランに含まれています。",
    plan_account_limit: "現在のプランでは連携アカウントは {n} 件までです。上位プランにすると追加できます。",
    plan_account_limit_one: "現在のプランでは連携アカウントは 1 件のみです。上位プランにすると追加できます。",
    plan_free_tagline: "まずは数字を把握するために。",
    plan_free_accounts: "連携アカウント 1 件",
    plan_pro_tagline: "毎日投稿して伸ばしたい方へ。",
    plan_pro_accounts: "連携アカウント 3 件",
    plan_studio_tagline: "代理店や複数ブランド運用向け。",
    plan_studio_accounts: "連携アカウント 10 件",
    plan_feat_all_socials: "対応する全 SNS の統計",
    plan_feat_manual_refresh: "手動での更新",
    plan_feat_analytics: "分析：人気投稿と時間帯",
    plan_feat_diagnostics: "エラーの自動診断",
    plan_feat_insights: "コンテンツの自動分析",
    plan_feat_history: "トレンドグラフ付きの完全な履歴",
    plan_feat_reports: "レポートの自動生成",
    plan_feat_all_free: "Free の全機能",
    plan_feat_compare: "期間比較と低下アラート",
    plan_feat_hours: "投稿時間の提案",
    plan_feat_csv: "CSV でのデータ書き出し",
    plan_feat_all_pro: "Pro の全機能",
    plan_feat_workspaces: "クライアントごとのワークスペース",
    plan_feat_whitelabel: "ホワイトラベル PDF レポート",
    plan_feat_multiuser: "チームでのマルチユーザー利用",
    plan_feat_priority: "優先サポート",
    aria_toggle_password: "パスワードを表示",
    aria_close: "閉じる",
    ins_some_zero: "{name}: 直近 {tot} 件のうち {n} 件がまだ再生数ゼロです。",
    ins_some_zero_one: "{name}: 直近 {tot} 件のうち 1 件がまだ再生数ゼロです。",
    ins_all_zero_one: "{name}: 唯一の最近のコンテンツにまだ再生数がありません。",
    ins_flop_one: "{name}: 平均の40%未満が 1 件：「{title}」で {v} 回再生。",
    ins_cadence_daily: "{name}: 1日に約 {n} 回投稿しています。",
    ins_cadence_broken_daily: "{name}: 普段は1日に複数回投稿していますが、最新のコンテンツは {d} 日前です。",
    ins_all_zero: "{name}: 直近 {n} 件のコンテンツにまだ再生数がありません。",
    ins_star: "{name}: 「{title}」は {v} 回再生され、アカウント平均の {x} 倍です。何が違ったのかを見て再現しましょう。",
    ins_flop: "{name}: 平均の40%未満のコンテンツが {n} 件。最も弱いのは「{title}」で {v} 回再生です。",
    ins_engagement: "{name}: 最近のコンテンツのエンゲージメントは {rate}%（{v} 回再生に対し {i} 件の反応）。",
    ins_cadence_broken: "{name}: 普段は {gap} 日ごとに投稿していますが、最新のコンテンツは {d} 日前です。",
    ins_cadence: "{name}: 平均して {gap} 日ごとに投稿しています。",
    ins_best_account: "{best} が最も成果の高いアカウントです：{bv} 回再生に対し {worst} は {wv} 回。",
    ins_x_free_plan: "X は無料プランで閲覧統計を提供していないため、分析できる項目はありません。",
    ins_no_data: "まだ分析するデータがありません。アカウントを連携して「更新」を押してください。",
    ins_nothing_notable: "最近のコンテンツに問題は見つかりませんでした。",
    analytics_empty: "分析に十分なデータのある投稿/動画がまだありません — Refreshを押してください。",
    analytics_engagement: "エンゲージメント",
    analytics_engagement_hint: "リーチした人のうち、いいね・コメント・シェア・保存をした割合。同程度の規模のアカウントの平均と比較しています。",
    analytics_heatmap: "曜日と時間帯",
    analytics_heatmap_hint: "コンテンツが実際に伸びた時間帯。色が濃いほど、その枠に投稿したコンテンツの平均再生数が多いことを示します。",
    eng_above: "平均を上回る（{e}%）", eng_below: "平均を下回る（{e}%）",
    eng_inline: "平均どおり（{e}%）",
    eng_no_benchmark: "比較用のフォロワー数を取得できません",
    eng_saves: "保存", eng_shares: "シェア",
    eng_saves_hint: "リーチした人のうち投稿を保存した割合。価値があったことを示す最も強いシグナルです。",
    eng_shares_hint: "リーチした人のうち他の人に送った割合。コンテンツが自分のフォロワー外へ広がる経路です。",
    heatmap_not_enough: "マップを描くには、日時のあるコンテンツがもっと必要です。",
    heatmap_cell: "{d} {h}:00 — {n}件の平均{v}回再生",
    weekday_short: "月,火,水,木,金,土,日",
    analytics_untitled: "（タイトルなし）", analytics_avg_views: "平均再生数", analytics_bucket_count: "この時間帯で分析された投稿数",
    analytics_last_refresh: "最終データ取得: {t}（{d}）", analytics_last_refresh_never: "最終データ取得: なし — Refreshを押してください。",
    footer_last_refresh: "最終更新: {d}", footer_never: "未更新", footer_error: "更新中にエラーが発生しました。再試行してください。",
    time_never: "なし", time_seconds_ago: "数秒前", time_min_ago: "{n}分前", time_hours_ago: "{n}時間前", time_days_ago: "{n}日前",
    diag_next_step_label: "次のステップ:",
    diag_unreachable_title: "{name}: 応答なし",
    diagerr_scope_denied_cat: "権限が未承認", diagerr_scope_denied_step: "統計読み取り権限をプラットフォームの開発者ポータルで承認する必要があります。アプリ側では解決できません。",
    diagerr_expired_cat: "アクセス期限切れ", diagerr_expired_step: "このアカウントを再連携してください。認証が期限切れか取り消されています。",
    diagerr_scope_mismatch_cat: "権限の不一致", diagerr_scope_mismatch_step: "要求した権限と当初許可された権限が一致しません。アカウントを再連携してください。",
    diagerr_permission_cat: "権限が不足", diagerr_permission_step: "必要な権限が許可されていません。すべての要求を承認して再連携してください。",
    diagerr_rate_cat: "リクエスト過多", diagerr_rate_step: "次の更新まで数分お待ちください。プラットフォームの上限に達しました。",
    diagerr_auth_cat: "認証情報が無効", diagerr_auth_step: "アカウントを再連携してアクセスを再生成してください。",
    diagerr_notfound_cat: "アカウントが見つかりません", diagerr_notfound_step: "連携済みアカウントに到達できません。削除または名前変更された可能性があります。",
    diagerr_network_cat: "ネットワークの問題", diagerr_network_step: "更新をもう一度お試しください。一時的な接続の問題のようです。",
    diagerr_unknown_cat: "未分類のエラー", diagerr_unknown_step: "更新を再試行してください。続く場合はアカウントを再連携してください。",
    diag_no_account_cat: "未連携", diag_no_account_title: "{p} のアカウントなし", diag_no_account_text: "{p} のアカウントはまだ連携されていません。", diag_no_account_step: "「連携」を押してログインしてください。数秒で完了します。",
    diag_no_data_cat: "データなし", diag_no_data_title: "{p} のデータなし", diag_no_data_text: "まだデータが読み込まれていません。", diag_no_data_step: "「更新」を押してデータを読み込んでください。",
    diag_all_ok_title_one: "{p}: アカウントは良好", diag_all_ok_cat_one: "問題なし", diag_all_ok_text_one: "アカウントは応答し、安定して投稿されています。", diag_all_ok_step_one: "対応は不要です。",
    diag_all_ok_cat: "問題なし", diag_all_ok_title: "{p}: {n} 件のアカウントは良好", diag_all_ok_text: "すべてのアカウントが応答し、安定して投稿されています。", diag_all_ok_step: "対応は不要です。",
    diag_stale_bad_cat: "投稿が停止", diag_stale_bad_title: "{name}: {d} 日間停止中", diag_stale_bad_text: "{p} の最新コンテンツは {d} 日前です。", diag_stale_bad_step: "何か投稿しましょう。継続は評価され、非アクティブなプロフィールはリーチが急速に落ちます。",
    diag_stale_warn_cat: "ペース低下", diag_stale_warn_title: "{name}: 最終投稿は {d} 日前", diag_stale_warn_text: "{p} では {d} 日間、新規投稿がありません。", diag_stale_warn_step: "リーチが落ち始める前に、いつものペースに戻しましょう。",
    diag_zero_views_cat: "再生数ゼロ", diag_zero_views_title: "{name}: 直近動画の再生数が 0", diag_zero_views_text: "最近公開した動画にまだ再生数がありません。", diag_zero_views_step: "公開直後なら普通ですが、数日経っているならタイトル・サムネイル・冒頭数秒を見直しましょう。",
    diag_not_configured_cat: "未設定", diag_not_configured_title: "{name}: 未設定", diag_not_configured_text: "アカウントは一覧にありますが、認証情報が紐づいていません。", diag_not_configured_step: "アカウントを連携するか、不要なら一覧から削除してください。",
    diag_x_not_linked_cat: "未連携", diag_x_not_linked_title: "X は未連携", diag_x_not_linked_text: "X の認証情報が設定されていません。", diag_x_not_linked_step: "X は無料プランでは閲覧統計を提供していないため、現時点でこのセクションは参考情報です。",
    diag_x_linked_cat: "連携済み", diag_x_linked_title: "X 連携済み", diag_x_linked_text: "認証情報があります。X の無料プランでは閲覧統計を利用できません。", diag_x_linked_step: "対応は不要です。",
    yt_total_views_lag_note: "YouTubeでは小規模・新規チャンネルの累計再生数の更新に数時間〜数日かかることがあります — ダッシュボードの不具合ではありません。",
    overview_sub: "{p}個のプラットフォームで{n}件のアカウントを監視中。", overview_sub_empty: "Refreshを押してデータを読み込んでください。",
    trend_since: "前回から", trend_no_history: "もう一度更新すると推移が表示されます。",
    account_guest: "ゲスト", account_signin_hint: "ログインして保存",
    auth_tab_login: "ログイン", auth_tab_register: "新規登録",
    auth_title_login: "おかえりなさい", auth_title_register: "アカウントを作成",
    auth_sub_login: "ログインしてプランと設定を同期しましょう。", auth_sub_register: "30秒で完了。カード不要です。",
    auth_name: "お名前", auth_first_name: "名", auth_last_name: "姓", auth_birth_date: "生年月日",
    auth_first_name_ph: "太郎", auth_last_name_ph: "山田", auth_email_ph: "you@example.com",
    auth_email: "メールアドレス", auth_password: "パスワード", auth_password_confirm: "パスワード（確認）",
    auth_switch_to_register: "アカウントをお持ちでないですか？", auth_switch_to_login: "すでにアカウントをお持ちですか？",
    auth_aside_badge: "すべてが一か所に",
    auth_aside_title: "調子を知るために6つのアプリを開くのはもう終わりです。",
    auth_aside_1: "すべてのアカウントをひと目で確認",
    auth_aside_2: "数値が下がったときに気づける",
    auth_aside_3: "投稿が伸びる時間帯がわかる",
    auth_aside_4: "トークンはサーバーではなく自分のPCに保存",
    auth_aside_foot: "開始にカードは不要です。",
    auth_logout: "ログアウト", account_upgrade: "Proにアップグレード", account_upgrade_studio: "Studioにアップグレード", account_since: "アカウント作成日: {d}",
    err_email_invalid: "有効なメールアドレスを入力してください。", err_password_short: "8文字以上で入力してください。",
    err_required: "必須項目です。", err_birth_date_future: "未来の日付は選択できません。",
    err_birth_invalid: "有効な生年月日を入力してください。", err_birth_too_young: "登録には13歳以上である必要があります。",
    err_first_name_required: "名を入力してください。", err_last_name_required: "姓を入力してください。",
    err_email_taken: "このメールアドレスのアカウントは既に存在します。", err_bad_credentials: "メールアドレスまたはパスワードが正しくありません。",
    err_session_expired: "セッションが無効または期限切れです。", err_login_required_for_plan: "プランを購入する前にログインしてください。",
    err_age_min: "{n}歳以上である必要があります。", err_password_mismatch: "パスワードが一致しません。",
    auth_forgot_password: "パスワードをお忘れですか？", reset_title: "パスワードを再設定", reset_step1_sub: "メールアドレスを入力すると6桁のコードを送信します。", reset_step2_sub: "{email} にコードを送信しました。迷惑メールフォルダもご確認ください。", reset_send_code: "コードを送信", reset_code_label: "6桁のコード", reset_new_password: "新しいパスワード", reset_confirm: "パスワードを再設定", reset_resend: "コードを再送信", reset_err_code_format: "コードは6桁で入力してください。", reset_success: "パスワードを再設定しました。ログインしました。", err_reset_invalid: "コードが無効です。", err_reset_expired: "コードの有効期限が切れました。再度リクエストしてください。", err_reset_too_many: "試行回数が多すぎます。コードを再度リクエストしてください。",
    toast_welcome: "ようこそ、{n}さん！", toast_logged_in: "おかえりなさい、{n}さん！", toast_logged_out: "ログアウトしました。",
    toast_refresh_done: "データを更新しました。", toast_export_done: "CSVを書き出しました。",
    toast_login_required: "プランを選ぶ前にログインしてください。",
    pricing_title: "必要な分だけ選べます", pricing_sub: "無料で開始。数字が重要になったらProへ。",
    pricing_monthly: "月額", pricing_yearly: "年額", pricing_save: "2か月無料",
    plan_popular: "一番人気", plan_free_cta: "無料で始める", plan_cta: "{p}を選ぶ",
    plan_current: "現在のプラン", plan_period_month: "/月", plan_period_year: "/年",
    plan_billed_yearly: "年1回 {a}€ のお支払い", plan_billed_free: "ずっと無料",
    pricing_note_ready: "Stripeによる安全な決済。いつでも解約できます。",
    pricing_note_setup: "現在お支払いはご利用いただけません。しばらくしてから再度お試しください。",
    checkout_unavailable: "決済サービスに接続できません。しばらくしてから再度お試しください。",
    plan_unknown: "無効なプランです。",
    checkout_opened: "ブラウザで決済ページを開きました。",
    licence_title: "ライセンス",
    licence_hint: "ProまたはStudioをご購入済みですか？お支払い後に届いたキーをここに貼り付けてください。",
    licence_placeholder: "SD-PRO-XXXX-XXXX-XXXX-XXXX",
    licence_activate: "有効化", licence_manage: "サブスクリプションを管理", licence_remove: "このコンピューターから削除",
    licence_state_free: "Freeプラン", licence_state_active: "{p} 有効",
    licence_state_expired: "ライセンスの確認が必要",
    licence_state_revoked: "ライセンス無効",
    licence_revoked_note: "このサブスクリプションは有効ではありません。誤りだと思われる場合はサポートにご連絡ください。",
    licence_active_on: "ライセンス有効（{k}）",
    licence_recheck_failed: "現在ライセンスを確認できません。接続をご確認ください。プランはあと数日間有効です。",
    licence_enter_key: "ライセンスキーを入力してください。",
    licence_activated: "{p} を有効化しました！", licence_removed: "このコンピューターからライセンスを削除しました。",
    license_missing: "ライセンスキーを入力してください。",
    license_not_found: "無効なキーです。すべてコピーされているかご確認ください。",
    license_inactive: "このライセンスは有効ではありません。サブスクリプションが有効な場合はサポートにご連絡ください。",
    license_service_unavailable: "確認サービスに接続できません。接続をご確認のうえ再度お試しください。",
    palette_placeholder: "移動先…", palette_empty: "結果がありません。",
    strength_labels: "弱い,弱い,普通,良い,強い",
  },
};

// L'inglese e' la lingua di partenza: il prodotto viene scaricato da
// chiunque, e l'italiano era una scelta comprensibile solo a chi l'ha
// scritto. La preferenza scelta dall'utente vive in localStorage, che la
// finestra dell'app conserva tra un avvio e l'altro (private_mode=False e
// storage_path in desktop_app.py), quindi va impostata una volta sola.
const DEFAULT_LANG = "en";
function currentLang() {
  const saved = localStorage.getItem("dashboard-lang");
  // Un codice non piu' previsto non deve inchiodare l'interfaccia su una
  // lingua inesistente: si torna al default.
  return LANGS.some(l => l.code === saved) ? saved : DEFAULT_LANG;
}
function langMeta() {
  return LANGS.find(l => l.code === currentLang()) || LANGS.find(l => l.code === DEFAULT_LANG);
}

function t(key, vars) {
  const lang = currentLang();
  // Singolare: se esiste una variante "<chiave>_one" e il conteggio è 1, è
  // quella la forma giusta. Senza, si leggeva "1 contenuti".
  if (vars && Number(vars.n) === 1) {
    const one = `${key}_one`;
    if ((I18N[lang] && I18N[lang][one]) || I18N[DEFAULT_LANG][one]) key = one;
  }
  // Se una chiave mancasse, meglio ripiegare sulla lingua predefinita che su
  // una frase italiana in mezzo a un'interfaccia inglese.
  let str = (I18N[lang] && I18N[lang][key]) || I18N[DEFAULT_LANG][key] || key;
  if (vars) Object.keys(vars).forEach(k => { str = str.split(`{${k}}`).join(vars[k]); });
  return str;
}

/** Messaggio arrivato dal server. Il backend manda un codice quando il testo
 *  deve seguire la lingua dell'utente (es. "unavail_x_no_read_api"); se non
 *  corrisponde a nessuna chiave, t() restituisce la stringa originale, quindi
 *  i messaggi liberi (errori di piattaforma) passano comunque intatti. */
function tServer(msg, vars) {
  if (!msg) return "";
  return t(String(msg), vars);
}

/** Traduce se la chiave esiste, altrimenti restituisce il testo gia' pronto
 *  arrivato dal server. Serve per la diagnostica: se una chiave manca si
 *  vede la frase di prima invece di un codice grezzo a schermo. */
function tOr(key, vars, fallback) {
  const lang = currentLang();
  const exists = (I18N[lang] && I18N[lang][key]) || I18N[DEFAULT_LANG][key];
  return exists ? t(key, vars) : (fallback || "");
}

/** Campo di una voce di diagnostica, tradotto quando il backend ha mandato
 *  un codice. Il testo degli errori di piattaforma resta quello originale:
 *  e' il messaggio grezzo dell'API, non una frase nostra da tradurre. */
function diagField(issue, field, suffix) {
  if (!issue.code) return issue[field] || "";
  // Gli errori di piattaforma cambiano categoria e prossimo passo ma hanno
  // tutti lo stesso titolo: una chiave sola invece di nove uguali.
  if (suffix === "title" && issue.code.startsWith("diagerr_")) {
    return tOr("diag_unreachable_title", issue.params || {}, issue.title);
  }
  return tOr(`${issue.code}_${suffix}`, issue.params || {}, issue[field]);
}

function applyStaticTranslations() {
  // Anche l'attributo lang deve seguire la scelta: e' quello su cui si
  // regolano lettori di schermo e correttore ortografico, e restava fisso
  // sull'italiano scritto nell'HTML.
  document.documentElement.lang = currentLang();
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  // I placeholder seguono la stessa strada del testo: dichiarati nell'HTML
  // con data-i18n-placeholder invece di essere scritti a mano in una lingua
  // sola (ed evitando di riempirli con dati personali reali).
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    el.title = t(el.dataset.i18nTitle);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach(el => {
    el.setAttribute("aria-label", t(el.dataset.i18nAria));
  });
}

// ---------- Utility ----------
const lastRefreshEl = document.getElementById("last-refresh");
const btnRefresh = document.getElementById("btn-refresh");
const progressWrap = document.getElementById("refresh-progress");
const progressBar = document.getElementById("refresh-progress-bar");
const progressLabel = document.getElementById("refresh-progress-label");

let currentSnapshot = {};
let currentUser = null;
let plansData = null;
let billingCycle = "monthly";
let appConfig = null;

/** Piattaforme realmente attive: nella build destinata ai clienti i moduli
 *  personali (CertSprint) non esistono e non devono comparire da nessuna
 *  parte - ne' in sidebar, ne' in panoramica, ne' in diagnostica. */
function activePlatforms() {
  const enabled = appConfig?.platforms;
  return Object.keys(PLATFORM_LABELS).filter(p => !enabled || enabled.includes(p));
}

/** Nasconde i richiami al collegamento per le piattaforme che in questa
 *  build non sono collegabili: un pulsante che non puo' funzionare e'
 *  peggio della sua assenza. */
function applyConnectAvailability() {
  const modes = connectionsData?.modes || {};
  document.querySelectorAll("[data-link-platform]").forEach(btn => {
    const mode = modes[btn.dataset.linkPlatform];
    btn.classList.toggle("hidden", !mode || mode === "unavailable" || mode === "unsupported");
  });
}

function applyConfig() {
  const enabled = appConfig?.platforms || [];
  Object.keys(PLATFORM_LABELS).forEach(p => {
    const hide = enabled.length > 0 && !enabled.includes(p);
    document.querySelectorAll(`.nav-item[data-section="${p}"]`).forEach(el => el.classList.toggle("hidden", hide));
    const section = document.getElementById(`section-${p}`);
    if (section && hide) section.classList.add("hidden");
  });
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function fmtNum(n) {
  if (n === undefined || n === null) return "–";
  return new Intl.NumberFormat(langMeta().locale).format(n);
}

function fmtTime(ts) {
  if (!ts) return t("time_never");
  return new Date(ts * 1000).toLocaleString(langMeta().locale);
}

function fmtDateOnly(ts) {
  if (!ts) return t("time_never");
  return new Date(ts * 1000).toLocaleDateString(langMeta().locale);
}

function fmtTimeAgo(ts) {
  if (!ts) return t("time_never");
  const diff = Math.max(0, Math.floor(Date.now() / 1000) - ts);
  if (diff < 60) return t("time_seconds_ago");
  if (diff < 3600) return t("time_min_ago", { n: Math.floor(diff / 60) });
  if (diff < 86400) return t("time_hours_ago", { n: Math.floor(diff / 3600) });
  return t("time_days_ago", { n: Math.floor(diff / 86400) });
}

function lastPublishTs(items, field, isUnix) {
  if (!items || !items.length) return null;
  let max = null;
  for (const it of items) {
    const raw = it[field];
    if (!raw) continue;
    const ts = isUnix ? raw : Math.floor(new Date(raw).getTime() / 1000);
    if (ts && (max === null || ts > max)) max = ts;
  }
  return max;
}

// ---------- Toast ----------
function toast(message, kind = "") {
  const host = document.getElementById("toasts");
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  host.appendChild(el);
  setTimeout(() => {
    el.classList.add("out");
    setTimeout(() => el.remove(), 250);
  }, 3600);
}

// ---------- Sparkline ----------
/** Curva Catmull-Rom convertita in bezier cubiche: passa esattamente per
 *  ogni punto (a differenza di una bezier "a occhio"), ma senza gli spigoli
 *  a zig-zag di una polilinea. */
function smoothPath(pts) {
  if (pts.length < 3) {
    return pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  }
  let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i === 0 ? 0 : i - 1];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}

/** Placeholder per le card "By platform" senza dati: una riga tratteggiata
 *  al posto dello spazio che occuperebbe la sparkline, invece del testo
 *  corsivo "No data" ripetuto identico in ogni card vuota - a colpo
 *  d'occhio si legge come "in attesa", non come un errore da leggere. */
function waitingPlaceholder(labelKey) {
  return `<div class="card-waiting">
    <svg class="waiting-line" viewBox="0 0 200 20" preserveAspectRatio="none">
      <line x1="2" y1="10" x2="198" y2="10" vector-effect="non-scaling-stroke"/>
    </svg>
    <span class="waiting-label">${t(labelKey)}</span>
  </div>`;
}

function sparkline(series, gradId) {
  if (!series || series.length < 2) return "";
  const w = 200, h = 34, pad = 3;
  const vals = series.map(p => p.v);
  const min = Math.min(...vals), max = Math.max(...vals);
  const range = (max - min) || 1;
  const pts = series.map((p, i) => {
    const x = (i / (series.length - 1)) * w;
    const y = h - pad - ((p.v - min) / range) * (h - pad * 2);
    return [x, y];
  });
  const line = smoothPath(pts);
  const area = `${line} L${w},${h} L0,${h} Z`;
  const [lx, ly] = pts[pts.length - 1];
  const gid = `spark-grad-${gradId || Math.random().toString(36).slice(2)}`;
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
    <defs>
      <linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.22"/>
        <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path class="spark-area" d="${area}" fill="url(#${gid})"/>
    <path class="spark-line" d="${line}" vector-effect="non-scaling-stroke"/>
    <circle class="spark-dot" cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="2.5" vector-effect="non-scaling-stroke"/>
  </svg>`;
}

function deltaChip(delta, invert = false) {
  if (!delta || delta.diff === 0) {
    return `<span class="delta flat">■ 0</span>`;
  }
  const positive = delta.diff > 0;
  // Per la latenza "in aumento" e' un peggioramento: invert ribalta i colori.
  const good = invert ? !positive : positive;
  const arrow = positive ? "▲" : "▼";
  const pct = delta.pct === null || delta.pct === undefined
    ? `${positive ? "+" : ""}${fmtNum(delta.diff)}`
    : `${positive ? "+" : ""}${delta.pct}%`;
  return `<span class="delta ${good ? "up" : "down"}">${arrow} ${pct}</span>`;
}

// ---------- Tema ----------
const THEMES = [
  { id: "dark", name: "Dark", colors: ["#0f1115", "#7c8cff", "#171a21"] },
  { id: "light", name: "Light", colors: ["#f4f5f8", "#5b6cf0", "#ffffff"] },
  { id: "midnight", name: "Midnight", colors: ["#080b18", "#5ee6ff", "#10142a"] },
  { id: "sunset", name: "Sunset", colors: ["#1a1210", "#ff8a5c", "#241a17"] },
  { id: "forest", name: "Forest", colors: ["#0e1712", "#4ade80", "#16211a"] },
  { id: "rose", name: "Rose", colors: ["#180f14", "#f472b6", "#221620"] },
  { id: "ocean", name: "Ocean", colors: ["#071620", "#38bdf8", "#0e2130"] },
  { id: "mono", name: "Mono", colors: ["#121212", "#d4d4d4", "#1c1c1c"] },
  { id: "amber", name: "Amber", colors: ["#1a140a", "#f5a623", "#241c0f"] },
  { id: "indigo", name: "Indigo", colors: ["#0f0f22", "#8b7cff", "#17173a"] },
  { id: "teal", name: "Teal", colors: ["#081815", "#2dd4bf", "#0f2420"] },
  { id: "clay", name: "Clay", colors: ["#1c1210", "#e2694c", "#271a17"] },
];

function renderThemeGrid() {
  const grid = document.getElementById("theme-grid");
  const current = localStorage.getItem("dashboard-theme") || "dark";
  grid.innerHTML = THEMES.map(th => `
    <button class="theme-row ${th.id === current ? "active" : ""}" data-theme="${th.id}">
      <span class="theme-dot" style="background:${th.colors[1]}"></span>
      <span class="theme-name">${th.name}</span>
      ${th.id === current ? `<span class="check">${icon("check")}</span>` : ""}
    </button>`).join("");
  grid.querySelectorAll(".theme-row").forEach(row => {
    row.addEventListener("click", () => { applyTheme(row.dataset.theme); renderThemeGrid(); });
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("dashboard-theme", theme);
}

function renderLanguageGrid() {
  const grid = document.getElementById("language-grid");
  if (!grid) return;
  const current = currentLang();
  grid.innerHTML = LANGS.map(l => `
    <button class="theme-card ${l.code === current ? "active" : ""}" data-lang="${l.code}">
      ${l.code === current ? `<span class="check">${icon("check")}</span>` : ""}
      <div class="swatch-row"><span class="lang-badge">${l.code.toUpperCase()}</span></div>
      <div class="theme-name">${l.name}</div>
    </button>`).join("");
  grid.querySelectorAll(".theme-card").forEach(card => {
    card.addEventListener("click", () => {
      localStorage.setItem("dashboard-lang", card.dataset.lang);
      applyStaticTranslations();
      renderLanguageGrid();
      renderAuthTexts();
      if (currentSnapshot) renderAll(currentSnapshot);
      if (plansData) renderPlans();
      if (connectionsData) { renderConnections(); applyConnectAvailability(); }
    });
  });
}

// ---------- Navigazione ----------
function goTo(section) {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.section === section));
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  const target = document.getElementById(`section-${section}`);
  if (target) target.classList.add("active");
  if (section === "pricing" && !plansData) loadPlans();
}

document.querySelectorAll("[data-section]").forEach(btn => {
  btn.addEventListener("click", () => goTo(btn.dataset.section));
});
document.querySelectorAll("[data-goto]").forEach(btn => {
  btn.addEventListener("click", () => goTo(btn.dataset.goto));
});

// ---------- Overview ----------
function countAccounts(snapshot) {
  let n = 0;
  (snapshot.youtube?.channels || []).forEach(c => { if (c.ok) n++; });
  (snapshot.instagram?.accounts || []).forEach(a => { if (a.ok) n++; });
  (snapshot.tiktok?.accounts || []).forEach(a => { if (a.ok) n++; });
  return n;
}

function tile(label, value, foot, suffix) {
  return `<div class="hero-tile">
    <div class="tile-label">${label}</div>
    <div class="tile-value">${value}${suffix ? `<small>${suffix}</small>` : ""}</div>
    ${foot ? `<div class="tile-foot">${foot}</div>` : ""}
  </div>`;
}

function renderHeroTiles(snapshot) {
  const host = document.getElementById("hero-tiles");
  const trends = snapshot.trends || {};
  const analytics = snapshot.analytics || {};

  // Segue snapshot.analytics (gia' calcolato server-side su tutte le
  // piattaforme) invece di risommare a mano solo YouTube e Instagram: la
  // versione precedente escludeva silenziosamente TikTok da follower ed
  // engagement, mentre Analytics lo includeva gia' correttamente - stesso
  // account, due totali diversi a seconda della sezione aperta.
  const followers = Object.values(analytics.followers_per_platform || {}).reduce((s, n) => s + n, 0);
  const engagement = analytics.engagement?.interactions || 0;

  const recentViews = (snapshot.youtube?.channels || []).reduce((s, c) => s + (c.recent_views_last10 || 0), 0)
    + (snapshot.instagram?.accounts || []).reduce((s, a) => s + ((a.totals_last_n || {}).views || 0), 0)
    + (snapshot.tiktok?.accounts || []).reduce((s, a) => s + ((a.totals_last_n || {}).views || 0), 0);

  const score = snapshot.diagnostics?.score;
  const ytDelta = trends.youtube?.primary?.delta;
  const igDelta = trends.instagram?.primary?.delta;
  const followerDelta = ytDelta || igDelta;

  host.innerHTML =
    tile(t("tile_followers"), fmtNum(followers), followerDelta ? deltaChip(followerDelta) : "")
    + tile(t("tile_recent_views"), fmtNum(recentViews), t("tile_recent_views_foot"))
    + tile(t("tile_engagement"), fmtNum(engagement), t("tile_engagement_foot"))
    + tile(t("tile_health"), score ?? "–", `${countAccounts(snapshot)} ${t("tile_accounts_foot")}`, score != null ? "%" : "");
}

function renderOverview(snapshot) {
  const grid = document.getElementById("overview-grid");
  const trends = snapshot.trends || {};

  const sub = document.getElementById("overview-sub");
  const n = countAccounts(snapshot);
  sub.textContent = n ? t("overview_sub", { n, p: activePlatforms().length }) : t("overview_sub_empty");
  renderHeroTiles(snapshot);
  renderTopContent(snapshot);

  // Stesso stato gia' calcolato per i pallini della sidebar, riletto qui
  // cosi' non serve aprire Diagnostics per capire perche' una card e' ferma.
  const statusByPlatform = platformStatusMap(snapshot.diagnostics?.issues);

  grid.innerHTML = activePlatforms().map(key => {
    const data = snapshot[key];
    const tr = trends[key]?.primary;
    let body;
    if (!data) {
      body = waitingPlaceholder("waiting_for_data");
    } else if (key === "youtube") {
      const total = (data.channels || []).reduce((s, c) => s + (c.subscribers || 0), 0);
      body = `<div class="stat-row"><span class="label">${t("label_subscribers_total")}</span><span class="value">${fmtNum(total)}</span></div>
              <div class="sub-item"><span class="name">${t("label_channels")}</span><span>${(data.channels || []).length}</span></div>`;
    } else if (key === "instagram") {
      const total = (data.accounts || []).reduce((s, a) => s + (a.followers || 0), 0);
      body = `<div class="stat-row"><span class="label">${t("label_followers_total")}</span><span class="value">${fmtNum(total)}</span></div>
              <div class="sub-item"><span class="name">${t("label_accounts")}</span><span>${(data.accounts || []).length}</span></div>`;
    } else if (key === "tiktok") {
      const ok = (data.accounts || []).filter(a => a.ok).length;
      body = ok
        ? `<div class="stat-row"><span class="label">${t("label_views")}</span><span class="value">${fmtNum((data.accounts || []).reduce((s, a) => s + ((a.totals_last_n || {}).views || 0), 0))}</span></div>`
        : waitingPlaceholder("empty_not_configured");
    } else if (key === "x") {
      body = `<div class="stat-row"><span class="label">${t("label_credentials")}</span><span class="value">${data.credentials_configured ? t("val_ok") : t("val_missing")}</span></div>`;
    } else if (key === "certsprint") {
      const up = data.uptime || {};
      body = `<div class="stat-row"><span class="label">${t("label_site")}</span><span class="value">${up.up ? t("val_online") : t("val_down")}</span></div>`;
    }

    const spark = tr && tr.series.length > 1 ? sparkline(tr.series, key) : "";
    const chip = tr && tr.delta ? deltaChip(tr.delta, key === "certsprint") : "";
    const statusDot = `<span class="nav-dot ${statusDotClass(statusByPlatform[key])}" title="${esc(t("platform_status_" + (statusByPlatform[key] || "grey")))}"></span>`;
    return `<div class="card">
      <div class="card-head">
        <h2><span class="card-ico">${PLATFORM_ICONS[key]}</span>${PLATFORM_LABELS[key]}${statusDot}</h2>
        ${chip}
      </div>
      ${body}
      ${spark}
    </div>`;
  }).join("");
}

/** Il contenuto migliore del periodo, gia' calcolato da analytics.py e mai
 *  mostrato fuori dalla sezione Analytics: su Overview e' l'informazione a
 *  colpo d'occhio piu' utile che manca - "cosa ha funzionato" senza dover
 *  cambiare sezione per scoprirlo. */
function renderTopContent(snapshot) {
  const host = document.getElementById("top-content");
  if (!host) return;
  const top = (snapshot.analytics?.top_posts || [])[0];
  if (!top || !top.views) { host.classList.add("hidden"); return; }
  host.classList.remove("hidden");
  host.innerHTML = `
    <span class="top-content-label">${t("overview_top_content")}</span>
    <span class="platform-chip">${esc(PLATFORM_LABELS[top.platform] || top.platform)}</span>
    <span class="top-content-title">${esc(top.title || "")}</span>
    <span class="top-content-views">${fmtNum(top.views)} ${t("label_views")}</span>`;
}

// ---------- Dettagli ----------
/** Bottone "Collega account" da mostrare dentro gli stati vuoti o di
 *  errore: e' li' che serve davvero, non solo in cima alla sezione. */
function connectCta(platform) {
  const mode = connectionsData?.modes?.[platform];
  if (!mode || mode === "unavailable" || mode === "unsupported") return "";
  return `<button class="btn-analyze inline-connect" data-inline-connect="${platform}">
    <span class="link-ico">\u{1F517}</span> ${t("btn_link_account_full")}</button>`;
}

function wireInlineConnect(root) {
  if (!root) return;
  root.querySelectorAll("[data-inline-connect]").forEach(btn => {
    btn.addEventListener("click", () => openConnectModal(btn.dataset.inlineConnect));
  });
}

function renderYoutubeDetail(data) {
  const el = document.getElementById("youtube-detail");
  if (!data) { el.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }
  const channels = data.channels || [];
  if (!channels.length) {
    el.innerHTML = `<div class="empty">${t("empty_configure_yt")}</div>${connectCta("youtube")}`;
    wireInlineConnect(el); return;
  }
  el.innerHTML = channels.map(c => {
    if (!c.ok) return `<div class="entity-block"><div class="entity-title">${esc(c.name)}</div><div class="error-text">${esc(c.error)}</div>${connectCta("youtube")}</div>`;
    const lastPub = lastPublishTs(c.recent_videos, "published", false);
    const viewsLag = c.total_views === 0 && (c.recent_views_last10 || 0) > 0;
    return `<div class="entity-block">
      <div class="entity-title">${esc(c.name)} <span class="muted">(${esc(c.title)})</span></div>
      <div class="stat-row"><span class="label">${t("label_subscribers")}</span><span class="value">${fmtNum(c.subscribers)}</span></div>
      <div class="stat-row"><span class="label">${t("label_total_views")}</span><span class="value">${fmtNum(c.total_views)}</span></div>
      ${viewsLag ? `<div class="rank-meta" style="margin:-4px 0 6px;">ℹ️ ${t("yt_total_views_lag_note")}</div>` : ""}
      <div class="sub-item"><span class="name">${t("label_videos_published")}</span><span>${fmtNum(c.video_count)}</span></div>
      <div class="sub-item"><span class="name">${t("label_recent_views")}</span><span>${fmtNum(c.recent_views_last10)}</span></div>
      <div class="sub-item"><span class="name">${t("label_last_publish")}</span><span>${lastPub ? fmtTime(lastPub) : t("label_never_published")}</span></div>
    </div>`;
  }).join("");
}

function renderInstagramDetail(data) {
  const el = document.getElementById("instagram-detail");
  if (!data) { el.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }
  const accounts = data.accounts || [];
  if (!accounts.length) {
    el.innerHTML = `<div class="empty">${t("empty_configure_ig")}</div>${connectCta("instagram")}`;
    wireInlineConnect(el); return;
  }
  el.innerHTML = accounts.map(a => {
    if (!a.ok) return `<div class="entity-block"><div class="entity-title">${esc(a.name)}</div><div class="error-text">${esc(a.error)}</div>${connectCta("instagram")}</div>`;
    const tot = a.totals_last_n || {};
    const lastPub = lastPublishTs(a.recent_posts, "timestamp", false);
    return `<div class="entity-block">
      <div class="entity-title">${esc(a.name)}</div>
      <div class="stat-row"><span class="label">${t("label_followers")}</span><span class="value">${fmtNum(a.followers)}</span></div>
      <div class="sub-item"><span class="name">${t("label_views_recent")}</span><span>${fmtNum(tot.views)}</span></div>
      <div class="sub-item"><span class="name">${t("label_likes")}</span><span>${fmtNum(tot.likes)}</span></div>
      <div class="sub-item"><span class="name">${t("label_comments")}</span><span>${fmtNum(tot.comments)}</span></div>
      <div class="sub-item"><span class="name">${t("label_last_publish")}</span><span>${lastPub ? fmtTime(lastPub) : t("label_never_published")}</span></div>
    </div>`;
  }).join("");
}

function renderTiktokDetail(data) {
  const el = document.getElementById("tiktok-detail");
  if (!data) { el.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }
  const accounts = data.accounts || [];
  if (!accounts.length) {
    el.innerHTML = `<div class="empty">${t("empty_configure_tt")}</div>${connectCta("tiktok")}`;
    wireInlineConnect(el); return;
  }
  el.innerHTML = accounts.map(a => {
    if (a.not_configured) return `<div class="entity-block"><div class="entity-title">${esc(a.name)}</div><div class="empty">${t("empty_not_configured")}</div>${connectCta("tiktok")}</div>`;
    if (!a.ok) return `<div class="entity-block"><div class="entity-title">${esc(a.name)}</div><div class="error-text">${esc(a.error)}</div>${connectCta("tiktok")}</div>`;
    const tot = a.totals_last_n || {};
    const lastPub = lastPublishTs(a.recent_videos, "create_time", true);
    return `<div class="entity-block">
      <div class="entity-title">${esc(a.name)}</div>
      <div class="stat-row"><span class="label">${t("label_views")}</span><span class="value">${fmtNum(tot.views)}</span></div>
      <div class="sub-item"><span class="name">${t("label_likes_comments_shares")}</span><span>${fmtNum(tot.likes)} / ${fmtNum(tot.comments)} / ${fmtNum(tot.shares)}</span></div>
      <div class="sub-item"><span class="name">${t("label_last_publish")}</span><span>${lastPub ? fmtTime(lastPub) : t("label_never_published")}</span></div>
    </div>`;
  }).join("");
}

function renderXDetail(data) {
  const el = document.getElementById("x-detail");
  if (!data) { el.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }
  el.innerHTML = `<div class="stat-row"><span class="label">${t("label_credentials")}</span><span class="value">${data.credentials_configured ? t("val_ok") : t("val_missing")}</span></div>
    <div class="sub-item">${esc(data.limitation || "")}</div>`;
}

function renderCertsprintDetail(data) {
  const el = document.getElementById("certsprint-detail");
  if (!data) { el.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }
  const lint = data.eslint || {};
  const uptime = data.uptime || {};
  const vulns = (data.npm_audit || {}).vulnerabilities || {};
  el.innerHTML = `
    <div class="stat-row"><span class="label">${t("label_site")}</span><span class="value">${uptime.up ? t("val_online_latency", { ms: uptime.latency_ms }) : t("val_down_error")}</span></div>
    <div class="stat-row"><span class="label">${t("label_npm_vulns")}</span><span class="value">${fmtNum(vulns.critical || 0)}C / ${fmtNum(vulns.high || 0)}H / ${fmtNum(vulns.moderate || 0)}M</span></div>
    <div class="sub-item"><span class="name">${t("label_eslint")}</span><span>${lint.configured ? t("val_errors_warnings", { e: fmtNum(lint.errors), w: fmtNum(lint.warnings) }) : t("val_not_configured")}</span></div>`;
}

const DETAIL_RENDERERS = {
  youtube: renderYoutubeDetail,
  instagram: renderInstagramDetail,
  tiktok: renderTiktokDetail,
  x: renderXDetail,
  certsprint: renderCertsprintDetail,
};

// ---------- Insight ----------
const INSIGHT_ICONS = { good: icon("trend-up"), warn: icon("alert-yellow"), info: icon("info") };

/** Le osservazioni arrivano gia' dentro lo snapshot (sono calcolate in
 *  locale, costano zero) quindi si disegnano da sole ad ogni render: niente
 *  pulsante da premere e, soprattutto, niente riquadro che resta appeso con
 *  un errore vecchio quando si cambia sezione. */
function showInsightBox(platform, items) {
  const box = document.getElementById(`${platform}-insight`);
  if (!box) return;
  if (!items || !items.length) { box.classList.add("hidden"); box.innerHTML = ""; return; }
  box.classList.remove("hidden");
  box.innerHTML = `<ul>${items.map(i => {
    // I conteggi arrivano come numeri grezzi: vanno formattati con i
    // separatori della lingua scelta, non lasciati come "10924".
    const params = {};
    Object.entries(i.params || {}).forEach(([k, v]) => {
      params[k] = typeof v === "number" && Number.isFinite(v) ? fmtNum(v) : v;
    });
    const text = i.code ? tOr(i.code, params, i.text) : (i.text || "");
    return `<li class="insight-${esc(i.kind || "info")}"><span class="insight-ico">${INSIGHT_ICONS[i.kind] || INSIGHT_ICONS.info}</span>${esc(text)}</li>`;
  }).join("")}</ul>`;
}

// ---------- Analitiche ----------
// Engagement per piattaforma, con il confronto rispetto a chi ha un
// pubblico della stessa taglia. Il confronto compare solo dove regge:
// senza follower noti o con troppi pochi non si dice niente, invece di
// dare un giudizio costruito sul nulla.
function renderEngagement(a, el) {
  if (!el) return;
  const perPlatform = a.engagement_per_platform || {};
  const platforms = Object.keys(perPlatform);
  if (!platforms.length) { el.innerHTML = ""; return; }

  const benchByPlatform = {};
  (a.benchmarks || []).forEach(b => { benchByPlatform[b.platform] = b; });

  el.innerHTML = platforms.map(p => {
    const m = perPlatform[p];
    const b = benchByPlatform[p];
    const nome = PLATFORM_LABELS[p] || p;

    let verdetto = `<span class="eng-verdict none">${esc(t("eng_no_benchmark"))}</span>`;
    if (b) {
      const cls = b.state === "above" ? "good" : b.state === "below" ? "bad" : "ok";
      const key = b.state === "above" ? "eng_above" : b.state === "below" ? "eng_below" : "eng_inline";
      verdetto = `<span class="eng-verdict ${cls}">${esc(t(key, { e: b.expected }))}</span>`;
    }

    return `
      <div class="eng-card">
        <div class="eng-head">
          <span class="eng-platform">${esc(nome)}</span>
          <span class="eng-rate">${m.rate}%</span>
        </div>
        ${verdetto}
        <div class="eng-detail">
          <span title="${esc(t("eng_saves_hint"))}">${esc(t("eng_saves"))} <b>${m.save_rate}%</b></span>
          <span title="${esc(t("eng_shares_hint"))}">${esc(t("eng_shares"))} <b>${m.share_rate}%</b></span>
        </div>
      </div>`;
  }).join("");
}

// Mappa giorno x ora. Si disegnano solo i giorni in cui hai davvero
// pubblicato: una griglia 7x24 quasi tutta vuota nasconde le poche celle
// che contano invece di metterle in evidenza.
function renderHeatmap(a, el) {
  if (!el) return;
  const celle = a.heatmap || [];
  if (celle.length < 3) {
    el.innerHTML = `<div class="empty">${t("heatmap_not_enough")}</div>`;
    return;
  }

  const giorni = [...new Set(celle.map(c => c.weekday))].sort((x, y) => x - y);
  const max = Math.max(...celle.map(c => c.avg_views));
  const perChiave = {};
  celle.forEach(c => { perChiave[`${c.weekday}-${c.hour}`] = c; });

  const nomiGiorni = t("weekday_short").split(",");

  el.innerHTML = `
    <div class="heat-grid" style="grid-template-columns: auto repeat(24, 1fr)">
      <span class="heat-corner"></span>
      ${Array.from({ length: 24 }, (_, h) =>
        `<span class="heat-hour">${h % 6 === 0 ? String(h).padStart(2, "0") : ""}</span>`).join("")}
      ${giorni.map(g => `
        <span class="heat-day">${esc(nomiGiorni[g] || g)}</span>
        ${Array.from({ length: 24 }, (_, h) => {
          const c = perChiave[`${g}-${h}`];
          if (!c) return `<span class="heat-cell empty-cell"></span>`;
          // Radice quadrata: senza, un solo contenuto molto virale
          // schiaccia tutte le altre celle a un grigio indistinguibile.
          const intensita = max > 0 ? Math.sqrt(c.avg_views / max) : 0;
          const titolo = t("heatmap_cell", {
            d: nomiGiorni[g] || g, h: String(h).padStart(2, "0"),
            v: fmtNum(c.avg_views), n: c.count,
          });
          return `<span class="heat-cell" style="opacity:${(0.15 + intensita * 0.85).toFixed(2)}" title="${esc(titolo)}"></span>`;
        }).join("")}
      `).join("")}
    </div>`;
}

/** Contenuti sopra/sotto la propria media: gia' calcolato da analytics.py
 *  (confronto con se stessi, non con un benchmark di settore che non
 *  conosce il tuo pubblico) e finora mai mostrato da nessuna parte -
 *  esattamente il tipo di "cosa ha funzionato" utile a colpo d'occhio. */
function renderOutliers(a) {
  const host = document.getElementById("outliers-panel");
  const hint = document.getElementById("outliers-hint");
  if (!host) return;
  const outliers = a.outliers || {};
  const over = outliers.over || [];
  const under = outliers.under || [];
  if (!over.length && !under.length) {
    host.innerHTML = `<div class="empty">${t("analytics_outliers_empty")}</div>`;
    if (hint) hint.textContent = "";
    return;
  }
  if (hint) hint.textContent = t("analytics_outliers_hint", { v: fmtNum(outliers.avg || 0) });
  const row = (o, positive) => `
    <div class="outlier-row">
      <span class="platform-chip">${esc(PLATFORM_LABELS[o.platform] || o.platform)}</span>
      <span class="outlier-title">${esc(o.title || t("analytics_untitled"))}</span>
      <span class="delta ${positive ? "up" : "down"}">${positive ? "▲" : "▼"} ${positive ? "+" : ""}${o.delta_pct}%</span>
    </div>`;
  host.innerHTML = over.map(o => row(o, true)).join("") + under.map(o => row(o, false)).join("");
}

function renderAnalytics(a) {
  const topEl = document.getElementById("top-posts-list");
  const hoursEl = document.getElementById("best-hours-list");
  const lastEl = document.getElementById("analytics-last-refresh");
  if (lastEl) {
    lastEl.textContent = a && a.last_refresh_at
      ? t("analytics_last_refresh", { t: fmtTimeAgo(a.last_refresh_at), d: fmtTime(a.last_refresh_at) })
      : t("analytics_last_refresh_never");
  }
  const tilesEl = document.getElementById("analytics-tiles");
  const chartEl = document.getElementById("hours-chart");

  const engEl = document.getElementById("engagement-cards");
  const heatEl = document.getElementById("heatmap-chart");

  if (!a || !a.total_items_analyzed) {
    const empty = `<div class="empty">${t("analytics_empty")}</div>`;
    topEl.innerHTML = empty; hoursEl.innerHTML = empty;
    tilesEl.innerHTML = ""; chartEl.innerHTML = "";
    if (engEl) engEl.innerHTML = "";
    if (heatEl) heatEl.innerHTML = "";
    const outliersEl = document.getElementById("outliers-panel");
    const outliersHint = document.getElementById("outliers-hint");
    if (outliersEl) outliersEl.innerHTML = "";
    if (outliersHint) outliersHint.textContent = "";
    return;
  }

  renderEngagement(a, engEl);
  renderHeatmap(a, heatEl);
  renderOutliers(a);

  // Tessere di riepilogo
  const best = a.best_hours[0];
  const bestPlatform = Object.entries(a.per_platform || {})
    .sort((x, y) => y[1].views - x[1].views)[0];
  // La media si calcola sui contenuti che hanno davvero dati: dividere per
  // tutti (compresi quelli ancora a zero views) da' un numero corretto ma
  // che l'utente legge come "quanto rende un mio contenuto", e non lo e'.
  const avgViews = a.avg_views_per_item ?? Math.round((a.total_views || 0) / a.total_items_analyzed);
  const withViews = a.items_with_views ?? a.total_items_analyzed;

  tilesEl.innerHTML =
    tile(t("tile_analyzed"), fmtNum(a.total_items_analyzed), t("tile_analyzed_foot"))
    + tile(t("tile_avg_per_post"), fmtNum(avgViews), t("tile_avg_per_post_foot_n", { n: fmtNum(withViews) }))
    + tile(t("tile_best_hour"), best ? `${String(best.hour).padStart(2, "0")}:00` : "–",
           best ? t("tile_best_hour_foot", { v: fmtNum(best.avg_views) }) : t("tile_best_hour_insufficient"))
    + tile(t("tile_best_platform"), bestPlatform ? PLATFORM_LABELS[bestPlatform[0]] || bestPlatform[0] : "–",
           bestPlatform ? t("tile_best_platform_foot", { v: fmtNum(bestPlatform[1].views) }) : "");

  // Grafico della giornata: tutte le 24 ore, con evidenziate le migliori
  const hours = a.all_hours || [];
  const maxAvg = Math.max(...hours.map(h => h.avg_views), 1);
  const topHours = new Set(a.best_hours.slice(0, 3).map(h => h.hour));
  chartEl.innerHTML = hours.map(h => {
    const pct = (h.avg_views / maxAvg) * 100;
    const cls = h.count === 0 ? "empty" : topHours.has(h.hour) ? "top" : "";
    const label = t("hours_tooltip", { h: String(h.hour).padStart(2, "0"), v: fmtNum(h.avg_views), n: h.count });
    return `<div class="hour-col ${cls}" title="${esc(label)}">
      <div class="hour-bar" style="height:${Math.max(pct, h.count ? 4 : 1.5)}%"></div>
      <span class="hour-label">${h.hour % 3 === 0 ? String(h.hour).padStart(2, "0") : ""}</span>
    </div>`;
  }).join("");

  const maxViews = Math.max(...a.top_posts.map(p => p.views), 1);
  topEl.innerHTML = a.top_posts.map((p, idx) => `
    <div class="rank-item">
      <div class="rank-item-top">
        <span class="rank-title"><span class="rank-num">${idx + 1}</span><span class="platform-chip">${esc(p.platform)}</span>${esc(p.title || t("analytics_untitled"))}</span>
        <span class="rank-value">${fmtNum(p.views)}</span>
      </div>
      <div class="rank-bar-track"><div class="rank-bar-fill" style="width:${(p.views / maxViews) * 100}%"></div></div>
      <div class="rank-meta">${esc(p.account)}</div>
    </div>`).join("");

  // Funzione Pro: il server non manda nemmeno i dati, qui si spiega perché
  // invece di lasciare una sezione vuota senza motivo.
  if (a.hours_locked) {
    hoursEl.innerHTML = lockedBox("locked_best_hours");
    chartEl.innerHTML = "";
    wireLocked(hoursEl);
    return;
  }

  // Con pochi contenuti una classifica di fasce orarie sarebbe solo
  // l'elenco dei singoli post travestito da consiglio: meglio dire
  // apertamente quanti dati mancano.
  if (!a.best_hours.length) {
    hoursEl.innerHTML = `<div class="empty">${t("analytics_hours_insufficient", { n: a.hours_items_needed || 0 })}</div>`;
    return;
  }

  const maxHour = Math.max(...a.best_hours.map(h => h.avg_views), 1);
  hoursEl.innerHTML = a.best_hours.map((h, idx) => `
    <div class="rank-item">
      <div class="rank-item-top">
        <span class="rank-title"><span class="rank-num">${idx + 1}</span>${String(h.hour).padStart(2, "0")}:00 UTC</span>
        <span class="rank-value">${fmtNum(h.avg_views)} ${t("analytics_avg_views")}</span>
      </div>
      <div class="rank-bar-track"><div class="rank-bar-fill" style="width:${(h.avg_views / maxHour) * 100}%"></div></div>
      <div class="rank-meta">${h.count} ${t("analytics_bucket_count")}</div>
    </div>`).join("");
}

// ---------- Diagnostica ----------
let diagFilter = "all";
let lastDiag = null;

// Rosso e giallo condividevano lo stesso "!": la severita' era leggibile solo
// dal colore, che e' esattamente cio' che un daltonico non distingue. Forme
// diverse la rendono leggibile anche in scala di grigi.
const DIAG_ICONS = { red: icon("alert-red"), yellow: icon("alert-yellow"), green: icon("check") };

function renderDiagnostics(diag) {
  lastDiag = diag || lastDiag;
  const list = document.getElementById("diagnostics-list");
  const badge = document.getElementById("diag-badge");
  if (!lastDiag || !lastDiag.issues) { list.innerHTML = `<div class="empty">${t("empty_no_data")}</div>`; return; }

  const counts = lastDiag.counts || {};
  // "actionable" esclude gli inviti a collegare un account (restano
  // nell'elenco sotto, solo non gonfiano il numero d'allarme in sidebar).
  // Fallback al totale per compatibilita' con snapshot piu' vecchi in cache.
  const problems = lastDiag.actionable ?? ((counts.red || 0) + (counts.yellow || 0));
  badge.textContent = problems;
  badge.classList.toggle("hidden", problems === 0);

  // Anello del punteggio di salute. Nessun account collegato = nessun
  // punteggio da mostrare: un anello a 0% "tutto rosso" darebbe un giudizio
  // (critico) che non e' quello reale (mancano semplicemente i dati).
  const hasScore = lastDiag.score !== null && lastDiag.score !== undefined;
  const score = hasScore ? lastDiag.score : 0;
  const ring = document.getElementById("health-ring-fg");
  const circumference = 2 * Math.PI * 42;
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = hasScore ? circumference * (1 - score / 100) : 0;
  ring.style.stroke = !hasScore ? "var(--card-border)" : score >= 80 ? "var(--green)" : score >= 50 ? "var(--yellow)" : "var(--red)";
  document.getElementById("health-score-num").textContent = hasScore ? score : "–";

  const key = !hasScore ? "health_nodata" : counts.red ? "health_bad" : problems > 0 ? "health_warn" : "health_good";
  document.getElementById("health-title").textContent = t(`${key}_title`);
  document.getElementById("health-sub").textContent = hasScore ? t(`${key}_sub`, { n: problems }) : t(`${key}_sub`);
  document.getElementById("hc-red").textContent = counts.red || 0;
  document.getElementById("hc-yellow").textContent = counts.yellow || 0;
  document.getElementById("hc-green").textContent = counts.green || 0;

  // Scomposizione: quale voce sta tirando giu' il punteggio. Le voci senza
  // dati sufficienti si mostrano spente invece di sparire, cosi' si capisce
  // che esistono e cosa serve perche' contino.
  const parts = document.getElementById("health-parts");
  const partsData = lastDiag.score_parts || [];
  parts.innerHTML = partsData.map(p => {
    const noData = p.score === null || p.score === undefined;
    const cls = noData ? "nodata" : p.score >= 70 ? "good" : p.score >= 40 ? "warn" : "bad";
    // Prima si leggeva solo passandoci sopra il mouse (title="..."): su un
    // monitor secondario, guardato di striscio, un tooltip non esiste.
    const detail = p.code ? t(p.code, p.params || {}) : (p.detail || "");
    return `
      <div class="health-part ${cls}">
        <div class="health-part-head">
          <span class="health-part-name">${esc(t(`health_part_${p.key}`))}</span>
          <span class="health-part-val">${noData ? "–" : p.score}</span>
        </div>
        <div class="health-part-bar"><i style="width:${noData ? 0 : Math.max(0, Math.min(100, Number(p.score) || 0))}%"></i></div>
        ${detail ? `<div class="health-part-detail">${esc(detail)}</div>` : ""}
      </div>`;
  }).join("");

  const visible = lastDiag.issues.filter(i =>
    diagFilter === "all" ? true
      : diagFilter === "problems" ? i.severity !== "green"
      : i.severity === "green"
  );

  // Raggruppate per piattaforma: prima era un elenco unico dove il problema
  // di YouTube stava fra due di Instagram e per capire "cosa non va sul mio
  // canale" bisognava leggerlo tutto. I controlli trasversali (strategia)
  // finiscono in un gruppo a parte invece di essere attribuiti a caso.
  const gruppi = new Map();
  visible.forEach(i => {
    const g = i.platform || "_all";
    if (!gruppi.has(g)) gruppi.set(g, []);
    gruppi.get(g).push(i);
  });

  const cardHtml = i => {
    const title = diagField(i, "title", "title");
    const category = diagField(i, "category", "cat");
    const text = diagField(i, "text", "text");
    const nextStep = diagField(i, "next_step", "step");
    return `
    <div class="diag-item ${i.severity}">
      <span class="diag-icon ${i.severity}">${DIAG_ICONS[i.severity] || icon("check")}</span>
      <div class="diag-body">
        <div class="diag-head">
          <span class="diag-title">${esc(title || text)}</span>
          ${category ? `<span class="diag-category">${esc(category)}</span>` : ""}
        </div>
        ${title && text ? `<div class="diag-text">${esc(text)}</div>` : ""}
        ${nextStep && i.severity !== "green"
          ? `<div class="diag-next-step"><b>${t("diag_next_step_label")}</b> ${esc(nextStep)}</div>` : ""}
        ${i.action && i.action.type === "goto"
          ? `<button class="btn-analyze diag-action" data-goto-action="${esc(i.action.section)}">${t("diag_go_connect")}</button>` : ""}
      </div>
    </div>`;
  };

  list.innerHTML = visible.length ? [...gruppi.entries()].map(([g, voci]) => {
    const meta = CONNECT_META[g];
    const nome = g === "_all" ? t("diag_group_strategy") : (meta ? meta.name : g);
    const icona = g === "_all" ? icon("strategy") : (meta ? meta.ico : icon("info"));
    const rossi = voci.filter(v => v.severity === "red").length;
    const gialli = voci.filter(v => v.severity === "yellow").length;
    const stato = rossi ? "red" : gialli ? "yellow" : "green";
    return `
      <div class="diag-group">
        <div class="diag-group-head">
          <span class="diag-group-ico ${stato}">${icona}</span>
          <span class="diag-group-name">${esc(nome)}</span>
          <span class="diag-group-count">${voci.length}</span>
        </div>
        <div class="diag-list">${voci.map(cardHtml).join("")}</div>
      </div>`;
  }).join("")
    : `<div class="empty">${t("diag_filter_empty")}</div>`;

  list.querySelectorAll("[data-goto-action]").forEach(btn => {
    btn.addEventListener("click", () => goTo(btn.dataset.gotoAction));
  });

  activePlatforms().forEach(p => {
    const dot = document.getElementById(`dot-${p}`);
    if (!dot) return;
    dot.className = "nav-dot " + statusDotClass(platformStatusMap(lastDiag.issues)[p]);
  });
}

// Stessa lista usata dal backend (diagnostics.py) per non contare gli
// inviti "non ancora collegato" come problemi: qui distingue anche il
// pallino grigio da quello giallo/rosso.
const NUDGE_CODES = new Set(["diag_no_account", "diag_no_data", "diag_x_not_linked", "diag_not_configured"]);
// X non ha mai dati da sincronizzare (il piano free della sua API non
// espone le metriche di lettura): "credenziali presenti" non e' la stessa
// cosa di "connesso e sincronizzato" degli altri social, quindi non merita
// lo stesso verde - resta un grigio informativo anche a credenziali ok.
const INFORMATIONAL_CODES = new Set(["diag_x_linked"]);
const DOT_CLASS = { green: "ok", yellow: "warn", red: "err", grey: "grey" };

/** Peggior stato per piattaforma dagli issue di diagnostica: quattro stati
 *  distinti, non solo verde/rosso. "Non ancora collegato" (grigio) non e'
 *  lo stesso allarme di "collegato ma con un problema" (giallo/rosso) -
 *  condivisa fra il pallino in sidebar e quello sulle card di Overview,
 *  cosi' raccontano sempre la stessa storia. */
function platformStatusMap(issues) {
  const worst = {};
  (issues || []).forEach(i => {
    if (worst[i.platform] === "red") return;
    if (i.severity === "red") { worst[i.platform] = "red"; return; }
    if (NUDGE_CODES.has(i.code) || INFORMATIONAL_CODES.has(i.code)) { if (!worst[i.platform]) worst[i.platform] = "grey"; return; }
    if (i.severity === "yellow") { if (worst[i.platform] !== "red") worst[i.platform] = "yellow"; return; }
    if (!worst[i.platform] || worst[i.platform] === "grey") worst[i.platform] = "green";
  });
  return worst;
}

function statusDotClass(status) {
  return DOT_CLASS[status] || "grey";
}

document.querySelectorAll(".filter-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    diagFilter = chip.dataset.filter;
    document.querySelectorAll(".filter-chip").forEach(c => c.classList.toggle("active", c === chip));
    renderDiagnostics(null);
  });
});

// ---------- Collega account ----------
const CONNECT_META = {
  youtube: { ico: PLATFORM_ICONS.youtube, name: "YouTube" },
  instagram: { ico: PLATFORM_ICONS.instagram, name: "Instagram" },
  tiktok: { ico: PLATFORM_ICONS.tiktok, name: "TikTok" },
  x: { ico: PLATFORM_ICONS.x, name: "X" },
};

let connectionsData = null;

async function loadConnections() {
  try {
    connectionsData = await (await fetch("/api/connections")).json();
    renderConnections();
    applyConnectAvailability();
    if (currentSnapshot) renderAll(currentSnapshot);
  } catch (e) {
    document.getElementById("connect-grid").innerHTML = `<div class="empty">${esc(String(e))}</div>`;
  }
}

function renderConnections() {
  if (!connectionsData) return;
  const grid = document.getElementById("connect-grid");
  const platforms = (appConfig?.platforms || Object.keys(CONNECT_META)).filter(p => CONNECT_META[p]);

  grid.innerHTML = platforms.map(p => {
    const meta = CONNECT_META[p];
    const linked = connectionsData.connections.filter(c => c.platform === p);
    const unavailable = connectionsData.unavailable[p];

    // Un account il cui accesso e' scaduto resta elencato, ma va detto:
    // prima risultava collegato e basta, mentre la diagnostica diceva che
    // il token non valeva piu' - due schermate che si contraddicevano.
    // `locked` e' il caso diverso del database aperto su un altro computer.
    const accountsHtml = linked.length ? `<div class="connect-accounts">${linked.map(c => {
      const rotto = c.needs_reauth || c.locked;
      const motivo = c.locked ? t("connect_locked_hint") : t("connect_reauth_hint");
      return `
      <div class="connect-account ${rotto ? "broken" : ""}">
        <span class="connect-account-name">${esc(c.account_name)}</span>
        ${rotto ? `<span class="connect-account-warn" title="${esc(motivo)}">${t("connect_reauth_badge")}</span>` : ""}
        <button class="btn-unlink" data-unlink="${c.id}">${t("connect_unlink")}</button>
      </div>`;
    }).join("")}</div>` : "";

    const mode = connectionsData.modes?.[p] || "unsupported";
    const guided = mode === "guided";
    // "In arrivo" passa dalla modale, che e' l'unico posto dove il cliente
    // trova anche l'alternativa "usa la tua app". Chiamando startConnect da
    // qui il server rispondeva connect_coming_soon e si vedeva solo un
    // avviso, senza mai sapere che poteva collegarlo lo stesso.
    const action = mode === "coming_soon" ? "modal" : (guided ? "guided" : "connect");
    const cta = unavailable
      ? `<button class="btn-connect soon" disabled>${t("connect_soon")}</button>`
      : `<button class="btn-connect btn-analyze" data-${action}="${p}">${linked.length ? t("connect_add_another") : t("connect_now", { p: meta.name })}</button>`;

    const guidedPanel = guided ? `
      <div class="guided-panel hidden" id="guided-${p}">
        <div class="guided-step"><b>1.</b> ${t("guided_step1")}</div>
        <div class="guided-step"><b>2.</b> ${t("guided_step2")}</div>
        <input type="text" class="guided-input" id="guided-input-${p}" placeholder="${t("guided_placeholder")}">
        <div class="guided-actions">
          <button class="btn-ghost" data-guided-cancel="${p}">${t("guided_cancel")}</button>
          <button class="btn-analyze" data-guided-finish="${p}">${t("guided_finish")}</button>
        </div>
      </div>` : "";

    return `<div class="connect-card">
      <div class="connect-head">
        <span class="connect-logo">${meta.ico}</span>
        <div>
          <div class="connect-name">${meta.name}</div>
          <div class="connect-state ${linked.length ? "linked" : ""}">
            ${linked.length ? t("connect_linked_n", { n: linked.length }) : t("connect_not_linked")}
          </div>
        </div>
      </div>
      <div class="connect-desc">${unavailable ? esc(tServer(unavailable)) : t("connect_desc", { p: meta.name })}</div>
      ${accountsHtml}
      ${cta}
      ${guidedPanel}
    </div>`;
  }).join("");

  grid.querySelectorAll("[data-connect]").forEach(btn => {
    btn.addEventListener("click", () => startConnect(btn.dataset.connect, btn));
  });
  grid.querySelectorAll("[data-modal]").forEach(btn => {
    btn.addEventListener("click", () => openConnectModal(btn.dataset.modal));
  });
  grid.querySelectorAll("[data-guided]").forEach(btn => {
    btn.addEventListener("click", () => startGuided(btn.dataset.guided, btn));
  });
  grid.querySelectorAll("[data-guided-cancel]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById(`guided-${btn.dataset.guidedCancel}`).classList.add("hidden");
    });
  });
  grid.querySelectorAll("[data-guided-finish]").forEach(btn => {
    btn.addEventListener("click", () => finishGuided(btn.dataset.guidedFinish, btn));
  });
  grid.querySelectorAll("[data-unlink]").forEach(btn => {
    btn.addEventListener("click", () => unlinkConnection(btn.dataset.unlink));
  });
}

// ---------- Modale "Collega account" ----------
// Stesso pannello richiamabile da ogni sezione, cosi' il collegamento e'
// sempre a un clic di distanza senza dover cercare una pagina dedicata.
const connectModal = document.getElementById("connect-modal");
let cmPlatform = null;

function openConnectModal(platform) {
  cmPlatform = platform;
  const meta = CONNECT_META[platform];
  if (!meta) return;

  const linked = (connectionsData?.connections || []).filter(c => c.platform === platform);
  const unavailable = connectionsData?.unavailable?.[platform];
  // E' il backend a dire come si collega: quando la finestra dell'app puo'
  // ospitare il login, anche Instagram e TikTok diventano un solo bottone
  // e i passaggi manuali non compaiono affatto.
  const mode = connectionsData?.modes?.[platform] || "unsupported";
  const isGuided = mode === "guided";
  const isAuto = mode === "oneclick";
  const isComingSoon = mode === "coming_soon";

  // `ico` e' markup SVG: con textContent finirebbe a schermo come sorgente.
  document.getElementById("cm-logo").innerHTML = meta.ico;
  document.getElementById("cm-title").textContent = meta.name;
  document.getElementById("cm-sub").textContent = linked.length
    ? t("connect_linked_n", { n: linked.length })
    : t("connect_not_linked");

  const linkedHost = document.getElementById("cm-linked");
  linkedHost.innerHTML = linked.map(c => `
    <div class="connect-account">
      <span class="connect-account-name">${esc(c.account_name)}</span>
      <button class="btn-unlink" data-cm-unlink="${c.id}">${t("connect_unlink")}</button>
    </div>`).join("");
  linkedHost.querySelectorAll("[data-cm-unlink]").forEach(b => {
    b.addEventListener("click", async () => {
      await unlinkConnection(b.dataset.cmUnlink);
      openConnectModal(platform);
    });
  });

  document.getElementById("cm-auto").classList.toggle("hidden", !isAuto);
  document.getElementById("cm-guided").classList.toggle("hidden", !isGuided);
  document.getElementById("cm-comingsoon").classList.toggle("hidden", !isComingSoon);
  document.getElementById("cm-unavailable").classList.toggle("hidden", !unavailable);
  document.getElementById("cm-unavailable").textContent = unavailable ? tServer(unavailable) : "";
  document.getElementById("cm-auto-label").textContent = t("connect_now", { p: meta.name });
  // Il pulsante e' identico a quello di un collegamento vero: chi lo vede
  // non deve capire dal solo aspetto che non fara' nulla finche' non ci clicca.
  document.getElementById("cm-comingsoon-label").textContent = t("connect_now", { p: meta.name });
  document.getElementById("cm-comingsoon-msg").classList.add("hidden");
  // L'alternativa "usa la tua app" resta nascosta finche' non si scopre che
  // la piattaforma non e' ancora pronta: proporla prima vorrebbe dire
  // chiedere dieci minuti di configurazione a chi puo' evitarli.
  document.getElementById("cm-ownapp-offer").classList.add("hidden");

  // Chi ha gia' registrato la propria app deve poterlo vedere e disfare.
  const own = connectionsData?.own_app?.[platform];
  const ownActive = !!own?.configured;
  document.getElementById("cm-ownapp-active").classList.toggle("hidden", !ownActive);
  if (ownActive) {
    document.getElementById("cm-ownapp-active-text").textContent =
      t("sw_own_active", { id: own.client_id_hint });
    document.getElementById("cm-ownapp-remove").textContent = t("sw_own_remove");
  }

  document.getElementById("cm-paste").value = "";
  cmError("");

  connectModal.classList.remove("hidden");
}

function closeConnectModal() { connectModal.classList.add("hidden"); }

function cmError(message) {
  const box = document.getElementById("cm-error");
  box.textContent = message || "";
  box.classList.toggle("hidden", !message);
}

document.getElementById("connect-modal-close").addEventListener("click", closeConnectModal);
connectModal.addEventListener("click", e => { if (e.target === connectModal) closeConnectModal(); });

document.getElementById("cm-auto-btn").addEventListener("click", e => {
  startConnect(cmPlatform, e.currentTarget);
});

document.getElementById("cm-comingsoon-btn").addEventListener("click", async e => {
  const btn = e.currentTarget;
  const original = btn.innerHTML;
  const msg = document.getElementById("cm-comingsoon-msg");
  btn.disabled = true;
  btn.textContent = t("connect_waiting");
  msg.classList.add("hidden");
  // Un caricamento vero e proprio: se sparisse all'istante sembrerebbe un
  // pulsante finto invece di un accesso non ancora pronto.
  await sleep(1200);
  msg.textContent = t("cm_coming_soon_text");
  msg.classList.remove("hidden");
  // Solo ora si offre la scorciatoia: il cliente ha appena scoperto che
  // deve aspettare, ed e' il momento in cui gli serve saperlo.
  document.getElementById("cm-ownapp-offer").classList.remove("hidden");
  btn.disabled = false;
  btn.innerHTML = original;
});

document.getElementById("cm-open-btn").addEventListener("click", async e => {
  const btn = e.currentTarget;
  btn.disabled = true;
  cmError("");
  try {
    const resp = await (await fetch(`/api/connections/authorize/${cmPlatform}`)).json();
    if (!resp.ok) { cmError(tServer(resp.message)); return; }
    window.open(resp.url, "_blank");
    toast(t("connect_browser_opened"));
  } catch (err) {
    cmError(String(err));
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("cm-finish").addEventListener("click", async e => {
  const btn = e.currentTarget;
  const pasted = document.getElementById("cm-paste").value.trim();
  if (!pasted) { cmError(t("guided_paste_needed")); return; }
  btn.disabled = true;
  cmError("");
  try {
    const resp = await (await fetch(`/api/connections/finish/${cmPlatform}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pasted }),
    })).json();
    if (!resp.ok) { cmError(tServer(resp.message)); return; }
    toast(t("connect_success", { n: resp.account || "" }), "ok");
    closeConnectModal();
    await loadConnections();
    await refreshAll();
  } catch (err) {
    cmError(String(err));
  } finally {
    btn.disabled = false;
  }
});

document.querySelectorAll("[data-link-platform]").forEach(btn => {
  btn.addEventListener("click", () => openConnectModal(btn.dataset.linkPlatform));
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !connectModal.classList.contains("hidden")) closeConnectModal();
});


// ---------- "Usa la tua app": procedura guidata ----------
//
// Instagram e TikTok non chiedono nessuna revisione a chi collega l'account
// con cui ha registrato l'app. Registrarne una richiede pero' di muoversi in
// due pannelli per sviluppatori pieni di opzioni che non c'entrano: qui il
// percorso e' ridotto a un passo alla volta, con il pulsante che apre la
// pagina giusta e il valore da incollare gia' pronto negli appunti.
//
// `open` apre una pagina, `copy` mostra un valore da copiare, `fields` e'
// l'ultimo passo con le due credenziali. Il testo di ogni passo vive nelle
// traduzioni come sw_<chiave>_t (titolo) e sw_<chiave>_d (descrizione).
const SETUP_STEPS = {
  instagram: [
    { k: "ig1" },
    { k: "ig2", open: "https://developers.facebook.com/apps/" },
    { k: "ig3" },
    { k: "ig4", copy: true },
    { k: "ig5", fields: true },
  ],
  tiktok: [
    { k: "tt1" },
    { k: "tt2", open: "https://developers.tiktok.com/apps" },
    { k: "tt3" },
    { k: "tt4" },
    { k: "tt5", copy: true },
    { k: "tt6", fields: true },
  ],
};

const setupModal = document.getElementById("setup-modal");
let swPlatform = null;
let swIndex = 0;

function swSteps() { return SETUP_STEPS[swPlatform] || []; }

function openSetup(platform) {
  if (!SETUP_STEPS[platform]) return;
  swPlatform = platform;
  swIndex = 0;
  document.getElementById("sw-id").value = "";
  document.getElementById("sw-secret").value = "";
  closeConnectModal();
  setupModal.classList.remove("hidden");
  renderSetup();
}

function closeSetup() { setupModal.classList.add("hidden"); }

function swError(message) {
  const box = document.getElementById("sw-error");
  box.textContent = message || "";
  box.classList.toggle("hidden", !message);
}

function renderSetup() {
  const steps = swSteps();
  const step = steps[swIndex];
  if (!step) return;
  const meta = CONNECT_META[swPlatform] || { name: swPlatform, ico: icon("overview") };
  const isLast = swIndex === steps.length - 1;

  // `ico` e' markup SVG: con textContent finirebbe a schermo come sorgente.
  document.getElementById("sw-logo").innerHTML = meta.ico;
  document.getElementById("sw-title").textContent = t("sw_title", { p: meta.name });
  document.getElementById("sw-counter").textContent =
    t("sw_step_of", { n: swIndex + 1, tot: steps.length });
  document.getElementById("sw-progress-bar").style.width =
    `${((swIndex + 1) / steps.length) * 100}%`;

  document.getElementById("sw-step-title").textContent = t(`sw_${step.k}_t`);
  document.getElementById("sw-step-text").textContent = t(`sw_${step.k}_d`);

  const openBtn = document.getElementById("sw-open");
  openBtn.classList.toggle("hidden", !step.open);

  document.getElementById("sw-copy-row").classList.toggle("hidden", !step.copy);
  if (step.copy) {
    document.getElementById("sw-copy-value").textContent = swRedirectUri();
    document.getElementById("sw-copy-btn").textContent = t("sw_copy");
  }

  document.getElementById("sw-fields").classList.toggle("hidden", !step.fields);
  if (step.fields) {
    const suffix = swPlatform === "instagram" ? "ig" : "tt";
    document.getElementById("sw-id-label").textContent = t(`sw_id_label_${suffix}`);
    document.getElementById("sw-secret-label").textContent = t(`sw_secret_label_${suffix}`);
    document.getElementById("sw-id").placeholder = t(`sw_id_ph_${suffix}`);
    document.getElementById("sw-secret").placeholder = t(`sw_secret_ph_${suffix}`);
  }

  const back = document.getElementById("sw-back");
  back.textContent = t("sw_back");
  back.disabled = swIndex === 0;
  document.getElementById("sw-next").textContent = isLast ? t("sw_finish") : t("sw_next");
  swError("");
}

function swRedirectUri() {
  return connectionsData?.own_app?.[swPlatform]?.redirect_uri || "";
}

// Gli appunti passano da navigator.clipboard quando c'e', ma questo valore
// e' il punto in cui la procedura si spezzerebbe se non funzionasse: senza
// il ripiego, chi non puo' copiare dovrebbe trascrivere a mano un URL lungo.
async function swCopy(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) { /* si prova sotto */ }
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch (e) {
    return false;
  }
}

document.getElementById("setup-close").addEventListener("click", closeSetup);
setupModal.addEventListener("click", e => { if (e.target === setupModal) closeSetup(); });
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !setupModal.classList.contains("hidden")) closeSetup();
});

document.getElementById("sw-open").addEventListener("click", () => {
  const step = swSteps()[swIndex];
  if (step?.open) { window.open(step.open, "_blank"); toast(t("connect_browser_opened")); }
});

document.getElementById("sw-copy-btn").addEventListener("click", async e => {
  const btn = e.currentTarget;
  const ok = await swCopy(swRedirectUri());
  if (!ok) { swError(t("sw_copy_failed")); return; }
  btn.textContent = t("sw_copied");
  setTimeout(() => { btn.textContent = t("sw_copy"); }, 1600);
});

document.getElementById("sw-back").addEventListener("click", () => {
  if (swIndex > 0) { swIndex--; renderSetup(); }
});

document.getElementById("sw-next").addEventListener("click", async e => {
  const steps = swSteps();
  if (swIndex < steps.length - 1) { swIndex++; renderSetup(); return; }

  // Ultimo passo: si salva, e se le credenziali reggono si prosegue dritti
  // al collegamento vero senza far ricominciare da capo.
  const btn = e.currentTarget;
  const platform = swPlatform;
  const clientId = document.getElementById("sw-id").value.trim();
  const clientSecret = document.getElementById("sw-secret").value.trim();
  if (!clientId || !clientSecret) { swError(t("ownapp_missing")); return; }

  btn.disabled = true;
  btn.textContent = t("sw_saving");
  swError("");
  try {
    const resp = await (await fetch(`/api/own-app/${platform}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
    })).json();
    if (!resp.ok) { swError(tServer(resp.message)); return; }

    toast(t("sw_saved"), "ok");
    closeSetup();
    await loadConnections();
    openConnectModal(platform);
    // La piattaforma ora e' collegabile davvero: si avvia subito il login,
    // che e' quello per cui il cliente ha fatto tutti questi passaggi.
    const auto = document.getElementById("cm-auto-btn");
    if (!document.getElementById("cm-auto").classList.contains("hidden")) auto.click();
  } catch (err) {
    swError(String(err));
  } finally {
    // Solo il pulsante torna com'era. Ridisegnare il passo cancellerebbe il
    // messaggio d'errore appena scritto, e il cliente si ritroverebbe con le
    // credenziali rifiutate senza sapere quale dei due campi rivedere.
    btn.disabled = false;
    btn.textContent = t("sw_finish");
  }
});

document.getElementById("cm-ownapp-start").addEventListener("click", () => openSetup(cmPlatform));

document.getElementById("cm-ownapp-remove").addEventListener("click", async () => {
  const platform = cmPlatform;
  await fetch(`/api/own-app/${platform}`, { method: "DELETE" });
  toast(t("sw_removed"));
  await loadConnections();
  openConnectModal(platform);
});

async function startGuided(platform, btn) {
  btn.disabled = true;
  try {
    const resp = await (await fetch(`/api/connections/authorize/${platform}`)).json();
    if (!resp.ok) { toast(tServer(resp.message), "err"); return; }
    window.open(resp.url, "_blank");
    document.getElementById(`guided-${platform}`).classList.remove("hidden");
    toast(t("connect_browser_opened"));
  } catch (e) {
    toast(String(e), "err");
  } finally {
    btn.disabled = false;
  }
}

async function finishGuided(platform, btn) {
  const input = document.getElementById(`guided-input-${platform}`);
  const pasted = input.value.trim();
  if (!pasted) { toast(t("guided_paste_needed"), "err"); return; }
  btn.disabled = true;
  try {
    const resp = await (await fetch(`/api/connections/finish/${platform}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pasted }),
    })).json();
    if (!resp.ok) { toast(tServer(resp.message), "err"); return; }
    toast(t("connect_success", { n: resp.account || "" }), "ok");
    input.value = "";
    await loadConnections();
    await refreshAll();
  } catch (e) {
    toast(String(e), "err");
  } finally {
    btn.disabled = false;
  }
}

async function startConnect(platform, btn) {
  const originalLabel = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = t("connect_waiting");
  cmError("");
  try {
    const resp = await (await fetch(`/api/connections/connect/${platform}`, {
      method: "POST", headers: authHeaders(),
    })).json();
    if (!resp.ok) {
      // Limite di piano: si dice quanti account include il piano attuale e
      // si offre la strada per alzarlo, invece di un rifiuto secco.
      const msg = resp.code === "plan_account_limit"
        ? t("plan_account_limit", { n: resp.limit })
        : (tServer(resp.message) || t("generic_error"));
      cmError(msg);
      toast(msg, "err");
      if (resp.code === "plan_account_limit") closeConnectModal(), goTo("pricing");
      return;
    }
    toast(t("connect_browser_opened"));

    // Il login avviene nel browser: si attende che il flusso finisca.
    for (let i = 0; i < 400; i++) {
      await sleep(500);
      const st = await (await fetch("/api/connections/status")).json();
      if (st.running) continue;
      if (st.error) { const msg = tServer(st.error); cmError(msg); toast(msg, "err"); return; }
      if (st.done) {
        toast(t("connect_success", { n: st.account || "" }), "ok");
        closeConnectModal();
        await loadConnections();
        await refreshAll();
      }
      return;
    }
    // Attesa esaurita: si azzera lo stato lato server, altrimenti resterebbe
    // "in corso" e ogni tentativo successivo verrebbe rifiutato.
    await fetch("/api/connections/cancel", { method: "POST" }).catch(() => {});
    cmError(t("connect_timeout"));
    toast(t("connect_timeout"), "err");
  } catch (e) {
    await fetch("/api/connections/cancel", { method: "POST" }).catch(() => {});
    cmError(String(e));
    toast(String(e), "err");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalLabel;
    renderConnections();
  }
}

async function unlinkConnection(id) {
  try {
    await fetch(`/api/connections/${id}`, { method: "DELETE" });
    toast(t("connect_unlinked"));
    await loadConnections();
  } catch (e) { toast(String(e), "err"); }
}

// ---------- Account ----------
function authToken() { return localStorage.getItem("dashboard-token") || ""; }
function authHeaders() {
  const tk = authToken();
  return tk ? { Authorization: `Bearer ${tk}` } : {};
}

function initials(user) {
  if (user.first_name || user.last_name) {
    return ((user.first_name?.[0] || "") + (user.last_name?.[0] || "")).toUpperCase() || "?";
  }
  const src = (user.name || user.email || "?").trim();
  const parts = src.split(/[\s@._-]+/).filter(Boolean);
  return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase() || "?";
}

function renderUser() {
  const loggedOut = document.getElementById("account-logged-out");
  const loggedIn = document.getElementById("account-logged-in");
  const avatar = document.getElementById("user-avatar");
  const nameEl = document.getElementById("user-name");
  const planEl = document.getElementById("user-plan");

  if (!currentUser) {
    loggedOut.classList.remove("hidden");
    loggedIn.classList.add("hidden");
    avatar.textContent = "?";
    nameEl.textContent = t("account_guest");
    planEl.textContent = t("account_signin_hint");
    return;
  }

  loggedOut.classList.add("hidden");
  loggedIn.classList.remove("hidden");
  const ini = initials(currentUser);
  avatar.textContent = ini;
  nameEl.textContent = currentUser.name || currentUser.email.split("@")[0];
  planEl.textContent = currentUser.plan.charAt(0).toUpperCase() + currentUser.plan.slice(1);

  document.getElementById("acc-avatar").textContent = ini;
  document.getElementById("acc-name").textContent = currentUser.name || currentUser.email.split("@")[0];
  document.getElementById("acc-email").textContent = currentUser.email;
  document.getElementById("acc-plan").textContent = currentUser.plan;
  document.getElementById("acc-since").textContent = t("account_since", { d: fmtDateOnly(currentUser.created_at) });

  const upgradeBtn = document.getElementById("btn-account-upgrade");
  if (currentUser.plan === "studio") {
    upgradeBtn.classList.add("hidden");
  } else {
    upgradeBtn.classList.remove("hidden");
    upgradeBtn.textContent = currentUser.plan === "pro" ? t("account_upgrade_studio") : t("account_upgrade");
  }
}

let authMode = "login";

function renderAuthTexts() {
  const isLogin = authMode === "login";
  document.getElementById("auth-title").textContent = t(isLogin ? "auth_title_login" : "auth_title_register");
  document.getElementById("auth-sub").textContent = t(isLogin ? "auth_sub_login" : "auth_sub_register");
  document.getElementById("auth-submit-label").textContent = t(isLogin ? "auth_tab_login" : "auth_tab_register");
  document.getElementById("auth-switch-text").textContent = t(isLogin ? "auth_switch_to_register" : "auth_switch_to_login");
  document.getElementById("auth-switch-btn").textContent = t(isLogin ? "auth_tab_register" : "auth_tab_login");
  document.getElementById("field-name-row").classList.toggle("hidden", isLogin);
  document.getElementById("field-birth-date").classList.toggle("hidden", isLogin);
  document.getElementById("field-password-confirm").classList.toggle("hidden", isLogin);
  document.getElementById("forgot-password-row").classList.toggle("hidden", !isLogin);
  document.getElementById("strength").classList.toggle("hidden", isLogin);
  document.getElementById("auth-first-name").required = !isLogin;
  document.getElementById("auth-last-name").required = !isLogin;
  document.getElementById("auth-birth-date").required = !isLogin;
  document.getElementById("auth-password-confirm").required = !isLogin;
  document.getElementById("auth-password").setAttribute("autocomplete", isLogin ? "current-password" : "new-password");
  document.querySelectorAll(".auth-tab").forEach(tab => tab.classList.toggle("active", tab.dataset.mode === authMode));
}

function setAuthMode(mode) {
  authMode = mode;
  document.getElementById("auth-error").classList.add("hidden");
  renderAuthTexts();
}

document.querySelectorAll(".auth-tab").forEach(tab => {
  tab.addEventListener("click", () => setAuthMode(tab.dataset.mode));
});
document.getElementById("auth-switch-btn").addEventListener("click", () => {
  setAuthMode(authMode === "login" ? "register" : "login");
});

document.getElementById("toggle-password").addEventListener("click", () => {
  const input = document.getElementById("auth-password");
  input.type = input.type === "password" ? "text" : "password";
});
document.getElementById("toggle-password-confirm").addEventListener("click", () => {
  const input = document.getElementById("auth-password-confirm");
  input.type = input.type === "password" ? "text" : "password";
});

const STRENGTH_COLORS = ["var(--red)", "var(--red)", "var(--yellow)", "var(--green)", "var(--green)"];
document.getElementById("auth-password").addEventListener("input", e => {
  if (authMode !== "register") return;
  const pw = e.target.value;
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^\w\s]/].filter(re => re.test(pw)).length;
  if (classes >= 3) score++;
  if (classes >= 4 && pw.length >= 10) score++;
  const labels = t("strength_labels").split(",");
  document.getElementById("strength-fill").style.width = `${(score / 4) * 100}%`;
  document.getElementById("strength-fill").style.background = STRENGTH_COLORS[score];
  document.getElementById("strength-label").textContent = pw ? labels[score] : "";
});

function fieldError(id, message) {
  document.getElementById(id).textContent = message || "";
}

const MIN_AGE_YEARS = 13;

function computeAge(isoDate) {
  const birth = new Date(isoDate + "T00:00:00");
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const beforeBirthday = (today.getMonth() < birth.getMonth())
    || (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate());
  if (beforeBirthday) age--;
  return age;
}

document.getElementById("auth-form").addEventListener("submit", async e => {
  e.preventDefault();
  const isLogin = authMode === "login";
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;
  const passwordConfirm = document.getElementById("auth-password-confirm").value;
  const firstName = document.getElementById("auth-first-name").value.trim();
  const lastName = document.getElementById("auth-last-name").value.trim();
  const birthDate = document.getElementById("auth-birth-date").value;
  const errBox = document.getElementById("auth-error");
  const submit = document.getElementById("auth-submit");

  ["err-email", "err-password", "err-first-name", "err-last-name", "err-birth-date", "err-password-confirm"]
    .forEach(id => fieldError(id, ""));
  errBox.classList.add("hidden");

  let bad = false;
  if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(email)) { fieldError("err-email", t("err_email_invalid")); bad = true; }
  if (password.length < 8) { fieldError("err-password", t("err_password_short")); bad = true; }

  if (!isLogin) {
    if (!firstName) { fieldError("err-first-name", t("err_required")); bad = true; }
    if (!lastName) { fieldError("err-last-name", t("err_required")); bad = true; }
    if (!birthDate) {
      fieldError("err-birth-date", t("err_required")); bad = true;
    } else if (new Date(birthDate) > new Date()) {
      fieldError("err-birth-date", t("err_birth_date_future")); bad = true;
    } else if (computeAge(birthDate) < MIN_AGE_YEARS) {
      fieldError("err-birth-date", t("err_age_min", { n: MIN_AGE_YEARS })); bad = true;
    }
    if (passwordConfirm !== password) { fieldError("err-password-confirm", t("err_password_mismatch")); bad = true; }
  }
  if (bad) return;

  submit.disabled = true;
  try {
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
    const body = isLogin
      ? { email, password }
      : { email, password, password_confirm: passwordConfirm, first_name: firstName, last_name: lastName, birth_date: birthDate };
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) {
      errBox.textContent = tServer(data.detail) || t("generic_error");
      errBox.classList.remove("hidden");
      return;
    }
    localStorage.setItem("dashboard-token", data.token);
    currentUser = data.user;
    renderUser();
    if (plansData) renderPlans();
    document.getElementById("auth-form").reset();
    document.getElementById("strength-fill").style.width = "0%";
    document.getElementById("strength-label").textContent = "";
    toast(t(isLogin ? "toast_logged_in" : "toast_welcome", {
      n: currentUser.first_name || currentUser.name || currentUser.email.split("@")[0],
    }), "ok");
  } catch (err) {
    errBox.textContent = String(err);
    errBox.classList.remove("hidden");
  } finally {
    submit.disabled = false;
  }
});

// ---------- Reset password ----------
const resetModal = document.getElementById("reset-modal");

function resetErr(id, message) {
  const box = document.getElementById(id);
  box.textContent = message || "";
  box.classList.toggle("hidden", !message);
}

function openResetModal() {
  document.getElementById("reset-email").value = document.getElementById("auth-email").value.trim();
  document.getElementById("reset-step-1").classList.remove("hidden");
  document.getElementById("reset-step-2").classList.add("hidden");
  document.getElementById("reset-sub").textContent = t("reset_step1_sub");
  resetErr("reset-error-1", "");
  resetErr("reset-error-2", "");
  resetModal.classList.remove("hidden");
}
function closeResetModal() { resetModal.classList.add("hidden"); }

document.getElementById("forgot-password-btn").addEventListener("click", openResetModal);
document.getElementById("reset-close").addEventListener("click", closeResetModal);
resetModal.addEventListener("click", e => { if (e.target === resetModal) closeResetModal(); });

document.getElementById("reset-send-code").addEventListener("click", async e => {
  const btn = e.currentTarget;
  const email = document.getElementById("reset-email").value.trim();
  if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(email)) {
    resetErr("reset-error-1", t("err_email_invalid"));
    return;
  }
  btn.disabled = true;
  try {
    await fetch("/api/auth/forgot-password", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    // Stessa schermata di successo esista o no l'account: il backend non
    // distingue i due casi (vedi commento su auth_forgot_password), il
    // frontend non deve farlo trapelare mostrando un errore diverso.
    document.getElementById("reset-step-1").classList.add("hidden");
    document.getElementById("reset-step-2").classList.remove("hidden");
    document.getElementById("reset-sub").textContent = t("reset_step2_sub", { email });
    document.getElementById("reset-code").focus();
  } catch (err) {
    resetErr("reset-error-1", t("generic_error"));
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("reset-resend").addEventListener("click", () => {
  document.getElementById("reset-send-code").click();
});

document.getElementById("reset-confirm").addEventListener("click", async e => {
  const btn = e.currentTarget;
  const email = document.getElementById("reset-email").value.trim();
  const code = document.getElementById("reset-code").value.trim();
  const password = document.getElementById("reset-new-password").value;
  const passwordConfirm = document.getElementById("reset-new-password-confirm").value;
  resetErr("reset-error-2", "");

  if (!/^\d{6}$/.test(code)) { resetErr("reset-error-2", t("reset_err_code_format")); return; }
  if (password.length < 8) { resetErr("reset-error-2", t("err_password_short")); return; }
  if (password !== passwordConfirm) { resetErr("reset-error-2", t("err_password_mismatch")); return; }

  btn.disabled = true;
  try {
    const resp = await fetch("/api/auth/reset-password", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, password, password_confirm: passwordConfirm }),
    });
    const data = await resp.json();
    if (!resp.ok) { resetErr("reset-error-2", tServer(data.detail) || t("generic_error")); return; }

    localStorage.setItem("dashboard-token", data.token);
    currentUser = data.user;
    renderUser();
    if (plansData) renderPlans();
    closeResetModal();
    toast(t("reset_success"), "ok");
  } catch (err) {
    resetErr("reset-error-2", t("generic_error"));
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("btn-logout").addEventListener("click", async () => {
  try { await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() }); } catch (e) { /* locale comunque */ }
  localStorage.removeItem("dashboard-token");
  currentUser = null;
  renderUser();
  if (plansData) renderPlans();
  toast(t("toast_logged_out"));
});

async function loadUser() {
  if (!authToken()) { renderUser(); return; }
  try {
    const resp = await fetch("/api/auth/me", { headers: authHeaders() });
    if (!resp.ok) { localStorage.removeItem("dashboard-token"); currentUser = null; }
    else currentUser = (await resp.json()).user;
  } catch (e) { currentUser = null; }
  renderUser();
}

// ---------- Licenza ----------
// Vale per l'installazione, non per l'account: chi ha appena pagato deve
// poter attivare subito, anche senza essersi registrato.
let licenceInfo = null;

function renderLicence() {
  const state = document.getElementById("licence-state");
  const active = document.getElementById("licence-active");
  const row = document.querySelector(".licence-row");
  const hint = document.querySelector(".licence-box .muted");
  if (!state) return;

  const lic = licenceInfo || { active: false, plan: "free" };
  state.classList.remove("on", "warn");

  if (lic.active) {
    state.textContent = t("licence_state_active", { p: planLabel(lic.plan) });
    state.classList.add("on");
    active.classList.remove("hidden");
    row.classList.add("hidden");
    hint.classList.add("hidden");
    document.getElementById("licence-active-text").textContent =
      lic.stale ? t("licence_recheck_failed") : t("licence_active_on", { k: lic.key });
    if (lic.stale) state.classList.add("warn");
  } else {
    // Revocata e "da verificare" non sono la stessa cosa: la prima e' una
    // decisione (rimborso, disdetta), la seconda un problema tecnico.
    state.textContent = lic.revoked
      ? t("licence_state_revoked")
      : (lic.expired ? t("licence_state_expired") : t("licence_state_free"));
    if (lic.expired) state.classList.add("warn");
    active.classList.add("hidden");
    row.classList.remove("hidden");
    hint.classList.remove("hidden");
    if (lic.revoked) licenceMsg(t("licence_revoked_note"), "err");
  }
}

function planLabel(id) {
  return id ? id.charAt(0).toUpperCase() + id.slice(1) : "Free";
}

async function loadLicence() {
  try {
    licenceInfo = await (await fetch("/api/license")).json();
  } catch (e) { licenceInfo = null; }
  renderLicence();
}

function licenceMsg(text, kind) {
  const box = document.getElementById("licence-msg");
  if (!box) return;
  box.textContent = text || "";
  box.className = "licence-msg" + (text ? ` ${kind || ""}` : " hidden");
}

document.getElementById("licence-activate")?.addEventListener("click", async e => {
  const btn = e.currentTarget;
  const input = document.getElementById("licence-key");
  const key = input.value.trim();
  if (!key) { licenceMsg(t("licence_enter_key"), "err"); return; }

  btn.disabled = true;
  licenceMsg("");
  try {
    const resp = await (await fetch("/api/license/activate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    })).json();

    if (!resp.ok) { licenceMsg(tServer(resp.code) || t("generic_error"), "err"); return; }

    input.value = "";
    licenceMsg(t("licence_activated", { p: planLabel(resp.plan) }), "ok");
    toast(t("licence_activated", { p: planLabel(resp.plan) }), "ok");
    await loadLicence();
    // I limiti cambiano subito: si ridisegna quello che li mostra.
    await loadSnapshot();
    if (plansData) renderPlans();
  } catch (err) {
    licenceMsg(t("generic_error"), "err");
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("licence-manage")?.addEventListener("click", async e => {
  // Il portale clienti Stripe e' l'unico posto dove l'abbonamento si
  // disdice davvero: "Remove" toglie solo la chiave da questo computer, ma
  // lascia l'abbonamento a rinnovarsi comunque.
  const btn = e.currentTarget;
  btn.disabled = true;
  try {
    const resp = await fetch("/api/license/portal", { method: "POST" });
    const data = await resp.json();
    if (!resp.ok) { licenceMsg(tServer(data.detail) || t("generic_error"), "err"); return; }
    window.open(data.url, "_blank");
  } catch (err) {
    licenceMsg(t("generic_error"), "err");
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("licence-remove")?.addEventListener("click", async () => {
  await fetch("/api/license/remove", { method: "POST" }).catch(() => {});
  licenceMsg("");
  toast(t("licence_removed"));
  await loadLicence();
  await loadSnapshot();
  if (plansData) renderPlans();
});

// ---------- Dati in cache ----------
document.getElementById("cache-clear")?.addEventListener("click", async e => {
  // Cancella statistiche e storico locali: chi lo preme deve sapere cosa
  // sta per succedere, non e' un'azione reversibile con un solo clic.
  if (!confirm(t("cache_confirm"))) return;
  const btn = e.currentTarget;
  const msg = document.getElementById("cache-msg");
  btn.disabled = true;
  msg.classList.add("hidden");
  try {
    await fetch("/api/cache/clear", { method: "POST" });
    msg.textContent = t("cache_cleared");
    msg.classList.remove("hidden", "err");
    msg.classList.add("ok");
    toast(t("cache_cleared"), "ok");
    await loadSnapshot();
    if (connectionsData) await loadConnections();
  } catch (err) {
    msg.textContent = t("generic_error");
    msg.classList.remove("hidden", "ok");
    msg.classList.add("err");
  } finally {
    btn.disabled = false;
  }
});

// ---------- Piani ----------
async function loadPlans() {
  try {
    const resp = await fetch("/api/billing/plans");
    plansData = await resp.json();
    renderPlans();
  } catch (e) {
    document.getElementById("plans-grid").innerHTML = `<div class="empty">${esc(String(e))}</div>`;
  }
}

function renderPlans() {
  if (!plansData) return;
  const grid = document.getElementById("plans-grid");
  const yearly = billingCycle === "yearly";

  grid.innerHTML = plansData.plans.map(p => {
    const amount = yearly ? Math.round(p.price_yearly / 12) : p.price_monthly;
    const isCurrent = currentUser && currentUser.plan === p.id;
    const billed = p.id === "free"
      ? t("plan_billed_free")
      : (yearly ? t("plan_billed_yearly", { a: p.price_yearly }) : "");

    // Le voci arrivano come {code, text}: si traduce il codice e si ricade
    // sulla frase del server se quella chiave non esiste.
    const featText = f => (typeof f === "string" ? f : tOr(f.code, {}, f.text));
    const feats = (p.features || []).map(f => `<li><span class="feat-ico">${icon("check")}</span><span>${esc(featText(f))}</span></li>`).join("")
      + (p.missing || []).map(f => `<li class="off"><span class="feat-ico">–</span><span>${esc(featText(f))}</span></li>`).join("");

    let cta;
    if (isCurrent) cta = `<button class="plan-cta current" disabled>${t("plan_current")}</button>`;
    else if (p.id === "free") cta = `<button class="plan-cta secondary" data-plan="free">${t("plan_free_cta")}</button>`;
    else cta = `<button class="plan-cta ${p.popular ? "" : "secondary"}" data-plan="${p.id}">${t("plan_cta", { p: p.name })}</button>`;

    return `<div class="plan-card ${p.popular ? "popular" : ""}">
      ${p.popular ? `<span class="plan-ribbon">${icon("sparkles")} ${t("plan_popular")}</span>` : ""}
      <div class="plan-name">${esc(p.name)}</div>
      <div class="plan-tagline">${esc(tOr(p.tagline_code, {}, p.tagline))}</div>
      <div class="plan-price">
        <span class="plan-amount">${amount === 0 ? "0" : amount}€</span>
        <span class="plan-period">${t("plan_period_month")}</span>
      </div>
      <div class="plan-billed">${billed}</div>
      <span class="plan-accounts">${esc(tOr(p.accounts_code, {}, p.accounts))}</span>
      <ul class="plan-features">${feats}</ul>
      ${cta}
    </div>`;
  }).join("");

  document.getElementById("pricing-note").textContent =
    plansData.checkout_ready ? t("pricing_note_ready") : t("pricing_note_setup");

  grid.querySelectorAll("[data-plan]").forEach(btn => {
    btn.addEventListener("click", () => startCheckout(btn.dataset.plan));
  });
}

async function startCheckout(planId) {
  if (planId === "free") { goTo("account"); return; }
  // Non serve un account per acquistare: la licenza vale per questa
  // installazione e si attiva incollando la chiave. Un passaggio in meno
  // fra il cliente e il pagamento.
  try {
    const resp = await fetch("/api/billing/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ plan_id: planId, billing_cycle: billingCycle }),
    });
    const data = await resp.json();
    if (!resp.ok) { toast(tServer(data.detail) || t("generic_error"), "err"); return; }
    if (data.ok && data.checkout_url) {
      // Il pagamento si apre nel browser di sistema, non nella finestra
      // dell'app: la chiave va letta, copiata e spesso conservata.
      window.open(data.checkout_url, "_blank");
      toast(t("checkout_opened"));
    } else {
      toast(tServer(data.message) || t("generic_error"), "err");
    }
  } catch (e) {
    toast(String(e), "err");
  }
}

document.querySelectorAll(".cycle-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    billingCycle = btn.dataset.cycle;
    document.querySelectorAll(".cycle-btn").forEach(b => b.classList.toggle("active", b === btn));
    renderPlans();
  });
});

// ---------- Command palette ----------
const PALETTE_ITEMS = [
  { section: "overview", key: "nav_overview", ico: icon("overview") },
  { section: "youtube", label: "YouTube", ico: PLATFORM_ICONS.youtube },
  { section: "instagram", label: "Instagram", ico: PLATFORM_ICONS.instagram },
  { section: "tiktok", label: "TikTok", ico: PLATFORM_ICONS.tiktok },
  { section: "x", label: "X", ico: PLATFORM_ICONS.x },
  { section: "certsprint", label: "CertSprint", ico: PLATFORM_ICONS.certsprint },
  { section: "analytics", key: "nav_analytics", ico: icon("analytics") },
  { section: "diagnostics", key: "nav_diagnostics", ico: icon("diagnostics") },
  { section: "connections", key: "nav_connections", ico: icon("connections") },
  { section: "account", key: "nav_account", ico: icon("account") },
  { section: "pricing", key: "nav_pricing", ico: icon("pricing") },
  { section: "themes", key: "nav_themes", ico: icon("themes") },
  { section: "language", key: "nav_language", ico: icon("language") },
];

const overlay = document.getElementById("palette-overlay");
const paletteInput = document.getElementById("palette-input");
const paletteResults = document.getElementById("palette-results");
let paletteSel = 0;

function paletteMatches() {
  const q = paletteInput.value.trim().toLowerCase();
  const active = activePlatforms();
  return PALETTE_ITEMS
    // Una piattaforma disattivata non deve restare raggiungibile dalla
    // palette: sarebbe l'unica scorciatoia rimasta verso una sezione che
    // in questa build non esiste.
    .filter(i => !(i.section in PLATFORM_LABELS) || active.includes(i.section))
    .map(i => ({ ...i, text: i.label || t(i.key) }))
    .filter(i => !q || i.text.toLowerCase().includes(q));
}

function renderPalette() {
  const items = paletteMatches();
  if (paletteSel >= items.length) paletteSel = 0;
  paletteResults.innerHTML = items.length
    ? items.map((i, idx) => `<div class="palette-item ${idx === paletteSel ? "sel" : ""}" data-section="${i.section}">
        <span class="nav-ico">${i.ico}</span>${esc(i.text)}</div>`).join("")
    : `<div class="palette-empty">${t("palette_empty")}</div>`;
  paletteResults.querySelectorAll(".palette-item").forEach(el => {
    el.addEventListener("click", () => { goTo(el.dataset.section); closePalette(); });
  });
}

function openPalette() {
  overlay.classList.remove("hidden");
  paletteInput.value = "";
  paletteSel = 0;
  renderPalette();
  paletteInput.focus();
}
function closePalette() { overlay.classList.add("hidden"); }

document.getElementById("palette-trigger").addEventListener("click", openPalette);
overlay.addEventListener("click", e => { if (e.target === overlay) closePalette(); });
paletteInput.addEventListener("input", () => { paletteSel = 0; renderPalette(); });

document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); return; }
  if (overlay.classList.contains("hidden")) return;
  const items = paletteMatches();
  if (e.key === "Escape") { closePalette(); }
  else if (e.key === "ArrowDown") { e.preventDefault(); paletteSel = (paletteSel + 1) % Math.max(items.length, 1); renderPalette(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); paletteSel = (paletteSel - 1 + items.length) % Math.max(items.length, 1); renderPalette(); }
  else if (e.key === "Enter" && items[paletteSel]) { goTo(items[paletteSel].section); closePalette(); }
});

// ---------- Limiti di piano ----------
/** Diritti dell'utente corrente. Arrivano dallo snapshot: è il server a
 *  deciderli, qui servono solo a disegnare lucchetti e inviti coerenti. */
let entitlements = null;

function showUpgradeNeeded(feature) {
  toast(t("plan_feature_locked"), "err");
  goTo("pricing");
}

/** Riquadro "questa funzione è del piano Pro" con il pulsante per passare. */
function lockedBox(featureKey) {
  return `<div class="locked-box">
    <span class="locked-ico">${icon("lock")}</span>
    <div>
      <div class="locked-title">${t("locked_title")}</div>
      <div class="locked-text">${t(featureKey)}</div>
    </div>
    <button class="btn-analyze" data-goto="pricing">${t("locked_cta")}</button>
  </div>`;
}

function wireLocked(root) {
  (root || document).querySelectorAll(".locked-box [data-goto]").forEach(btn => {
    btn.addEventListener("click", () => goTo(btn.dataset.goto));
  });
}

// ---------- Export ----------
// Una navigazione diretta non puo' portarsi dietro l'intestazione di
// autenticazione, e senza quella il server non sa quale piano applicare:
// si scarica via fetch e si salva il file a mano.
document.getElementById("btn-export").addEventListener("click", async () => {
  try {
    const resp = await fetch("/api/export.csv", { headers: authHeaders() });
    if (resp.status === 403) { showUpgradeNeeded("csv_export"); return; }
    if (!resp.ok) { toast(t("generic_error"), "err"); return; }

    const url = URL.createObjectURL(await resp.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = "social-dashboard.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast(t("toast_export_done"), "ok");
  } catch (e) {
    toast(t("generic_error"), "err");
  }
});

// ---------- Orchestrazione ----------
function renderAll(snapshot) {
  currentSnapshot = snapshot;
  entitlements = snapshot.entitlements || null;
  renderOverview(snapshot);
  activePlatforms().forEach(key => {
    DETAIL_RENDERERS[key]?.(snapshot[key]);
    wireInlineConnect(document.getElementById(`${key}-detail`));
  });
  renderDiagnostics(snapshot.diagnostics);
  renderAnalytics(snapshot.analytics);

  // Sempre tutte le piattaforme attive, anche quelle senza osservazioni:
  // cosi' un riquadro di una sezione precedente non resta visibile.
  activePlatforms().forEach(platform => {
    showInsightBox(platform, snapshot.insights?.[platform]);
  });

  const times = activePlatforms().map(k => snapshot[k]?.fetched_at).filter(Boolean);
  const latest = times.length ? Math.max(...times) : null;
  lastRefreshEl.textContent = latest ? t("footer_last_refresh", { d: fmtTime(latest) }) : t("footer_never");
}

async function loadSnapshot() {
  // Con il token il server sa quale piano applicare: storico e fasce orarie
  // arrivano solo a chi ne ha diritto.
  const resp = await fetch("/api/snapshot", { headers: authHeaders() });
  renderAll(await resp.json());
}

function setProgress(pct) {
  progressBar.style.width = `${pct}%`;
  progressLabel.textContent = `${Math.round(pct)}%`;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function refreshAll() {
  btnRefresh.disabled = true;
  btnRefresh.classList.add("spinning");
  progressWrap.classList.remove("hidden");
  setProgress(0);

  try {
    await fetch("/api/refresh", { method: "POST" });
    let running = true, attempts = 0;
    while (running && attempts < 200) {
      await sleep(300);
      attempts++;
      try {
        const status = await (await fetch("/api/refresh/status")).json();
        setProgress((status.done_units / status.total_units) * 100);
        running = status.running;
      } catch (pollErr) { break; }
    }
    setProgress(100);
    await loadSnapshot();
    toast(t("toast_refresh_done"), "ok");
  } catch (e) {
    lastRefreshEl.textContent = t("footer_error");
    toast(t("footer_error"), "err");
    console.error(e);
  } finally {
    progressWrap.classList.add("hidden");
    btnRefresh.classList.remove("spinning");
    btnRefresh.disabled = false;
  }
}

btnRefresh.addEventListener("click", refreshAll);

// ---------- Avvio ----------
document.getElementById("auth-birth-date").max = new Date().toISOString().slice(0, 10);

applyTheme(localStorage.getItem("dashboard-theme") || "dark");
renderThemeGrid();
applyStaticTranslations();
renderLanguageGrid();
renderAuthTexts();

// Se c'e' gia' un token salvato, non si mostra "ospite" nemmeno per un
// istante: si aspetta la risposta di loadUser() prima di scoprire la carta.
// Senza questo, ad ogni riavvio si vedeva un lampo da disconnesso mentre
// /api/auth/me era ancora in volo - a un'occhiata veloce sembrava un logout.
if (authToken()) {
  document.getElementById("account-logged-out").classList.add("hidden");
}

loadUser();

(async () => {
  // La config decide quali piattaforme esistono: va letta prima di
  // disegnare qualsiasi cosa, altrimenti CertSprint comparirebbe per un
  // istante anche nella build destinata ai clienti. Indipendente dalla
  // sessione utente, quindi parte in parallelo e non la rallenta piu'.
  try {
    appConfig = await (await fetch("/api/config")).json();
  } catch (e) {
    appConfig = null;
  }
  applyConfig();
  loadConnections();
  loadSnapshot();
  loadLicence();
  loadUpdateCheck();
})();

// ---------- Aggiornamento automatico in background ----------
// Chi tiene questa dashboard aperta su un monitor secondario durante una
// live o uno stream non deve premere Refresh a mano per vedere i numeri
// aggiornati. Riusa la stessa refreshAll() del pulsante, non una versione
// separata: stessa barra di avanzamento, stesso stato "gia' in corso".
const AUTO_REFRESH_EVERY_MS = 5 * 60 * 1000;
setInterval(() => {
  if (!btnRefresh.disabled) refreshAll();
}, AUTO_REFRESH_EVERY_MS);

// ---------- Controllo aggiornamenti ----------
// Prova prima il vero updater interno (scarica, verifica la firma e
// sostituisce i file da solo). Se questa copia e' gestita da winget o gira
// dai sorgenti, il backend lo dice esplicitamente (managed_externally) e si
// torna al vecchio avviso passivo con solo il link alla pagina di download,
// perche' in quei casi l'app non ha il diritto di toccare i propri file.
let _updateInfo = null;

async function loadUpdateCheck() {
  try {
    const resp = await (await fetch("/api/update/check")).json();
    if (resp.managed_externally) {
      return loadPassiveUpdateNotice();
    }
    if (!resp.available) return;
    _updateInfo = resp;
    const banner = document.getElementById("update-banner");
    banner.querySelector("span:last-child").textContent =
      t("update_available_v", { v: resp.version });
    banner.title = t("update_hint", { v: resp.version });
    banner.classList.remove("hidden");
    banner.dataset.mode = "install";
  } catch (e) {
    // Offline o GitHub irraggiungibile: nessun avviso, si riprova al
    // prossimo avvio. Non deve mai interrompere l'uso dell'app.
  }
}

// Ripiego per winget/sorgenti: nessun'altra via se non mandare l'utente
// alla pagina di download, esattamente come prima di questo aggiornamento.
async function loadPassiveUpdateNotice() {
  try {
    const resp = await (await fetch("/api/version")).json();
    if (!resp.update_available) return;
    const banner = document.getElementById("update-banner");
    banner.querySelector("span:last-child").textContent =
      t("update_available_v", { v: resp.latest });
    banner.title = t("update_hint", { v: resp.latest });
    banner.classList.remove("hidden");
    banner.dataset.mode = "link";
    banner.dataset.url = resp.url;
  } catch (e) {
    // vedi sopra
  }
}

document.getElementById("update-banner").addEventListener("click", e => {
  const banner = e.currentTarget;
  if (banner.dataset.mode === "install") {
    openUpdateModal();
  } else {
    const url = banner.dataset.url;
    if (url) window.open(url, "_blank");
  }
});

function openUpdateModal() {
  if (!_updateInfo) return;
  document.getElementById("um-title").textContent =
    t("update_available_v", { v: _updateInfo.version });
  document.getElementById("um-sub").textContent =
    t("um_size", { size: formatBytes(_updateInfo.size) });
  const notes = document.getElementById("um-notes");
  if (_updateInfo.release_notes_url) {
    notes.innerHTML = "";
    const a = document.createElement("a");
    a.href = _updateInfo.release_notes_url;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = t("um_release_notes");
    notes.appendChild(a);
  } else {
    notes.textContent = "";
  }
  document.getElementById("um-error").classList.add("hidden");
  document.getElementById("um-progress").classList.add("hidden");
  document.getElementById("um-actions").classList.remove("hidden");
  const skipBtn = document.getElementById("um-skip");
  skipBtn.classList.toggle("hidden", !!_updateInfo.mandatory);
  document.getElementById("update-modal").classList.remove("hidden");
}

function closeUpdateModal() {
  document.getElementById("update-modal").classList.add("hidden");
}

function formatBytes(n) {
  if (!n) return "";
  const mb = n / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`;
}

document.getElementById("update-modal-close").addEventListener("click", closeUpdateModal);
document.getElementById("update-modal").addEventListener("click", e => {
  if (e.target.id === "update-modal") closeUpdateModal();
});

document.getElementById("um-later").addEventListener("click", async () => {
  try {
    await fetch("/api/update/postpone", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hours: 24 }),
    });
  } catch (e) { /* riproposto comunque al prossimo controllo periodico */ }
  document.getElementById("update-banner").classList.add("hidden");
  closeUpdateModal();
});

document.getElementById("um-skip").addEventListener("click", async () => {
  if (!_updateInfo) return;
  try {
    await fetch("/api/update/postpone", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skip_version: _updateInfo.version }),
    });
  } catch (e) { /* vedi sopra */ }
  document.getElementById("update-banner").classList.add("hidden");
  closeUpdateModal();
});

document.getElementById("um-install").addEventListener("click", async () => {
  document.getElementById("um-actions").classList.add("hidden");
  document.getElementById("um-error").classList.add("hidden");
  document.getElementById("um-progress").classList.remove("hidden");
  try {
    const resp = await fetch("/api/update/install", { method: "POST" });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "update failed");
    }
    // Da qui l'app viene chiusa e sostituita dall'updater esterno: la
    // barra resta al 100% finche' il processo non termina da solo.
    document.getElementById("um-progress-bar").style.width = "100%";
  } catch (e) {
    document.getElementById("um-progress").classList.add("hidden");
    document.getElementById("um-actions").classList.remove("hidden");
    const errBox = document.getElementById("um-error");
    errBox.textContent = t("um_error");
    errBox.classList.remove("hidden");
  }
});
