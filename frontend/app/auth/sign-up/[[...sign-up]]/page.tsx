import { SignUp } from "@clerk/nextjs";
import { clerkAppearance } from "@/lib/clerk-appearance";

export default function AuthSignUpPage() {
  return (
    <SignUp
      appearance={clerkAppearance}
      path="/sign-up"
      routing="path"
      signInUrl="/sign-in"
      fallbackRedirectUrl="/discover"
      forceRedirectUrl="/discover"
    />
  );
}
