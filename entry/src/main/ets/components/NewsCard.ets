// ============================================
// 文件名: entry/src/main/ets/components/NewsCard.ets
// 功能: 新闻卡片组件（列表项）
// ============================================

import { NewsItem } from '../models/NewsModel'

/**
 * 新闻卡片组件
 * 展示: 类别标签 + 正文预览 + 长度信息
 */
@Component
export struct NewsCard {
  @Prop news: NewsItem
  // 点击回调
  onCardClick?: () => void

  // 类别颜色映射
  private categoryColors: Record<string, string> = {
    '科技': '#007AFF',
    '体育': '#FF3B30',
    '财经': '#FF9500',
    '娱乐': '#AF52DE',
    '教育': '#34C759',
    '时政': '#E52B50',
    '社会': '#5AC8FA',
    '游戏': '#5856D6',
    '时尚': '#FF6482',
    '家居': '#8E8E93',
    '房产': '#FF6B35',
    '星座': '#AA47BC',
    '股票': '#F44336',
    '彩票': '#FF9800'
  }

  build() {
    Column() {
      // 类别标签
      Row() {
        Text(this.news.category)
          .fontSize(12)
          .fontColor(this.categoryColors[this.news.category] || '#666666')
          .backgroundColor((this.categoryColors[this.news.category] || '#666666') + '18')
          .borderRadius(4)
          .padding({ left: 8, right: 8, top: 2, bottom: 2 })
          .maxLines(1)
      }
      .width('100%')

      // 正文预览
      Text(this.news.content_preview || '暂无内容')
        .fontSize(15)
        .fontColor('#1A1A1A')
        .lineHeight(22)
        .maxLines(3)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
        .margin({ top: 8 })
        .width('100%')

      // 底部信息
      Row() {
        Text(`${this.news.length} 字`)
          .fontSize(12)
          .fontColor('#999999')

        Blank()

        Text(this.formatDate(this.news.created_at))
          .fontSize(12)
          .fontColor('#999999')
      }
      .width('100%')
      .margin({ top: 10 })
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .onClick(() => {
      if (this.onCardClick) {
        this.onCardClick()
      }
    })
  }

  /**
   * 格式化日期（ISO 字符串 → 短日期）
   */
  private formatDate(dateStr: string): string {
    if (!dateStr) return ''
    try {
      // 简单截取日期部分
      const idx = dateStr.indexOf('T')
      if (idx > 0) {
        return dateStr.substring(0, idx)
      }
      return dateStr.substring(0, 10)
    } catch (e) {
      return dateStr
    }
  }
}
