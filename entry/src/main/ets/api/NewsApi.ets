// ============================================
// 文件名: entry/src/main/ets/api/NewsApi.ets
// 功能: NewsMind 业务 API
// ============================================

import { ApiConfig } from './ApiConfig'
import { get, post, del } from './ApiClient'
import {
  NewsListResponse, NewsDetail, CategoriesResponse,
  SummaryResponse, SummaryRequest,
  FavoriteListResponse, FeedbackRequest,
  HistoryListResponse, MessageResponse
} from '../models/NewsModel'

// ============================================
// 新闻 API
// ============================================

/**
 * 获取新闻列表
 */
export async function fetchNewsList(
  page: number, pageSize: number, category?: string, keyword?: string
): Promise<NewsListResponse> {
  let url: string = `${ApiConfig.NEWS_LIST}?page=${page}&page_size=${pageSize}`
  if (category && category.length > 0) {
    url += `&category=${encodeURIComponent(category)}`
  }
  if (keyword && keyword.length > 0) {
    url += `&keyword=${encodeURIComponent(keyword)}`
  }
  return get<NewsListResponse>(url)
}

/**
 * 获取新闻详情
 */
export async function fetchNewsDetail(id: number): Promise<NewsDetail> {
  const url: string = ApiConfig.newsDetailPath(id)
  return get<NewsDetail>(url)
}

/**
 * 获取所有类别
 */
export async function fetchCategories(): Promise<CategoriesResponse> {
  return get<CategoriesResponse>(ApiConfig.NEWS_CATEGORIES)
}

// ============================================
// 摘要 API
// ============================================

/**
 * 生成摘要
 */
export async function generateSummary(
  newsId?: number, text?: string, topK: number = 5
): Promise<SummaryResponse> {
  const body: SummaryRequest = { top_k: topK }
  if (newsId !== undefined) {
    body.news_id = newsId
  }
  if (text !== undefined) {
    body.text = text
  }
  return post<SummaryResponse>(ApiConfig.SUMMARY, body)
}

// ============================================
// 收藏 API
// ============================================

/**
 * 添加收藏
 */
export async function addFavorite(newsId: number): Promise<MessageResponse> {
  const body: Record<string, number> = { 'news_id': newsId }
  return post<MessageResponse>(ApiConfig.FAVORITE, body)
}

/**
 * 取消收藏
 */
export async function removeFavorite(newsId: number): Promise<MessageResponse> {
  return del<MessageResponse>(`${ApiConfig.FAVORITE}?news_id=${newsId}`)
}

/**
 * 获取收藏列表
 */
export async function fetchFavorites(
  page: number, pageSize: number, category?: string, keyword?: string
): Promise<FavoriteListResponse> {
  let url: string = `${ApiConfig.FAVORITE}?page=${page}&page_size=${pageSize}`
  if (category && category.length > 0) {
    url += `&category=${encodeURIComponent(category)}`
  }
  if (keyword && keyword.length > 0) {
    url += `&keyword=${encodeURIComponent(keyword)}`
  }
  return get<FavoriteListResponse>(url)
}

// ============================================
// 历史 API
// ============================================

/**
 * 获取操作历史
 */
export async function fetchHistory(page: number, pageSize: number, action?: string): Promise<HistoryListResponse> {
  let url: string = `${ApiConfig.HISTORY}?page=${page}&page_size=${pageSize}`
  if (action && action.length > 0) {
    url += `&action=${action}`
  }
  return get<HistoryListResponse>(url)
}

// ============================================
// 反馈 API
// ============================================

/**
 * 提交反馈
 */
export async function submitFeedback(
  rating: number, comment?: string, newsId?: number, summaryId?: number
): Promise<MessageResponse> {
  const body: FeedbackRequest = { rating: rating }
  if (comment !== undefined) {
    body.comment = comment
  }
  if (newsId !== undefined) {
    body.news_id = newsId
  }
  if (summaryId !== undefined) {
    body.summary_id = summaryId
  }
  return post<MessageResponse>(ApiConfig.FEEDBACK, body)
}
