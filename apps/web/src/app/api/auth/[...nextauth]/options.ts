import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

/** Server-side API base (Docker: api:8000). Browser uses NEXT_PUBLIC_API_URL via rewrites. */
function getAuthApiBaseUrl(): string {
  return (
    process.env.API_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");
}

export const authOptions: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET || "dev-nextauth-secret-change-me-in-production-32chars",
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Email", type: "text", placeholder: "you@example.com" },
        password: { label: "Password", type: "password" }
      },
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
      async authorize(credentials, _req) {
        try {          if (!credentials?.username || !credentials?.password) return null;
                    const res = await fetch(`${getAuthApiBaseUrl()}/api/v1/auth/login`, {
            method: 'POST',
            body: new URLSearchParams({
              username: credentials.username,
              password: credentials.password,
            }),
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
          });
          const data = await res.json();
          if (res.ok && data.user) {
            return {
              id: data.user.id,
              name: data.user.name,
              email: data.user.email,
              role: data.user.role,
              tenantId: data.user.tenant_id,
              accessToken: data.access_token,
            };
          }
          return null;
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_e) {
          return null;
        }
      }
    })
  ],
  callbacks: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async jwt({ token, user }: { token: any, user: any }) {
      if (user) {
        token.role = user.role;
        token.tenantId = user.tenantId;
        token.accessToken = user.accessToken;
      }
      return token;
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async session({ session, token }: { session: any, token: any }) {
      if (token) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (session.user as any).role = token.role;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (session.user as any).tenantId = token.tenantId;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (session as any).accessToken = token.accessToken;
      }
      return session;
    }
  },
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: '/login',
  }
};
