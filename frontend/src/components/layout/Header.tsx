"use client";

import { useState } from "react";
import { useAuth } from "@/hooks";
import { Button } from "@/components/ui/button";
import { LogOut, Loader2 } from "lucide-react";
import { toast } from "@/lib/toast";

export default function Header() {
  const { user, signOut } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      const { error } = await signOut();

      if (error) {
        toast.error("Failed to logout: " + error.message);
        setIsLoggingOut(false);
        return;
      }

      toast.success("Logged out successfully");
      // Use window.location to avoid React hooks issues during auth state change
      window.location.href = "/login";
    } catch (err) {
      toast.error("An error occurred while logging out");
      console.error("Logout error:", err);
      setIsLoggingOut(false);
    }
  };

  return (
    <header className="h-14 border-b bg-background flex items-center justify-between px-6">
      <div className="text-sm text-muted-foreground">Shared dependency workspace</div>
      <div className="flex items-center gap-3">
        <div className="text-sm">
          <div className="font-medium leading-none">{user?.email ?? "You"}</div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          disabled={isLoggingOut}
        >
          {isLoggingOut ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </>
          )}
        </Button>
      </div>
    </header>
  );
}
