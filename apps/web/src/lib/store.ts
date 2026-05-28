import { create } from 'zustand'

interface TestRepositoryState {
  searchQuery: string
  setSearchQuery: (query: string) => void
  selectedModule: string | null
  setSelectedModule: (module: string | null) => void
}

export const useTestRepositoryStore = create<TestRepositoryState>((set) => ({
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
  selectedModule: null,
  setSelectedModule: (module) => set({ selectedModule: module }),
}))
