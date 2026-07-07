// ============================================
// 文件名: entry/src/main/ets/pages/MainPage.ets
// 功能: 主页面 - 底部Tab导航
// 结构: 首页 | 收藏 | 我的
// 所有子组件(HomeContent/FavoriteContent/ProfileContent)内联定义,
// 因为 @Entry 页面不能被其他组件引用。
// ============================================

import { NewsItem, NewsListResponse, FavoriteItem, FavoriteListResponse, HistoryItem, HistoryListResponse } from '../models/NewsModel'
import { fetchNewsList, fetchCategories, fetchFavorites, removeFavorite, fetchHistory, submitFeedback } from '../api/NewsApi'
import { NewsCard } from '../components/NewsCard'
import { CategoryTab } from '../components/CategoryTab'
import { SearchBar } from '../components/SearchBar'
import { LoadingView, EmptyView, ErrorView } from '../components/LoadingView'
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'

/**
 * 主页面 - 底部 Tab 导航容器
 */
@Entry
@Component
struct MainPage {
  @State currentTabIndex: number = 0

  // Tab 标题
  private tabTitles: string[] = ['首页', '收藏', '我的']
  // Tab 图标（未选中）
  private tabIcons: string[] = ['🏠', '🤍', '👤']
  // Tab 图标（选中）
  private tabActiveIcons: string[] = ['🏠', '❤️', '👤']

  build() {
    Tabs({ barPosition: BarPosition.End }) {
      // ===== Tab 0: 首页 =====
      TabContent() {
        HomeContent()
      }
      .tabBar(this.tabBuilder(0))

      // ===== Tab 1: 收藏 =====
      TabContent() {
        FavoriteContent()
      }
      .tabBar(this.tabBuilder(1))

      // ===== Tab 2: 我的 =====
      TabContent() {
        ProfileContent()
      }
      .tabBar(this.tabBuilder(2))
    }
    .barHeight(56)
    .barBackgroundColor('#FFFFFF')
    .onChange((index: number) => {
      this.currentTabIndex = index
    })
    .width('100%')
    .height('100%')
  }

  @Builder
  tabBuilder(index: number) {
    Column() {
      Text(this.currentTabIndex === index
        ? this.tabActiveIcons[index]
        : this.tabIcons[index])
        .fontSize(22)

      Text(this.tabTitles[index])
        .fontSize(10)
        .fontColor(this.currentTabIndex === index ? '#007AFF' : '#8E8E93')
        .margin({ top: 2 })
    }
    .width('100%')
    .padding({ top: 4 })
  }
}

// ============================================
// 首页内容组件（内联，避免跨 @Entry 引用）
// ============================================

