// ============================================
// 文件名: entry/src/main/ets/components/SearchBar.ets
// 功能: 搜索栏组件
// ============================================

/**
 * 搜索栏组件
 */
@Component
export struct SearchBar {
  // 搜索回调
  onSearch?: (keyword: string) => void
  // 清除回调
  onClear?: () => void

  @State searchText: string = ''

  build() {
    Row() {
      // 搜索图标（文字）
      Text('🔍')
        .fontSize(16)
        .margin({ left: 12 })

      // 输入框
      TextInput({ placeholder: '搜索新闻...', text: this.searchText })
        .fontSize(14)
        .backgroundColor(Color.Transparent)
        .height(36)
        .layoutWeight(1)
        .onChange((value: string) => {
          this.searchText = value
        })
        .onSubmit(() => {
          if (this.onSearch) {
            this.onSearch(this.searchText.trim())
          }
        })

      // 清除按钮
      if (this.searchText.length > 0) {
        Text('✕')
          .fontSize(14)
          .fontColor('#CCCCCC')
          .margin({ right: 8 })
          .onClick(() => {
            this.searchText = ''
            if (this.onClear) {
              this.onClear()
            }
          })
      }

      // 搜索按钮
      Text('搜索')
        .fontSize(13)
        .fontColor('#FFFFFF')
        .backgroundColor('#007AFF')
        .borderRadius(16)
        .padding({ left: 14, right: 14, top: 6, bottom: 6 })
        .margin({ right: 6 })
        .onClick(() => {
          if (this.onSearch) {
            this.onSearch(this.searchText.trim())
          }
        })
    }
    .width('100%')
    .height(40)
    .backgroundColor('#F2F2F7')
    .borderRadius(20)
  }
}
