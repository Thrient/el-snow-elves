import mitt from 'mitt'
import type { NotificationData } from '@/types/notification'

type Events = {
  notification: NotificationData
}

export const eventBus = mitt<Events>()
