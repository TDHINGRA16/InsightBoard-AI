import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

type PublicHeaderProps = {
  showAuthActions?: boolean;
};

export default function PublicHeader({ showAuthActions = true }: PublicHeaderProps) {
  return (
    <header className="h-14 border-b bg-background flex items-center justify-between px-6">
      <Link href="/" className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <span className="text-lg md:text-xl font-semibold md:font-bold tracking-tight">
          InsightBoard
        </span>
      </Link>

      {showAuthActions ? (
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="outline" size="sm">
              Sign In
            </Button>
          </Link>
          <Link href="/signup">
            <Button size="sm">Get Started</Button>
          </Link>
        </div>
      ) : null}
    </header>
  );
}

