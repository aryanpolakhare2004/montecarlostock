import { inject, type InjectionKey } from 'vue';

export type ToastKind = 'success' | 'error' | 'info';

export interface ToastContextValue {
  showToast: (message: string, kind?: ToastKind) => void;
  dismissToast: (id: number) => void;
}

export const ToastKey: InjectionKey<ToastContextValue> = Symbol('toast');

export function useToast(): ToastContextValue {
  const ctx = inject(ToastKey);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}
