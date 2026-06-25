# 个人语录管理器

> 用于：电视大屏，web banner抬头显示（广告位），个人管理app的开头页面。
>
> 平时活动/交往 记录自己的经验与知识（习惯，反思等等）以日记、分散形式记录的内容，统一保存并定时输出
>
> 输入：
>
> - 内容：来自活动、日常、学习、交往事件后的思考 反思和经验，以碎片化、简短的内容维系
> - 形式：记录在飞书里
> - 格式：主题/概述：不超过20个字；正文：点开后的详细描述；分类&场景标签；纪录时间
>
> 输出：
>
> - 内容：【标题+详情，可点击】【一行小字】
> - 形式：在个人主页的一个窗格、加载页面、过渡页、页底/顶广告栏位
> - 格式：

核心解决：

1. 语录多，看的少，回顾少
2. 精准在不同场景推送语录分享经验，在闲暇时间看到自己记录的经验
3. 语录经验不重复、不浪费、不漏重要，长期均匀推送
4. 更多功能与需求：
   - 新建语录后，短时间内高概率推送一次（不管语录规模多大），然后冷却



目前的个人语录方案：

- 使用飞书多为表格+导出为excel/csv，记录上千条后维护和浏览困难，优先级不可知，回顾困难，并且数据量大导致加载速度很慢（有时候我并不需要一次性浏览全部）



## 前端



## 后端

语录表的核心内容，就是在不断增长的上千条语录中，每次筛选几条（每天可能就会浏览1-2次，也不可能有大块时间系统整理语录）

那么语录的推送系统就很重要，对此设计一个mysql数据库和记录维护字段：

| mysql          |                    |      |
| -------------- | ------------------ | ---- |
| topic          | [基本信息]         |      |
| plaintext      | [基本信息]         |      |
| class          | [基本信息]分类     |      |
| pin            | [基本信息]场景标签 |      |
| from_who       | [基本信息]作者     |      |
| create_time    | [基本信息]         |      |
| 【后端维护】   |                    |      |
| update_time    | 更新日期           |      |
| show_times     | 展示次数           |      |
| weight         | 权重(初始为10)     |      |
| status         | 状态               |      |
| last_view_time |                    |      |
|                |                    |      |
|                |                    |      |
|                |                    |      |
|                |                    |      |

status状态：ENUM('normal','mastered','skipped') DEFAULT 'normal',

推送算法 = 权重 ÷ 推送次数的 0.8 次方

weight权重计算逻辑：

1. 推送后降低权重，短时间内降低权重，
2. 若推送的内容有反馈，则：【根据反馈内容调整权重】
   - 反馈"已收到！"，则短时间降低更多权重，且恢复权重更慢
   - 反馈"有帮助！"，则短时间内略微降低权重，但回复权重很快且恢复后权重更高
   - 反馈"不再提醒/已知晓"，降低大幅权重
3. 对于刚刚创建的语录，则：【短时间内推送一次】
   - 权重大幅提高




## 数据库

mysql，详见 [`docs/DATABASE.md`](docs/DATABASE.md) 与 [`database/init.sql`](database/init.sql)。

## 接口与鉴权

所有业务接口需要 `X-Token: dancehole` 鉴权（默认 token 在 `backend/random_push.py` 的 `AUTH_TOKEN` 修改）。

返回格式参考 [Hitokoto](https://developer.hitokoto.cn/sentence/) 规范：`id / content / type / from / from_who / created_at / length`。
支持参数：`c`（按类型过滤）、`min_length`、`max_length`、`encode`（`text` / `json`）。

完整接口文档：[`docs/API.md`](docs/API.md)  
部署与启动：[`docs/DEPLOY.md`](docs/DEPLOY.md)  
数据库（建表 / 导入 / 导出 / 备份恢复）：[`docs/DATABASE.md`](docs/DATABASE.md)

## 快速开始

```bash
# 1) 初始化数据库
mysql -uroot -p < database/init.sql

# 2) 安装依赖
pip install flask flask-cors pymysql sqlalchemy pandas

# 3) 启动后端
cd backend && python random_push.py

# 4) 打开前端
#    内置：访问 http://127.0.0.1:5000/
#    独立：直接用浏览器打开 fontend/index.html
```

调用示例：

```bash
curl -H "X-Token: dancehole" "http://127.0.0.1:5000/push?c=%E5%AD%A6%E4%B9%A0&min_length=5&max_length=50&encode=json"
```

## 扩展与使用