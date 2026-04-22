import { redirect } from "next/navigation";

export default function LegacySubscribeRedirect() {
  redirect("/auth/sign-in");
}
