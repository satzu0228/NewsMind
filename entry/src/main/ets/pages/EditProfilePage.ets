// ============================================
// 文件名: entry/src/main/ets/pages/EditProfilePage.ets
// 功能: 编辑用户资料 - 修改用户名和头像
// ============================================

import { updateUserProfile } from '../api/NewsApi'
import { AuthResponse } from '../models/NewsModel'
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import dataPreferences from '@ohos.data.preferences'

const PREF_NAME: string = 'NewsMindPrefs'

/**
 * 编辑资料页面
 */
@Entry
@Component
export struct EditProfilePage {
  @State username: string = ''
  @State selectedAvatar: string = '😀'
  @State isLoading: boolean = false
  @State errorMessage: string = ''

  // 可选头像 emoji 列表
  private avatarOptions: string[] = [
    '😀', '😎', '🤓', '😊', '🥰', '😺',
    '🦊', '🐼', '🐨', '🦁', '🐯', '🐸',
    '🌟', '🎮', '📚', '🎵', '⚽', '🏀',
    '🚀', '💡', '🎨', '🌈', '☕', '🍀'
  ]

  aboutToAppear(): void {
    // 从 AppStorage 读取当前用户信息
    this.username = AppStorage.Get<string>('authUsername') || ''
    this.selectedAvatar = AppStorage.Get<string>('authAvatar') || '😀'
  }

  private async handleSave(): Promise<void> {
    if (this.username.length === 0) {
      this.errorMessage = '用户名不能为空'
      return
    }

    this.errorMessage = ''
    this.isLoading = true

    try {
      const response: AuthResponse = await updateUserProfile(this.username, this.selectedAvatar)

      if (response.success) {
        // 更新 AppStorage
        AppStorage.SetOrCreate('authUsername', response.username || this.username)
        AppStorage.SetOrCreate('authAvatar', response.avatar || this.selectedAvatar)

        // 持久化到 Preferences
        try {
          const context = getContext(this)
          const prefs: dataPreferences.Preferences = dataPreferences.getPreferencesSync(context, { name: PREF_NAME })
          prefs.putSync('authUsername', response.username || this.username)
          prefs.putSync('authAvatar', response.avatar || this.selectedAvatar)
          prefs.flush()
        } catch (e) {
          // 静默失败
        }

        promptAction.showToast({ message: '资料更新成功', duration: 1500 })
        router.back()
      } else {
        this.errorMessage = response.message || '更新失败'
      }
    } catch (err) {
      this.errorMessage = '更新失败，用户名可能已被占用'
      console.error(`[Profile] ${(err as Error).message}`)
    } finally {
      this.isLoading = false
    }
  }

  build() {
    Column() {
      // 顶部导航栏
      Row() {
        Text('← 返回')
          .fontSize(16)
          .fontColor('#007AFF')
          .onClick(() => router.back())

        Blank()

        Text('编辑资料')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)

        Blank()

        Text('保存')
          .fontSize(16)
          .fontColor(this.isLoading ? '#CCCCCC' : '#007AFF')
          .fontWeight(FontWeight.Medium)
          .onClick(() => {
            if (!this.isLoading) {
              this.handleSave()
            }
          })
      }
      .width('100%')
      .height(48)
      .padding({ left: 16, right: 16 })
      .backgroundColor('#FFFFFF')

      Scroll() {
        Column() {
          // 头像预览
          Column() {
            Text(this.selectedAvatar)
              .fontSize(48)
            Text('点击选择头像')
              .fontSize(12)
              .fontColor('#999999')
              .margin({ top: 8 })
          }
          .width('100%')
          .padding({ top: 24, bottom: 24 })
          .alignItems(HorizontalAlign.Center)

          // 头像选择网格
          Column() {
            Text('选择头像').fontSize(15).fontWeight(FontWeight.Medium).margin({ bottom: 12 })

            Flex({ wrap: FlexWrap.Wrap, justifyContent: FlexAlign.Start }) {
              ForEach(this.avatarOptions, (emoji: string) => {
                Column() {
                  Text(emoji).fontSize(28)
                }
                .width(56)
                .height(56)
                .borderRadius(12)
                .backgroundColor(this.selectedAvatar === emoji ? '#E3F2FD' : '#F5F5F5')
                .border({
                  width: this.selectedAvatar === emoji ? 2 : 0,
                  color: this.selectedAvatar === emoji ? '#007AFF' : 'transparent'
                })
                .justifyContent(FlexAlign.Center)
                .margin({ right: 8, bottom: 8 })
                .onClick(() => {
                  this.selectedAvatar = emoji
                  this.errorMessage = ''
                })
              })
            }
            .width('100%')
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })

          // 用户名编辑
          Column() {
            Text('用户名').fontSize(15).fontWeight(FontWeight.Medium).margin({ bottom: 8 })
            TextInput({ text: this.username, placeholder: '请输入用户名' })
              .type(InputType.Normal)
              .fontSize(15)
              .height(44)
              .backgroundColor('#F5F5F5')
              .borderRadius(10)
              .padding({ left: 14, right: 14 })
              .onChange((value: string) => {
                this.username = value
                this.errorMessage = ''
              })
          }
          .width('100%')
          .padding(16)
          .backgroundColor('#FFFFFF')
          .borderRadius(12)
          .margin({ left: 16, right: 16, top: 12 })
          .alignItems(HorizontalAlign.Start)

          // 错误提示
          if (this.errorMessage.length > 0) {
            Text(this.errorMessage)
              .fontSize(13)
              .fontColor('#FF3B30')
              .width('100%')
              .textAlign(TextAlign.Center)
              .margin({ top: 16 })
          }

          // 保存按钮
          Button(this.isLoading ? '保存中...' : '保存修改')
            .type(ButtonType.Capsule)
            .width('80%')
            .height(44)
            .fontSize(16)
            .fontWeight(FontWeight.Medium)
            .fontColor('#FFFFFF')
            .backgroundColor(this.isLoading ? '#B0B0B0' : '#007AFF')
            .enabled(!this.isLoading)
            .margin({ top: 32 })
            .onClick(() => this.handleSave())
        }
        .padding({ bottom: 40 })
      }
      .width('100%')
      .layoutWeight(1)
      .scrollBar(BarState.Off)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F2F7')
  }
}
