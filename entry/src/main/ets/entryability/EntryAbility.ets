import AbilityConstant from '@ohos.app.ability.AbilityConstant';
import ConfigurationConstant from '@ohos.app.ability.ConfigurationConstant';
import UIAbility from '@ohos.app.ability.UIAbility';
import Want from '@ohos.app.ability.Want';
import hilog from '@ohos.hilog';
import window from '@ohos.window';
import dataPreferences from '@ohos.data.preferences';

const DOMAIN = 0x0000;
const PREF_NAME = 'NewsMindPrefs';

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    try {
      this.context.getApplicationContext().setColorMode(ConfigurationConstant.ColorMode.COLOR_MODE_NOT_SET);
    } catch (err) {
      hilog.error(DOMAIN, 'testTag', 'Failed to set colorMode. Cause: %{public}s', JSON.stringify(err));
    }
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onCreate');
  }

  onDestroy(): void {
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageCreate');

    // 读取持久化的登录状态
    try {
      const prefs: dataPreferences.Preferences = dataPreferences.getPreferencesSync(this.context, { name: PREF_NAME });
      const token: string = (prefs.getSync('authToken', '') as string);
      const username: string = (prefs.getSync('authUsername', '') as string);
      const avatar: string = (prefs.getSync('authAvatar', '😀') as string);
      const userId: number = (prefs.getSync('authUserId', 0) as number);

      // 初始化 AppStorage
      const isLoggedIn: boolean = token.length > 0;
      AppStorage.setOrCreate('authToken', token);
      AppStorage.setOrCreate('authUsername', username);
      AppStorage.setOrCreate('authAvatar', avatar);
      AppStorage.setOrCreate('authUserId', userId);
      AppStorage.setOrCreate('isLoggedIn', isLoggedIn);

      // 根据登录状态决定首页
      const startPage: string = isLoggedIn ? 'pages/MainPage' : 'pages/LoginPage';

      windowStage.loadContent(startPage, (err) => {
        if (err.code) {
          hilog.error(DOMAIN, 'testTag', 'Failed to load content. Cause: %{public}s', JSON.stringify(err));
          return;
        }
        hilog.info(DOMAIN, 'testTag', 'Succeeded in loading content: %{public}s', startPage);
      });
    } catch (err) {
      hilog.error(DOMAIN, 'testTag', 'Failed to read preferences: %{public}s', JSON.stringify(err));
      // 降级：直接加载登录页
      AppStorage.setOrCreate('isLoggedIn', false);
      windowStage.loadContent('pages/LoginPage', (err) => {
        if (err.code) {
          hilog.error(DOMAIN, 'testTag', 'Failed to load content. Cause: %{public}s', JSON.stringify(err));
        }
      });
    }
  }

  onWindowStageDestroy(): void {
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageDestroy');
  }

  onForeground(): void {
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onForeground');
  }

  onBackground(): void {
    hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onBackground');
  }
}
