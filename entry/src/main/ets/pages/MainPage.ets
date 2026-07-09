// ============================================
// 文件名: entry/src/main/ets/pages/MainPage.ets
// 功能: 主页面 - 底部Tab导航
// 结构: 首页 | 收藏 | 我的
// 所有子组件(HomeContent/FavoriteContent/ProfileContent)内联定义,
// 因为 @Entry 页面不能被其他组件引用。
// ============================================

import { NewsItem, NewsListResponse, FavoriteItem, FavoriteListResponse } from '../models/NewsModel'
import { fetchNewsList, fetchCategories, fetchFavorites, removeFavorite, logoutUser } from '../api/NewsApi'
import { NewsCard } from '../components/NewsCard'
import { CategoryTab } from '../components/CategoryTab'
import { SearchBar } from '../components/SearchBar'
import { LoadingView, EmptyView, ErrorView } from '../components/LoadingView'
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import dataPreferences from '@ohos.data.preferences'

const PREF_NAME: string = 'NewsMindPrefs'

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
  @StorageLink('authUsername') authUsername: string = ''
  @StorageLink('authAvatar') authAvatar: string = '😀'

  private menuItems: MenuItem[] = [
    { icon: '🕐', title: '阅读历史', subtitle: '查看最近浏览的新闻' },
    { icon: '✏️', title: '编辑资料', subtitle: '修改用户名和头像' },
    { icon: '📊', title: '数据统计', subtitle: '查看使用数据和分析' },
    { icon: '💬', title: '意见反馈', subtitle: '帮助我们改进产品' },
    { icon: 'ℹ️', title: '关于 NewsMind', subtitle: '版本 1.0.0 | BERT + T5' }
  ]

  private onMenuClick(index: number): void {
    if (index === 0) {
      router.pushUrl({ url: 'pages/HistoryPage' })
      return
    }
    if (index === 1) {
      router.pushUrl({ url: 'pages/EditProfilePage' })
      return
    }
    if (index === 2) {
      AlertDialog.show({
        title: 'Stats',
        message: 'Read and summary records are connected to the backend history API.',
        primaryButton: { value: 'OK', action: () => {} }
      })
      return
    }
    if (index === 3) {
      router.pushUrl({ url: 'pages/FeedbackPage' })
      return
    }
    AlertDialog.show({
      title: 'About NewsMind',
      message: 'NewsMind 1.0.0\nNews summarization app based on ArkTS, BERT, TextRank and Transformer.',
      primaryButton: { value: 'OK', action: () => {} }
    })
  }

  private onLogout(): void {
    AlertDialog.show({
      title: '退出登录',
      message: `确定要退出登录吗？`,
      primaryButton: {
        value: '取消',
        action: () => {}
      },
      secondaryButton: {
        value: '确定',
        fontColor: '#FF3B30',
        action: async () => {
          try {
            await logoutUser()
          } catch (e) {
            // 静默失败
          }
          // 清除登录状态
          AppStorage.SetOrCreate('authToken', '')
          AppStorage.SetOrCreate('authUsername', '')
          AppStorage.SetOrCreate('authAvatar', '')
          AppStorage.SetOrCreate('authUserId', 0)
          AppStorage.SetOrCreate('isLoggedIn', false)
          // 清除持久化数据
          try {
            const context = getContext(this)
            const prefs: dataPreferences.Preferences = dataPreferences.getPreferencesSync(context, { name: PREF_NAME })
            prefs.deleteSync('authToken')
            prefs.deleteSync('authUserId')
            prefs.deleteSync('authUsername')
            prefs.deleteSync('authAvatar')
            prefs.flush()
          } catch (e) {
            // 静默失败
          }
          // 跳转到登录页
          router.replaceUrl({ url: 'pages/LoginPage' })
        }
      }
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
              Text(this.authAvatar).fontSize(28)
            }
            .width(56).height(56).backgroundColor('#E3F2FD').borderRadius(28).justifyContent(FlexAlign.Center)
            Column() {
              Text(this.authUsername || 'NewsMind 用户').fontSize(17).fontWeight(FontWeight.Medium)
              Text('AI 驱动 · 智能新闻摘要').fontSize(13).fontColor('#999999').margin({ top: 4 })
            }
            .alignItems(HorizontalAlign.Start).margin({ left: 14 })
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

          // 退出登录按钮
          Button('退出登录')
            .type(ButtonType.Capsule)
            .width('80%')
            .height(42)
            .fontSize(15)
            .fontColor('#FF3B30')
            .backgroundColor('#FFFFFF')
            .border({ width: 1, color: '#FF3B30' })
            .margin({ top: 24 })
            .onClick(() => this.onLogout())
        }
        .padding({ bottom: 40 })
      }
      .width('100%').layoutWeight(1).scrollBar(BarState.Off)
    }
    .width('100%').height('100%').backgroundColor('#F2F2F7')
  }
}
