import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DashboardPage from '../src/app/dashboard/page'

jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: { user: { name: "Test User", role: "super_admin" } },
    status: "authenticated",
  })),
  signOut: jest.fn()
}))

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() })
}))

describe('DashboardPage', () => {
  it('renders dashboard overview correctly', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument()
    expect(screen.getByText('Total Test Cases')).toBeInTheDocument()
  })
})
