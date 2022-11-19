# clashprofile

生成并更新 clash 配置文件，并提供 http 下载和规则文件镜像下载。

## 说明

本项目使用 `配置模板` 以及节点的 `订阅链接` 生成多种不同的配置文件，也可以将多个订阅中的节点整合至一个配置文件中~~但会导致部分功能丧失~~。

### 配置模板(template)

位于 `/data/template` 文件夹的半成品配置文件，在每日的更新中会被填入订阅节点并生成配置文件，存放于 `/data` 文件夹下。

您可以仿照 `/static/template` 中预设的默认模板文件和 [clash文档](https://github.com/Dreamacro/clash/wiki/Configuration) 创建自己的模板。

### 订阅链接(subscribe)

通常由服务商所提供，以获取节点信息的订阅链接。如果您愿意临时提供订阅链接，可以联系开发者进行更多服务商适配。

目前支持的服务商/订阅方式:

- [Just My Socks](https://justmysocks3.net/members/index.php)
  - 类型： `jms`
  - 特殊配置项：
    - counter：节点的剩余流量API

计划支持的提供商/订阅方式:

- clash配置文件
- 单独的ss节点
- 单独的ssr节点

### 规则集(ruleset)

或称规则提供者(rule-provider)，是一系列域名或应用程序的列表，可以用于规则的编写。

本项目默认模板使用的规则集来源于 [@Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules)，于每日 22:30(UTC) / 06:30(UTC+8) 使用 GitHub Action 自动生成，因此本项目的定时更新也设定为其后5分钟更新。

### 特色功能

#### 规则集的本地缓存

在部分地区，直接访问 GitHub 获取规则集是较为困难和耗时的行为，因此由配置模板生成配置文件时会将其中的规则集下载至本地并替换配置文件中的下载链接，使规则文件的下载更加高效稳定。

当然，您可以自由的在配置文件中添加不属于默认规则集以外的链接，只需要注意：在启用的规则文件中的规则集若出现**重复的文件名**，将会只保留**靠后**的规则集的文件，因此请务必注意不要出现**不同的文件但文件名相同**的情况。

### 剩余流量及租期

部分服务商会提供接口供用户查询剩余流量及到期时间，在 [Clash for Windows](https://github.com/Fndroid/clash_for_windows_pkg/releases) 中可以通过 `Header` 中的信息将上述信息展示在配置文件界面，若您的服务商提供了接口且在配置文件中**仅启用了一个订阅**，那么您可以在获取配置文件时自动额外取得这些信息。

## 项目配置文件

```yaml
# ============================== 日志相关设置 ==============================
## 终端输出的日志等级，取值范围如下，排名越靠后其等级越高、详细程度越低、内容越少
## TRACE / DEBUG / INFO / WARNING / ERROR / CRITICAL 推荐取 INFO 即可
log_level: INFO

# ============================== 下载相关设置 ==============================
## 下载的最大携程数，服务器网络质量越好可以设置的值越高
download_sem: 3
## 下载失败的重试次数，若服务器网络质量较差，建议设置较高数值
download_retry: 3

#  ============================== 更新相关设置 ==============================
## 触发更新的cron表达式，仅支持五位表达式，其格式为: 分 时 日 月 周
update_cron: 35 6 * * *
## 更新所参考的时区，如果是国内用户请勿改动
update_tz: Asia/Shanghai

# ============================== API相关设置 ==============================
## 填写到 *配置文件中* 的服务器域名/IP地址，如果填写错误可能造成规则集无法更新成功
## 例如此处的默认值即为供本机使用的地址
domian: http://127.0.0.1:46199
## fastapi监听的地址，一般情况下不需要改动
host: 0.0.0.0
## fastapi监听的端口，请与domain保持一致
port: 46199
## 监听的路径前缀，例如在默认值时，监听地址为 http://0.0.0.0:46199/path/to/mess/url
## 主要目的是为了混淆url地址，使其不易被误触，防止配置文件泄露
urlprefix: /path/to/mess/url
## 响应配置文件中包含的 headers，用于填充额外数据，以供CFW等支持的客户端进行解析
## 注意: subscription-userinfo 将会根据配置信息，由脚本自动生成并添加，不要自定义！
headers:
  cache-Control: "no-store,no-cache,must-revalidate"
  profile-update-interval: "24"

# ============================== 订阅相关设置 ==============================
subscribes:
  JMS: # 节点名，可以自定义，注意不要重名
    # 节点的服务商，请参考文档获取支持的服务商
    type: jms
    # 节点的订阅地址
    url: https://jmssub.net/members/getsub.php?service=<service>&id=<id>
    # <特殊,可选>节点的剩余流量API
    counter: https://justmysocks5.net/members/getbwcounter.php?service=<service>&id=<id>
    # <可选>节点的时区信息，用于计算节点过期时间的时间参考
    subtz: America/Los_Angeles

# ============================== 配置文件相关设置 ==============================
profiles:
  JMS-blacklist: # 配置文件名，注意不要重名，否则将会被覆盖
    template: blacklist # 使用的配置模板
    subs: # 使用的订阅节点，可添加多个节点但会失去部分功能
      - JMS # 节点名为订阅信息中的节点名
  whitelist-jms:
    template: whitelist
    subs:
      - JMS
```

## 项目部署

注意，本项目需要 Python3.9 或以上的版本。

1. 将仓库clone至本地 `git clone https://github.com/Well2333/clashprofile.git` 。
2. 在文件夹内执行 `poetry install` 或 `pip install -r requirements.txt` 完成依赖的安装。
3. 使用 screen 或其他虚拟终端，执行 `poetry run python main.py` 或 `python3 main.py`。
