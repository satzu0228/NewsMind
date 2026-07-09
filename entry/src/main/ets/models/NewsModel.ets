// ============================================
// 文件名: entry/src/main/ets/models/NewsModel.ets
// 功能: 数据模型定义（前端数据结构）
// ============================================

// --- 用户认证相关 ---

/**
 * 用户资料
 */
export interface UserProfile {
  id: number
  username: string
  avatar: string
  created_at: string
}

/**
 * 登录/注册响应
 */
export interface AuthResponse {
  success: boolean
  message: string
  token?: string
  user_id?: number
  username?: string
  avatar?: string
}

/**
 * 登录/注册请求体
 */
export class AuthCredential {
  username: string = ''
  password: string = ''
}

/**
 * 更新资料请求体
 */
export class UpdateProfileBody {
  username?: string
  avatar?: string
}

// --- 新闻相关 ---

/**
 * 新闻列表项（简要信息）
 */
export interface NewsItem {
  id: number
  category: string
  content_preview: string    // 正文前200字预览
  length: number
  created_at: string
}

/**
 * 新闻详情（完整信息）
 */
export interface NewsDetail {
  id: number
  category: string
  content: string            // 完整正文
  length: number
  token_length: number
  has_summary: boolean       // 是否已有摘要
  is_favorite: boolean       // 是否已收藏
  created_at: string
}

/**
 * 新闻列表响应
 */
export interface NewsListResponse {
  total: number
  page: number
  page_size: number
  items: NewsItem[]
}

// --- 摘要相关 ---

/**
 * 生成摘要的请求参数
 */
export interface SummaryRequest {
  news_id?: number           // 已有新闻ID
  text?: string              // 或直接输入文本
  top_k?: number             // 关键句数量，默认5
}

/**
 * 摘要生成响应
 */
export interface SummaryResponse {
  news_id: number
  summary_id: number
  extractive_summary: string    // 抽取式摘要
  abstractive_summary: string   // 生成式摘要
  inference_time: number        // 推理耗时（秒）
  rouge_l: number | null
  created_at: string
}

// --- 收藏相关 ---

/**
 * 收藏项
 */
export interface FavoriteItem {
  id: number
  news_id: number
  category: string
  content_preview: string
  length: number
  created_at: string
}

/**
 * 收藏列表响应
 */
export interface FavoriteListResponse {
  total: number
  items: FavoriteItem[]
}

// --- 历史相关 ---

/**
 * 历史记录项
 */
export interface HistoryItem {
  id: number
  news_id: number
  action: string             // read / summarize
  category: string
  content_preview: string
  length: number
  created_at: string
}

/**
 * 历史列表响应
 */
export interface HistoryListResponse {
  total: number
  page: number
  page_size: number
  items: HistoryItem[]
}

// --- 反馈相关 ---

/**
 * 反馈请求
 */
export interface FeedbackRequest {
  news_id?: number
  summary_id?: number
  rating: number             // 1-5
  comment?: string
}

// --- 通用响应 ---

/**
 * 通用消息响应
 */
export interface MessageResponse {
  success: boolean
  message: string
  data?: Record<string, Object>
}

// --- 类别 ---

/**
 * 类别列表响应
 */
export interface CategoriesResponse {
  categories: string[]
  count: number
}
