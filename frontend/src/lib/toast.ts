import { toast as sonnerToast } from "sonner"

type ToastValue = string | number | null | undefined | Error | Record<string, unknown>

const toMessage = (value: ToastValue) => {
  if (value instanceof Error) {
    return value.message || "Something went wrong"
  }

  if (typeof value === "string" || typeof value === "number") {
    return String(value)
  }

  if (value && typeof value === "object") {
    if ("message" in value && typeof value.message === "string") {
      return value.message
    }

    if ("detail" in value && typeof value.detail === "string") {
      return value.detail
    }

    try {
      return JSON.stringify(value)
    } catch {
      return "Something went wrong"
    }
  }

  return "Something went wrong"
}

export const toast = {
  ...sonnerToast,
  success: (value: ToastValue, options?: Parameters<typeof sonnerToast.success>[1]) =>
    sonnerToast.success(toMessage(value), options),
  error: (value: ToastValue, options?: Parameters<typeof sonnerToast.error>[1]) =>
    sonnerToast.error(toMessage(value), options),
  info: (value: ToastValue, options?: Parameters<typeof sonnerToast.info>[1]) =>
    sonnerToast.info(toMessage(value), options),
  warning: (value: ToastValue, options?: Parameters<typeof sonnerToast.warning>[1]) =>
    sonnerToast.warning(toMessage(value), options),
}
