# BCZ-Group-Manager

### A small group management tool for Chinese vocabulary software which  called [Bai Ci Zhan](https://www.baicizhan.com/), depends on [Flask](https://github.com/pallets/flask).

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/shadlc/BCZ-Group-Manager)
![Scc Count Badge](https://sloc.xyz/github/shadlc/BCZ-Group-Manager)
![GitHub repo size](https://img.shields.io/github/repo-size/shadlc/BCZ-Group-Manager)
![GitHub - License](https://img.shields.io/github/license/shadlc/BCZ-Group-Manager)
![platform](https://img.shields.io/badge/platform-linux-blue)
![GitHub last commit](https://img.shields.io/github/last-commit/shadlc/BCZ-Group-Manager)

## 💬 简介
**背个单词卷就算了，没想到连小班都这么卷了吗？！(＃°Д°)**

**百词斩小班数据提取器，这个工具可以方便的为各大百词斩班长管理小班提供便捷的操作，可以自动化的提取小班列表和打卡数据，通过直接对官方API进行爬取，并输出为Excel表格，以后就可以放心嘎嘎踢人啦（不是**

### **注意‼️使用本程序前，需要自行对百词斩APP进行抓包**

## ✨ 主要功能

- **实时获取指定用户名下所有小班和成员的打卡信息(成员ID、打卡时间、昵称、打卡是否作弊等)**
- **使用`Crontab`语法定时获取打卡信息**
- **使用友好的前端页面提供数据下载**
- **其他已封装API，请自行调用**


## 📝 使用指南

### 启动步骤
- **点击这里[Latest Release Download](https://github.com/shadlc/BCZ-Group-Manager/releases/latest)下载最新可执行文件**
- **启动程序，会生成一个json格式的配置文件并退出**
- **对百词斩APP进行抓包获取你的`access_token`，请先使用一个未加入需要统计数据的小班的小号，将其`access_token`填入配置文件的`unauthorized_token`，然后使用已加入小班的账号`access_token`填入`authorized_token`(这不是必要的，但是没有已加入小班的账号，无法获取班内昵称)**
- **再次启动程序，则可以获取实时小班数据**
- **或者添加`-s`或者`--server`参数启动，将会启动本地监听(默认`8840`端口)并根据`Crontab`计划地获取小班数据**

### 自编译步骤
- **首先确保你安装了 Python3.11、git**
- **本项目使用了 pipenv 依靠虚拟环境进行依赖项管理，请使用 pip install pipenv 安装模块之后启动**
- **本项目没有安全验证系统，请自行增加鉴权模块‼️注意，直接暴露在公网上是极其危险的行为‼️**
- **启动步骤**
  1. 执行 `git clone https://github.com/shadlc/BCZ-Group-Manager.git`
  2. 执行 `cd BCZ-Group-Manager/`
  3. 执行 `pipenv install`
  4. 执行 `pipenv run python ./app.py -s`
  5. 使用任意反向代理软件代理本机8840端口到目标路径
  6. 打开网页并使用

### 配置说明
- **`unauthorized_token`必填，是本程序用以获取小班数据的主要使用凭证，不要加入任何需要获取数据的小班**
- **`authorized_token`非必填，是本程序用以获取班内昵称的token，必须加入所有想要获取班内昵称的小班，即`user_id`用户的token最佳**
- **`user_id`为程序默认爬取的指定用户百词斩ID**
- **`only_own_group`决定了是否只获取`user_id`为班长的小班数据，默认为`true`**
- **`output_file`是程序输出Excel文件的指定目录和默认文件名，默认为`xlsx/百词斩小班数据.xlsx`**
- **`schedules`是以`Crontab`语法记录的用以自动记录小班数据的时间段列表，填写多个可识别的`Crontab`参数，将按指定时间获取`user_id`填写的用户小班数据，默认为`["59 23 * * *"]`**


## 🔌 API

**部分较为实用百词斩官方接口在这里整理一下**

### 班级列表
`https://group.baicizhan.com/group/own_groups?uniqueId=XXXXXX`

### 授权班列表
`https://group.baicizhan.com/group/get_group_authorization_page?uniqueId=XXXXXX`

### 班级排名
`https://group.baicizhan.com/group/get_group_rank`

### 打卡信息
`https://group.baicizhan.com/group/information?shareKey=XXXXXX`

### 铜板数量
`https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_vo`

### 铜板记录
`https://learn.baicizhan.com/api/mall/proxy/creditmall/get_credit_records`
