import { redirect } from "next/navigation";

export default function LegacySubscribeRedirect() {
  redirect("/sign-in");
}
