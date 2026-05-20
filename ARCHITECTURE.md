# Архитектура проекта

## 1. Структура файлов

```
site/
├── index.html              # Главная страница
├── about.html              # Обо мне
├── services.html           # Услуги
├── how-it-works.html       # Как проходит консультация
├── blog.html               # Блог
├── faq.html                # FAQ
├── contact.html            # Контакты
├── css/
│   ├── base.css            # Базовые стили, сброс, переменные
│   ├── components.css      # Компоненты (кнопки, карточки, формы)
│   ├── layout.css          # Сетка, хедер, футер
│   ├── pages/
│   │   ├── home.css        # Стили главной страницы
│   │   ├── about.css       # Стили страницы "Обо мне"
│   │   ├── services.css    # Стили страницы услуг
│   │   └── contact.css     # Стили страницы контактов
│   └── responsive.css      # Медиа-запросы для адаптивности
├── js/
│   ├── main.js             # Основной JS (меню, плавная прокрутка)
│   ├── faq.js              # Аккордеон для FAQ
│   └── form.js             # Валидация формы записи
├── img/
│   ├── logo.svg            # Логотип
│   ├── icons/              # Иконки мессенджеров и соцсетей
│   │   ├── telegram.svg
│   │   ├── whatsapp.svg
│   │   ├── instagram.svg
│   │   ├── vk.svg
│   │   └── max.svg
│   └── placeholders/       # Заглушки для фото
└── assets/
    └── fonts/              # Шрифты (если локальные)
```

## 2. Компонентная архитектура

### 2.1 Общие компоненты (переиспользуются на всех страницах)

| Компонент | Описание | Где используется |
|-----------|----------|-----------------|
| Header | Фиксированный хедер с навигацией | Все страницы |
| Footer | Футер с контактами и соцсетями | Все страницы |
| CTA Button | Кнопка призыва к действию | Главная, Услуги, Контакты |
| Service Card | Карточка услуги | Главная, Услуги |
| Messenger Buttons | Блок кнопок мессенджеров | Все страницы |
| Section | Секция с заголовком и контентом | Все страницы |

### 2.2 Уникальные компоненты по страницам

| Страница | Компоненты |
|----------|-----------|
| Главная | Hero, Directions, Testimonials, CTA Banner |
| Обо мне | Timeline (образование), Philosophy Block, Certificates |
| Услуги | Service Grid, Price Table, FAQ Preview |
| Как проходит консультация | Steps, Requirements List, Tech Checklist |
| Блог | Article Grid, Article Card, Pagination |
| FAQ | Accordion, Search (опционально) |
| Контакты | Contact Form, Messenger Links, Map (опционально) |

## 3. CSS Архитектура

### 3.1 CSS Custom Properties (переменные)

```css
:root {
  /* Цвета */
  --color-bg-primary: #F5F0EB;
  --color-bg-secondary: #FFFFFF;
  --color-text-primary: #2D2D2D;
  --color-text-secondary: #6B6B6B;
  --color-accent-green: #7FB069;
  --color-accent-blue: #6B9DAD;
  --color-accent-warm: #D4A574;
  --color-border: #E0D5CC;

  /* Типографика */
  --font-body: 'Inter', system-ui, sans-serif;
  --font-heading: 'Playfair Display', Georgia, serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;
  --text-4xl: 2.5rem;

  /* Отступы */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
  --space-3xl: 4rem;

  /* Скругления */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Тени */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* Переходы */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
  --transition-slow: 400ms ease;
}
```

### 3.2 Breakpoints

| Имя | Ширина | Описание |
|-----|--------|----------|
| mobile | < 768px | Мобильные устройства |
| tablet | 768px – 1023px | Планшеты |
| desktop | 1024px+ | Десктоп |

## 4. JavaScript Архитектура

### 4.1 Модули

| Модуль | Ответственность |
|--------|----------------|
| `navigation.js` | Мобильное меню, бургер, активные ссылки |
| `smooth-scroll.js` | Плавная прокрутка к якорям |
| `faq-accordion.js` | Раскрытие/закрытие вопросов |
| `form-validation.js` | Валидация формы записи |
| `lazy-load.js` | Ленивая загрузка изображений |

### 4.2 Паттерны

- IIFE (Immediately Invoked Function Expression) для изоляции
- Event delegation для динамических элементов
- Progressive enhancement (сайт работает без JS, с JS — лучше)

## 5. Данные и контент

### 5.1 Направления работы

| Направление | Аудитория | Описание |
|-------------|-----------|----------|
| Детская психология | Дети 4-12 лет, родители | Помощь детям в решении эмоциональных и поведенческих трудностей |
| Подростковая психология | Подростки 13-17 лет | Поддержка в период взросления, самооценка, отношения |
| Терапия отношений | Пары | Решение конфликтов, восстановление близости, коммуникация |
| Работа со стрессом | Взрослые | Тревожность, выгорание, панические атаки |
| Личностный рост | Взрослые | Самооценка, границы, жизненные цели |

### 5.2 Мессенджеры для записи

| Платформа | Формат ссылки |
|-----------|--------------|
| Telegram | `https://t.me/username` |
| WhatsApp | `https://wa.me/7XXXXXXXXXX` |
| Instagram | `https://instagram.com/username` |
| VK | `https://vk.com/username` |
| Max | `max://username` (уточнить формат) |

## 6. SEO структура

### 6.1 Мета-теги

Каждая страница содержит:
- `<title>` — уникальный, до 60 символов
- `<meta description>` — до 160 символов
- `<meta keywords>` — опционально
- Open Graph теги (`og:title`, `og:description`, `og:image`)
- Canonical URL

### 6.2 Структура заголовков

```
H1 — один на страницу, основной ключ
H2 — основные секции
H3 — подсекции
H4 — детали (если нужно)
```

## 7. План разработки

| Этап | Задачи | Результат |
|------|--------|-----------|
| 1. Каркас | HTML-структура всех страниц, навигация | Базовый сайт с переходами |
| 2. Стили | CSS переменные, компоненты, адаптивность | Визуально готовый сайт |
| 3. Контент | Тексты для всех страниц | Заполненный сайт |
| 4. Интерактив | JS: меню, аккордеон, валидация | Функциональный сайт |
| 5. Финализация | SEO, мета-теги, оптимизация | Готовый к публикации сайт |
