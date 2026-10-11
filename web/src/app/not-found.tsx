import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-4 px-6">
      <h1 className="text-3xl font-semibold" lang="ru">
        Страница не найдена
      </h1>
      <ul className="space-y-2">
        <li>
          <Link href="/ru" hrefLang="ru" lang="ru">
            Русский
          </Link>
        </li>
        <li>
          <Link href="/uz" hrefLang="uz" lang="uz">
            Oʻzbekcha
          </Link>
        </li>
        <li>
          <Link href="/en" hrefLang="en" lang="en">
            English
          </Link>
        </li>
      </ul>
    </main>
  );
}
