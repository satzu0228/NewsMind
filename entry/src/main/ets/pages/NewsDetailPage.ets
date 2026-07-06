// ============================================
// 文件名: entry/src/main/ets/pages/NewsDetailPage.ets
// 功能: 新闻详情页 - 正文/摘要/收藏/分享
// ============================================

import { NewsDetail, SummaryResponse } from '../models/NewsModel'
import { fetchNewsDetail, generateSummary, addFavorite, removeFavorite } from '../api/NewsApi'
import { LoadingView, EmptyView, ErrorView } from '../components/LoadingView'
import { router } from '@kit.ArkUI'
import { promptAction } from '@kit.ArkUI'
import { pasteboard } from '@kit.BasicServicesKit'

/**
 * 新闻详情页
 */
@Entry
@Component
export struct NewsDetailPage {
  @State newsId: number = 0
  @State category: string = ''
  @State newsDetail: NewsDetail | null = null
  @State isLoading: boolean = true
  @State hasError: boolean = false
  @State errorMessage: string = ''
  @State isGeneratingSummary: boolean = false
  @State summary: SummaryResponse | null = null
  @State showAbstractive: boolean = true
  @State isFavorite: boolean = false

  aboutToAppear(): void {
    const params: Record<string, Object> = router.getParams() as Record<string, Object>
    if (params) {
      this.newsId = (params['news_id'] as number) || 0
      this.category = (params['category'] as string) || ''
    }
    this.loadDetail()
  }

  private async loadDetail(): Promise<void> {
    this.isLoading = true
    this.hasError = false
    try {
      this.newsDetail = await fetchNewsDetail(this.newsId)
      this.isFavorite = this.newsDetail.is_favorite
    } catch (err) {
      this.hasError = true
      this.errorMessage = '新闻加载失败'
    } finally {
      this.isLoading = false
    }
  }

  private async onGenerateSummary(): Promise<void> {
    if (this.isGeneratingSummary) return
    this.isGeneratingSummary = true
    try {
      this.summary = await generateSummary(this.newsId, undefined, 5)
      promptAction.showToast({ message: `摘要生成成功 (${this.summary.inference_time.toFixed(2)}s)`, duration: 2000 })
    } catch (err) {
      promptAction.showToast({ message: '摘要生成失败，请重试', duration: 2000 })
    } finally {
      this.isGeneratingSummary = false
    }
  }

  private async onToggleFavorite(): Promise<void> {
    try {
      if (this.isFavorite) {
        await removeFavorite(this.newsId)
        this.isFavorite = false
        promptAction.showToast({ message: '已取消收藏', duration: 1500 })
      } else {
        await addFavorite(this.newsId)
        this.isFavorite = true
        promptAction.showToast({ message: '已添加收藏', duration: 1500 })
      }
    } catch (err) {
      promptAction.showToast({ message: '操作失败', duration: 1500 })
    }
  }

  private onShare(): void {
    const summaryText: string = this.summary?.abstractive_summary ||
      this.newsDetail?.content?.substring(0, 200) || ''
    try {
      const pasteData: pasteboard.PasteData = pasteboard.createData(pasteboard.MIMETYPE_TEXT_PLAIN, summaryText)
      const systemPasteboard: pasteboard.SystemPasteboard = pasteboard.getSystemPasteboard()
      systemPasteboard.setData(pasteData)
      promptAction.showToast({ message: '已复制到剪贴板', duration: 1500 })
    } catch (err) {
      promptAction.showToast({ message: '已复制到剪贴板', duration: 1500 })
    }
  }

