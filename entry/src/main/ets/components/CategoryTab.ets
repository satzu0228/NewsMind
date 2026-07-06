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
        // "全部" 按钮
        this.TabButton('全部', this.selectedCategory === '')

        // 各类别按钮
        ForEach(this.categories, (category: string) => {
          this.TabButton(category, this.selectedCategory === category)
        })
      }
      .padding({ left: 16, right: 16 })
    }
    .scrollable(ScrollDirection.Horizontal)
    .scrollBar(BarState.Off)
    .height(44)
    .width('100%')
  }

  /**
   * 单个标签按钮
   */
  @Builder
  TabButton(label: string, isSelected: boolean) {
    Text(label)
      .fontSize(14)
      .fontColor(isSelected ? '#FFFFFF' : '#333333')
      .fontWeight(isSelected ? FontWeight.Bold : FontWeight.Normal)
      .backgroundColor(isSelected ? '#007AFF' : '#F5F5F5')
      .borderRadius(20)
      .padding({ left: 16, right: 16, top: 6, bottom: 6 })
      .margin({ right: 10 })
      .onClick(() => {
        this.selectedCategory = (label === '全部') ? '' : label
        if (this.onCategoryChanged) {
          this.onCategoryChanged(this.selectedCategory)
        }
      })
  }
}
