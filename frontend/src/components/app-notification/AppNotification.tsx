import { useEffect } from 'react'
import { App } from 'antd'
import { eventBus } from '@/utils/event-bus'
import type { NotificationData } from '@/types/notification'

const AppNotification = () => {
  const { notification } = App.useApp()

  useEffect(() => {
    window.__eventBus = eventBus

    const handler = (data: NotificationData) => {
      notification.open({
        message: data.title,
        description: data.description,
        type: data.type ?? 'info',
        duration: data.duration != null ? data.duration / 1000 : 5,
      })
    }

    eventBus.on('notification', handler)
    return () => {
      eventBus.off('notification', handler)
      delete window.__eventBus
    }
  }, [notification])

  return null
}

export default AppNotification
