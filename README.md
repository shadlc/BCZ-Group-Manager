# BCZ-Group-Manager

### A small group management tool for Chinese vocabulary software which  called [Bai Ci Zhan](https://www.baicizhan.com/), depends on [Flask](https://github.com/pallets/flask).

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/shadlc/BCZ-Group-Manager)
![Scc Count Badge](https://sloc.xyz/github/shadlc/BCZ-Group-Manager)
![GitHub repo size](https://img.shields.io/github/repo-size/shadlc/BCZ-Group-Manager)
![GitHub - License](https://img.shields.io/github/license/shadlc/BCZ-Group-Manager)
![GitHub last commit](https://img.shields.io/github/last-commit/shadlc/BCZ-Group-Manager)

## 💬 简介
**背个单词卷就算了，没想到连小班都这么卷了吗？！(＃°Д°)**

**百词斩小班数据管理器，这个工具可以方便的为各大百词斩班长管理小班提供便捷的操作，可以自动化的查询小班列表和打卡数据，通过直接对官方API进行爬取，并展示数据，极大地为各大王者小班长省心**

### **注意‼️使用本程序前，需要自行对百词斩APP进行抓包获取授权令牌**

## ✨ 主要功能

- **使用友好的前端页面进行展示以及提供供数据下载，以假乱真（不是**
- **直观的添加和删除关注的小班功能，并以小班为单位展示成员打卡数据**
- **清晰明了地展示小班成员的背单词数量、缺卡、晚卡、漏卡情况**
- **实时获取指关注小班的信息和其成员的打卡信息**
- **使用`Crontab`语法定时获取打卡信息，并有历史数据修正**
 
## 📸 界面展示

<div align=center>
<img src="https://github.com/shadlc/BCZ-Group-Manager/assets/46913095/93017366-a7bc-4bbf-9718-0e18c878917b" height=400px>
<img src="https://github.com/shadlc/BCZ-Group-Manager/assets/46913095/7bae85f6-eaa3-44ca-8e79-16f14f6da89e" height=400px>
<img src="https://github.com/shadlc/BCZ-Group-Manager/assets/46913095/fea62527-c138-45f1-84d3-e251e11ab551" height=400px>
</div>

## 📝 使用指南

### 启动步骤
- **首先确保你安装了 Python3.11、git**
- **本项目使用了 pipenv 依靠虚拟环境进行依赖项管理，请使用 pip install pipenv 安装模块之后启动**
- **本项目没有安全验证系统，请自行增加鉴权模块‼️注意，直接暴露在公网上是极其危险的行为‼️**
- **启动步骤**
  1. 执行 `git clone https://github.com/shadlc/BCZ-Group-Manager.git`
  2. 执行 `cd BCZ-Group-Manager/`
  3. 执行 `pipenv install`
  4. 执行 `pipenv run python ./app.py`
  5. 启动程序后，会生成一个json格式的配置文件并退出
  6. 对百词斩APP进行抓包获取你的`access_token`，将其`access_token`填入配置文件的`main_token`
  7. 再次启动程序，将会启动本地监听(默认`8840`端口)，打开浏览器`http://127.0.0.1:8840`访问并使用

### 配置说明
- **`host`监听地址，默认只允许本地访问，即`127.0.0.1`**
- **`port`监听端口，默认为`8840`**
- **`database_path`数据库路径，默认为`./data.db`**
- **`main_token`必填，是本程序用以获取小班数据的主要使用授权令牌，不要加入任何需要获取数据的小班**
- **`output_file`是程序输出Excel文件的指定目录和默认文件名，默认为`小班数据.xlsx`**
- **`daily_record`以`Crontab`语法自动记录每天数据，默认为晚上23点59分，即`59 23 * * *`**
- **`daily_verify`晚于自动记录时间后的打卡数据会遗失，因此以`Crontab`语法自动校验本周与上周打卡记录，补上遗失的打卡数据，默认为凌晨4点整，即`00 04 * * *`**
- **`cache_second`数据查询功能实时数据的查询间隔，设置缓存时间防止过于频繁的实时查询，默认为600秒**


## 🔌 API

**部分较为实用百词斩官方接口在这里整理一下**

### 个人主页
GET `https://social.baicizhan.com/api/deskmate/home_page`

### 用户信息
GET `https://social.baicizhan.com/api/deskmate/personal_details?uniqueId=XXXXXX`

### 小班列表
GET `https://group.baicizhan.com/group/own_groups?uniqueId=XXXXXX`

### 授权班列表
GET `https://group.baicizhan.com/group/get_group_authorization_page?uniqueId=XXXXXX`

### 小班排名
GET `https://group.baicizhan.com/group/get_group_rank`

### 小班打卡信息
GET `https://group.baicizhan.com/group/information?shareKey=XXXXXX`

### 小班本周打卡详情
GET `https://group.baicizhan.com/group/get_week_rank?shareKey=XXXXXX&week=1`

### 小班上周打卡详情
GET `https://group.baicizhan.com/group/get_week_rank?shareKey=XXXXXX&week=2`

### 小班移除用户
POST `https://group.baicizhan.com/group/remove_members`
```
{
  "shareKey":"XXXXXX",
  "memberIds":[
    XXXXXX
  ]
}
```

### 搜索用户
GET `https://social.baicizhan.com/api/social/get_friend_state?uniqueId=XXXXXX`

### 铜板数量
GET `https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_vo`

### 铜板记录
GET `https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_records`

## ⚠️ 免责申明

感谢您选择使用本小班数据管理器。在使用本程序之前, 请您**仔细阅读**并理解以下免责声明内容：

 - 本程序基于[GPLv3](https://www.gnu.org/licenses/agpl-3.0.html)开源，仅供个人学习、研究和其他非商业性质的合法用途, 任何因违反相关法律法规或侵犯他人权益所导致的法律责任, 由用户自行承担。
 - 用户在使用本程序时, 应遵守所在国家或地区的法律法规, 并对使用该程序产生的一切后果负全部责任。
 - 本程序对于用户使用过程中可能产生的各种风险（包括但不限于被数据来源公司的封禁、用户自身合规问题等）不承担任何责任。
 - 用户违反本声明或者滥用本程序进行非法活动的, 数据来源公司将有权追究您的法律责任。
 - 本程序作者对用户使用本程序产生的一切纠纷、损失或伤害不承担任何责任。
 - 一旦用户开始使用本程序, 则视为用户已充分理解并同意本免责声明的全部内容, 如果您无法接受上述条款, 请**立即停止**使用本程序。
