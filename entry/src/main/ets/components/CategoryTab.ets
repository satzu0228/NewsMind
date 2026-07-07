// ============================================
// 文件名: entry/src/main/ets/components/CategoryTab.ets
// 功能: 新闻分类横向标签栏
// ============================================

/**
 * 分类标签栏组件
 * 横向滚动，点击切换分类
 */
@Component
export struct CategoryTab {
  @Prop categories: string[]         // 类别列表
  @Link selectedCategory: string     // 当前选中类别（双向绑定）
  // 选中回调
  onCategoryChanged?: (category: string) => void

  build() {
    Scroll() {
      Row() {
        // “全部” 按钮
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

        // 各类别按钮
        ForEach(this.categories, (category: string) => {
          Text(category)
            .fontSize(14)
            .fontColor(this.selectedCategory === category ? '#FFFFFF' : '#333333')
            .fontWeight(this.selectedCategory === category ? FontWeight.Bold : FontWeight.Normal)
            .backgroundColor(this.selectedCategory === category ? '#007AFF' : '#F5F5F5')
            .borderRadius(20)
            .padding({ left: 16, right: 16, top: 6, bottom: 6 })
            .margin({ right: 10 })
            .onClick(() => {
              this.selectedCategory = category
              if (this.onCategoryChanged) {
                this.onCategoryChanged(category)
              }
            })
        })
      }
      .padding({ left: 16, right: 16 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .height(44)
    .width('100%')
  }
}
