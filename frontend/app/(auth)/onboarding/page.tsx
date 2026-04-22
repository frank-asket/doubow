import { redirect } from "next/navigation";

export default function LegacyOnboardingRedirect() {
  redirect("/auth/sign-up");
}
