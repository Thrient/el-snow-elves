export type NotificationType = 'success' | 'info' | 'warning' | 'error'

export interface NotificationData {
  title: string
  description: string
  type: NotificationType
  duration: number
}
