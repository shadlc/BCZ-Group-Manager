# BCZ-Group-Manager

### A small group management tool for Chinese vocabulary software which  called [Bai Ci Zhan](https://www.baicizhan.com/), depends on [Flask](https://github.com/pallets/flask).

[![GitHub All Releases](https://img.shields.io/github/downloads/shadlc/BCZ-Group-Manager/total)](../../releases)
![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/shadlc/BCZ-Group-Manager)
![Scc Count Badge](https://sloc.xyz/github/shadlc/BCZ-Group-Manager)
![GitHub repo size](https://img.shields.io/github/repo-size/shadlc/BCZ-Group-Manager)
![GitHub - License](https://img.shields.io/github/license/shadlc/BCZ-Group-Manager)
![GitHub last commit](https://img.shields.io/github/last-commit/shadlc/BCZ-Group-Manager)

## 💬 简介
**背个单词卷就算了，没想到连小班都这么卷了吗？！(＃°Д°)**

**百词斩小班数据管理器，这个工具可以方便的为各大百词斩班长管理小班提供便捷的操作，可以自动化的查询小班列表和打卡数据，通过直接对官方API进行爬取，并展示数据，以后就可以放心嘎嘎踢人啦（不是**

### **注意‼️使用本程序前，需要自行对百词斩APP进行抓包获取授权令牌**

## ✨ 主要功能

- **使用友好的前端页面进行展示以及提供供数据下载，以假乱真（不是**
- **实时获取指关注小班的信息和其成员的打卡信息（成员ID、打卡时间、昵称、打卡是否作弊等）**
- **使用`Crontab`语法定时获取打卡信息**
- **其他已封装API，请自行调用**


## 📝 使用指南

### 启动步骤
- **点击这里[Latest Release Download](https://github.com/shadlc/BCZ-Group-Manager/releases/latest)下载最新可执行文件**
- **启动程序，会生成一个json格式的配置文件并退出**
- **对百词斩APP进行抓包获取你的`access_token`，请先使用一个未加入需要统计数据的小班的小号，将其`access_token`填入配置文件的`main_token`**
- **再次启动程序，将会启动本地监听(默认`8840`端口)，请打开浏览器访问`http://127.0.0.1:8840`访问应用**

### 自编译步骤
- **首先确保你安装了 Python3.11、git**
- **本项目使用了 pipenv 依靠虚拟环境进行依赖项管理，请使用 pip install pipenv 安装模块之后启动**
- **本项目没有安全验证系统，请自行增加鉴权模块‼️注意，直接暴露在公网上是极其危险的行为‼️**
- **启动步骤**
  1. 执行 `git clone https://github.com/shadlc/BCZ-Group-Manager.git`
  2. 执行 `cd BCZ-Group-Manager/`
  3. 执行 `pipenv install`
  4. 执行 `pipenv run python ./app.py`
  5. 使用任意反向代理软件代理本机8840端口到目标路径
  6. 打开网页并使用

### 配置说明
- **`host`监听地址，默认只允许本地访问，即`127.0.0.1`**
- **`port`监听端口，默认为`8840`**
- **`database_path`数据库路径，默认为`./data.db`**
- **`main_token`必填，是本程序用以获取小班数据的主要使用授权令牌，不要加入任何需要获取数据的小班**
- **`output_file`是程序输出Excel文件的指定目录和默认文件名，默认为`百词斩小班数据.xlsx`**
- **`daily_record`以`Crontab`语法自动记录每天数据，默认为晚上23点59分，即`59 23 * * *`**
- **`cache_second`数据查询功能实时数据的查询间隔，设置缓存时间防止过于频繁的实时查询，默认为60秒**


## 🔌 API

**部分较为实用百词斩官方接口在这里整理一下**

### 个人主页
`https://social.baicizhan.com/api/deskmate/home_page`

### 用户信息
`https://social.baicizhan.com/api/deskmate/personal_details?uniqueId=XXXXXX`

### 小班列表
`https://group.baicizhan.com/group/own_groups?uniqueId=XXXXXX`

### 授权班列表
`https://group.baicizhan.com/group/get_group_authorization_page?uniqueId=XXXXXX`

### 小班排名
`https://group.baicizhan.com/group/get_group_rank`

### 小班打卡信息
`https://group.baicizhan.com/group/information?shareKey=XXXXXX`

### 小班本周打卡详情
`https://group.baicizhan.com/group/get_week_rank?shareKey=XXXXXX&week=1`

### 小班上周打卡详情
`https://group.baicizhan.com/group/get_week_rank?shareKey=XXXXXX&week=2`

### 搜索用户
`https://social.baicizhan.com/api/social/get_friend_state?uniqueId=XXXXXX`

### 铜板数量
`https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_vo`

### 铜板记录
`https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_records`
