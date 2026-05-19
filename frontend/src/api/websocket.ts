import { ElMessage } from 'element-plus'

const WS_RECONNECT_INTERVAL = 3000
const WS_MAX_RETRIES = 5

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private token: string
  private retries = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private messageHandlers: Map<string, (data: any) => void> = new Map()
  private onConnectHandlers: (() => void)[] = []
  private onDisconnectHandlers: (() => void)[] = []

  constructor(url: string, token: string) {
    this.url = url
    this.token = token
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const fullUrl = `${this.url}?token=${this.token}`
      this.ws = new WebSocket(fullUrl)

      this.ws.onopen = () => {
        this.retries = 0
        this.onConnectHandlers.forEach(handler => handler())
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const type = data.type || 'message'
          const handler = this.messageHandlers.get(type)
          if (handler) {
            handler(data)
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }

      this.ws.onclose = () => {
        this.onDisconnectHandlers.forEach(handler => handler())
        this.scheduleReconnect()
      }
    })
  }

  private scheduleReconnect() {
    if (this.retries >= WS_MAX_RETRIES) {
      ElMessage.error('WebSocket 连接失败，请刷新页面')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      this.retries++
      this.connect().catch(() => {})
    }, WS_RECONNECT_INTERVAL)
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  sendBinary(data: Uint8Array) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    }
  }

  on(type: string, handler: (data: any) => void) {
    this.messageHandlers.set(type, handler)
  }

  off(type: string) {
    this.messageHandlers.delete(type)
  }

  onConnect(handler: () => void) {
    this.onConnectHandlers.push(handler)
  }

  onDisconnect(handler: () => void) {
    this.onDisconnectHandlers.push(handler)
  }

  get readyState() {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const createEventsWS = (runId: string, token: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${protocol}//${host}/ws/runs/${runId}/events`
  return new WebSocketClient(url, token)
}

export const createTerminalWS = (runId: string, token: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${protocol}//${host}/ws/runs/${runId}/terminal`
  return new WebSocketClient(url, token)
}
