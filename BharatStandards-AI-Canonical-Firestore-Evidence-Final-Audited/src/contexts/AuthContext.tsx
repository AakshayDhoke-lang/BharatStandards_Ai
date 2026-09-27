import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  createUserWithEmailAndPassword, onAuthStateChanged, sendPasswordResetEmail,
  signInWithEmailAndPassword, signInWithPopup, signOut, updateProfile, type User,
} from "firebase/auth";
import { doc, onSnapshot } from "firebase/firestore";
import { auth, db, firebaseConfigured, googleProvider } from "@/lib/firebase";
import { ensureUserProfile, type UserRole } from "@/lib/knowledge-base";

interface AuthContextValue {
  user: User | null;
  role: UserRole;
  loading: boolean;
  firebaseConfigured: boolean;
  signInEmail: (email: string, password: string) => Promise<void>;
  signUpEmail: (email: string, password: string, displayName?: string) => Promise<void>;
  signInGoogle: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<UserRole>("USER");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!firebaseConfigured) { setLoading(false); return; }
    let stopProfile: (() => void) | undefined;
    return onAuthStateChanged(auth, async (nextUser) => {
      stopProfile?.(); stopProfile = undefined;
      setUser(nextUser);
      if (!nextUser) { setRole("USER"); setLoading(false); return; }
      try { await ensureUserProfile(nextUser); } catch { /* rules/network errors remain visible on data pages */ }
      stopProfile = onSnapshot(doc(db, "users", nextUser.uid), snap => {
        const value = String(snap.data()?.role || "USER").toUpperCase();
        setRole((["USER","CONTRIBUTOR","REVIEWER","ADMIN"].includes(value) ? value : "USER") as UserRole);
        setLoading(false);
      }, () => { setRole("USER"); setLoading(false); });
    });
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user, role, loading, firebaseConfigured,
    signInEmail: async (email, password) => { await signInWithEmailAndPassword(auth, email, password); },
    signUpEmail: async (email, password, displayName) => {
      const credential = await createUserWithEmailAndPassword(auth, email, password);
      if (displayName?.trim()) await updateProfile(credential.user, { displayName: displayName.trim() });
      await ensureUserProfile(credential.user);
    },
    signInGoogle: async () => { const credential = await signInWithPopup(auth, googleProvider); await ensureUserProfile(credential.user); },
    resetPassword: async (email) => { await sendPasswordResetEmail(auth, email); },
    logout: async () => { await signOut(auth); },
  }), [user, role, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