@Component
struct HomeContent {
  @State newsList: NewsItem[] = []
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
    this.loadNewsList()
  }

  private async loadNewsList(isRefresh: boolean = false): Promise<void> {
    if (this.isLoading) return
    if (isRefresh) {
      this.isRefreshing = true
      this.currentPage = 1
    } else {
      this.isLoading = true
    }
    this.hasError = false
    try {
      const response: NewsListResponse = await fetchNewsList(
        this.currentPage, 20,
        this.selectedCategory || undefined,
        this.searchKeyword || undefined
      )
      if (isRefresh || this.currentPage === 1) {
        this.newsList = response.items
      } else {
        this.newsList = this.newsList.concat(response.items)
      }
      this.totalCount = response.total
    } catch (err) {
      this.hasError = true
    } finally {
      this.isLoading = false
      this.isRefreshing = false
    }
  }

  private async loadCategories(): Promise<void> {
    try {
      const result = await fetchCategories()
      this.categories = result.categories
    } catch (err) {
      // 静默失败
    }
  }

  build() {
    Column() {
      // 标题
      Row() {
        Text('NewsMind')
          .fontSize(28)
          .fontWeight(FontWeight.Bold)
        Blank()
        if (this.totalCount > 0) {
          Text(`${this.totalCount} 篇`)
            .fontSize(13)
            .fontColor('#999999')
        }
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12, bottom: 8 })

      // 搜索栏
      SearchBar({
        onSearch: (keyword: string) => {
          this.searchKeyword = keyword
          this.isSearchMode = keyword.length > 0
          this.currentPage = 1
          this.loadNewsList(true)
        },
        onClear: () => {
          this.searchKeyword = ''
          this.isSearchMode = false
          this.currentPage = 1
          this.loadNewsList(true)
        }
      })
        .padding({ left: 16, right: 16, bottom: 8 })

      // 分类标签
      if (!this.isSearchMode) {
        CategoryTab({
          categories: this.categories,
          selectedCategory: $selectedCategory,
          onCategoryChanged: (category: string) => {
            this.selectedCategory = category
            this.currentPage = 1
            this.loadNewsList(true)
          }
        })
      }

      // 内容区域
      if (this.hasError && this.newsList.length === 0) {
        ErrorView({ message: '新闻加载失败，请检查网络', onRetry: () => this.loadNewsList(true) })
      } else if (!this.isLoading && this.newsList.length === 0 && !this.isRefreshing) {
        EmptyView({
          icon: '📰',
          title: this.isSearchMode ? '未找到相关新闻' : '暂无新闻数据',
          subtitle: this.isSearchMode ? '请尝试其他关键词' : '请先导入新闻数据到后端'
        })
      } else {
        Refresh({ refreshing: $$this.isRefreshing }) {
          List() {
            ForEach(this.newsList, (news: NewsItem, index: number) => {
              ListItem() {
                NewsCard({
                  news: news,
                  onCardClick: () => {
                    router.pushUrl({
                      url: 'pages/NewsDetailPage',
                      params: { news_id: news.id, category: news.category }
                    })
                  }
                })
              }
              .margin({ left: 16, right: 16, top: index === 0 ? 8 : 0, bottom: 8 })
            })

            if (this.isLoading) {
              ListItem() { LoadingView({ message: '加载更多...' }) }
            }

            if (this.newsList.length >= this.totalCount && this.newsList.length > 0) {
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
          .layoutWeight(1)
          .scrollBar(BarState.Off)
          .onReachEnd(() => {
            if (this.newsList.length < this.totalCount) {
              this.currentPage++
              this.loadNewsList(false)
            }
          })
        }
        .onRefreshing(() => {
          this.loadNewsList(true)
        })
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F2F7')
  }
}

// ============================================
// 收藏内容组件
// ============================================

@Component
struct FavoriteContent {
  @State favorites: FavoriteItem[] = []
  @State isLoading: boolean = true
  @State hasError: boolean = false

  aboutToAppear(): void {
    this.loadFavorites()
  }

  private async loadFavorites(): Promise<void> {
    this.isLoading = true
    this.hasError = false
    try {
      const response: FavoriteListResponse = await fetchFavorites(1, 100)
      this.favorites = response.items
    } catch (err) {
      this.hasError = true
    } finally {
      this.isLoading = false
    }
  }

  private async onRemoveFavorite(newsId: number, index: number): Promise<void> {
    try {
      await removeFavorite(newsId)
      this.favorites.splice(index, 1)
      promptAction.showToast({ message: '已取消收藏', duration: 1500 })
    } catch (err) {
      promptAction.showToast({ message: '操作失败', duration: 1500 })
    }
  }

  private toNewsItem(fav: FavoriteItem): NewsItem {
    const item: NewsItem = {
      id: fav.news_id, category: fav.category,
      content_preview: fav.content_preview, length: 0, created_at: fav.created_at
    }
    return item
  }

  build() {
    Column() {
      Row() {
        Text('我的收藏').fontSize(28).fontWeight(FontWeight.Bold)
        Blank()
        Text(`${this.favorites.length} 篇`).fontSize(13).fontColor('#999999')
      }
      .width('100%').padding({ left: 16, right: 16, top: 12, bottom: 8 })

      if (this.isLoading) {
        LoadingView({ message: '加载收藏...' })
      } else if (this.hasError) {
        ErrorView({ message: '收藏加载失败', onRetry: () => this.loadFavorites() })
      } else if (this.favorites.length === 0) {
        EmptyView({ icon: '⭐', title: '暂无收藏', subtitle: '浏览新闻时点击收藏即可添加' })
      } else {
        List() {
          ForEach(this.favorites, (fav: FavoriteItem, index: number) => {
            ListItem() {
              Stack({ alignContent: Alignment.TopEnd }) {
                NewsCard({
                  news: this.toNewsItem(fav),
                  onCardClick: () => {
                    router.pushUrl({
                      url: 'pages/NewsDetailPage',
                      params: { news_id: fav.news_id, category: fav.category }
                    })
                  }
                })
                Text('🗑️').fontSize(18).margin({ top: 14, right: 14 })
                  .onClick(() => this.onRemoveFavorite(fav.news_id, index))
              }
            }
            .margin({ left: 16, right: 16, top: index === 0 ? 8 : 0, bottom: 8 })
          })
        }
        .width('100%').layoutWeight(1).scrollBar(BarState.Off)
      }
    }
    .width('100%').height('100%').backgroundColor('#F2F2F7')
  }
}

// ============================================
// 我的页内容组件
// ============================================

interface MenuItem {
  icon: string
  title: string
  subtitle: string
}

@Component
struct ProfileContent {
  @State recentHistory: HistoryItem[] = []
  @State isLoadingHistory: boolean = false
  @State showFeedbackPanel: boolean = false
  @State profileFeedbackRating: number = 0
  @State profileFeedbackComment: string = ''
  @State isSubmittingProfileFeedback: boolean = false

  private menuItems: MenuItem[] = [
    { icon: '🕐', title: '阅读历史', subtitle: '查看最近浏览的新闻' },
    { icon: '📊', title: '数据统计', subtitle: '查看使用数据和分析' },
    { icon: '💬', title: '意见反馈', subtitle: '帮助我们改进产品' },
    { icon: 'ℹ️', title: '关于 NewsMind', subtitle: '版本 1.0.0 | BERT + T5' }
  ]

  aboutToAppear(): void {
    this.loadHistory()
  }

  private async loadHistory(): Promise<void> {
    this.isLoadingHistory = true
    try {
      const response: HistoryListResponse = await fetchHistory(1, 5)
      this.recentHistory = response.items
    } catch (err) {
      // 静默
    } finally {
      this.isLoadingHistory = false
    }
  }

  private onShowAllHistory(): void {
    promptAction.showToast({ message: `History: ${this.recentHistory.length} recent items`, duration: 1800 })
  }

  private onOpenHistoryItem(item: HistoryItem): void {
    router.pushUrl({
      url: 'pages/NewsDetailPage',
      params: { news_id: item.news_id, category: item.category }
    })
  }

  private onMenuClick(index: number): void {
    if (index === 0) {
      promptAction.showToast({ message: `Showing ${this.recentHistory.length} recent history items`, duration: 1800 })
      return
    }
    if (index === 1) {
      AlertDialog.show({
        title: 'Stats',
        message: `Recent history: ${this.recentHistory.length}\nRead and summary records are connected to the backend history API.`,
        primaryButton: { value: 'OK', action: () => {} }
      })
      return
    }
    if (index === 2) {
      this.showFeedbackPanel = !this.showFeedbackPanel
      return
    }
    AlertDialog.show({
      title: 'About NewsMind',
      message: 'NewsMind 1.0.0\nNews summarization app based on ArkTS, BERT, TextRank and Transformer.',
      primaryButton: { value: 'OK', action: () => {} }
    })
  }

  private async onSubmitProfileFeedback(): Promise<void> {
    if (this.profileFeedbackRating <= 0) {
      promptAction.showToast({ message: 'Please select a rating first', duration: 1500 })
      return
    }
    if (this.isSubmittingProfileFeedback) return

    this.isSubmittingProfileFeedback = true
    try {
      await submitFeedback(this.profileFeedbackRating, this.profileFeedbackComment)
      promptAction.showToast({ message: 'Feedback submitted', duration: 1500 })
      this.profileFeedbackRating = 0
      this.profileFeedbackComment = ''
      this.showFeedbackPanel = false
    } catch (err) {
      promptAction.showToast({ message: 'Feedback failed', duration: 1500 })
    } finally {
      this.isSubmittingProfileFeedback = false
    }
  }

  build() {
    Column() {
      Row() {
        Text('我的').fontSize(28).fontWeight(FontWeight.Bold)
      }
      .width('100%').padding({ left: 16, right: 16, top: 12, bottom: 4 })

      Scroll() {
        Column() {
          // 用户卡片
          Row() {
            Column() {
              Text('NM').fontSize(20).fontColor('#FFFFFF').fontWeight(FontWeight.Bold)
            }
            .width(56).height(56).backgroundColor('#007AFF').borderRadius(28).justifyContent(FlexAlign.Center)
            Column() {
              Text('NewsMind 用户').fontSize(17).fontWeight(FontWeight.Medium)
              Text('AI 驱动 · 智能新闻摘要').fontSize(13).fontColor('#999999').margin({ top: 4 })
            }
            .alignItems(HorizontalAlign.Start).margin({ left: 14 })
          }
          .width('100%').padding(16).backgroundColor('#FFFFFF').borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          // 最近历史
          Column() {
            Row() {
              Text('最近浏览').fontSize(16).fontWeight(FontWeight.Medium)
              Blank()
              Text('查看全部 >').fontSize(12).fontColor('#007AFF')
            }
            .width('100%').margin({ bottom: 10 })
            .onClick(() => this.onShowAllHistory())
            if (this.isLoadingHistory) {
              LoadingView({ message: '加载中...' }).height(80)
            } else if (this.recentHistory.length === 0) {
              Text('暂无浏览记录').fontSize(13).fontColor('#999999').padding(20)
                .width('100%').textAlign(TextAlign.Center)
            } else {
              ForEach(this.recentHistory, (item: HistoryItem) => {
                Row() {
                  Text(item.action === 'summarize' ? '🤖' : '👁️').fontSize(16)
                  Text(item.content_preview || '(无内容)')
                    .fontSize(13).fontColor('#333333').maxLines(1)
                    .textOverflow({ overflow: TextOverflow.Ellipsis })
                    .layoutWeight(1).margin({ left: 10 })
                  Text(item.action === 'summarize' ? '摘要' : '阅读')
                    .fontSize(11).fontColor('#999999').backgroundColor('#F0F0F0')
                    .borderRadius(4).padding({ left: 6, right: 6, top: 2, bottom: 2 })
                }
                .width('100%').padding({ top: 8, bottom: 8 })
                .onClick(() => this.onOpenHistoryItem(item))
              })
            }
          }
          .width('100%').padding(16).backgroundColor('#FFFFFF').borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          // 菜单
          Column() {
            ForEach(this.menuItems, (item: MenuItem, index: number) => {
              Row() {
                Text(item.icon).fontSize(24)
                Column() {
                  Text(item.title).fontSize(15).fontWeight(FontWeight.Medium)
                  Text(item.subtitle).fontSize(12).fontColor('#999999').margin({ top: 2 })
                }
                .alignItems(HorizontalAlign.Start).margin({ left: 14 }).layoutWeight(1)
                Text('>').fontSize(16).fontColor('#CCCCCC')
              }
              .width('100%').height(56).padding({ left: 16, right: 16 })
              .onClick(() => this.onMenuClick(index))
              if (index < this.menuItems.length - 1) {
                Divider().margin({ left: 54 })
              }
            })
          }
          .width('100%').backgroundColor('#FFFFFF').borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          if (this.showFeedbackPanel) {
            Column() {
              Text('Feedback')
                .fontSize(18)
                .fontWeight(FontWeight.Medium)
                .width('100%')

              Row() {
                Text('Rating').fontSize(14).fontColor('#666666')
                Blank()
                ForEach([1, 2, 3, 4, 5], (score: number) => {
                  Text(score <= this.profileFeedbackRating ? '*' : '-')
                    .fontSize(28)
                    .fontColor(score <= this.profileFeedbackRating ? '#FFB400' : '#C7C7CC')
                    .margin({ left: 4 })
                    .onClick(() => {
                      this.profileFeedbackRating = score
                    })
                })
              }
              .width('100%')
              .margin({ top: 12 })

              TextArea({
                placeholder: 'Write your suggestion here',
                text: this.profileFeedbackComment
              })
                .height(96)
                .fontSize(14)
                .backgroundColor('#F8F8FA')
                .borderRadius(8)
                .margin({ top: 12 })
                .onChange((value: string) => {
                  this.profileFeedbackComment = value
                })

              Button(this.isSubmittingProfileFeedback ? 'Submitting...' : 'Submit Feedback')
                .width('100%')
                .height(42)
                .fontSize(15)
                .fontColor('#FFFFFF')
                .backgroundColor(this.profileFeedbackRating > 0 ? '#34C759' : '#C7C7CC')
                .borderRadius(21)
                .margin({ top: 12 })
                .enabled(this.profileFeedbackRating > 0 && !this.isSubmittingProfileFeedback)
                .onClick(() => this.onSubmitProfileFeedback())
            }
            .width('100%')
            .padding(16)
            .backgroundColor('#FFFFFF')
            .borderRadius(12)
            .margin({ left: 16, right: 16, top: 12 })
          }
        }
        .padding({ bottom: 24 })
      }
      .width('100%').layoutWeight(1).scrollBar(BarState.Off)
    }
    .width('100%').height('100%').backgroundColor('#F2F2F7')
  }
}
