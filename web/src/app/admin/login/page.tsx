import { LoginForm } from "@/components/admin/login-form";
import { readLocale } from "@/lib/locale";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const locale = await readLocale();
  return <LoginForm locale={locale} />;
}
