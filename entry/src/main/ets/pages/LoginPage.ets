// ============================================
// 文件名: entry/src/main/ets/pages/LoginPage.ets
// 功能: 用户登录/注册页面（美化版 + 记住用户名）
// ============================================

import { registerUser, loginUser } from '../api/NewsApi'
import { AuthResponse } from '../models/NewsModel'
import router from '@ohos.router'
import promptAction from '@ohos.promptAction'
import dataPreferences from '@ohos.data.preferences'

const PREF_NAME: string = 'NewsMindPrefs'

/**
 * 登录/注册页面
 */
@Entry
@Component
export struct LoginPage {
  @State isRegisterMode: boolean = false
  @State username: string = ''
  @State password: string = ''
  @State confirmPassword: string = ''
  @State isLoading: boolean = false
  @State errorMessage: string = ''
  @State lastUsername: string = ''

  aboutToAppear(): void {
    // 从 Preferences 读取上次登录的用户名
    try {
      const context = getContext(this)
      const prefs: dataPreferences.Preferences = dataPreferences.getPreferencesSync(context, { name: PREF_NAME })
      const saved: string = prefs.getSync('lastUsername', '') as string
      if (saved.length > 0) {
        this.lastUsername = saved
        this.username = saved
      }
    } catch (e) {
      // 静默失败
    }
  }

  private async handleSubmit(): Promise<void> {
    if (this.username.length === 0) {
      this.errorMessage = '请输入用户名'
      return
    }
    if (this.password.length < 4) {
      this.errorMessage = '密码至少4位'
      return
    }
    if (this.isRegisterMode && this.password !== this.confirmPassword) {
      this.errorMessage = '两次密码不一致'
      return
    }

    this.errorMessage = ''
    this.isLoading = true

    try {
      let response: AuthResponse
      if (this.isRegisterMode) {
        response = await registerUser(this.username, this.password)
      } else {
        response = await loginUser(this.username, this.password)
      }

      if (response.success && response.token) {
        // 保存登录状态到 AppStorage
        AppStorage.SetOrCreate('authToken', response.token)
        AppStorage.SetOrCreate('authUserId', response.user_id || 0)
        AppStorage.SetOrCreate('authUsername', response.username || '')
        AppStorage.SetOrCreate('authAvatar', response.avatar || '😀')
        AppStorage.SetOrCreate('isLoggedIn', true)

        // 持久化到 Preferences
        try {
          const context = getContext(this)
          const prefs: dataPreferences.Preferences = dataPreferences.getPreferencesSync(context, { name: PREF_NAME })
          prefs.putSync('authToken', response.token || '')
          prefs.putSync('authUserId', response.user_id || 0)
          prefs.putSync('authUsername', response.username || '')
          prefs.putSync('authAvatar', response.avatar || '😀')
          // 记住上次登录的用户名
          prefs.putSync('lastUsername', response.username || '')
          prefs.flush()
        } catch (e) {
          console.error(`[Prefs] ${(e as Error).message}`)
        }

        promptAction.showToast({
          message: response.message,
          duration: 1500
        })

        // 跳转到主页
        router.replaceUrl({ url: 'pages/MainPage' })
      } else {
        this.errorMessage = response.message || '操作失败'
      }
    } catch (err) {
      const error: Error = err as Error
      this.errorMessage = this.isRegisterMode ? '注册失败，用户名可能已存在' : '登录失败，请检查用户名和密码'
      console.error(`[Auth] ${error.message}`)
    } finally {
      this.isLoading = false
    }
  }

