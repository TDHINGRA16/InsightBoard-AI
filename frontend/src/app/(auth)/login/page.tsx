import { LoginForm } from "@/components/auth";
import { GitBranch } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    <Link href="/" className="flex items-center gap-2">
                        <GitBranch className="h-10 w-10 text-cyan-400" />
                        <span className="font-bold text-2xl text-white">InsightBoard</span>
                    </Link>
                </div>

                {/* Form */}
                <LoginForm />
            </div>
        </div>
    );
}
