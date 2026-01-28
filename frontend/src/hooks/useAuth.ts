"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { Session, User } from "@supabase/supabase-js";

export const useAuth = () => {
    const [session, setSession] = useState<Session | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const getSession = async () => {
            const {
                data: { session },
            } = await supabase.auth.getSession();
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        };

        getSession();

        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        return () => subscription?.unsubscribe();
    }, []);

    const signIn = async (email: string, password: string) => {
        const result = await supabase.auth.signInWithPassword({ email, password });
        return result;
    };

    const signUp = async (email: string, password: string) => {
        const result = await supabase.auth.signUp({ email, password });
        return result;
    };

    const signOut = async () => {
        const result = await supabase.auth.signOut();
        return result;
    };

    const resetPassword = async (email: string) => {
        const result = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`,
        });
        return result;
    };

    return {
        session,
        user,
        loading,
        isAuthenticated: !!session,
        signIn,
        signUp,
        signOut,
        resetPassword,
    };
};