  build() {
    Column() {
      // 顶部导航
      this.buildNavBar()

      if (this.isLoading) {
        LoadingView({ message: '加载中...' })
      } else if (this.hasError) {
        ErrorView({ message: this.errorMessage, onRetry: () => this.loadDetail() })
      } else if (!this.newsDetail) {
        EmptyView({ icon: '📄', title: '新闻不存在' })
      } else {
        Scroll() {
          Column() {
            // 类别 + 字数
            this.buildTitleSection()

            // 正文
            Text(this.newsDetail.content)
              .fontSize(16)
              .fontColor('#333333')
              .lineHeight(28)
              .padding({ left: 16, right: 16, top: 8, bottom: 20 })
              .width('100%')

            // 摘要区域
            this.buildSummarySection()

            // 摘要结果
            if (this.summary) {
              this.buildSummaryResult()
            }
          }
        }
        .width('100%')
        .layoutWeight(1)
        .scrollBar(BarState.Off)

        // 底部操作栏
        this.buildBottomBar()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F2F7')
  }

  @Builder
  buildNavBar() {
    Row() {
      Text('← 返回')
        .fontSize(16)
        .fontColor('#007AFF')
        .onClick(() => router.back())

      Blank()

      Text(this.category || '新闻详情')
        .fontSize(18)
        .fontWeight(FontWeight.Medium)

      Blank()

      Text('    ')  // 占位
        .fontSize(16)
    }
    .width('100%')
    .height(48)
    .padding({ left: 16, right: 16 })
    .backgroundColor('#FFFFFF')
  }

  @Builder
  buildTitleSection() {
    Column() {
      Row() {
        Text(this.newsDetail!.category)
          .fontSize(12)
          .fontColor('#007AFF')
          .backgroundColor('#007AFF18')
          .borderRadius(4)
          .padding({ left: 8, right: 8, top: 2, bottom: 2 })
        Blank()
        Text(`${this.newsDetail!.length} 字`)
          .fontSize(12)
          .fontColor('#999999')
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 12 })
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
  }

  @Builder
  buildSummarySection() {
    Column() {
      Divider().margin({ top: 12, bottom: 12 })

      Text('AI 智能摘要')
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .width('100%')
        .margin({ bottom: 10 })

      Button() {
        Row() {
          if (this.isGeneratingSummary) {
            LoadingProgress().width(18).height(18).color('#FFFFFF').margin({ right: 8 })
          }
          Text(this.isGeneratingSummary ? '正在生成摘要...' : (this.summary ? '重新生成摘要' : '✨ 一键生成摘要'))
            .fontSize(15)
            .fontColor('#FFFFFF')
        }
        .justifyContent(FlexAlign.Center)
      }
      .width('100%')
      .height(44)
      .backgroundColor(this.isGeneratingSummary ? '#80BDFF' : '#007AFF')
      .borderRadius(10)
      .enabled(!this.isGeneratingSummary)
      .onClick(() => this.onGenerateSummary())
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 8, bottom: 8 })
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .margin({ left: 16, right: 16 })
  }

  @Builder
  buildSummaryResult() {
    Column() {
      Row() {
        Text('抽取式').fontSize(13)
          .fontColor(this.showAbstractive ? '#999999' : '#007AFF')
          .onClick(() => this.showAbstractive = false)
        Text(' | ').fontSize(13).fontColor('#DDDDDD')
        Text('生成式').fontSize(13)
          .fontColor(this.showAbstractive ? '#007AFF' : '#999999')
          .onClick(() => this.showAbstractive = true)
        Blank()
        Text(`${this.summary!.inference_time.toFixed(2)}s`)
          .fontSize(12).fontColor('#999999')
      }
      .width('100%')
      .margin({ bottom: 10 })

      Text(this.showAbstractive ? this.summary!.abstractive_summary : this.summary!.extractive_summary)
        .fontSize(15)
        .fontColor('#333333')
        .lineHeight(24)
        .width('100%')
        .backgroundColor('#F8F8FA')
        .borderRadius(8)
        .padding(12)
    }
    .width('100%')
    .padding({ left: 16, right: 16, top: 12, bottom: 16 })
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .margin({ left: 16, right: 16, top: 12 })
  }

  @Builder
  buildBottomBar() {
    Row() {
      Column() {
        Text(this.isFavorite ? '❤️' : '🤍').fontSize(22)
        Text(this.isFavorite ? '已收藏' : '收藏').fontSize(11).fontColor('#666666').margin({ top: 2 })
      }
      .onClick(() => this.onToggleFavorite())

      Blank()

      Button('生成摘要')
        .fontSize(14)
        .fontColor('#FFFFFF')
        .backgroundColor('#007AFF')
        .borderRadius(20)
        .height(40)
        .padding({ left: 20, right: 20 })
        .onClick(() => this.onGenerateSummary())

      Blank()

      Column() {
        Text('📤').fontSize(22)
        Text('分享').fontSize(11).fontColor('#666666').margin({ top: 2 })
      }
      .onClick(() => this.onShare())
    }
    .width('100%')
    .height(56)
    .padding({ left: 24, right: 24 })
    .backgroundColor('#FFFFFF')
    .shadow({ radius: 4, color: '#00000010' })
  }
}
