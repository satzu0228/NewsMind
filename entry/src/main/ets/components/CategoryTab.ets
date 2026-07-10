// ============================================
// 文件名: entry/src/main/ets/components/CategoryTab.ets
// 功能: 新闻分类横向标签栏
// ============================================

@Component
export struct CategoryTab {
  @Prop categories: string[]
  @Link selectedCategory: string
  onCategoryChanged?: (category: string) => void

  private contentWidth(): number {
    return Math.max(360, (this.categories.length + 1) * 78)
  }

  @Builder
  categoryButton(label: string) {
    Text(label)
      .fontSize(14)
      .fontColor(this.selectedCategory === label ? '#FFFFFF' : '#333333')
      .fontWeight(this.selectedCategory === label ? FontWeight.Bold : FontWeight.Normal)
      .backgroundColor(this.selectedCategory === label ? '#007AFF' : '#F5F5F5')
      .borderRadius(20)
      .padding({ left: 16, right: 16, top: 6, bottom: 6 })
      .margin({ right: 10 })
      .onClick(() => {
        this.selectedCategory = label
        if (this.onCategoryChanged) {
          this.onCategoryChanged(label)
        }
      })
  }

  build() {
    Scroll() {
      Row() {
        Text('全部')
          .fontSize(14)
          .fontColor(this.selectedCategory === '' ? '#FFFFFF' : '#333333')
          .fontWeight(this.selectedCategory === '' ? FontWeight.Bold : FontWeight.Normal)
          .backgroundColor(this.selectedCategory === '' ? '#007AFF' : '#F5F5F5')
          .borderRadius(20)
          .padding({ left: 16, right: 16, top: 6, bottom: 6 })
          .margin({ right: 10 })
          .onClick(() => {
            this.selectedCategory = ''
            if (this.onCategoryChanged) {
              this.onCategoryChanged('')
            }
          })

        ForEach(this.categories, (category: string) => {
          this.categoryButton(category)
        })
      }
      .width(this.contentWidth())
      .padding({ left: 16, right: 16 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .edgeEffect(EdgeEffect.Spring)
    .height(44)
    .width('100%')
  }
}
