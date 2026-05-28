import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    user: {
      id: string
      role: string
      tenantId: string
    } & DefaultSession["user"]
  }

  interface User {
    id: string
    role: string
    tenantId: string
    accessToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: string
    tenantId?: string
    accessToken?: string
  }
}
