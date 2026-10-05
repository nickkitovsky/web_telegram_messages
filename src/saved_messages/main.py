from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from saved_messages.routes import auth, messages, tasks, telegram

app = FastAPI(title="Saved Messages Organizer", version="0.1.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(auth.router)
app.include_router(telegram.router)
app.include_router(messages.router)
app.include_router(tasks.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#eceff4">
  <title>Saved Messages — Telegram Organizer</title>
  <link rel="icon" type="image/png" sizes="64x64" href="/static/favicon.png">
  <link rel="apple-touch-icon" href="/static/app-logo.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@1.0.0-beta.11/bundles/datastar.js"></script>
  <style>
    :root{
      color-scheme:light;
      --nord0:#2e3440;--nord1:#3b4252;--nord2:#434c5e;--nord3:#4c566a;
      --nord4:#d8dee9;--nord5:#e5e9f0;--nord6:#eceff4;
      --nord7:#8fbcbb;--nord8:#88c0d0;--nord9:#81a1c1;--nord10:#5e81ac;
      --nord11:#bf616a;--nord12:#d08770;--nord13:#ebcb8b;--nord14:#a3be8c;--nord15:#b48ead;
      --app-bg:var(--nord6);--app-surface:var(--nord5);--app-raised:#fff;
      --app-text:var(--nord0);--app-muted:var(--nord3);--app-border:var(--nord4);
      --app-hover:var(--nord5);--app-active:var(--nord4);--app-accent:var(--nord10);
      --app-accent-soft:var(--nord5);--app-link:var(--nord3);
      --app-primary:var(--nord3);--app-primary-hover:var(--nord0);
      --app-on-primary:var(--nord6);--app-icon:var(--nord3);--app-danger:var(--nord11);
      --app-shadow:#2e34401a;
    }
    html.dark{
      color-scheme:dark;
      --app-bg:var(--nord0);--app-surface:var(--nord1);--app-raised:var(--nord1);
      --app-text:var(--nord6);--app-muted:#c2cad6;--app-border:var(--nord3);
      --app-hover:var(--nord2);--app-active:var(--nord3);--app-accent:var(--nord8);
      --app-accent-soft:var(--nord1);--app-link:var(--nord8);
      --app-primary:var(--nord8);--app-primary-hover:var(--nord7);
      --app-on-primary:var(--nord0);--app-icon:var(--nord8);--app-danger:#d7828c;
      --app-shadow:#1c202933;
    }
    body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;position:relative;isolation:isolate;background:var(--app-bg);color:var(--app-text);transition:background-color .2s,color .2s}
    #ambient-scene{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:-1;background:linear-gradient(132deg,var(--nord5) 0 18%,var(--nord6) 18% 74%,#dce3ef 74% 100%)}
    html.dark #ambient-scene{background:linear-gradient(132deg,var(--nord1) 0 18%,var(--nord0) 18% 74%,#343c4b 74% 100%)}
    .scene-shape{position:absolute;display:block;background:#d8e0ec}
    html.dark .scene-shape{background:#394353}
    .scene-shape--orb{width:34rem;height:34rem;left:-13rem;top:-20rem;border-radius:44% 56% 51% 49%;transform:rotate(-25deg)}
    .scene-shape--arc{width:26rem;height:40rem;right:-20rem;top:-12rem;border-radius:48%;transform:rotate(31deg)}
    .scene-shape--wave{width:35rem;height:24rem;left:37%;bottom:-22rem;border-radius:48% 52% 0 0;transform:rotate(-22deg)}
    .scene-shape--band{width:120vw;height:9rem;left:-10vw;top:44%;border-radius:999px;transform:rotate(-38deg);background:#f4f6fa;opacity:.7}
    html.dark .scene-shape--band{background:#3b4252;opacity:.65}
    #login-screen,#app-shell{position:relative;z-index:1}
    [hidden]{display:none!important}
    .tg-blue{background:var(--app-primary);color:var(--app-on-primary)}
    #app-shell .tg-blue:hover,#login-screen .tg-blue:hover{background:var(--app-primary-hover);color:var(--app-on-primary)}
    .tg-blue-text{color:var(--app-link)}
    .tg-bg{background:var(--app-surface)}
    .telegram-pre{display:block;white-space:pre-wrap;background:var(--app-surface);padding:.75rem;border-radius:.75rem}
    .telegram-blockquote{display:inline-block;border-left:3px solid var(--app-accent);padding-left:.75rem;color:var(--app-muted)}
    .telegram-spoiler{background:var(--nord1);color:transparent;border-radius:3px;cursor:pointer}
    .telegram-spoiler:hover{color:inherit}
    .scrollbar-thin{scrollbar-width:thin}
    .brand-mark{display:block;object-fit:cover;border:1px solid var(--app-border);box-shadow:0 8px 20px #2e344033}
    .login-logo{width:max-content;margin:0 auto 1.5rem}
    button{transition:background-color .16s ease,color .16s ease,border-color .16s ease,box-shadow .16s ease}
    button:focus{outline:none}
    button:focus-visible{outline:3px solid var(--app-accent);outline-offset:3px}
    .side-item:focus:not(:focus-visible){outline:none;box-shadow:none}
    #app-shell .menu-item{background:transparent;color:var(--app-text)}
    #app-shell .menu-item svg{color:var(--app-icon)}
    #app-shell .menu-item:hover,#app-shell .menu-item:focus-visible{background:var(--app-hover);color:var(--app-text)}
    #app-shell .menu-item:hover svg,#app-shell .menu-item:focus-visible svg{color:var(--app-icon)}
    #app-shell .menu-item[aria-current="page"]{background:var(--app-active);color:var(--app-text);font-weight:650}
    #app-shell .menu-item[aria-current="page"] svg{color:var(--app-icon)}
    #app-shell .menu-item[aria-current="page"]:hover{background:var(--app-hover)}
    #app-shell .menu-item.text-rose-600{color:var(--app-danger)}
    #app-shell .menu-item.text-rose-600 svg{color:var(--app-danger)}
    #app-shell .side-item{background:transparent;color:var(--app-muted)}
    #app-shell .side-item svg{color:var(--app-icon)}
    #app-shell .side-item:hover,#app-shell .side-item:focus-visible{background:var(--app-hover);color:var(--app-text)}
    #app-shell .side-item:hover svg,#app-shell .side-item:focus-visible svg{color:var(--app-icon)}
    #app-shell .side-item[aria-current="page"]{background:var(--app-active);color:var(--app-text);font-weight:650}
    #app-shell .side-item[aria-current="page"] svg{color:var(--app-icon)}
    #app-shell .side-item[aria-current="page"]:hover{background:var(--app-hover)}
    #app-shell .bg-white{background-color:var(--app-raised)!important}
    #app-shell .bg-slate-50,#app-shell .bg-slate-50\/70{background-color:var(--app-surface)!important}
    #app-shell .bg-slate-100{background-color:var(--app-bg)!important}
    #app-shell .bg-sky-50{background-color:var(--app-accent-soft)!important}
    #app-shell .bg-sky-100{background-color:var(--app-surface)!important}
    #app-shell .text-slate-800,#app-shell .text-slate-700,#app-shell .text-slate-600{color:var(--app-text)!important}
    #app-shell .text-slate-500,#app-shell .text-slate-400{color:var(--app-muted)!important}
    #app-shell .text-rose-600{color:var(--app-danger)!important}
    #app-shell .border-slate-100,#app-shell .border-slate-200{border-color:var(--app-border)!important}
    #app-shell input,#login-screen input{background-color:var(--app-raised);color:var(--app-text);border-color:var(--app-border)}
    #app-shell input::placeholder,#login-screen input::placeholder{color:var(--app-muted);opacity:.8}
    #app-shell input:focus,#login-screen input:focus{border-color:var(--app-accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--app-accent) 24%,transparent)}
    #app-shell .shadow-sm,#app-shell .shadow-xl{--tw-shadow-color:var(--app-shadow)}
    #login-screen>section{background:var(--app-raised);color:var(--app-text)}
    #login-screen .text-slate-500,#login-screen .text-slate-600{color:var(--app-muted)}
    #login-screen .text-rose-600{color:var(--app-danger)}
    #login-screen .border-sky-100{border-color:var(--app-border)}
    #login-screen .bg-sky-50{background:var(--app-accent-soft)}
    #login-screen .tg-blue-text{color:var(--app-link)}
    #theme-toggle,#login-theme-toggle{color:var(--app-icon)}
    #theme-toggle:hover,#login-theme-toggle:hover{background:var(--app-hover);color:var(--app-accent)}
  </style>
</head>
<body class="min-h-screen" data-signals="{search: ''}">
  <div id="ambient-scene" aria-hidden="true">
    <span class="scene-shape scene-shape--orb"></span>
    <span class="scene-shape scene-shape--arc"></span>
    <span class="scene-shape scene-shape--wave"></span>
    <span class="scene-shape scene-shape--band"></span>
  </div>
  <svg aria-hidden="true" class="hidden">
    <symbol id="icon-home" viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z"/></symbol>
    <symbol id="icon-tag" viewBox="0 0 24 24"><path d="M20.6 13.4 13 21a2 2 0 0 1-2.8 0L3 13.8V4h9.8l7.8 7.8a1.1 1.1 0 0 1 0 1.6Z"/><circle cx="7.5" cy="8" r="1.4"/></symbol>
    <symbol id="icon-archive" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9m-9 4h4"/></symbol>
    <symbol id="icon-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></symbol>
    <symbol id="icon-exit" viewBox="0 0 24 24"><path d="M10 17l5-5-5-5m5 5H3"/><path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7"/></symbol>
    <symbol id="icon-search" viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="7.3"/><path d="m16.2 16.2 4.3 4.3"/></symbol>
    <symbol id="icon-sync" viewBox="0 0 24 24"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.6 9A7 7 0 0 1 18 6l2 2M4 16l2 2a7 7 0 0 0 12.4-3"/></symbol>
    <symbol id="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></symbol>
    <symbol id="icon-moon" viewBox="0 0 24 24"><path d="M20.8 15.2A8.5 8.5 0 0 1 8.8 3.2 8.5 8.5 0 1 0 20.8 15.2Z"/></symbol>
    <symbol id="icon-message" viewBox="0 0 24 24"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z"/></symbol>
  </svg>
  <main id="login-screen" class="relative min-h-screen flex items-center justify-center px-4 py-12">
    <button id="login-theme-toggle" onclick="toggleTheme()" aria-label="Переключить тему" title="Переключить тему" class="absolute right-5 top-5 rounded-full p-3 text-slate-600 hover:bg-slate-200">
      <svg id="login-theme-icon" class="h-5 w-5 fill-none stroke-current" stroke-width="1.8"><use href="#icon-moon"/></svg>
    </button>
    <section class="w-full max-w-md rounded-3xl bg-white p-8 shadow-xl shadow-slate-200/70">
      <img class="brand-mark login-logo h-24 w-24 rounded-[1.6rem]" src="/static/app-logo.png" alt="Логотип Saved Messages">
      <h1 class="text-center text-2xl font-bold">Saved Messages</h1>
      <p class="mb-7 mt-2 text-center text-sm text-slate-500">Войдите, чтобы открыть личный архив Telegram</p>
      <form id="auth-form" class="space-y-3" onsubmit="event.preventDefault();authenticate('/auth/login')">
        <label class="block text-sm font-medium text-slate-600">Email
          <input id="email" type="email" autocomplete="email" required placeholder="name@example.com"
            class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100">
        </label>
        <label class="block text-sm font-medium text-slate-600">Пароль
          <input id="password" type="password" autocomplete="current-password" minlength="12" required placeholder="Не менее 12 символов"
            class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100">
        </label>
        <p id="login-error" class="min-h-5 text-sm text-rose-600" role="alert"></p>
        <button class="w-full rounded-xl tg-blue px-4 py-3 font-semibold text-white transition hover:bg-sky-600">Войти</button>
        <button type="button" onclick="authenticate('/auth/register')" class="w-full rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 font-semibold tg-blue-text transition hover:bg-sky-100">Зарегистрироваться</button>
      </form>
    </section>
  </main>

  <div id="app-shell" hidden>
    <header class="sticky top-0 z-30 bg-white shadow-sm">
      <div class="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
        <a href="#" onclick="showView('home');return false" class="flex shrink-0 items-center gap-2 font-bold">
          <img class="brand-mark h-10 w-10 rounded-xl" src="/static/app-logo.png" alt="">
          <span class="hidden sm:inline">Saved Messages</span>
        </a>
        <label class="relative mx-auto flex min-w-0 max-w-2xl flex-1 items-center">
          <svg class="absolute left-4 h-5 w-5 fill-none stroke-current text-slate-400" stroke-width="2"><use href="#icon-search"/></svg>
          <input id="search" type="search" placeholder="Поиск по сообщениям, авторам и тегам"
            data-bind="search" data-on:input__debounce.300ms="searchMessages()"
            class="w-full rounded-full bg-slate-100 py-3 pl-11 pr-4 text-sm outline-none transition focus:bg-white focus:ring-2 focus:ring-sky-200">
        </label>
        <button id="theme-toggle" onclick="toggleTheme()" aria-label="Переключить тему" title="Переключить тему" class="rounded-full p-2.5 text-slate-500 hover:bg-slate-100">
          <svg id="theme-icon" class="h-5 w-5 fill-none stroke-current" stroke-width="1.8"><use href="#icon-moon"/></svg>
        </button>
        <details class="relative shrink-0">
          <summary class="flex cursor-pointer list-none items-center gap-2 rounded-full p-1.5 hover:bg-slate-100">
            <span id="user-avatar" class="flex h-9 w-9 items-center justify-center rounded-full bg-sky-100 font-bold tg-blue-text">U</span>
            <span id="user-name" class="hidden max-w-36 truncate text-sm font-semibold md:inline">Профиль</span>
            <span class="text-xs text-slate-400">▾</span>
          </summary>
          <nav class="absolute right-0 mt-2 w-52 overflow-hidden rounded-2xl border border-slate-100 bg-white p-2 shadow-xl">
            <button data-view="home" onclick="showView('home')" class="menu-item"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-home"/></svg> Главная</button>
            <button data-view="tags" onclick="showView('tags')" class="menu-item"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-tag"/></svg> Теги</button>
            <button data-view="archive" onclick="showView('archive')" class="menu-item"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-archive"/></svg> Архив</button>
            <button data-view="profile" onclick="showView('profile')" class="menu-item"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-user"/></svg> Профиль</button>
            <div class="my-1 border-t border-slate-100"></div>
            <button onclick="logout()" class="menu-item text-rose-600"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-exit"/></svg> Выход</button>
          </nav>
        </details>
      </div>
    </header>
    <div class="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[250px_minmax(0,1fr)]">
      <aside class="hidden lg:block">
        <div class="sticky top-24 space-y-4">
          <nav class="rounded-2xl bg-white p-2 shadow-sm">
            <button id="nav-home" onclick="showView('home')" class="side-item"><svg class="h-5 w-5 fill-none stroke-current"><use href="#icon-home"/></svg><span>Главная</span></button>
            <button id="nav-tags" onclick="showView('tags')" class="side-item"><svg class="h-5 w-5 fill-none stroke-current"><use href="#icon-tag"/></svg><span>Теги</span></button>
            <button id="nav-archive" onclick="showView('archive')" class="side-item"><svg class="h-5 w-5 fill-none stroke-current"><use href="#icon-archive"/></svg><span>Архив</span></button>
            <button id="nav-profile" onclick="showView('profile')" class="side-item"><svg class="h-5 w-5 fill-none stroke-current"><use href="#icon-user"/></svg><span>Профиль</span></button>
          </nav>
          <section class="rounded-2xl bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <h2 class="font-semibold">Telegram</h2>
              <span id="telegram-dot" class="h-2.5 w-2.5 rounded-full bg-slate-300"></span>
            </div>
            <p id="telegram-indicator" class="mt-2 text-sm text-slate-500">Проверяем статус…</p>
            <button onclick="showView('profile')" class="mt-3 w-full rounded-xl bg-sky-50 px-3 py-2 text-sm font-semibold tg-blue-text hover:bg-sky-100">Настроить</button>
          </section>
          <button onclick="syncLatest()" class="flex w-full items-center justify-center gap-2 rounded-2xl tg-blue px-4 py-3 font-semibold text-white shadow-sm hover:bg-sky-600"><svg class="h-5 w-5 fill-none stroke-current" stroke-width="1.8"><use href="#icon-sync"/></svg>Синхронизировать</button>
        </div>
      </aside>

      <section class="min-w-0">
        <div id="status" class="mb-3 hidden rounded-xl bg-white px-4 py-3 text-sm text-slate-600 shadow-sm" role="status"></div>
        <section id="view-home" class="view-panel">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div><h1 class="text-xl font-bold">Главная</h1><p class="mt-1 text-sm text-slate-500">Ваши сохранённые сообщения</p></div>
            <button onclick="syncLatest()" class="flex items-center gap-2 rounded-xl tg-blue px-4 py-2.5 text-sm font-semibold text-white hover:bg-sky-600 lg:hidden"><svg class="h-4 w-4 fill-none stroke-current"><use href="#icon-sync"/></svg>Синхронизировать</button>
          </div>
          <main id="messages" class="space-y-4"></main>
          <div id="home-sentinel" class="flex min-h-16 items-center justify-center text-sm text-slate-400" aria-live="polite"></div>
        </section>
        <section id="view-tags" class="view-panel" hidden>
          <div class="mb-4"><h1 class="text-xl font-bold">Теги</h1><p class="mt-1 text-sm text-slate-500">Выберите тег, чтобы найти связанные сообщения</p></div>
          <div id="tags" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"></div>
        </section>
        <section id="view-archive" class="view-panel" hidden>
          <div class="mb-4"><h1 class="text-xl font-bold">Архив</h1><p class="mt-1 text-sm text-slate-500">Сообщения, скрытые с главной страницы</p></div>
          <main id="archived-messages" class="space-y-4"></main>
          <div id="archive-sentinel" class="flex min-h-16 items-center justify-center text-sm text-slate-400" aria-live="polite"></div>
        </section>
        <section id="view-profile" class="view-panel" hidden>
          <div class="mb-4"><h1 class="text-xl font-bold">Профиль</h1><p class="mt-1 text-sm text-slate-500">Настройки аккаунта и подключение Telegram</p></div>
          <div class="max-w-2xl rounded-2xl bg-white p-5 shadow-sm sm:p-7">
            <div class="flex items-center gap-4 border-b border-slate-100 pb-5">
              <span id="profile-avatar" class="flex h-14 w-14 items-center justify-center rounded-full bg-sky-100 text-xl font-bold tg-blue-text">U</span>
              <div><p id="profile-name" class="font-semibold"></p><p class="text-sm text-slate-500">Аккаунт приложения</p></div>
            </div>
            <div class="py-5">
              <div class="flex items-center gap-2"><span id="profile-telegram-dot" class="h-2.5 w-2.5 rounded-full bg-slate-300"></span><h2 class="font-semibold">Подключение Telegram</h2></div>
              <p id="profile-telegram-status" class="mt-1 text-sm text-slate-500"></p>
              <div id="telegram-login-fields" class="mt-4 space-y-3">
                <div id="telegram-phone-step" class="flex flex-col gap-2 sm:flex-row">
                  <input id="telegram-phone" type="tel" autocomplete="tel" placeholder="+7 900 000-00-00" class="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-100">
                  <button onclick="startTelegramLogin()" class="rounded-xl tg-blue px-4 py-3 font-semibold text-white hover:bg-sky-600">Получить код</button>
                </div>
                <div id="telegram-code-step" class="flex flex-col gap-2 sm:flex-row" hidden>
                  <input id="telegram-code" inputmode="numeric" autocomplete="one-time-code" placeholder="Код из Telegram" class="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-100">
                  <button onclick="submitTelegramCode()" class="rounded-xl tg-blue px-4 py-3 font-semibold text-white hover:bg-sky-600">Подтвердить код</button>
                </div>
                <div id="telegram-password-step" class="flex flex-col gap-2 sm:flex-row" hidden>
                  <input id="telegram-password" type="password" autocomplete="current-password" placeholder="Пароль двухэтапной проверки" class="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-100">
                  <button onclick="submitTelegramPassword()" class="rounded-xl tg-blue px-4 py-3 font-semibold text-white hover:bg-sky-600">Войти</button>
                </div>
              </div>
            </div>
            <button onclick="logout()" class="rounded-xl border border-rose-100 px-4 py-2.5 text-sm font-semibold text-rose-600 hover:bg-rose-50">Выйти из аккаунта</button>
          </div>
        </section>
      </section>
    </div>
  </div>
  <script>
    const pageSize=50;
    let currentOffset=0,archiveOffset=0,hasNextPage=false,archiveHasNextPage=false;
    let lastVisibleTelegramId=null,activeView='home',currentUser=null,telegramConnected=false;
    let loadingFeed=false,loadingArchive=false,feedObserver=null;
    const mediaHydrationPages=new Set();
    document.querySelectorAll('.menu-item').forEach(button=>button.className='menu-item flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm hover:bg-slate-100 '+(button.className.includes('text-rose')?'text-rose-600':''));
    document.querySelectorAll('.side-item').forEach(button=>button.className='side-item flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left font-medium text-slate-600 hover:bg-sky-50 hover:text-sky-700');

    async function authenticate(path){
      const error=document.querySelector('#login-error');
      error.textContent='';
      const response=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:document.querySelector('#email').value,password:document.querySelector('#password').value})});
      const body=await response.json().catch(()=>({}));
      if(!response.ok){error.textContent=body.detail||'Не удалось войти';return;}
      currentUser=body;
      await enterApp();
    }
    async function enterApp(){
      document.querySelector('#login-screen').hidden=true;
      document.querySelector('#app-shell').hidden=false;
      const name=currentUser.email;
      document.querySelector('#user-name').textContent=name;
      document.querySelector('#profile-name').textContent=name;
      const initial=initials(name);
      document.querySelector('#user-avatar').textContent=initial;
      document.querySelector('#profile-avatar').textContent=initial;
      applyTheme();
      setActiveNavigation(activeView);
      await Promise.all([loadTelegramStatus(),loadTags()]);
      const messages=await loadMessages(0);
      if(!messages?.length&&telegramConnected)await syncLatest();
      setupFeedObserver();
    }
    async function initialize(){
      const response=await fetch('/auth/me',{credentials:'same-origin'});
      if(response.ok){currentUser=await response.json();await enterApp();}
      else document.querySelector('#login-screen').hidden=false;
    }
    async function logout(){
      await fetch('/auth/logout',{method:'POST',credentials:'same-origin'});
      location.reload();
    }
    function initials(value){return String(value||'?').trim().slice(0,1).toLocaleUpperCase('ru-RU')||'?';}
    function applyTheme(){
      const dark=localStorage.getItem('saved-messages-theme')==='dark';
      document.documentElement.classList.toggle('dark',dark);
      document.querySelector('meta[name="theme-color"]').content=dark?'#2e3440':'#eceff4';
      document.querySelectorAll('#theme-icon use,#login-theme-icon use').forEach(icon=>icon.setAttribute('href',dark?'#icon-sun':'#icon-moon'));
      document.querySelectorAll('#theme-toggle,#login-theme-toggle').forEach(button=>button.title=dark?'Переключить на светлую тему':'Переключить на тёмную тему');
    }
    function toggleTheme(){
      localStorage.setItem('saved-messages-theme',document.documentElement.classList.contains('dark')?'light':'dark');
      applyTheme();
    }
    function setActiveNavigation(view){
      document.querySelectorAll('.side-item').forEach(item=>item.removeAttribute('aria-current'));
      document.querySelectorAll('#app-shell .menu-item[data-view]').forEach(item=>item.removeAttribute('aria-current'));
      document.querySelector('#nav-'+view)?.setAttribute('aria-current','page');
      document.querySelector(`#app-shell .menu-item[data-view="${view}"]`)?.setAttribute('aria-current','page');
    }
    async function showResponse(response){
      const body=response instanceof Response?await response.json().catch(()=>({detail:response.statusText})):response;
      const status=document.querySelector('#status');
      status.textContent=typeof body==='string'?body:(body.detail||(response instanceof Response&&!response.ok?response.statusText:(body.status||'Готово')));
      status.classList.remove('hidden');
      if(response instanceof Response&&response.ok)setTimeout(()=>status.classList.add('hidden'),3500);
    }
    async function loadTelegramStatus(){
      const response=await fetch('/telegram/status',{credentials:'same-origin'});
      if(!response.ok)return;
      const result=await response.json();
      telegramConnected=result.connected;
      const label=result.connected?'Telegram подключён':'Telegram не подключён';
      document.querySelector('#telegram-indicator').textContent=label;
      document.querySelector('#profile-telegram-status').textContent=label+(result.connected_at?' · сессия сохранена':'');
      for(const id of ['telegram-dot','profile-telegram-dot']){
        const dot=document.getElementById(id);
        dot.className='h-2.5 w-2.5 rounded-full '+(result.connected?'bg-emerald-500':'bg-rose-400');
      }
      document.querySelector('#telegram-login-fields').hidden=result.connected;
      document.querySelector('#telegram-password-step').hidden=!result.password_required;
      document.querySelector('#telegram-code-step').hidden=result.password_required||!result.pending;
      document.querySelector('#telegram-phone-step').hidden=result.password_required||Boolean(result.pending);
    }
    async function showView(view){
      activeView=view;
      currentOffset=0;
      archiveOffset=0;
      document.querySelectorAll('.view-panel').forEach(panel=>panel.hidden=true);
      document.querySelector('#view-'+view).hidden=false;
      setActiveNavigation(view);
      document.querySelector('header details').open=false;
      if(view==='home')await loadMessages(0);
      if(view==='archive')await loadMessages(0,true);
      if(view==='tags')await loadTags();
      if(view==='profile')await loadTelegramStatus();
    }
    async function loadMessages(offset=0,archivedOnly=false,skipMediaHydration=false,append=false){
      const params=new URLSearchParams();
      const query=document.querySelector('#search').value.trim();
      const selectedTag=document.querySelector('#tag-filter')?.value;
      if(query)params.set('q',query);
      if(selectedTag)params.set('tag',selectedTag);
      if(archivedOnly)params.set('archived_only','true');
      params.set('limit',String(pageSize));params.set('offset',String(offset));
      const response=await fetch('/messages?'+params,{credentials:'same-origin'});
      if(response.status===401){location.reload();return null;}
      if(!response.ok){await showResponse(response);return null;}
      const items=await response.json();
      if(archivedOnly)archiveHasNextPage=response.headers.get('X-Has-Next')==='true';
      else hasNextPage=response.headers.get('X-Has-Next')==='true';
      lastVisibleTelegramId=response.headers.get('X-Older-Telegram-ID')||lastVisibleTelegramId;
      const root=document.querySelector(archivedOnly?'#archived-messages':'#messages');
      const sentinel=document.querySelector(archivedOnly?'#archive-sentinel':'#home-sentinel');
      if(!append){
        root.innerHTML='';
        if(archivedOnly)archiveOffset=0;else currentOffset=0;
      }
      if(items.length){
        root.insertAdjacentHTML('beforeend',items.map(renderMessage).join(''));
        if(archivedOnly)archiveOffset=offset+items.length;else currentOffset=offset+items.length;
      }else if(offset===0&&!append){
        root.innerHTML=`<div class="rounded-2xl bg-white px-6 py-12 text-center shadow-sm"><div class="mb-3 flex justify-center text-slate-300">${icon('message','h-9 w-9')}</div><p class="font-semibold">${archivedOnly?'Архив пока пуст':'Здесь пока нет сообщений'}</p><p class="mt-1 text-sm text-slate-500">${archivedOnly?'Архивированные сообщения появятся здесь':'Нажмите «Синхронизировать», чтобы загрузить Saved Messages'}</p></div>`;
      }
      sentinel.textContent=items.length?'':(archivedOnly?'Архив загружен':'Сообщений больше нет');
      const unchecked=items.filter(message=>!message.media_checked);
      if(unchecked.length&&!skipMediaHydration){
        const key=unchecked.map(message=>message.id).sort((a,b)=>a-b).join(',');
        if(!mediaHydrationPages.has(key)){mediaHydrationPages.add(key);hydratePageMedia(unchecked.flatMap(message=>message.message_ids),offset,archivedOnly,key);}
      }
      return items;
    }
    function renderMessage(message){
      const author=message.channel||currentUser?.email||'Вы';
      const tags=message.tags.map(tag=>`<button data-tag="${escapeHtml(tag)}" onclick="filterByTag(this.dataset.tag)" class="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-medium tg-blue-text hover:bg-sky-100">#${escapeHtml(tag)}</button>`).join('');
      const formattedDate=new Intl.DateTimeFormat('ru-RU',{dateStyle:'medium',timeStyle:'short'}).format(new Date(message.message_date));
      return `<article class="overflow-hidden rounded-2xl bg-white shadow-sm transition hover:shadow-md">
        <div class="flex items-center gap-3 px-5 pt-5">
          <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sky-100 font-bold tg-blue-text">${escapeHtml(initials(author))}</span>
          <div class="min-w-0 flex-1"><p class="truncate font-semibold">${escapeHtml(author)}</p><p class="text-xs text-slate-400">${message.is_forwarded?'Переслано из Telegram':'Ваше сообщение в Saved Messages'}</p></div>
          <time class="shrink-0 text-xs text-slate-400" title="${escapeHtml(message.message_date)}">${escapeHtml(formattedDate)}</time>
        </div>
        <div class="px-5 pb-4 pt-4">
          ${message.title?`<h2 class="mb-2 text-base font-semibold">${escapeHtml(message.title)}</h2>`:''}
          <div class="break-words text-[15px] leading-6">${message.text?renderText(message.text,message.text_entities):'<span class="italic text-slate-400">Медиа или сообщение без текста</span>'}</div>
          ${renderMedia(message)}
        </div>
        <div class="flex flex-wrap items-center gap-2 border-t border-slate-100 px-5 py-3">
          ${tags||'<span class="text-xs text-slate-400">Без тегов</span>'}
          <span class="ml-auto text-xs text-slate-400">${message.classification_confidence===null?'':`LLM ${Math.round(message.classification_confidence*100)}%`}</span>
        </div>
        <div class="flex flex-wrap gap-2 border-t border-slate-100 bg-slate-50/70 px-5 py-3">
          <button data-tags="${escapeHtml(JSON.stringify(message.tags))}" data-candidates="${escapeHtml(JSON.stringify(message.classification_candidates))}" onclick="editTags(${message.id},JSON.parse(this.dataset.tags),JSON.parse(this.dataset.candidates))" class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-white">${icon('tag','h-4 w-4')}Теги</button>
          <button onclick="archiveMessage(${message.id},${!message.archived})" class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-white">${icon('archive','h-4 w-4')}${message.archived?'Вернуть':'Архивировать'}</button>
          <button onclick="deleteMessage(${message.id})" class="ml-auto inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"><span class="text-lg leading-none">×</span>Удалить</button>
        </div>
      </article>`;
    }
    async function loadTags(){
      const response=await fetch('/tags',{credentials:'same-origin'});
      if(!response.ok)return;
      const tags=await response.json();
      document.querySelector('#tags').innerHTML=tags.map(tag=>`<button data-tag="${escapeHtml(tag.name)}" onclick="filterByTag(this.dataset.tag)" class="flex items-center justify-between rounded-2xl bg-white p-4 text-left shadow-sm hover:shadow-md"><span class="font-medium tg-blue-text">#${escapeHtml(tag.name)}</span><span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">${tag.count}</span></button>`).join('')||'<p class="rounded-2xl bg-white p-6 text-sm text-slate-500">Теги появятся здесь после обработки сообщений.</p>';
    }
    async function filterByTag(tag){
      let field=document.querySelector('#tag-filter');
      if(!field){field=document.createElement('input');field.id='tag-filter';field.type='hidden';document.body.append(field);}
      field.value=tag;document.querySelector('#search').value='';await showView('home');
    }
    async function searchMessages(){
      if(activeView==='archive'){archiveOffset=0;return loadMessages(0,true);}
      if(activeView!=='home')await showView('home');
      currentOffset=0;
      return loadMessages(0);
    }
    function setupFeedObserver(){
      if(feedObserver)feedObserver.disconnect();
      feedObserver=new IntersectionObserver(entries=>{
        for(const entry of entries){
          if(!entry.isIntersecting)continue;
          if(entry.target.id==='home-sentinel'&&activeView==='home')loadNextBatch(false);
          if(entry.target.id==='archive-sentinel'&&activeView==='archive')loadNextBatch(true);
        }
      },{rootMargin:'700px 0px'});
      feedObserver.observe(document.querySelector('#home-sentinel'));
      feedObserver.observe(document.querySelector('#archive-sentinel'));
    }
    async function loadNextBatch(archivedOnly){
      if((archivedOnly&&loadingArchive)||(!archivedOnly&&loadingFeed))return;
      if(!(archivedOnly?archiveHasNextPage:hasNextPage))return;
      if(archivedOnly)loadingArchive=true;else loadingFeed=true;
      const sentinel=document.querySelector(archivedOnly?'#archive-sentinel':'#home-sentinel');
      try{
        const offset=archivedOnly?archiveOffset:currentOffset;
        let items=await loadMessages(offset,archivedOnly,false,true);
        if(items?.length||archivedOnly||!hasNextPage||!lastVisibleTelegramId)return;
        sentinel.textContent='Подгружаю сообщения из Telegram…';
        let beforeId=lastVisibleTelegramId;
        for(let batch=0;batch<6&&hasNextPage;batch++){
          const response=await fetch('/tasks/sync?before_telegram_id='+encodeURIComponent(beforeId),{method:'POST',credentials:'same-origin'});
          if(!response.ok){await showResponse(response);return;}
          await response.json();
          let advanced=false;
          for(let attempt=0;attempt<30;attempt++){
            await new Promise(resolve=>setTimeout(resolve,1000));
            items=await loadMessages(offset,false,true,true);
            if(items?.length)return;
            if(!hasNextPage)return;
            if(lastVisibleTelegramId!==beforeId){advanced=true;break;}
          }
          if(!advanced){sentinel.textContent='Загрузка продолжается. Прокрутите вниз ещё раз, чтобы повторить проверку.';return;}
          beforeId=lastVisibleTelegramId;
        }
      }finally{
        if(archivedOnly)loadingArchive=false;else loadingFeed=false;
        if(feedObserver&&activeView===(archivedOnly?'archive':'home')){
          feedObserver.unobserve(sentinel);
          feedObserver.observe(sentinel);
        }
      }
    }
    async function syncLatest(){
      if(activeView!=='home')await showView('home');
      document.querySelector('#search').value='';const field=document.querySelector('#tag-filter');if(field)field.value='';
      currentOffset=0;hasNextPage=false;
      document.querySelector('#messages').innerHTML='';
      document.querySelector('#home-sentinel').textContent='Синхронизирую последние сообщения…';
      const response=await fetch('/tasks/sync',{method:'POST',credentials:'same-origin'});
      if(!response.ok)return showResponse(response);
      const queued=await response.json();showResponse('Синхронизация последних сообщений поставлена в очередь…');
      for(let attempt=0;attempt<30;attempt++){await new Promise(resolve=>setTimeout(resolve,1000));const items=await loadMessages(0);if(items?.length){showResponse('Синхронизация выполнена');return;}}
      showResponse(`Задача ${queued.task_id} ожидает обработки. Проверьте, что запущен TaskIQ worker.`);
    }
    async function hydratePageMedia(messageIds,offset,archivedOnly,key){
      const response=await fetch('/tasks/media',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({message_ids:messageIds})});
      if(!response.ok){await showResponse(response);mediaHydrationPages.delete(key);return;}
      const queued=await response.json();if(queued.status==='complete'){await refreshLoadedMessages(archivedOnly);return;}
      for(let attempt=0;attempt<30;attempt++){await new Promise(resolve=>setTimeout(resolve,1000));const items=await fetchMessageBatch(offset,archivedOnly);if(items&&!items.some(message=>message.message_ids.some(id=>messageIds.includes(id))&&!message.media_checked)){await refreshLoadedMessages(archivedOnly);return;}}
      mediaHydrationPages.delete(key);
    }
    async function fetchMessageBatch(offset,archivedOnly){
      const params=new URLSearchParams({limit:String(pageSize),offset:String(offset)});
      const query=document.querySelector('#search').value.trim();
      const selectedTag=document.querySelector('#tag-filter')?.value;
      if(query)params.set('q',query);
      if(selectedTag)params.set('tag',selectedTag);
      if(archivedOnly)params.set('archived_only','true');
      const response=await fetch('/messages?'+params,{credentials:'same-origin'});
      return response.ok?response.json():null;
    }
    async function refreshLoadedMessages(archivedOnly){
      const count=archivedOnly?archiveOffset:currentOffset;
      const root=document.querySelector(archivedOnly?'#archived-messages':'#messages');
      const messages=[];
      for(let offset=0;offset<count;offset+=pageSize){
        const batch=await fetchMessageBatch(offset,archivedOnly);
        if(!batch)break;
        messages.push(...batch);
      }
      root.innerHTML=messages.map(renderMessage).join('');
    }
    async function startTelegramLogin(){
      const response=await fetch('/telegram/start',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({phone:document.querySelector('#telegram-phone').value})});
      if(!response.ok)return showResponse(response);
      document.querySelector('#telegram-phone-step').hidden=true;document.querySelector('#telegram-code-step').hidden=false;
      showResponse('Код подтверждения отправлен в Telegram');
    }
    async function submitTelegramCode(){
      const response=await fetch('/telegram/code',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({code:document.querySelector('#telegram-code').value})});
      const result=await response.json().catch(()=>({}));
      if(!response.ok)return showResponse(result);
      if(result.password_required){document.querySelector('#telegram-code-step').hidden=true;document.querySelector('#telegram-password-step').hidden=false;showResponse('Введите пароль двухэтапной проверки');}
      else{showResponse('Telegram подключён');await loadTelegramStatus();}
    }
    async function submitTelegramPassword(){
      const response=await fetch('/telegram/password',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({password:document.querySelector('#telegram-password').value})});
      if(!response.ok)return showResponse(response);
      showResponse('Telegram подключён');await loadTelegramStatus();
    }
    async function archiveMessage(id,archived){
      const response=await fetch('/messages/'+id,{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({archived})});
      if(!response.ok)return showResponse(response);
      await loadMessages(activeView==='archive'?archiveOffset:currentOffset,activeView==='archive');
    }
    async function editTags(id,tags,candidates){
      const suggestions=candidates.length?'\\nВарианты от LLM: '+candidates.join(', '):'';
      const value=prompt('Теги через запятую'+suggestions,tags.join(', '));if(value===null)return;
      const response=await fetch('/messages/'+id,{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({tags:value.split(',')})});
      if(!response.ok)return showResponse(response);
      await loadMessages(activeView==='archive'?archiveOffset:currentOffset,activeView==='archive');await loadTags();
    }
    async function deleteMessage(id){
      if(!confirm('Удалить сообщение из приложения и Telegram?'))return;
      const response=await fetch('/messages/'+id,{method:'DELETE'});
      if(!response.ok)return showResponse(response);
      await loadMessages(activeView==='archive'?archiveOffset:currentOffset,activeView==='archive');
    }
    function renderMedia(message){
      return (message.media_files||[]).map(file=>{
        if(!file.media_checked)return '<p class="mt-3 text-sm text-slate-400">Загружаю вложение…</p>';
        if(!file.media_url||!file.media_mime_type)return '';
        const url=escapeHtml(file.media_url);
        if(file.media_mime_type.startsWith('image/'))return `<a href="${url}" target="_blank" rel="noopener noreferrer"><img src="${url}" alt="${escapeHtml(file.media_file_name||'Изображение')}" loading="lazy" class="mt-3 max-h-[460px] max-w-full rounded-xl object-contain"></a>`;
        if(file.media_mime_type.startsWith('video/'))return `<video controls preload="metadata" class="mt-3 max-h-[460px] max-w-full rounded-xl"><source src="${url}" type="${escapeHtml(file.media_mime_type)}"></video>`;
        if(file.media_mime_type.startsWith('audio/'))return `<audio controls preload="metadata" class="mt-3 w-full"><source src="${url}" type="${escapeHtml(file.media_mime_type)}"></audio>`;
        return `<p class="mt-3"><a class="tg-blue-text underline" href="${url}">${escapeHtml(file.media_file_name||'Скачать вложение')}</a></p>`;
      }).join('');
    }
    function icon(name,className='h-5 w-5'){
      return `<svg class="${className} fill-none stroke-current" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><use href="#icon-${name}"/></svg>`;
    }
    function renderText(value,entities=[]){
      const urlPattern=/(https?:\\/\\/[^\\s<>"']+|www\\.[^\\s<>"']+|(?:t\\.me|telegram\\.me)\\/[^\\s<>"']+)/gi;
      const text=String(value),formatTags={bold:['<strong>','</strong>'],italic:['<em>','</em>'],underline:['<u>','</u>'],strike:['<del>','</del>'],strikethrough:['<del>','</del>'],code:['<code>','</code>'],pre:['<code class="telegram-pre">','</code>'],blockquote:['<span class="telegram-blockquote">','</span>'],expandable_blockquote:['<span class="telegram-blockquote">','</span>'],spoiler:['<span class="telegram-spoiler">','</span>']};
      const spans=(Array.isArray(entities)?entities:[]).flatMap(entity=>{const start=Number(entity.offset),end=start+Number(entity.length);return Number.isInteger(start)&&Number.isInteger(end)&&start>=0&&end>start&&start<text.length?[{...entity,start,end:Math.min(end,text.length)}]:[];});
      const links=[];for(const match of text.matchAll(urlPattern)){let url=match[0];while(/[.,!?;:]$/.test(url))url=url.slice(0,-1);if(url)links.push({start:match.index,end:match.index+url.length,url});}
      const breaks=new Set([0,text.length]);for(const span of [...spans,...links]){breaks.add(span.start);breaks.add(span.end);}
      const points=[...breaks].sort((a,b)=>a-b);let html='';
      for(let i=0;i<points.length-1;i++){
        const start=points[i],end=points[i+1],segment=text.slice(start,end);if(!segment)continue;
        const active=spans.filter(span=>span.start<=start&&span.end>=end).sort((a,b)=>a.start-b.start||b.end-a.end);
        const link=active.find(span=>['text_url','url','email','phone'].includes(span.type));
        const automatic=links.find(item=>item.start<=start&&item.end>=end);
        let href=link?(link.type==='text_url'?link.url:link.type==='email'?'mailto:'+text.slice(start,end):link.type==='phone'?'tel:'+text.slice(start,end):text.slice(start,end)):automatic?.url;
        if(href&&(/^www\\./i.test(href)||/^(?:t\\.me|telegram\\.me)\\//i.test(href)))href='https://'+href;
        if(href&&!/^(https?:|tg:|mailto:|tel:)/i.test(href))href=null;
        const wrappers=active.map(span=>formatTags[span.type]).filter(Boolean);
        html+=wrappers.map(tags=>tags[0]).join('');
        html+=href?`<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(segment)}</a>`:escapeHtml(segment);
        html+=wrappers.reverse().map(tags=>tags[1]).join('');
      }
      return html;
    }
    function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
    applyTheme();
    initialize();
  </script>
</body>
</html>"""
    )
