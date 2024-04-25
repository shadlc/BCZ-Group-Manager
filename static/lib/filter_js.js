

/* <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.min.css">

    <script src="https://cdn.bootcdn.net/ajax/libs/jquery/3.5.1/jquery.min.js">//swal2需要</script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.all.min.js"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js">//折线图绘制</script> 
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js">//日期处理</script>  



*/






//初始化部分


//初始化数据，从服务器获取
var initData = null;


//全局服务器地址
const url = 'ws://192.168.1.101:8080';



// Establish WebSocket connection
var socket = new WebSocket(`${url}/filter/a/`);
socket.onmessage = function (event) {
    if (event.data) {
        initData = JSON.parse(event.data);
        init(initData);
    }
};
socket.onopen = function () {
    console.log('WebSocket connection established');
};
socket.onerror = function (error) {
    console.log('WebSocket error: ' + error);
};
socket.onclose = function () {
    console.log('WebSocket connection closed');
};

function getTimestamp() {
    var date = new Date();
    const timestamp = parseint(date.getTime() / 1000);
    return timestamp;
}
function setCookie(token) {
    document.cookie = `access_token=${token};Pay-Support-H5=alipay_mob_client:qq_app device_name="android/V2218A-vivo"; bcz_dmid="2a16dfbb"; device_version="12"; device_id="032ae8f8427885d7"; app_name="7060100"; channel="qq"; client_time="${getTimestamp()}"
pay-support: alipay_mob_client;qq_app;`;
}
function setHeader(xhr) {
    xhr.withCredentials = true;
    setCookie(getAccessToken());
    xhr.setRequestHeader("Accept", "*/*");
    xhr.setRequestHeader("Origin", "");
    xhr.setRequestHeader("X-Requested-With", "");
    xhr.setRequestHeader("Sec-Fetch-Site", "same-site");
    xhr.setRequestHeader("Sec-Fetch-Mode", "cors");
    xhr.setRequestHeader("Sec-Fetch-Dest", "empty");
    xhr.setRequestHeader("Referer", "");
    xhr.setRequestHeader("Accept-Encoding", "gzip, deflate");
    xhr.setRequestHeader("Accept-Language", "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7");
    xhr.setRequestHeader('User-Agent', 'bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI');

}
function init(initData) {
    //主初始化函数
    // Load user information
    if (initData.accountCount == 0) swal2.fire("错误", "没有可用的账号，请先创建账号", "error");
    setCookie(main_access_token);
    // var xhr = new XMLHttpRequest();

    // xhr.open('GET', 'https://social.baicizhan.com/api/deskmate/home_page', true);
    // setHeader(xhr);

    // xhr.onload = function () {
    // if (xhr.status === 200) {
    // var userData = JSON.parse(xhr.responseText);
    document.getElementById('useravatar').src = initData.avatarUrl;
    // }
    // };
    // xhr.send();

    // Load sub-class information
    var groupCount = initData.groupCount;

    for (var i = 0; i < groupCount; i++) {
        var shareKey = initData.shareKeys[i];
        var status = initData.statuses[i];
        loadGroupInfo(shareKey, status, xhr);
        //前面已经创建了div，这里只需要填充折线图
        drawChart(initData.times[i], initData.rank[i], initData.dakaCounts[i])
    }
}
function loadGroupInfo(shareKey, status, xhr) {

    xhr.open('GET', 'https://group.baicizhan.com/group/information?shareKey=' + shareKey, true);

    xhr.onload = function () {
        if (xhr.status === 200) {
            var groupData = JSON.parse(xhr.responseText);
            var className = groupData.className;
            var leaderName = groupData.leaderName;
            var studentCount = groupData.studentCount;
            var todayDakaCounts = groupData.todayDakaCounts;
            var intro = groupData.introduction;
            var avatarUrl = groupData.avatarUrl;
            // Create a new div for the sub-class avatar

            const template = `
                            <div class="card">
                                <div class="frame">
                                    <div class="tag" name="classinfo">
                                        <div class="avatar ${shareKey}" id="classavatar"></div>
                                        <div class="frame">
                                            <div class="tag">
                                                <div class="${shareKey}" id="name">${className}</div>
                                                <div class="box-separator"></div>
                                                <div class="${shareKey}" id="leader">${leaderName}</div>
                                            </div>
                                            <div class="tag">
                                                <div class="${shareKey}" id="students">${studentCount}</div>
                                                <div class="box-separator"></div>
                                                <div class="${shareKey}" id="todayDakaCounts">${todayDakaCounts}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="graph ${shareKey}" id = "graph"></div>
                                    <div class="${shareKey}" id="status">${status}</div>
                                    <div class="separator"></div>
                                    <div class="tag center">
                                        <div class="tag button ${shareKey}" id="strata">策略</div>
                                        <div class="box-separator"></div>
                                        <div class="tag button ${shareKey}" id="members">成员</div>
                                        <div class="box-separator"></div>
                                        <div class="tag button ${shareKey}" id="notice">公告</div>
                                        <div class="box-separator"></div>
                                        <div class="tag button ${shareKey}" id="log">日志</div>
                                    </div>
                                </div>
                            </div>`;

            // 使用DOMParser解析模板字符串为HTML元素
            const parser = new DOMParser();
            const doc = parser.parseFromString(template, 'text/html');
            const divElement = doc.body.firstChild;

            // 将新创建的元素添加到文档中
            document.body.appendChild(divElement);

        }
    };
    xhr.send();
}



