// ============================================
// 文件名: entry/src/main/ets/api/ApiConfig.ets
// 功能: API 地址配置
// ============================================

/**
 * API 配置类
 */
export class ApiConfig {
  // 开发环境地址
  // 模拟器用 10.0.2.2 访问宿主机，真机用电脑局域网 IP
  static readonly BASE_URL: string = "http://10.0.2.2:8000"

  // 请求超时（毫秒）
  static readonly TIMEOUT: number = 30000

  // API 路径 — 认证
  static readonly AUTH_REGISTER: string = "/auth/register"
  static readonly AUTH_LOGIN: string = "/auth/login"
  static readonly AUTH_LOGOUT: string = "/auth/logout"
  static readonly AUTH_PROFILE: string = "/auth/profile"

  // API 路径 — 业务
  static readonly NEWS_LIST: string = "/news"
  static readonly NEWS_CATEGORIES: string = "/news/categories/all"
  static readonly SUMMARY: string = "/summary"
  static readonly FAVORITE: string = "/favorite"
  static readonly HISTORY: string = "/history"
  static readonly FEEDBACK: string = "/feedback"
  static readonly HEALTH: string = "/health"

  /**
   * 获取新闻详情路径
   */
  static newsDetailPath(id: number): string {
    return `/news/${id}`
  }
}
