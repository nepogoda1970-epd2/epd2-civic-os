# web-shell

Минимальный Next.js frontend-каркас EPD² Civic OS.

## Назначение

Показать статическую страницу со статусом инфраструктурного каркаса, а
также (с PACK-08) первый read-only vertical slice — раздел
`/organizations`, витрину домена «Organization & Regional Scope» (canon
19e), поверх статических примерных данных.

## Ограничения этого пакета

- без API-маршрутов;
- без login/аутентификации;
- без форм (`<form>`) — интерактивные элементы `/organizations` реализованы
  через `<select>`/`<button>`/`<input type="date">` вне `<form>`, без
  отправки на сервер;
- без сторонних UI-библиотек (никакого component kit);
- без сложного дизайна (только минимальные, базовые стили);
- без аналитики;
- без cookies;
- без внешних шрифтов (используется системный font stack).

## `/organizations` — PACK-08 read-only vertical slice

- **Область**: организации, `OrganizationalUnit`, `CivicSpace`,
  типизированные `OrganizationalRelation`, `OrganizationalAuthority` —
  только чтение, только статические примерные данные
  (`app/organizations/data.ts`). Никакого реального обращения к
  `organization-service` нет и не может быть — соответствующего HTTP API
  не существует (см. `contracts/openapi/pack-08.yaml`, раздел «minimal
  reference APIs only»).
- **Явно не реализовано** (сознательное решение, не пробел): массовый
  межрегиональный справочник организаций и публичный справочник участников
  — оба намеренно исключены и из `pack-08.yaml`, и из этого frontend-среза.
- **Язык**: немецкий — авторитетный текст (`lang="de"` на каждом `<main>`);
  английский — только информационная подпись рядом (`lang="en"`,
  `.informational`), никогда не единственный текст метки. См.
  `app/organizations/labels.ts`.
- **Страницы**:
  - `app/organizations/page.tsx` — обзор организаций (таблица, без
    массового межрегионального справочника);
  - `app/organizations/[id]/page.tsx` — детальная карточка: текущий/
    исторический статус (селектор «Stichtag», клиентский компонент
    `AsOfSelector.tsx`, вычисляется из статических `status_history`, без
    сети), типизированные связи (`OrganizationalRelation`), институциональные
    полномочия (`OrganizationalAuthority`) — показываются только явно
    присвоенные роли, без вывода/домыслов о дополнительных полномочиях;
  - `app/organizations/dev-authorization-console/page.tsx` —
    **отдельно и явно помеченная** консоль для разработки/тестирования
    (баннер `role="alert"`), демонстрирующая форму default-deny проверки
    региональной области доступа (canon 19e.12, шесть режимов доступа) на
    фиксированных примерных грантах (`app/organizations/authorization.ts`,
    `SAMPLE_ACCESS_GRANTS`). Это не настоящая функция авторизации, вызовов
    к API нет.
- **Доступность**: семантические `<table>`/`<caption>`/`<th scope="col">`,
  ориентиры `<section aria-labelledby>`, `role="group"` для группы
  элементов управления, `aria-live="polite"` для результата проверки и
  выбранного «Stichtag», видимые `:focus-visible`-обводки в
  `globals.css`.

## Запуск

```bash
npm install
npm run dev      # локальная разработка
npm run build    # production build
npm run test     # smoke tests
npm run lint     # ESLint
npm run typecheck
```

## Тесты

- `tests/smoke.test.ts` — проверяет, что главная страница содержит
  заголовок `EPD² Civic OS`.
- `tests/organizations.test.ts` — PACK-08 vertical slice: наличие
  требуемых заголовков/секций, отсутствие `fetch(`/`<form` на всех
  страницах раздела, поведение default-deny-проверки
  (`checkSampleRegionalScopeAccess`) и разрешения исторического статуса
  (`statusAsOf`) на конкретных примерах.
