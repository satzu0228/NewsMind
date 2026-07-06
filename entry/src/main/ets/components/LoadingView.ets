// ============================================
// 文件名: entry/src/main/ets/components/LoadingView.ets
// 功能: 加载中 / 空状态 / 错误状态 占位组件
// ============================================

/**
 * 加载中指示器
 */
@Component
export struct LoadingView {
  @Prop message: string = '加载中...'

  build() {
    Column() {
      LoadingProgress()
        .width(40)
        .height(40)
        .color('#007AFF')

      Text(this.message)
        .fontSize(14)
        .fontColor('#999999')
        .margin({ top: 12 })
    }
    .width('100%')
    .height(200)
    .justifyContent(FlexAlign.Center)
  }
}

/**
 * 空状态占位
 */
@Component
export struct EmptyView {
  @Prop icon: string = '📰'
  @Prop title: string = '暂无内容'
  @Prop subtitle: string = ''

  build() {
    Column() {
      Text(this.icon)
        .fontSize(48)
        .margin({ bottom: 12 })

      Text(this.title)
        .fontSize(16)
        .fontColor('#333333')
        .fontWeight(FontWeight.Medium)

      if (this.subtitle) {
        Text(this.subtitle)
          .fontSize(13)
          .fontColor('#999999')
          .margin({ top: 6 })
      }
    }
    .width('100%')
    .height(300)
    .justifyContent(FlexAlign.Center)
  }
}

/**
 * 错误状态占位
 */
@Component
export struct ErrorView {
  @Prop message: string = '加载失败'
  // 重试回调
  onRetry?: () => void

  build() {
    Column() {
      Text('😞')
        .fontSize(48)
        .margin({ bottom: 12 })

      Text(this.message)
        .fontSize(15)
        .fontColor('#666666')

      Button('点击重试')
        .fontSize(14)
        .backgroundColor('#007AFF')
        .borderRadius(20)
        .margin({ top: 16 })
        .onClick(() => {
          if (this.onRetry) {
            this.onRetry()
          }
        })
    }
    .width('100%')
    .height(300)
    .justifyContent(FlexAlign.Center)
  }
}