function drawChart(cnt, t, a, b) {
    // 加载Google Charts库
    google.charts.load('current', { 'packages': ['corechart'] });
    // 创建数据表
    var data = new google.visualization.DataTable();
    data.addColumn('datetime', 'Time'); // 时间列
    data.addColumn('number', 'Series A'); // 左侧Y轴的数据列
    data.addColumn('number', 'Series B'); // 右侧Y轴的数据列

    // 添加数据行
    for (var i = 0; i < cnt; i++) {
        data.addRow([new Date(t[i]), a[i], b[i]]);
    }

    // 设置图表选项
    var options = {
        title: 'Line Chart with Two Axes',
        hAxis: {
            title: 'Time',
            format: 'yyyy-MM-dd HH:mm:ss' // 根据你的时间格式调整
        },
        vAxes: {
            // 左侧Y轴
            0: { title: 'Values for A' },
            // 右侧Y轴
            1: { title: 'Values for B', viewWindow: { min: 0 } } // 设置合适的视图窗口
        },
        series: {
            // 系列A使用左侧Y轴
            0: { targetAxisIndex: 0 },
            // 系列B使用右侧Y轴
            1: { targetAxisIndex: 1, type: 'line' }
        }
    };

    // 绘制图表
    var chart = new google.visualization.LineChart(document.querySelector(`${shareKey}.#graph`));
    chart.draw(data, options);
}


function getAccessToken() {
    return document.cookie.match(/access_token=([^;]*)/)[1];
}















// 事件绑定:account管理
document.getElementById('account').addEventListener('click', function () {
    Swal.fire({//弹窗，选择、删除、创建账号
        title: 'Account Management',
        html: '<ul id="account-list"></ul>',
        showCancelButton: false,
        showConfirmButton: false,
        footer: '<button id="add-button">Add</button>'
    });
    var accountCount = initData.accountCount;
    for (var i = 0; i < accountCount; i++) {//遍历账号信息，创建列表项
        var avatarPath = initData.avatarPaths[i];
        var username = initData.usernames[i];
        var uniqueId = initData.uniqueIds[i];
        var listItem = document.createElement('li');
        listItem.innerHTML = `
            <img src="${avatarPath}" alt="${username}">
            ${username} - ${uniqueId}
            <button class="switch-button">Switch</button>
            <button class="delete-button">Delete</button>
            `;
        document.getElementById('account-list').appendChild(listItem);
    }
    document.querySelectorAll('.switch-button').forEach(function (button) {//每一行的切换按钮
        button.addEventListener('click', function (event) {
            var uniqueId = event.target.parentNode.querySelector('img').alt;//获取用户名
            Swal.fire({
                title: 'Are you sure?',
                text: "Switching account?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, switch it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    sendRequest({ "uniqueId": uniqueId, 'action': 'switch' }, 'switch');
                }
            });
        });
    });
    document.querySelectorAll('.delete-button').forEach(function (button) {//每一行的删除按钮
        button.addEventListener('click', function (event) {
            var uniqueId = event.target.parentNode.querySelector('img').alt;
            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to recover this account!",
                icon: 'error',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    sendRequest({ "uniqueId": uniqueId, 'action': 'delete' }, 'delete');
                }
            });
        });
    });
    document.getElementById('add-button').addEventListener('click', function () {//添加账号按钮
        Swal.fire({
            title: 'Add Account',
            html: `  
            <input id="uniqueIdInput" type="text" placeholder="Enter uniqueId">  
            <input id="accessTokenInput" type="text" placeholder="Enter accessToken">  
            `,
            focusConfirm: false,
            preConfirm: function () {
                var uniqueId = document.getElementById('uniqueIdInput').value;
                var accessToken = document.getElementById('accessTokenInput').value;
                if (!uniqueId || !accessToken) {
                    Swal.showValidationMessage('Please fill out all the fields!');
                    return false;
                }
                return true;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                var uniqueId = document.getElementById('unique-id').value;
                var accessToken = document.getElementById('access-token').value;
                sendRequest({ "uniqueId": uniqueId, "accessToken": accessToken, "action": "add" }, 'add');
            }
        });
    });
    function sendRequest(data, operation) {
        fetch('/filter/a/' + operation, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                console.log(`${operation} account successfully:`, data);
            })
            .catch(error => {
                console.error(`Error:failed to ${operation} account:`, error);
            });
        // var xhr = new XMLHttpRequest();
        // xhr.open('POST', '/filter/a/' + operation, true);
        // xhr.setRequestHeader('Content-Type', 'application/json');
        // xhr.send(JSON.stringify(data));
    }
});


