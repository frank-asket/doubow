import { redirect } from "next/navigation";
import type { Route } from "next";

export default function AuthIndexPage() {
  redirect("/auth/sign-in" as Route);
}