  build() {
    Column() {
      Scroll() {
        Column() {
          // ====== 顶部品牌区 ======
          Column() {
            // 装饰圆点
            Stack() {
              Column()
                .width(100)
                .height(100)
                .borderRadius(50)
                .backgroundColor('rgba(255,255,255,0.15)')
              Column()
                .width(80)
                .height(80)
                .borderRadius(40)
                .backgroundColor('rgba(255,255,255,0.2)')
              Text('📰')
                .fontSize(42)
            }
            .margin({ top: 50, bottom: 16 })

            Text('NewsMind')
              .fontSize(32)
              .fontWeight(FontWeight.Bold)
              .fontColor('#FFFFFF')
              .letterSpacing(2)

            Text('AI 智能新闻摘要')
              .fontSize(14)
              .fontColor('rgba(255,255,255,0.75)')
              .margin({ top: 8 })
          }
          .width('100%')
          .padding({ top: 10, bottom: 48 })
          .linearGradient({
            direction: GradientDirection.Right,
            colors: [['#4A90D9', 0.0], ['#007AFF', 0.5], ['#5AC8FA', 1.0]]
          })
          .borderRadius({ bottomLeft: 40, bottomRight: 40 })
          .alignItems(HorizontalAlign.Center)

          // ====== 表单卡片 ======
          Column() {
            // 标题行
            Row() {
              Text(this.isRegisterMode ? '创建账号' : '欢迎回来')
                .fontSize(24)
                .fontWeight(FontWeight.Bold)
                .fontColor('#1A1A2E')
            }
            .width('100%')
            .margin({ bottom: 4 })

            Text(this.isRegisterMode ? '注册新账号开始使用' : '登录以继续使用')
              .fontSize(14)
              .fontColor('#999999')
              .width('100%')
              .margin({ bottom: 8 })

            // 上次登录提示
            if (this.lastUsername.length > 0 && !this.isRegisterMode) {
              Row() {
                Text('👋 ').fontSize(13)
                Text('上次以 ').fontSize(12).fontColor('#999999')
                Text(this.lastUsername).fontSize(12).fontColor('#007AFF').fontWeight(FontWeight.Medium)
                Text(' 登录').fontSize(12).fontColor('#999999')
              }
              .width('100%')
              .padding({ left: 12, right: 12, top: 8, bottom: 8 })
              .backgroundColor('#F0F7FF')
              .borderRadius(8)
              .margin({ bottom: 20 })
            } else {
              Blank().height(12)
            }

            // ---- 用户名 ----
            Text('用户名').fontSize(13).fontColor('#666666').fontWeight(FontWeight.Medium)
              .width('100%').margin({ bottom: 6 })
            Row() {
              Text('👤').fontSize(16).margin({ right: 10 })
              TextInput({ text: this.username, placeholder: '请输入用户名' })
                .type(InputType.Normal)
                .fontSize(15)
                .fontColor('#333333')
                .layoutWeight(1)
                .backgroundColor(Color.Transparent)
                .padding(0)
                .onChange((value: string) => {
                  this.username = value
                  this.errorMessage = ''
                })
            }
            .width('100%')
            .height(48)
            .backgroundColor('#F7F8FA')
            .borderRadius(12)
            .padding({ left: 16, right: 16 })
            .margin({ bottom: 18 })

            // ---- 密码 ----
            Text('密码').fontSize(13).fontColor('#666666').fontWeight(FontWeight.Medium)
              .width('100%').margin({ bottom: 6 })
            Row() {
              Text('🔒').fontSize(16).margin({ right: 10 })
              TextInput({ text: this.password, placeholder: '请输入密码（至少4位）' })
                .type(InputType.Password)
                .fontSize(15)
                .fontColor('#333333')
                .layoutWeight(1)
                .backgroundColor(Color.Transparent)
                .padding(0)
                .onChange((value: string) => {
                  this.password = value
                  this.errorMessage = ''
                })
            }
            .width('100%')
            .height(48)
            .backgroundColor('#F7F8FA')
            .borderRadius(12)
            .padding({ left: 16, right: 16 })
            .margin({ bottom: 18 })

            // ---- 确认密码（注册模式） ----
            if (this.isRegisterMode) {
              Text('确认密码').fontSize(13).fontColor('#666666').fontWeight(FontWeight.Medium)
                .width('100%').margin({ bottom: 6 })
              Row() {
                Text('🔒').fontSize(16).margin({ right: 10 })
                TextInput({ text: this.confirmPassword, placeholder: '再次输入密码' })
                  .type(InputType.Password)
                  .fontSize(15)
                  .fontColor('#333333')
                  .layoutWeight(1)
                  .backgroundColor(Color.Transparent)
                  .padding(0)
                  .onChange((value: string) => {
                    this.confirmPassword = value
                    this.errorMessage = ''
                  })
              }
              .width('100%')
              .height(48)
              .backgroundColor('#F7F8FA')
              .borderRadius(12)
              .padding({ left: 16, right: 16 })
              .margin({ bottom: 18 })
            }

            // ---- 错误提示 ----
            if (this.errorMessage.length > 0) {
              Row() {
                Text('⚠️').fontSize(14).margin({ right: 6 })
                Text(this.errorMessage)
                  .fontSize(13)
                  .fontColor('#FF3B30')
                  .layoutWeight(1)
              }
              .width('100%')
              .padding({ left: 14, right: 14, top: 10, bottom: 10 })
              .backgroundColor('#FFF5F5')
              .borderRadius(8)
              .margin({ bottom: 12 })
            }

            // ---- 提交按钮 ----
            Column() {
              if (this.isLoading) {
                LoadingProgress().width(22).height(22).color('#FFFFFF')
              } else {
                Text(this.isRegisterMode ? '注 册' : '登 录')
                  .fontSize(17)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#FFFFFF')
              }
            }
            .width('100%')
            .height(50)
            .borderRadius(25)
            .justifyContent(FlexAlign.Center)
            .linearGradient(this.isLoading
              ? { direction: GradientDirection.Right, colors: [['#B0B0B0', 0.0], ['#B0B0B0', 1.0]] }
              : { direction: GradientDirection.Right, colors: [['#4A90D9', 0.0], ['#007AFF', 0.5], ['#5AC8FA', 1.0]] })
            .shadow({ radius: 12, color: 'rgba(0,122,255,0.3)', offsetX: 0, offsetY: 4 })
            .margin({ top: 12 })
            .onClick(() => {
              if (!this.isLoading) {
                this.handleSubmit()
              }
            })

            // ---- 分割线 ----
            Row() {
              Divider().layoutWeight(1).color('#E8E8E8')
              Text(this.isRegisterMode ? '或' : '或').fontSize(12).fontColor('#CCCCCC')
                .padding({ left: 16, right: 16 })
              Divider().layoutWeight(1).color('#E8E8E8')
            }
            .width('100%')
            .margin({ top: 24, bottom: 24 })

            // ---- 切换登录/注册 ----
            Row() {
              Text(this.isRegisterMode ? '已有账号？' : '还没有账号？')
                .fontSize(14)
                .fontColor('#888888')
              Text(this.isRegisterMode ? ' 立即登录' : ' 立即注册')
                .fontSize(14)
                .fontColor('#007AFF')
                .fontWeight(FontWeight.Bold)
                .onClick(() => {
                  this.isRegisterMode = !this.isRegisterMode
                  this.errorMessage = ''
                  this.confirmPassword = ''
                })
            }
            .width('100%')
            .justifyContent(FlexAlign.Center)
          }
          .width('100%')
          .padding({ left: 28, right: 28, top: 28, bottom: 20 })
          .margin({ left: 16, right: 16, top: -20 })
          .backgroundColor('#FFFFFF')
          .borderRadius(20)
          .shadow({ radius: 16, color: 'rgba(0,0,0,0.08)', offsetX: 0, offsetY: 4 })

          // 底部版权
          Text('NewsMind v1.0.0 · AI 驱动')
            .fontSize(11)
            .fontColor('#CCCCCC')
            .margin({ top: 32, bottom: 24 })
        }
        .alignItems(HorizontalAlign.Center)
      }
      .width('100%')
      .height('100%')
      .scrollBar(BarState.Off)
      .edgeEffect(EdgeEffect.Spring)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F2F3F5')
  }
}