//导出日志按钮




document.getElementById('export').addEventListener('click', function () {
    // 获取本周一和今天的日期  
    const startDate = moment().startOf('week').format('YYYY-MM-DD');
    const endDate = moment().format('YYYY-MM-DD');

    Swal.fire({
        title: '请选择日期范围',
        html: `  
                <input type="text" id="swal-input-start" class="swal2-input" value="${startDate}">  
                <input type="text" id="swal-input-end" class="swal2-input" value="${endDate}">  
            `,
        focusConfirm: false,
        preConfirm: () => {
            const start = document.getElementById('swal-input-start').value || '-1';
            const end = document.getElementById('swal-input-end').value || '-1';

            return {
                startDate: start,
                endDate: end
            };
        },
        showCancelButton: true,
        confirmButtonText: '导出运行日志',
        cancelButtonText: '取消',
        showLoaderOnConfirm: true,
        didOpen: () => {
            Swal.getHtmlContainer().querySelector('#swal2-confirm').addEventListener('click', () => {
                const type = 'run'; // 运行日志  
                exportLog(type);
            });

            const notifyBtn = Swal.getHtmlContainer().insertAdjacentHTML
                ('beforeend', '<button class="swal2-confirm swal2-styled" style="display:inline-block;margin-left:10px;">导出通知日志</button>');
            notifyBtn.addEventListener('click', () => {
                const type = 'notify'; // 通知日志  
                exportLog(type);
            });
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.close();
        }
    });
});

