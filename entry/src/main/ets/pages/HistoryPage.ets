// ============================================
// 文件名: entry/src/main/ets/pages/HistoryPage.ets
// 功能: 阅读历史页面 - 分类/搜索/历史记录列表
// ============================================

import { HistoryItem, HistoryListResponse, NewsItem } from '../models/NewsModel'
import { fetchHistory, fetchCategories } from '../api/NewsApi'
import { NewsCard } from '../components/NewsCard'
import { CategoryTab } from '../components/CategoryTab'
import { SearchBar } from '../components/SearchBar'
import { LoadingView, EmptyView, ErrorView } from '../components/LoadingView'
import router from '@ohos.router'

/**
 * 阅读历史页面
 */
@Entry
@Component
export struct HistoryPage {
  @State historyList: HistoryItem[] = []
  @State categories: string[] = []
  @State selectedCategory: string = ''
  @State searchKeyword: string = ''
  @State isSearchMode: boolean = false
  @State currentPage: number = 1
  @State totalCount: number = 0
  @State isLoading: boolean = false
  @State isRefreshing: boolean = false
  @State hasError: boolean = false

  aboutToAppear(): void {
    this.loadCategories()
    this.loadHistory(true)
  }

  private async loadCategories(): Promise<void> {
    try {
      const result = await fetchCategories()
      this.categories = result.categories
    } catch (err) {
      // 静默失败
    }
  }

  private async loadHistory(isRefresh: boolean = false): Promise<void> {
    if (this.isLoading) return
    if (isRefresh) {
      this.isRefreshing = true
      this.currentPage = 1
    } else {
      this.isLoading = true
    }
    this.hasError = false
    try {
      const response: HistoryListResponse = await fetchHistory(
        this.currentPage, 20,
        undefined,
        this.selectedCategory || undefined,
        this.searchKeyword || undefined
      )
      if (isRefresh || this.currentPage === 1) {
        this.historyList = response.items
      } else {
        this.historyList = this.historyList.concat(response.items)
      }
      this.totalCount = response.total
    } catch (err) {
      this.hasError = true
    } finally {
      this.isLoading = false
      this.isRefreshing = false
    }
  }

  private toNewsItem(item: HistoryItem): NewsItem {
    const newsItem: NewsItem = {
      id: item.news_id,
      category: item.category,
      content_preview: item.content_preview,
      length: item.length || 0,
      created_at: item.created_at
    }
    return newsItem
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('← 返回')
          .fontSize(16)
          .fontColor('#007AFF')
          .onClick(() => router.back())

        Blank()

        Text('阅读历史')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)

        Blank()

        if (this.totalCount > 0) {
          Text(`${this.totalCount} 条`)
            .fontSize(13)
            .fontColor('#999999')
        } else {
          Text('    ')
            .fontSize(16)
        }
      }
      .width('100%')
      .height(48)
      .padding({ left: 16, right: 16 })
      .backgroundColor('#FFFFFF')

      // 搜索栏
      SearchBar({
        onSearch: (keyword: string) => {
          this.searchKeyword = keyword
          this.isSearchMode = keyword.length > 0
          this.loadHistory(true)
        },
        onClear: () => {
          this.searchKeyword = ''
          this.isSearchMode = false
          this.loadHistory(true)
        }
      })
        .padding({ left: 16, right: 16, bottom: 8, top: 8 })

      // 分类标签
      if (!this.isSearchMode) {
        CategoryTab({
          categories: this.categories,
          selectedCategory: $selectedCategory,
          onCategoryChanged: (category: string) => {
            this.selectedCategory = category
            this.loadHistory(true)
          }
        })
      }

      // 内容区域
      if (this.hasError && this.historyList.length === 0) {
        ErrorView({ message: '历史加载失败', onRetry: () => this.loadHistory(true) })
      } else if (!this.isLoading && this.historyList.length === 0 && !this.isRefreshing) {
        EmptyView({
          icon: '🕐',
          title: this.isSearchMode ? '未找到匹配的历史' : '暂无浏览记录',
          subtitle: this.isSearchMode ? '请尝试其他关键词或分类' : '浏览新闻后会自动记录'
        })
      } else {
        Refresh({ refreshing: $$this.isRefreshing }) {
          List() {
            ForEach(this.historyList, (item: HistoryItem, index: number) => {
              ListItem() {
                Stack({ alignContent: Alignment.TopEnd }) {
                  NewsCard({
                    news: this.toNewsItem(item),
                    onCardClick: () => {
                      router.pushUrl({
                        url: 'pages/NewsDetailPage',
                        params: { news_id: item.news_id, category: item.category }
                      })
                    }
                  })
                  Text(item.action === 'summarize' ? '🤖' : '👁️')
                    .fontSize(14)
                    .margin({ top: 14, right: 14 })
                }
              }
              .margin({ left: 16, right: 16, top: index === 0 ? 8 : 0, bottom: 8 })
            })

            if (this.isLoading) {
              ListItem() { LoadingView({ message: '加载更多...' }) }
            }

            if (this.historyList.length >= this.totalCount && this.historyList.length > 0) {
              ListItem() {
                Text('— 已经到底了 —')
                  .fontSize(12)
                  .fontColor('#CCCCCC')
                  .width('100%')
                  .textAlign(TextAlign.Center)
                  .padding({ top: 12, bottom: 24 })
              }
            }
          }
          .width('100%')
          .scrollBar(BarState.Off)
          .onReachEnd(() => {
            if (this.historyList.length < this.totalCount) {
              this.currentPage++
              this.loadHistory(false)
            }
          })
        }
        .layoutWeight(1)
        .onRefreshing(() => {
          this.loadHistory(true)
        })
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F2F7')
  }
}
