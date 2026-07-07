// ============================================
// 文件名: entry/src/main/ets/pages/MainPage.ets
// 功能: 主页面 - 底部Tab导航
// 结构: 首页 | 收藏 | 我的
// 所有子组件(HomeContent/FavoriteContent/ProfileContent)内联定义,
// 因为 @Entry 页面不能被其他组件引用。
// ============================================

import { NewsItem, NewsListResponse, FavoriteItem, FavoriteListResponse, HistoryItem, HistoryListResponse } from '../models/NewsModel'
import { fetchNewsList, fetchCategories, fetchFavorites, removeFavorite, fetchHistory } from '../api/NewsApi'
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
  @State favoriteRefreshCounter: number = 0

  // Tab 标题
  private tabTitles: string[] = ['首页', '收藏', '我的']
  // Tab 图标（未选中）
  private tabIcons: string[] = ['🏠', '🤍', '👤']
  // Tab 图标（选中）
  private tabActiveIcons: string[] = ['🏠', '❤️', '👤']

  onPageShow(): void {
    this.favoriteRefreshCounter++
  }

  build() {
    Tabs({ barPosition: BarPosition.End }) {
      // ===== Tab 0: 首页 =====
      TabContent() {
        HomeContent()
      }
      .tabBar(this.tabBuilder(0))

      // ===== Tab 1: 收藏 =====
      TabContent() {
        FavoriteContent({ refreshTrigger: this.favoriteRefreshCounter })
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
    .scrollable(false)
    .onChange((index: number) => {
      this.currentTabIndex = index
      if (index === 1) {
        this.favoriteRefreshCounter++
        AppStorage.SetOrCreate('favoriteRefreshTick', Date.now())
      } else if (index === 2) {
        AppStorage.SetOrCreate('historyRefreshTick', Date.now())
      }
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
          .scrollBar(BarState.Off)
          .onReachEnd(() => {
            if (this.newsList.length < this.totalCount) {
              this.currentPage++
              this.loadNewsList(false)
            }
          })
        }
        .layoutWeight(1)
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
  @StorageLink('favoriteRefreshTick')
  @Watch('onFavoriteRefreshChanged')
  favoriteRefreshTick: number = 0
  @State favorites: FavoriteItem[] = []
  @State categories: string[] = []
  @State selectedCategory: string = ''
  @State searchKeyword: string = ''
  @State isSearchMode: boolean = false
  @State isLoading: boolean = true
  @State hasError: boolean = false
  @Prop @Watch('onRefreshTriggered') refreshTrigger: number = 0

  aboutToAppear(): void {
    this.loadCategories()
    this.loadFavorites()
  }

  onRefreshTriggered(): void {
    this.loadFavorites()
  }

  private onFavoriteRefreshChanged(): void {
    this.loadFavorites()
  }

  private async loadCategories(): Promise<void> {
    try {
      const result = await fetchCategories()
      this.categories = result.categories
    } catch (err) {
      // 静默失败
    }
  }

  private async loadFavorites(): Promise<void> {
    this.isLoading = true
    this.hasError = false
    try {
      const response: FavoriteListResponse = await fetchFavorites(
        1, 100,
        this.selectedCategory || undefined,
        this.searchKeyword || undefined
      )
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
      content_preview: fav.content_preview, length: fav.length, created_at: fav.created_at
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

      // 搜索栏
      SearchBar({
        onSearch: (keyword: string) => {
          this.searchKeyword = keyword
          this.isSearchMode = keyword.length > 0
          this.loadFavorites()
        },
        onClear: () => {
          this.searchKeyword = ''
          this.isSearchMode = false
          this.loadFavorites()
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
            this.loadFavorites()
          }
        })
      }

      if (this.isLoading) {
        LoadingView({ message: '加载收藏...' })
      } else if (this.hasError) {
        ErrorView({ message: '收藏加载失败', onRetry: () => this.loadFavorites() })
      } else if (this.favorites.length === 0) {
        EmptyView({
          icon: '⭐',
          title: this.isSearchMode ? '未找到匹配的收藏' : '暂无收藏',
          subtitle: this.isSearchMode ? '请尝试其他关键词或分类' : '浏览新闻时点击收藏即可添加'
        })
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
  @StorageLink('historyRefreshTick')
  @Watch('onHistoryRefreshChanged')
  historyRefreshTick: number = 0
  @State recentHistory: HistoryItem[] = []
  @State isLoadingHistory: boolean = false

  private menuItems: MenuItem[] = [
    { icon: '🕐', title: '阅读历史', subtitle: '查看最近浏览的新闻' },
    { icon: '📊', title: '数据统计', subtitle: '查看使用数据和分析' },
    { icon: '💬', title: '意见反馈', subtitle: '帮助我们改进产品' },
    { icon: 'ℹ️', title: '关于 NewsMind', subtitle: '版本 1.0.0 | BERT + T5' }
  ]

  aboutToAppear(): void {
    this.loadHistory()
  }

  private onHistoryRefreshChanged(): void {
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
      router.pushUrl({ url: 'pages/FeedbackPage' })
      return
    }
    AlertDialog.show({
      title: 'About NewsMind',
      message: 'NewsMind 1.0.0\nNews summarization app based on ArkTS, BERT, TextRank and Transformer.',
      primaryButton: { value: 'OK', action: () => {} }
    })
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
        }
        .padding({ bottom: 24 })
      }
      .width('100%').layoutWeight(1).scrollBar(BarState.Off)
    }
    .width('100%').height('100%').backgroundColor('#F2F2F7')
  }
}