function exportLog(type) {//导出某物并且下载
    const { startDate, endDate } = Swal.getPopup().preConfirm();

    const data = {
        type: type,
        startDate: startDate,
        endDate: endDate
    };

    // 发送POST请求到服务器  
    fetch(`${url}/filter/a/${type}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // 假设服务器返回的是blob文件  
            return response.blob();
        })
        .then(blob => {
            // 创建一个用于下载文件的链接  
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // 设置下载文件名  
            a.download = 'export.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'An error occurred while exporting the log.', 'error');
        });

}


//好了，到这里就结束了，可以愉快的玩耍了。———— fittencode

//下一个，策略管理
//动画切换函数
function Fade(element) {
    element.style.animation = 'Fade 0.8s forwards';
}
function Show(element) {
    element.style.animation = 'Show 0.8s forwards';
}

//策略按钮点击事件


const data = {};
// 假设服务器响应的JSON结构如下  
const mockServerResponse = {
    totalStrategies: 3,
    strategies: {
        "策略一": {
            weekDays: ["周一", "周三"],
            timesStart: ["09:00"],
            timesEnd: ["10:00"],
            minPeople: 5,
            subItemsCount: 2,
            subItems: {
                "子条目1": {
                    operation: "接受",
                    validity: "本周",
                    conditionsCount: 3,
                    conditions: [
                        { name: "同桌天数", value: 5, operator: "大于", equality: false },
                        // ... 其他条件  
                    ]
                },
                // ... 其他子条目  
            }
        },
        "策略二": {
            weekDays: ["周二", "周四"],
            timesStart: ["10:00"],
            timesEnd: ["11:00"],
            minPeople: 3,
            subItemsCount: 1,
            subItems: {
                "子条目1": {
                    operation: "拒绝",
                    validity: "本周",
                    conditionsCount: 2,
                    conditions: [
                        { name: "同桌天数", value: 3, operator: "大于", equality: false },
                        // ... 其他条件  
                    ]
                },
                // ... 其他子条目  
            }
        },
        // ... 其他策略  
    }
};
//点击策略按钮时调用
function showStrategyPage(button)
{
    shareKey = button.classList[1];
    data = fetchStrategyData(shareKey, 1);
    updateStrategyButtonsAndInfo(data);
}
// 初始化：模拟从服务器获取JSON的异步操作  
function fetchStrategyData(shareKey, week) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(mockServerResponse);
        }, 500); // 模拟网络延迟  
    });
    fetch(`${url}/strategy?shareKey=${shareKey}&week=${week}`)
        .then(response)
        .catch(error => {
            console.error('Error:', error);
        });
    return response.json();
}

// 初始化：更新策略按钮并显示第一个策略信息  
function updateStrategyButtonsAndInfo(data) {
    const operationCard = document.getElementById('operation');
    operationCard.innerHTML = ''; // 清空operation内容 ，删除现有所有按钮  


    // 添加额外按钮：保存并返回、不保存、新建  
    ['保存并返回', '不保存', '新建'].forEach((text, index) => {
        const btn = document.createElement('div');
        btn.classList.add('center-tag button');
        btn.textContent = text;
        if (text === '新建') {
            btn.addEventListener('click', () => {

                createNewStrategy();
            });
        }
        operationCard.appendChild(btn);
    });

    // 分割线
    const separator = document.createElement('div');
    separator.classList.add('separator');
    operationCard.appendChild(separator);


    // 创建并添加策略按钮  
    data.strategies.forEach((strategyname, strategy) => {
        const btn = document.createElement('div');
        btn.classList.add('center-tag button');
        btn.textContent = strategy.name;
        btn.addEventListener('click', () => {
            // 点击时更新页面显示该策略信息（此处省略实现细节）  
            showStrategyInfo(strategyname);
            strategyButtons = operationCard.querySelectorAll('.center-tag');
            // 先清除所有按钮的active样式
            strategyButtons.forEach(btn => btn.classList.remove('active'));
            // 切换按钮样式  
            btn.classList.add('active');
        });
        if (index === 0) {
            btn.classList.add('active'); // 默认选中第一个策略按钮  
            showStrategyInfo(strategyname);
        }
        operationCard.appendChild(btn);
    });
}
// 初始化结束
// 以下是 策略 实现细节


function showWeekDays() {
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

    const inputOptions = {};
    days.forEach((day, index) => {
        inputOptions[index] = day;
    });

    Swal.fire({
        title: '选择星期',
        input: 'checkbox',
        inputOptions: inputOptions,
        inputValidator: (result) => {
            if (!result) {
                return '至少选择一天';
            }
        },
        inputPlaceholder: '选择星期',
        showCancelButton: true,
        confirmButtonText: '确认',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            const selectedDays = Object.keys(result.value).map(key => days[key]);
            // 输出选中的星期字符串列表
            console.log(selectedDays);
            return selectedDays;
        }
    });
}

function addStrategy() {
    // 新建策略的逻辑（后台数据）  
    const newStrategy = {
        name: "新策略",
        weekDays: ["周一", "周三"],
        timesStart: ["09:00"],
        timesEnd: ["10:00"],
        minPeople: 5,
        subItemsCount: 2,
        subItems: {
            "子条目1": {
                operation: "接受",
                validity: "本周",
                conditionsCount: 3,
                conditions: [
                    { name: "同桌天数", value: 5, operator: "大于", equality: false },
                    // ... 其他条件  
                ]
            },
            // ... 其他子条目  
        }
    };
    data.strategies.push(newStrategy);

    // 更新按钮
    newButton = document.createElement('div');
    newButton.innerHTML = `
        <div class="center-tag button" id="${newStrategy.name}">${newStrategy.name} onclick="showStrategyInfo(this.id)"></div>
    `;
    document.getElementById('operation').appendChild(newButton);

    // 更新页面显示
    showStrategyInfo(newStrategy);
}
function deleteStrategy(button) {
    // 删除策略的逻辑（后台数据）  
    const strategyName = button.parentNode.parentNode.parentNode.id;
    const index = data.strategies.findIndex(strategy => strategy.name === strategyName);
    data.strategies.splice(index, 1);

    // 删除策略卡片
    button.parentNode.parentNode.parentNode.remove();

}
function saveStrategy(strategyName) {
    // 保存策略的逻辑（后台数据）  

    const strategyName = this.parentNode.parentNode.parentNode.id;
    const strategyData = { strategyName: {} };
    const index = data.strategies.findIndex(strategy => strategy.name === strategyName);
    data.strategies[index] = this.parentNode.parentNode.parentNode.strategy;

}
function addSubItem(button) {
    // 在策略中添加子条目，仍属于策略部分

    // 添加后台数据
    const newSubItem = {
        name: "子条目1",
        operation: "接受",
        validity: "本次",
        conditions: [

        ]
    };

    thisStrategy = data.strategies.find(strategy => strategy.name === button.parentNode.parentNode.parentNode.id)
    thisStrategy.subItems.push(newSubItem);



    // 添加子条目卡片  
    const subItemCard = document.createElement('div');
    subItemCard.classList.add('card subItem');
    subItemCard.id = 'newSubItem';

    subItemCard.innerHTML = `
        <div class="tag subItemName">
            <input type="text" value="子条目1">
        </div>
        <div class="tag actions">
            <div class="center-tag button" onclick="addCondition(this)">添加条件</div>
            <div class="center-tag button" onclick="copySubItem(this)">复制</div>
            <div class="center-tag button" onclick="deleteSubItem(this)">删除</div>
        </div>
    `;

    document.getElementById('column').appendChild(subItemCard);
}

// 显示策略信息  
function showStrategyInfo(strategyName) {
    const column = document.getElementById('column');
    column.innerHTML = ''; // 清空column内容  

    // 获得策略对象
    const strategy = data.strategies.find(strategy => strategy.name === strategyName);

    // 创建并添加策略名的card  (包括操作按钮)
    const strategyCard = document.createElement('div');
    strategyCard.classList.add('card strategyName');
    strategyCard.id = strategy.name;


    const strategyNameInput = document.createElement('input');
    strategyNameInput.value = strategy.name;
    strategyCard.appendChild(strategyNameInput);

    // 添加子条目、复制、删除按钮 
    const actionButtonsDiv = document.createElement('div');
    actionButtonsDiv.innerHTML = `
        <div class="center-tag button" onclick="addSubItem(this)">添加子条目</div>
        <div class="center-tag button" onclick="copySubItem(this)">复制</div>
        <div class="center-tag button" onclick="deleteSubItem(this)">删除</div>
    `;

    addSubItemButton.addEventListener('click', () => {
        // 添加子条目的逻辑  (要记得后台数据的更新)
        const newSubItem = {
            name: "子条目1",
            operation: "接受",
            validity: "本次",
            conditions: [

            ]
        };
        strategy.subItems.push(newSubItem);

        // 添加子条目卡片  
        const subItemCard = document.createElement('div');
        subItemCard.classList.add('card subItem');
        subItemCard.id = newSubItem.name;

        subItemCard.innerHTML = `
            <div class="tag subItemName">
                <input type="text" value="${newSubItem.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag button" onclick="addCondition(this)">添加条件</div>
                <div class="center-tag button" onclick="copySubItem(this)">复制</div>
                <div class="center-tag button" onclick="deleteSubItem(this)">删除</div>
            </div>
        `;

    });

    const copyButton = document.createElement('div');
    copyButton.classList.add('center-tag button');
    copyButton.textContent = '复制';
    copyButton.addEventListener('click', () => {
        // 复制策略的逻辑  
        const copiedStrategy = JSON.parse(JSON.stringify(strategy));
        copiedStrategy.name = '复制的' + copiedStrategy.name;
        data.strategies.push(copiedStrategy);
        updateStrategyButtonsAndInfo(data);
    });

    const deleteButton = document.createElement('div');
    deleteButton.classList.add('center-tag button');
    deleteButton.textContent = '删除';
    deleteButton.addEventListener('click', () => {
        // 删除策略的逻辑  
        const index = data.strategies.indexOf(strategy);
        data.strategies.splice(index, 1);
        updateStrategyButtonsAndInfo(data);
    });

    actionButtonsDiv.appendChild(addSubItemButton);
    actionButtonsDiv.appendChild(copyButton);
    actionButtonsDiv.appendChild(deleteButton);

    strategyCard.appendChild(actionButtonsDiv);
    column.appendChild(strategyCard);

    // 创建并添加每个子条目的card  
    strategy.subItems.forEach((subItem) => {

        // 添加子条目名称（单独卡片）
        const subItemNameCard = document.createElement('div');
        subItemNameCard.classList.add('card subItemName');
        subItemNameCard.id = subItem.name;

        const subItemNameInput = document.createElement('input');
        subItemNameInput.value = subItem.name;
        subItemNameCard.appendChild(subItemNameInput);
        // 添加条件、复制、删除按钮
        const actionButtonsDiv = document.createElement('div');
        actionButtonsDiv.classList.add('tag actions');
        const addConditionButton = document.createElement('div');
        addConditionButton.classList.add('center-tag button');
        addConditionButton.textContent = '添加条件';
        addConditionButton.addEventListener('click', () => {
            // 添加条件的逻辑  
            const newCondition = ```
                    <div class="tag condition">
                        <div class="tag name">
                            <select>
                                <option>同桌天数</option>
                                <option>总榜最长天数</option>
                                <option>今日已打卡0/1</option>
                                <option>作弊0/1</option>
                                <option>总榜最高完成率</option>
                                <option>小队头像框</option>
                                <option>上周打卡天数</option>
                                <option>本周打卡天数</option>
                                <option>加入天数</option>
                                <option>上周晚卡天数</option>
                                <option>本周晚卡天数</option>
                            </select>
                        </div>
                        <div class="tag operator">
                            <select>
                                <option>大于</option>
                                <option>小于</option>
                            </select>
                        </div>
                        <div class="tag value">
                            <input type="number">
                        </div>
                        <div class="tag equality">
                            <select>
                                <option>包含</option>
                                <option>不包含</option>
                            </select>
                        </div>
                        <div class="tag actions">
                            <div class="center-tag button">复制</div>
                            <div class="center-tag button">删除</div>
                        </div>
                    </div>
            ```
            document.getElementById(subItem.name).appendChild(newCondition);
        });


        subItem.Conditions.forEach((Condition) => {
            // 创建tag元素  
            const ConditionTag = document.createElement('div');
            ConditionTag.id = Condition.name;
            ConditionTag.classList.add('tag');

            // 创建子条目名称  
            const nameDiv = document.createElement('div');
            nameDiv.classList.add('tag name');
            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.value = Condition.name; // 初始化为子条目的名称  
            nameDiv.appendChild(nameInput);

            // 添加复制和删除按钮到子条目名称右侧
            const copyButton = document.createElement('div');
            copyButton.classList.add('center-tag button');
            copyButton.textContent = '复制';
            copyButton.addEventListener('click', () => {
                // 复制子条目的逻辑

                // 创建一个新的元素，并将要复制的元素的innerHTML赋值给新元素
                const copiedElement = document.createElement('div');
                copiedElement.innerHTML = copyButton.parentNode.parentNode.parentNode.innerHTML;
                // 将新创建的元素插入到目标位置
                document.getElementById(subItem.name).appendChild(copiedElement);
            });
            const deleteButton = document.createElement('div');
            deleteButton.classList.add('center-tag button');
            deleteButton.textContent = '删除';
            deleteButton.addEventListener('click', () => {
                // 删除子条目的逻辑
                deleteButton.parentNode.parentNode.parentNode.remove();
            });

            actionButtonsDiv.appendChild(copyButton);
            actionButtonsDiv.appendChild(deleteButton);

            nameDiv.appendChild(actionButtonsDiv);
            ConditionTag.appendChild(nameDiv);

            // 创建子条目操作下拉框  
            const actionDiv = document.createElement('div');
            actionDiv.classList.add('tag action');
            const actionSelect = document.createElement('select');
            const actionOptions = ['接受', '移出'];
            actionOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.textContent = option;
                actionSelect.appendChild(optionElement);
            });
            actionSelect.value = Condition.action; // 初始化为子条目的操作  
            actionDiv.appendChild(actionSelect);
            ConditionTag.appendChild(actionDiv);

            // 创建子条目操作有效期下拉框  
            const validityDiv = document.createElement('div');
            validityDiv.classList.add('tag validity');
            const validitySelect = document.createElement('select');
            const validityOptions = ['本次', '今天', '本周'];
            validityOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.textContent = option;
                validitySelect.appendChild(optionElement);
            });
            validitySelect.value = Condition.validity; // 初始化为子条目的有效期  
            validityDiv.appendChild(validitySelect);
            ConditionTag.appendChild(validityDiv);

            // 添加条件的frame  
            Condition.conditions.forEach(condition => {
                addConditionTag(ConditionTag, condition);
            });

            // 将卡片添加到容器  
            column.appendChild(ConditionTag);
        });

        // 辅助函数：添加条件的frame到卡片中  
        function addConditionTag(card, condition = {}) {
            // 创建条件frame的容器  
            const ConditionTag = document.createElement('div');
            ConditionTag.classList.add('card-condition');

            // 创建条件名下拉框  
            const conditionNameDiv = document.createElement('div');
            const conditionNameSelect = document.createElement('select');
            const conditionNameOptions = [
                '同桌天数', '总榜最长天数', '今日已打卡0/1', '作弊0/1', '总榜最高完成率',
                '小队头像框', '上周打卡天数', '本周打卡天数', '加入天数', '上周晚卡天数', '本周晚卡天数'
            ];
            conditionNameOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.textContent = option;
                conditionNameSelect.appendChild(optionElement);
            });
            conditionNameSelect.value

            conditionNameSelect.value = condition.name || conditionNameOptions[0]; // 初始化为条件名或默认选项
            conditionNameDiv.appendChild(conditionNameSelect);

            // 添加复制和删除按钮到条件名右侧
            const conditionButtonsDiv = document.createElement('div');
            conditionButtonsDiv.classList.add('condition-actions');
            const copyConditionButton = document.createElement('div');
            copyConditionButton.textContent = '复制';
            copyConditionButton.addEventListener('click', () => {
                // 复制条件的逻辑
                // ...
            });
            const deleteConditionButton = document.createElement('div');
            deleteConditionButton.textContent = '删除';
            deleteConditionButton.addEventListener('click', () => {
                // 删除条件的逻辑
                // ...
                ConditionTag.remove();
            });
            conditionButtonsDiv.appendChild(copyConditionButton);
            conditionButtonsDiv.appendChild(deleteConditionButton);
            conditionNameDiv.appendChild(conditionButtonsDiv);

            // 添加条件的其他部分
            const operatorDiv = document.createElement('div');
            const operatorSelect = document.createElement('select');
            const operatorOptions = ['大于', '小于'];
            operatorOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.textContent = option;
                operatorSelect.appendChild(optionElement);
            });
            operatorSelect.value = condition.operator || operatorOptions[0]; // 初始化为条件操作符或默认选项
            operatorDiv.appendChild(operatorSelect);
            ConditionTag.appendChild(operatorDiv);

            const valueInput = document.createElement('input');
            valueInput.type = 'number';
            valueInput.value = condition.value || ''; // 初始化为条件值或空字符串
            ConditionTag.appendChild(valueInput);

            const equalityDiv = document.createElement('div');
            const equalitySelect = document.createElement('select');
            const equalityOptions = ['包含', '不包含'];
            equalityOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.textContent = option;
                equalitySelect.appendChild(optionElement);
            });
            equalitySelect.value = condition.equality || equalityOptions[0]; // 初始化为相等性选项或默认选项
            equalityDiv.appendChild(equalitySelect);
            ConditionTag.appendChild(equalityDiv);

            // 将条件frame添加到卡片中
            card.appendChild(ConditionTag);
        }

        // 注意：这里的代码只是框架性的示例，实际开发中还需要考虑事件绑定、状态管理、数据验证等多个方面。
        // 另外，对于删除和复制按钮的操作，需要根据实际的应用逻辑来编写相应的函数。

        // 假设 column 是卡片应该被添加到的列容器元素
        // column.appendChild(ConditionTag); // 最后，将卡片添加到列容器中




        column.appendChild(ConditionTag);
    });
}


// 以下是 子条目 实现细节
function copySubItem(button) {
    // 同步后台数据

    thisStrategy = data.strategies.find(strategy => strategy.name === button.parentNode.parentNode.parentNode.id)
    thisSubItem = thisStrategy.subItems.find(subItem => subItem.name === button.parentNode.parentNode.id)
        .name = '复制的' + button.parentNode.parentNode.parentNode.id;
    // 复制子条目卡片  
    const subItemCard = button.parentNode.parentNode.parentNode;
    const copiedSubItem = document.createElement('div');
    copiedSubItem.classList.add('card subItem');

    copiedSubItem.innerHTML = subItemCard.innerHTML;
    document.getElementById('column').appendChild(copiedSubItem);
}
function deleteSubItem(button) {
    // 删除子条目卡片  
    const subItemCard = button.parentNode.parentNode.parentNode;
    subItemCard.remove();
}
function addCondition(button) {
    // 添加条件卡片  
    const conditionCard = document.createElement('div');
    conditionCard.classList.add('card-condition');

    conditionCard.innerHTML = `
        <div class="tag name">
            <select>
                <option>同桌天数</option>
                <option>总榜最长天数</option>
                <option>今日已打卡0/1</option>
                <option>作弊0/1</option>
                <option>总榜最高完成率</option>
                <option>小队头像框</option>
                <option>上周打卡天数</option>
                <option>本周打卡天数</option>
                <option>加入天数</option>
                <option>上周晚卡天数</option>
                <option>本周晚卡天数</option>
            </select>
        </div>
        <div class="tag operator">
            <select>
                <option>大于</option>
                <option>小于</option>
            </select>
        </div>
        <div class="tag value">
            <input type="number">
        </div>
        <div class="tag equality">
            <select>
                <option>包含</option>
                <option>不包含</option>
            </select>
        </div>
        <div class="tag actions">
            <div class="center-tag button">复制</div>
            <div class="center-tag button">删除</div>
        </div>
    `;

    document.getElementById('newSubItem').appendChild(conditionCard);
}



//以下是 条件 实现细节
function copyConditionTag(button) {
    // 复制条件卡片  
    const conditionCard = button.parentNode.parentNode.parentNode;
}




// 显示新建策略
function showNewStrategy(newStrategy) {
    // 在这里添加逻辑来在页面上显示新建的策略信息
    // 这通常包括清空当前显示的策略信息，并填充新策略的信息
}

// 将新策略添加到数据结构
function addStrategyToData(newStrategy) {
    // 在这里添加逻辑来更新你的数据结构以包含新策略
    // 这可能涉及到修改一个数组或对象来存储所有策略
}

// 处理保存并返回按钮点击事件
function handleSaveAndReturn() {
    // 读取页面上输入框、下拉框的信息
    const formData = collectFormData();
    // 打包成JSON
    const jsonData = JSON.stringify(formData);
    // 发送POST请求到服务器
    fetch('/filter/a/strategy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: jsonData
    })
        .then(response => response.json())
        .then(data => {
            // 处理服务器响应
            console.log('Saved successfully:', data);
            // 可能需要更新页面上的信息或执行其他操作
        })
        .catch(error => {
            console.error('Error saving data:', error);
        });
}

// 收集表单数据
function collectFormData() {
    // 遍历页面上的输入框、下拉框等元素，收集它们的值
    // 并返回一个对象，其中包含所有需要保存的数据
    const formData = {};
    // 假设你有一些逻辑来填充这个对象
    return formData;
}

// 监听浏览器的后退事件
window.onpopstate = function (event) {
    // 弹出swal2弹窗询问是否保存
    swal2.fire({
        title: '离开前确认',
        text: '你是否要保存当前的更改？',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '是',
        cancelButtonText: '否'
    }).then((result) => {
        if (result.isConfirmed) {
            // 用户点击了“是”，执行保存操作
            handleSaveAndReturn();
        } else if (result.isDenied) {
            // 用户点击了“否”，可以执行其他操作或什么都不做
        }
    });
};

// 监听页面关闭事件
window.addEventListener('beforeunload', function (e) {
    // 取消事件的默认动作
    e.preventDefault();
    // Chrome 需要返回值来显示自定义消息
    e.returnValue = '直接关闭页面将不会保存更改的策略';
});

// 初始化页面时，从服务器获取数据并更新页面内容
fetchStrategyData()
    .then(data => {
        updateStrategyButtonsAndInfo(data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });

// 为类名含有strategy的按钮添加点击事件监听器
document.querySelectorAll('.strategy').forEach(button => {
    button.addEventListener('click', function () {
        // 调用HideandShow函数来替换元素
        const hideElement = document.querySelector('#hideElement');
        const showElement = document.querySelector('#showElement');
        HideandShow(hideElement, showElement);

        // 发送GET请求到服务器  
        fetch('/filter/a/strategy')
            .then(response => response.json())
            .then(data => {
                // 处理服务器响应的JSON数据  
                // ...  
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    });
});
