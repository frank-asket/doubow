import { SignIn } from "@clerk/nextjs";
import { clerkAppearance } from "@/lib/clerk-appearance";

export default function AuthSignInPage() {
  return (
    <SignIn
      appearance={clerkAppearance}
      path="/sign-in"
      routing="path"
      signUpUrl="/sign-up"
      fallbackRedirectUrl="/discover"
      forceRedirectUrl="/discover"
    />
  );
}
