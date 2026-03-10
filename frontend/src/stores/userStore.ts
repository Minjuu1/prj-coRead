import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserStore {
  userId: string | null
  setUserId: (id: string) => void
  logout: () => void
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      userId: null,
      setUserId: (id) => set({ userId: id }),
      logout: () => set({ userId: null }),
    }),
    { name: 'coread-user' }
  )
)
