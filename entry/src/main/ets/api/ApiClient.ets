// ============================================
// 文件名: entry/src/main/ets/api/ApiClient.ets
// 功能: HTTP 请求客户端
// ============================================

import http from '@ohos.net.http'
import { ApiConfig } from './ApiConfig'

/**
 * HTTP 请求配置接口
 */
interface RequestConfig {
  url: string
  method: http.RequestMethod
  body?: Object
}

/**
 * 发送 HTTP 请求
 */
export async function request<T>(url: string, method: http.RequestMethod, body?: Object): Promise<T> {
  const fullUrl: string = ApiConfig.BASE_URL + url
  const httpRequest: http.HttpRequest = http.createHttp()

  // 构建请求选项
  const options: http.HttpRequestOptions = {
    method: method,
    header: { 'Content-Type': 'application/json' },
    connectTimeout: ApiConfig.TIMEOUT,
    readTimeout: ApiConfig.TIMEOUT
  }

  // POST/PUT 请求体
  if (body !== undefined && (method === http.RequestMethod.POST || method === http.RequestMethod.PUT)) {
    options.extraData = JSON.stringify(body) as string | ArrayBuffer
  }

  try {
    const response: http.HttpResponse = await httpRequest.request(fullUrl, options)

    if (response.responseCode === 200 || response.responseCode === 201) {
      const resultStr: string = response.result as string
      const result: T = JSON.parse(resultStr) as T
      return result
    } else {
      const errorMsg: string = `HTTP ${response.responseCode}`
      console.error(`[API] ${errorMsg} ${url}`)
      throw new Error(errorMsg)
    }
  } catch (err) {
    const error: Error = err as Error
    console.error(`[API] ${method} ${url}: ${error.message}`)
    throw error
  } finally {
    httpRequest.destroy()
  }
}

/**
 * GET 请求
 */
export async function get<T>(url: string): Promise<T> {
  return request<T>(url, http.RequestMethod.GET)
}

/**
 * POST 请求
 */
export async function post<T>(url: string, body?: Object): Promise<T> {
  return request<T>(url, http.RequestMethod.POST, body)
}

/**
 * DELETE 请求
 */
export async function del<T>(url: string): Promise<T> {
  return request<T>(url, http.RequestMethod.DELETE)
}
