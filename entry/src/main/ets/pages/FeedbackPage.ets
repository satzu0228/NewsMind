// ============================================
// 文件名: entry/src/main/ets/pages/FeedbackPage.ets
// 功能: 意见反馈页面 - 评分 + 文字反馈
// ============================================

import { submitFeedback } from '../api/NewsApi'
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'

@Entry
@Component
export struct FeedbackPage {
  @State rating: number = 0
  @State comment: string = ''
  @State isSubmitting: boolean = false

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('← 返回')
          .fontSize(16)
          .fontColor('#007AFF')
          .onClick(() => router.back())

        Blank()

        Text('意见反馈')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)

        Blank()

        Text('    ')
          .fontSize(16)
      }
      .width('100%')
      .height(48)
      .padding({ left: 16, right: 16 })
      .backgroundColor('#FFFFFF')

      Scroll() {
        Column() {
          // 标题描述
          Column() {
            Text('您的反馈对我们非常重要')
              .fontSize(16)
              .fontColor('#333333')
              .width('100%')
            Text('请花几分钟告诉我们您的使用体验和改进建议')
              .fontSize(13)
              .fontColor('#999999')
              .width('100%')
              .margin({ top: 6 })
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16, top: 16 })

          // 评分区域
          Column() {
            Text('整体评分')
              .fontSize(15)
              .fontWeight(FontWeight.Medium)
              .fontColor('#333333')
              .width('100%')
              .margin({ bottom: 14 })

            Row() {
              ForEach([1, 2, 3, 4, 5], (score: number) => {
                Text(score <= this.rating ? '★' : '☆')
                  .fontSize(36)
                  .fontColor(score <= this.rating ? '#FFB400' : '#D8D8D8')
                  .margin({ left: score === 1 ? 0 : 12 })
                  .onClick(() => {
                    this.rating = score
                  })
              })
            }
            .width('100%')
            .justifyContent(FlexAlign.Center)

            Text(this.ratingLabel())
              .fontSize(13)
              .fontColor('#999999')
              .margin({ top: 10 })
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          // 意见与建议
          Column() {
            Text('意见与建议')
              .fontSize(15)
              .fontWeight(FontWeight.Medium)
              .fontColor('#333333')
              .width('100%')
              .margin({ bottom: 8 })

            TextArea({
              placeholder: '请描述您的使用体验、遇到的问题或改进建议...',
              text: this.comment
            })
              .height(100)
              .fontSize(14)
              .backgroundColor('#F8F8FA')
              .borderRadius(10)
              .padding(12)
              .onChange((value: string) => {
                this.comment = value
              })

            Row() {
              Text(`${this.comment.length}/500`)
                .fontSize(11)
                .fontColor('#CCCCCC')
              Blank()
              Text('感谢您的反馈')
                .fontSize(11)
                .fontColor('#CCCCCC')
            }
            .width('100%')
            .margin({ top: 4 })
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          // 提交按钮
          Button(this.isSubmitting ? '提交中...' : '提交反馈')
            .width('100%')
            .height(48)
            .fontSize(16)
            .fontWeight(FontWeight.Medium)
            .fontColor('#FFFFFF')
            .backgroundColor(this.rating > 0 && !this.isSubmitting ? '#007AFF' : '#C7C7CC')
            .borderRadius(24)
            .margin({ left: 16, right: 16, top: 20 })
            .enabled(this.rating > 0 && !this.isSubmitting)
            .onClick(() => this.onSubmit())

          // 底部留白
          Blank().height(32)
        }
      }
      .width('100%')
      .layoutWeight(1)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F2F7')
  }

  private ratingLabel(): string {
    const labels: string[] = ['', '非常不满意', '不太满意', '一般', '比较满意', '非常满意']
    return this.rating > 0 ? labels[this.rating] : '请选择评分'
  }

  private async onSubmit(): Promise<void> {
    if (this.rating <= 0) {
      promptAction.showToast({ message: '请先选择评分', duration: 1500 })
      return
    }
    if (this.isSubmitting) return

    this.isSubmitting = true
    try {
      await submitFeedback(this.rating, this.comment)
      promptAction.showToast({ message: '反馈已提交，感谢您的意见！', duration: 2000 })
      setTimeout(() => router.back(), 1200)
    } catch (err) {
      promptAction.showToast({ message: '提交失败，请检查网络后重试', duration: 1500 })
    } finally {
      this.isSubmitting = false
    }
  }
}
