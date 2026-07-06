// ============================================
// 文件名: entry/src/main/ets/api/ApiConfig.ets
// 功能: API 地址配置
// ============================================

/**
 * API 配置类
 */
export class ApiConfig {
  // 开发环境地址
  static readonly BASE_URL: string = "http://10.0.2.2:8000"

  // 请求超时（毫秒）
  static readonly TIMEOUT: number = 30000

  // API 路径
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
