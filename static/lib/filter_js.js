


/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/*丢进html的部分*/
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */

/* <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.min.css">
    <link rel="stylesheet" href="https://cdn.staticfile.org/font-awesome/4.7.0/css/font-awesome.css">
    <link rel="stylesheet" href="../lib/style.css">

    <script src="https://cdn.bootcdn.net/ajax/libs/jquery/3.5.1/jquery.min.js">//swal2和通知动画需要</script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.all.min.js"></script>
    <script src="https://www.gstatic.com/charts/loader.js">//折线图绘制</script> 
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js">//日期处理</script>  
    
    
    <script src=`../lib/filter_js.js`></script>




*/

/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/*功能module：发送请求，动画切换， */
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */



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
            console.error(`Error:failed to ${operation} `, error);
        });

}
//动画切换函数
function Fade(elementName) {
    document.getElementById(elementName).style.animation = 'Fade 0.8s forwards';
}
function Show(elementName) {
    document.getElementById(elementName).style.animation = 'Show 0.8s forwards';
}
function SwitchLeft(elementHide, elementShow)
//切换页面时使用，在添加动画的同时注册历史记录
{
    document.getElementById(elementHide).style.animation = 'Hide 0.8s forwards';
    document.getElementById(elementShow).style.animation = 'Show 0.8s forwards';
    historyLeft.push(elementShow);
}
function SwitchRight(elementHide, elementShow)
// 这个是右半边，刚才是左半边
{
    document.getElementById(elementHide).style.animation = 'Hide 0.8s forwards';
    document.getElementById(elementShow).style.animation = 'Show 0.8s forwards';
    historyRight.push(elementShow);
}
function SwitchPop()
// 弹出历史记录，若没有才退回到上一页
{
    if (historyLeft.length === 0 && historyRight.length === 0) {
        // 浏览器返回上一页
        window.history.back();
    }
    if (historyLeft.length > 0) {
        document.getElementById(historyLeft.top()).style.animation = 'Hide 0.8s forwards';
        historyLeft.pop();
        document.getElementById(historyLeft.top()).style.animation = 'Show 0.8s forwards';
    }
    if (historyRight.length > 0) {
        document.getElementById(historyRight.top()).style.animation = 'Hide 0.8s forwards';
        historyRight.pop();
        document.getElementById(historyRight.top()).style.animation = 'Show 0.8s forwards';
    }
}


window.onpopstate = function (event) {
    // 监听浏览器的后退事件
    if (historyRight.top === 'stragety-column')
    // 正在strategy页面，弹出swal2弹窗询问是否保存 
    {
        swal2.fire({
            title: '策略已修改',
            text: '策略已修改，是否要保存当前的更改？',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: '是',
            cancelButtonText: '否'
        }).then((result) => {
            if (result.isConfirmed) {
                saveCurrentStrategy();
            } else if (result.isDenied) {

            }
        });
    }
    else {
        // 其他页面，弹出历史记录弹窗，如果没有才上一页
        if (historyLeft.length === 0 && historyRight.length === 0) {
            SwitchPop();
        }
    }

};



/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/*初始化module：获取数据、加载用户、加载班级信息、加载折线图、初始化websocket*/
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */


// 页面ajax历史记录，便于返回，分为左右两部分
var historyLeft = {};
var historyRight = {};

// 初始化数据，从服务器获取，包含用户信息、班级信息、班级折线图数据
var initData = null;


// 全局服务器地址，后端接口地址（通知信息专用，后 => 前）
const url = 'ws://192.168.1.101:8080';
var socket = new WebSocket(`${url}/filter/a/notice`);

// data：策略信息；currentStrategy：当前策略；currentStrategyIndex：当前策略索引
const data = {};
const currentStrategy = {};
const currentStrategyIndex = 1;

// 容器：策略卡片，
var strategycontainer;



// Establish WebSocket connection
socket.onmessage = function (event) {
    if (event.data.type === 'init') {
        initData = JSON.parse(event.data);
        init(initData);
    }
    else if (event.data.type === 'update') {
        initData = JSON.parse(event.data);
        init(initData);
    }
    else if (event.data.type === 'notice') {
        showNotice(JSON.parse(event.data));
    }
};
// 确保WebSocket连接打开  
socket.onopen = function (event) {
    console.log("WebSocket is connected now.");
};

// 处理WebSocket错误  
socket.onerror = function (error) {
    console.error("WebSocket Error: " + error);
};

// 处理WebSocket关闭  
socket.onclose = function (event) {
    if (event.wasClean) {
        console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
    } else {
        // 例如，服务器进程被杀死，浏览器刷新，网络断开等情况  
        console.log('[close] Connection died');
    }
};

// 废弃：前端不再直接向bcz发送请求，通过服务器中转


function init(initData) {
    // 添加ajax初始记录
    historyLeft.pushState(null, null, `.left-column`);
    historyRight.pushState(null, null, `.right-column`);

    //主初始化函数：从服务器获取数据并初始化用户信息、班级信息、折线图

    if (initData.accountCount == 0) swal2.fire("错误", "没有可用的账号，请先创建账号", "error");
    setCookie(main_access_token);

    document.getElementById('useravatar').src = initData.avatarUrl;

    initData.groups.forEach(function (groupData) {
        loadGroupInfo(groupData);
        //前面已经创建了div，这里只需要填充折线图
        drawChart(groupData);
    });
}
// 页面加载完成后执行初始化  
window.onload = init();



function loadGroupInfo(groupData) {
    // 加载班级信息，将写入class-info卡片然后加载到right-column中
    var className = groupData.className;
    var leaderName = groupData.leaderName;
    var studentCount = groupData.studentCount;
    var todayDakaCounts = groupData.todayDakaCounts;
    var intro = groupData.introduction;
    var avatarUrl = groupData.avatarUrl;
    // Create a new div for the sub-class avatar

    const classInfoCard = document.createElement('div');
    classInfoCard.innerHTML = `
                <div class="card">
                    <div class="frame">
                        <div class="tag" name="classinfo">
                            <div class="avatar ${shareKey}" id="classavatar">
                                <img src="${avatarUrl}" alt="${className}">
                            </div>
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
                                    <div class="box-separator"></div>
                                    <div class="${shareKey}" id="intro">${intro}</div>
                                </div>
                            </div>
                        </div>
                        <div class="graph ${shareKey}" id = "graph"></div>
                        <div class="${shareKey}" id="status"> </div>
                        <div class="separator"></div>
                        <div class="tag center">
                            <div class="tag button ${shareKey}" id="strata" onclick="setStrategy('${shareKey}')">策略</div>
                            <div class="box-separator"></div>
                            <div class="tag button ${shareKey}" id="members" onclick="showMember('${shareKey}')">成员</div>
                            <div class="box-separator"></div>
                            <div class="tag button ${shareKey}" id="notice" onclick="editBoards('${shareKey}')">公告</div>
                            <div class="box-separator"></div>
                            <div class="tag button ${shareKey}" id="log" onclick="showLog('${shareKey}')">日志</div>
                        </div>
                    </div>
                </div>`;

    document.querySelector('right-column').appendChild(classInfoCard);

}




function drawChart(cnt, t, a, b) {
    // 绘制小班数据折线图，参数cnt为数据数量，t为时间数组，ab待定（到时后端实现）暂定是卡数和排名

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



/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/*account管理*/
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */


function manageAccount() {
    // 点击主页账号管理按钮后弹出

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

}



/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/* 导出日志 */
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */

function exportLog() {
    // 点击导出日志按钮后弹出
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
                exportAndDownload(type);
            });

            const notifyBtn = Swal.getHtmlContainer().insertAdjacentHTML
                ('beforeend', '<button class="swal2-confirm swal2-styled" style="display:inline-block;margin-left:10px;">导出通知日志</button>');
            notifyBtn.addEventListener('click', () => {
                const type = 'notify'; // 通知日志  
                exportAndDownload(type);
            });
        }
    });
}

function exportAndDownload(type) {
    //请求服务器导出某物并且下载
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




/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */
/* （大件警告）策略管理页面：策略列表、策略详情、策略编辑、策略删除、策略新建、策略保存  */
//好了，到这里就结束了，可以愉快的玩耍了。———— fittencode
//策略按钮点击事件
/* ---------------- 32 (●´∀｀●) ---------------- (●´∀｀●) ---------------- (●´∀｀●) 32 ---------------- */



// 模拟服务器返回的策略数据  
const mockServerResponse = {
    totalStrategies: 3,
    strategies: [
        {
            name: "策略一",
            weekDays: ["周一", "周三"],
            timesStart: ["09:00"],
            timesEnd: ["10:00"],
            minPeople: 5,
            subItemsCount: 2,
            subItems: [
                {
                    name: "子条目1",
                    operation: "接受",
                    validity: "本周",
                    conditionsCount: 3,
                    conditions: [
                        { name: "同桌天数", value: 5, operator: "大于", equality: false },
                        // ... 其他条件  
                    ]
                },
                // ... 其他子条目  
            ]
        },
        {
            name: "策略二",
            weekDays: ["周二", "周四"],
            timesStart: "10:00",
            timesEnd: "11:00",
            minPeople: 3,
            subItemsCount: 1,
            subItems: [
                {
                    name: "子条目1",
                    operation: "拒绝",
                    validity: "本周",
                    conditionsCount: 2,
                    conditions: [
                        { name: "同桌天数", value: 3, operator: "大于", equality: false },
                        // ... 其他条件  
                    ]
                },
                // ... 其他子条目  
            ]
        },
        // ... 其他策略  
    ]
};


function fetchStrategyData() {
    // 初始化：模拟从服务器获取JSON的异步操作 ，然后储存到data全局变量
    data = new Promise((resolve) => {
        setTimeout(() => {
            resolve(mockServerResponse);
        }, 500); // 模拟网络延迟  
    });
    return;
    fetch(`${url}/strategy`)
        .then(response => {
            data = response.json();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    return;
}

//点击策略按钮时调用，初始化strategy页面
function showStrategyPage() {

    data = fetchStrategyData();

    // 初始化容器
    strategycontainer = document.getElementById('strategy-column');
    SwitchRight('right-column', 'strategy-column');


    const operationCard = document.getElementById('operation');
    operationCard.innerHTML = ''; // 清空operation内容 ，删除现有所有按钮  


    // 添加额外按钮：保存并返回、不保存、新建  
    ['保存并返回', '不保存', '新建'].forEach((text, index) => {
        const btn = document.createElement('div');
        btn.classList.add('center-tag button');
        btn.textContent = text;
        if (text === '新建') {
            btn.addEventListener('click', () => {

                addStrategy();
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



// 以下是 策略 实现细节


function showWeekDays() {
    // 点击策略页面，的星期按钮时弹出选择星期的弹窗
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
            currentStrategy.weekDays = selectedDays;
        }
    });
}
function showTimes() {
    // 点击策略页面，的运行时间按钮时弹出选择时间的弹窗
    Swal.fire({
        title: '选择运行时间',
        html: `  
            <input type="time" id="swal-input-start" class="swal2-input" value="06:00">  
            <input type="time" id="swal-input-end" class="swal2-input" value="08:00">  
        `,
        focusConfirm: false,
        preConfirm: () => {
            const start = document.getElementById('swal-input-start').value || '06:00';
            const end = document.getElementById('swal-input-end').value || '08:00';

            return {
                timesStart: start,
                timesEnd: end
            };
        },
        showCancelButton: true,
        confirmButtonText: '确认',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            currentStrategy.timesStart = result.value.timesStart;
            currentStrategy.timesEnd = result.value.timesEnd;
        }
    });
}
function showMinPeople() {
    // 点击策略页面，的最小人数按钮时弹出设置最小人数的弹窗
    Swal.fire({
        title: '设置最小人数',
        input: 'range',
        type: 'question',
        inputValue: 1,
        inputAttributes: {
            min: 1,
            max: 200,
            step: 1
        },
        showCancelButton: true,
        confirmButtonText: '确认',
    }.then((result) => {
        if (result.isConfirmed) {
            currentStrategy.minPeople = result.value;
        }
    }));
}

function addStrategy() {
    // 新建策略

    //（后台数据）  
    const newStrategy = {
        name: "新策略",
        weekDays: ["周一", "周三"],
        timesStart: "09:00",
        timesEnd: "10:00",
        minPeople: 5,
        subItemsCount: 2,
        subItems: [
            {
                name: "子条目1",
                operation: "接受",
                validity: "本周",
                conditionsCount: 3,
                conditions: [
                    { name: "同桌天数", value: 5, operator: "大于", equality: false },
                    // ... 其他条件  
                ]
            }
        ],
        // ... 其他子条目  
    };

    data.strategies.push(newStrategy);

    // 更新按钮
    newButton = document.createElement('div');
    newButton.innerHTML = `
        <div class="center-tag button" id="${newStrategy.name}" onclick="showStrategyInfo(this.id)">${newStrategy.name} </div>
    `;
    document.getElementById('operation').appendChild(newButton);

    // 更新页面显示
    showStrategyInfo(newStrategy);
}
function copyCurrentStrategy() {
    // 复制当前策略

    // 提醒先保存

    Swal.fire({
        title: '请先保存策略',
        text: '是否保存当前策略？若不保存，将复制保存前的策略，当前更改将丢失。',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '保存',
        cancelButtonText: '不保存'
    }).then((result) => {
        if (result.isConfirmed) {
            // 保存策略
            saveCurrentStrategy();
        }
    });

    const name = '复制的' + currentStrategy.name;

    // 复制策略的逻辑（后台数据）  
    const strategy = currentStrategy;
    strategy.name = name;
    data.strategies.push(strategy);

    // 添加按钮
    const newButton = document.createElement('div');
    newButton.innerHTML = `
        <div class="center-tag button" id="${copiedStrategy.name}" onclick="showStrategyInfo(this.id)">${copiedStrategy.name} </div>
    `;
    document.getElementById('operation').appendChild(newButton);

    // 更新页面显示，含按钮更新
    showStrategyInfo(name);

}
function deleteCurrentStrategy() {
    // 删除当前策略

    // 警告
    Swal.fire({
        title: '删除策略',
        text: `是否删除策略${currentStrategy.name}？此操作无法撤销`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            // （后台数据）  
            data.strategies.splice(currentStrategyIndex, 1);
            // 更新页面显示
            showStrategyInfo(data.strategies[0].name);
        }
    });

}
function saveCurrentStrategy() {
    // 因为页面上的输入框没有监听，所以此函数用于保存页面上的数据到currentStrategy对象，并保存到data对象，然后发送到服务器

    // （后台数据）
    const strategyCard = container.getElementByClass('strategy')
    currentStrategy.name = strategyCard.querySelector('.name input').value;
    // 星期、时间、最小人数有监听，所以不需要处理
    currentStrategy.subItems = [];

    const subItems = strategyCard.querySelectorAll('.subItem');
    subItems.forEach((subItem) => {
        const subItemData = {
            name: subItem.querySelector('.name input').value,
            operation: subItem.querySelector('.operation select').value,
            validity: subItem.querySelector('.validity select').value,
            conditions: []
        };
        const conditions = subItem.querySelectorAll('.condition');
        conditions.forEach((condition) => {
            const conditionData = {
                name: condition.querySelector('.name select').value,
                operator: condition.querySelector('.operator select').value,
                value: condition.querySelector('.value input').value,
                equality: condition.querySelector('.equality select').value
            };
            subItemData.conditions.push(conditionData);
        });
        currentStrategy.subItems.push(subItemData);
    });
    data.strategies[currentStrategyIndex] = currentStrategy;

    // 更新页面显示
    showStrategyInfo(currentStrategy.name);


    // 发送到服务器
    fetch(`${url}/strategy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.ok)
            Swal.fire({
                title: '保存成功',
                type: 'success',
                showConfirmButton: false,
                timer: 1000
            });
    }).catch(error => {
        console.error('Error:', error);
    });

}
function addSubItem(button) {
    // 在策略中添加子条目，仍属于策略部分

    // 添加后台数据
    const subItem = {
        name: "子条目",
        operation: "接受",
        validity: "本次",
        conditions: [

        ]
    };

    thisStrategy = data.strategies.find(strategy => strategy.name === button.parentNode.parentNode.parentNode.id)
    thisStrategy.subItem.push(subItem);

    // 添加子条目卡片  
    const subItemCard = document.createElement('div');

    subItemCard.innerHTML = /*跟后面showSubItem的结构一样*/`
        <div class="card subItem" id="${subItem.name}">
            <div class="tag name">
                <input type="text" value="${subItem.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag button" onclick="addCondition(this)">添加条件</div>
                <div class="center-tag button" onclick="copySubItem(this)">复制</div>
                <div class="center-tag button" onclick="deleteSubItem(this)">删除</div>
            </div>
            <div class="tag operation">
                <select value="${subItem.operation || '请选择'}">
                    <option value="接受">接受</option>
                    <option value="移出">移出</option>
                </select>
            </div>
            <div class="tag validity">
                <select value="${subItem.validity || '请选择'}">
                    <option value="本次">本次</option>
                    <option value="今天">今天</option>
                    <option value="本周">本周</option>
                </select>
            </div>
        </div>
    `;

    container.appendChild(subItemCard);
}


function showStrategyInfo(strategyName) {
    // 显示策略信息  

    // 更改按钮样式
    const operationButtons = document.getElementById('operation');

    operationButtons.querySelectorAll('.button').forEach(btn => btn.classList.remove('active'));
    operationButtons.find(strategyName).classList.add('active');

    // 更改全局变量
    currentStrategy = data.strategies.find(strategy => strategy.name === strategyName);// 加载策略对象
    currentStrategyIndex = data.strategies.findIndex(strategy => strategy.name === strategyName);// 用来找保存位置


    // 清空column内容
    strategycontainer.innerHTML = '';


    // 创建并添加策略名的card  (包括操作按钮)

    const strategyCard = document.createElement('div');
    strategyCard.innerHTML = `
        <div class="card strategy" id="${currentStrategy.name}">
            <div class="tag name">
                <input type="text" value="${currentStrategy.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag button" onclick="addSubItem(this)">添加子条目</div>
                <div class="center-tag button" onclick="copyStrategy(this)">复制本策略</div>
                <div class="center-tag button" onclick="deleteStrategy(this)">删除本策略</div>
            </div>
            <div class="frame settings">
                <div class="center-tag button" onclick="showWeekDays()">
                    设置星期：${currentStrategy.weekDays}
                </div>
                <div class="center-tag button" onclick="showTimes()">
                    运行时间：${currentStrategy.timesStart}-${currentStrategy.timesEnd}
                </div>
                <div class="center-tag button" onclick="showMinPeople()">
                    最小人数：${currentStrategy.minPeople}
                </div>
            </div>
        </div>
    `;
    column.appendChild(strategyCard);

    // 创建并添加每个子条目的card  
    strategy.subItems.forEach((subItem) => {

        // 添加子条目卡片
        const subItemCard = document.createElement('div');
        subItemCard.innerHTML = `
            <div class="card subItem" id="${subItem.name}">
                <div class="tag name">
                    <input type="text" value="${subItem.name}">
                </div>
                <div class="tag actions">
                    <div class="center-tag button" onclick="addCondition(${subItem.name})">添加条件</div>
                    <div class="center-tag button" onclick="copySubItem(${subItem.name})">复制</div>
                    <div class="center-tag button" onclick="deleteSubItem(${subItem.name})">删除</div>
                </div>
                <div class="tag operation">
                    <select value="${subItem.operation || '请选择'}">
                        <option value="接受">接受</option>
                        <option value="移出">移出</option>
                    </select>
                </div>
                <div class="tag validity">
                    <select value="${subItem.validity || '请选择'}">
                        <option value="本次">本次</option>
                        <option value="今天">今天</option>
                        <option value="本周">本周</option>
                    </select>
                </div>
            </div>
        `;

        subItem.Conditions.forEach((Condition) => {
            // 创建tag元素  
            const ConditionTag = document.createElement('div');
            ConditionTag.innerHTML = `
                <div class="tag condition" id="${Condition.name}">
                    <div class="tag name">
                        <select value="${Condition.name || '请选择'}">
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
                        <select value="${Condition.operator || '大于'}">
                            <option>大于</option>
                            <option>小于</option>
                        </select>
                    </div>
                    <div class="tag value">
                        <input type="number" value="${Condition.value || '1'}">
                    </div>
                    <div class="tag equality">
                        <select value="${Condition.equality || '包含'}">
                            <option>包含</option>
                            <option>不包含</option>
                        </select>
                    </div>
                    <div class="tag actions">
                        <div class="center-tag button" onclick="deleteCondition(this)">删除</div>
                    </div>
                </div>
            `;
            // 将tag添加到subItem
            subItemCard.appendChild(ConditionTag);
        });

        // 将子条目名称卡片添加到容器  
        container.appendChild(subItemCard);

    });
}


// 以下是 子条目 实现细节
function copySubItem(subItemName) {


    const subItem = currentStrategy.subItems.find(subItem => subItem.name === subItemName);
    const name = '复制的' + subItem.name;

    // 同步后台数据
    subItem.name = name;
    currentStrategy.subItems.push(subItem);


    // 复制子条目卡片  
    const subItemCard = button.parentNode.parentNode.parentNode;
    const copiedSubItem = document.createElement('div');
    copiedSubItem.innerHTML = subItemCard.innerHTML;
    copiedSubItem.id = name;
    copiedSubItem.textContent = name;
    container.appendChild(copiedSubItem);
}
function deleteSubItem(subItemName) {
    // 警告
    Swal.fire({
        title: '删除子条目',
        text: `是否删除子条目${subItemName}？此操作无法撤销`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
    }).then((result) => {
        // 删除后台数据
        currentStrategy.subItems.splice(currentStrategy.subItems.findIndex(subItem => subItem.name === subItemName), 1);
        // 删除子条目卡片  
        document.getElementByClassAndId(`${subItemName}.subItem`).remove();
    });
}
function addCondition(button) {
    // 添加条件的逻辑（后台数据）  
    const subItemName = button.parentNode.parentNode.parentNode.id;
    const subItem = currentStrategy.subItems.find(subItem => subItem.name === subItemName);
    const Condition = {
        name: "请选择",
        operator: "大于",
        value: 1,
        equality: "包含"
    };
    subItem.Conditions.push(Condition);



    // 添加条件卡片  
    const conditionCard = document.createElement('div');
    conditionCard.classList.add('card-condition');

    conditionCard.innerHTML = /*跟后面showSubItem的结构一样*/`
        <div class="tag condition" id="${Condition.name}">
            <div class="tag name">
                <select value="${Condition.name || '请选择'}">
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
                <select value="${Condition.operator || '大于'}">
                    <option>大于</option>
                    <option>小于</option>
                </select>
            </div>
            <div class="tag value">
                <input type="number" value="${Condition.value || '1'}">
            </div>
            <div class="tag equality">
                <select value="${Condition.equality || '包含'}">
                    <option>包含</option>
                    <option>不包含</option>
                </select>
            </div>
            <div class="tag actions">
                <div class="center-tag button" onclick="deleteCondition(this)">删除</div>
            </div>
        </div>
`;

    document.getElementById('newSubItem').appendChild(conditionCard);
}



//以下是 条件 实现细节
function deleteCondition(button) {
    // 删除条件
    button.parentNode.parentNode.remove();
}


// 监听页面关闭事件
window.addEventListener('beforeunload', function (e) {
    // 取消事件的默认动作
    e.preventDefault();
    // Chrome 需要返回值来显示自定义消息
    e.returnValue = '直接关闭页面将不会保存更改的策略';
});





// 通知栏实现  


const notice_data_example = {
    id: 6666,
    height: 200,
    timeout: 12000,
    content: `
        <div class="frame notice-content">
            <div class="tag" id="userInfo" style="justify-content:start">
                <div class="avatar" id="useravatar">
                    <img src="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png" alt="">
                </div>
                <div class="center-frame">
                    <div class="center-tag">
                        <div class="tag" id="name">某不达标用户</div>
                        <div class="checkbox" id="checked"></div>
                    </div>
                    <div class="center-tag">
                        <div class="tag" id="district">District</div>
                        <div class="box-separator"></div>
                        <div class="tag" id="grade">Grade</div>
                        <div class="box-separator"></div>
                        <div class="tag" id="book">Book</div>
                    </div>
                    <div class="center-tag">
                        <div class="tag" id="todayWords">Words</div>
                        <div class="box-separator"></div>
                        <div class="tag" id="totalDakaDays">Checks</div>
                        <div class="box-separator"></div>
                        <div class="tag" id="totalDays">Days</div>
                    </div>
                </div>
            </div>
            <div class="tag operation">
                加入了 xx 班级/将要从 xx 班级移除
            </div>
        </div>
    `,
    confirm: true,
    confirmContent: `
        <div class="tag maximized-content">
            <div class="tag infoTag">
                <div class="frame" id="userInfoExpanded">
                <!-- 包含用户数据图表 -->
                    <div class="tag" id="userInfo" style="justify-content:start">
                        <div class="avatar" id="useravatar">
                            <img src="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png" alt="">
                        </div>
                        <div class="center-frame">
                            <div class="center-tag">
                                <div class="tag" id="name">某不达标用户</div>
                                <div class="checkbox" id="checked"></div>
                            </div>
                            <div class="center-tag">
                                <div class="tag" id="district">District</div>
                                <div class="box-separator"></div>
                                <div class="tag" id="grade">Grade</div>
                                <div class="box-separator"></div>
                                <div class="tag" id="book">Book</div>
                            </div>
                            <div class="center-tag">
                                <div class="tag" id="todayWords">Words</div>
                                <div class="box-separator"></div>
                                <div class="tag" id="totalDakaDays">Checks</div>
                                <div class="box-separator"></div>
                                <div class="tag" id="totalDays">Days</div>
                            </div>
                        </div>
                    </div>
                    <div class="graph">

                    </div>
                </div>
                <div class="frame">
                    <div class="tag" name="classinfo">
                        <div class="avatar 1234abcdef" id="classavatar">
                            <img src="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png" alt="">
                        </div>
                        <div class="frame">
                            <div class="tag">
                                <div class="1234abcdef" id="name">小学一年级</div>
                                <div class="box-separator"></div>
                                <div class="1234abcdef" id="leader">神探小可爱</div>
                            </div>
                            <div class="tag">
                                <div class="1234abcdef" id="students">200</div>
                                <div class="box-separator"></div>
                                <div class="1234abcdef" id="todayDakaCounts">195</div>
                            </div>
                        </div>
                    </div>
                    <div class="graph 1234abcdef" id = "graph">

                    </div>
                    <div class="1234abcdef" id="status">策略 xx 正在运行</div>
                </div>
            </div>
            <div class="center-tag operation">
                <div class="center-tag button" onclick="wssend(6666,'accept')">接受</div>
                <div class="center-tag button" onclick="wssend(6666,'reject')">移除</div>
                <!-- 后台支持的其他操作 -->
                <div class="center-tag button" onclick="wssend(6666,'ignore')">忽略</div>
            </div>
        </div>
    `};
function wssend(confirmId, operation) {
    if (socket.readyState === 1) {
        socket.send(JSON.stringify({
            confirm_id: confirmId,
            operation: operation
        }));
    }
    else console.log('socket not ready');
}
function showNotice(data) {
    const container = document.getElementById('column left-column');
    height = data.height || 100; // 通知框的高度  

    // 创建新的card notice类的框  
    const newCard = document.createElement('div');
    newCard.innerHTML = /*最外层的div并不是真正的card，转换jquery对象时还有一层*/`
        <div>
            <div class="notice-line" style="width: 100%; height: 3px; background: black; position: relative; top: 0; left: 0;"></div>
            <div class="card notice" style="height: ${height}px; position: relative; touch-action: none; background-color: #ffffffaa; cursor:pointer; ">
                ${data.content}
            </div>
        </div>
    `;
    // 如果需要确认，则先弹窗
    if (data.confirm) {
        setTimeout(function () {
            swal.fire({
                innerHtml: data.confirmContent,
                showConfirmButton: false,
                showCancelButton: false,
            });
            // 所有操作按钮都在content中，由后台设置id
        }, 100);
    }

    var $newCard = $(newCard);
    $newCard.appendTo(container);

    // 添加触摸事件监听器  
    var touchStartX = 0;
    var isSwiping = false;
    var cardWidth = $newCard.width();
    var swipeDistance = 0;
    var cardY = $newCard.offset().top + height; // 获取通知框的Y坐标 + 高度


    $newCard.on('touchstart mousedown', function (e) {

        touchStartX = e.originalEvent.touches ? e.originalEvent.touches[0].clientX : e.clientX; // 记录触摸/鼠标开始的X坐标      
        // 缩小一圈，模拟卡片的缩放效果  
        $newCard.css('transform', 'scale(0.9)');
        $newCard.css('transition', 'transform 0.3s ease-in-out');
        isSwiping = true; // 标记为正在滑动  
    });

    $newCard.on('touchmove mousemove', function (e) {

        if (!isSwiping) return; // 如果不是滑动状态，直接返回  
        var touchEndX = e.originalEvent.touches ? e.originalEvent.touches[0].clientX : e.clientX; // 获取触摸/鼠标结束的X坐标

        swipeDistance = touchEndX - touchStartX; // 计算滑动距离  

        // 改变通知框margin，达到左右滑动的效果，同时有消失的动画效果  

        $newCard.css('margin-left', swipeDistance + 'px');
        $newCard.css('margin-right', -swipeDistance + 'px')
        // if (1 - Math.abs(swipeDistance / cardWidth) < 0)
        // $newCard.css('opacity', 0);
        $newCard.css('opacity', 1 - Math.abs(swipeDistance / cardWidth));

        // 有可能鼠标超过了newCard的高度，此时收不到mouseup，此时newCard通过动画返回原位
        var touchY = e.originalEvent.touches ? e.originalEvent.touches[0].clientY : e.clientY; // 获取触摸/鼠标的Y坐标

        if (touchY > cardY) {
            isSwiping = false; // 标记为不是滑动状态  
            $newCard.animate({
                marginLeft: 0,
                marginRight: 0,
                opacity: 1
            }, 500);
        }
    });

    $newCard.on('touchend mouseup', function (e) {

        // 还原框大小
        $newCard.css('transform', 'scale(1)');
        $newCard.css('transition', 'transform 0.2s ease-in-out');
        // 设定滑动阈值，比如50%的宽度 

        if (Math.abs(swipeDistance) < cardWidth * 0.1) { // 如果滑动距离很小，则认为是点击事件，打开详情页  
            // 打开详情页  
            setTimeout(function () {
                swal.fire({
                    innerHtml: data.confirmContent,
                    showConfirmButton: true,
                    showCancelButton: true,
                });
            }, 100);
        }

        if (isSwiping && Math.abs(swipeDistance) > cardWidth * 0.3) { // 如果滑动距离超过阈值  
            // 滑动淡出，然后删除通知框  
            if (swipeDistance > 0) dist = cardWidth; // 右滑，消失到右边  
            else dist = -cardWidth; // 左滑，消失到左边  
            $newCard.animate({

                marginLeft: dist,
                marginRight: -dist,
                opacity: 0
            }, 500, function () {

                // 删除通知框  
                isSwiping = false; // 标记为不是滑动状态  
                $newCard.remove();
            });
        }
        else { // 如果滑动距离不超过阈值  
            // 回到原位并恢复动画效果  
            $newCard.animate({

                marginLeft: 0,
                marginRight: 0,
                opacity: 1

            }, 500);
        }
        isSwiping = false; // 标记为不是滑动状态  
    });
    $newCard.css('opacity', '0');
    $newCard.animate({
        marginLeft: 10,
        marginRight: -10,
        opacity: 0.5,
    }, 200, function () {
        $newCard.animate({
            marginLeft: 0,
            marginRight: 0,
            opacity: 1,
        }, 200, function () {
            if (data.timeout === -1)// 不自动消失
                return;
            // 线的宽度逐渐减少到0%  
            $newCard.find('.notice-line').animate({
                width: '0%'
            }, data.timeout, function () {
                // 淡出通知框  
                setTimeout(function () {
                    $newCard.animate({
                        opacity: 0
                    }, 500, function () {
                        // 删除通知框  
                        $newCard.remove();
                    });
                });
            });
        });
    });
}

// 班级功能按钮实现  

// 获取策略列表并显示Swal2弹窗  
function switchStrategy(shareKey) {
    // 用于选择对应班级的策略

    // 发送请求 更新 策略列表  
    fetchStrategyData();



    Swal.fire({
        title: '选择策略',
        text: '请选择要应用的策略',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        html: '<div id="swal2-content"></div>',
        preConfirm: () => {
            // 这里可以处理用户点击确定前的逻辑，比如验证选择等  
            return true;
        }
    }).catch(swal2 => {
        // 用户点击了取消按钮或者发生了错误  
        if (swal2.dismiss === Swal.DismissReason.cancel) {
            console.log('用户取消了选择');
        }
    });

    // 动态生成策略选择列表  
    const swalContent = document.getElementById('swal2-content');
    data.strategies.forEach(strategy, index => {
        const radio = document.createElement('div');
        radio.innerHTML = `
                <div class="center-tag button" onclick="sendRequest({strategy_id: ${index},shareKey: '${shareKey}'},'apply')">${strategy.name}</div>`;
        swalContent.appendChild(radio);
    });
}
function setStrategy(shareKey) {// 用于设置策略（开始、停止、选择策略）
    swal.fire({
        title: '策略设置',
        html: `
            <div class="center-tag button" onclick="sendRequest({shareKey: '${shareKey}'},'start')">开始</div>
            <div class="center-tag button" onclick="sendRequest({shareKey: '${shareKey}'},'stop')">停止</div>
            <div class="center-tag button" onclick="switchStrategy('${shareKey}')">选择策略</div>
        `,
        showConfirmButton: false,
        showCancelButton: false,
    });
}




// 设置页面


function showSettings() {
    // 显示设置面板  
    fetch(`${url}/filter/a/settings`)
        .then(response => response.json())
        .then(settingsData => {


            swal.fire({
                title: '设置',
                html: `
                    <div id="swal-settings">
                        <div class="center-tag button" id="removeConfirm">移除成员确认：${settingsData.removeConfirm}</div>
                        <div class="center-tag button" id="about">：${settingsData.resetConfirm}</div>
                    </div>
                `,
                showConfirmButton: false,
                showCancelButton: false,
            }).then(() => {
                document.querySelector("swal-settings").querySelectorAll("button").forEach(button => {
                    button.addEventListener("click", event => {
                        if (button.id === "removeConfirm") {
                            settingsData.removeConfirm = !settingsData.removeConfirm;
                            button.innerText = `移除成员确认：${settingsData.removeConfirm}`;
                        }

                        else if (button.id === "about") {
                            // 显示关于页面  
                            swal.fire({
                                title: '关于',
                                html: `
                                    <div class="center-tag">
                                        <div class="tag">BCZ-Group-Manager</div>
                                        <div class="separator"></div>
                                        <div class="tag">${settingsData.description}</div>
                                        <div class="tag">${settingsData.author}</div>
                                        <div class="tag">${settingsData.contact}</div>
                                        <div class="separator"></div>
                                        <div class="tag">项目地址：${settingsData.url}</div>
                                        <div class="tag">版本：${settingsData.version}</div>
                                        <div class="separator"></div>
                                    </div>
                                `});
                        }
                    });
                });

            }).then((result) => {
                if (result.isConfirmed) {
                    // 用户点击了“是”，执行保存操作
                    sendRequest(settingsData, 'settings');
                }
            });

        });
}




// notice column 实现  


function noticePage() {
    // 隐藏left-column并显示notice-column  
    Hide(document.querySelector('.left-column'));
    Show(document.querySelector('.notice-column'));

    // 获取operation card上的按钮  
    const buttons = document.querySelectorAll('.notice-operation button');
    buttons.forEach(button => {
        // 为每个按钮添加点击事件  
        button.addEventListener('click', async function () {
            // 加载时显示loading动画  
            swal.fire({
                title: '加载中',
                html: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i>',
                showConfirmButton: false,
                allowOutsideClick: false
            });
            const buttonType = this.textContent.toLowerCase().replace(' ', ''); // 获取按钮类型  
            const startDate = document.querySelector('.notice-operation #startDate').value; // 日期选择框的ID  
            const endDate = document.querySelector('.notice-operation #endDate').value;

            // 构建GET请求的URL 

            try {
                // 发送GET请求  
                const response = await fetch(`${url}/filter/a/notice/${buttonType}?startDate=${startDate}&endDate=${endDate}`);
                if (!response.ok) {
                    throw new Error('网络响应不ok');
                }
                const noticeData = await response.json();

                // 遍历返回的json中的每一个notice并显示  
                noticeData.forEach(notice => {
                    showNotice(notice);
                });
            } catch (error) {
                console.error('加载通知时出错:', error);
                // 在这里可以添加错误处理逻辑，比如显示错误消息  
            }
        });
    });
}
// 成员页面

function showMember(shareKey) {
    // 班级成员展示，强行采用了ajax（嗯，强迫症吧）

    const days = 7;
    const groupId = 795528; // 神探小可爱的班级ID
    error("还没有处理groupId的问题！记得处理：将shareKey转换为groupId");

    // 隐藏当前列并显示替换列  
    Fade('right-column');
    Show('member-column');


    //  我要开始ajax了（炸毛）

    fetch(`${url}/group/id/${groupId}`)
        .then(response => response.text())
        .then(html => {
            // 创建一个新的 HTMLDocument 对象来处理小班详情页
            const parser = new DOMParser();
            const detailsDocument = parser.parseFromString(html, 'text/html');

            // 提取main节点
            const mainNode = detailsDocument.querySelector('main');

            // 加载main节点到当前页面的right-column元素中
            const rightColumn = document.querySelector('.right-column');
            rightColumn.innerHTML = '';
            rightColumn.appendChild(mainNode);


            // 处理脚本文件，替换链接地址（定点爆破，仅1处）
            const scripts = serverDocument.querySelectorAll('script');
            scripts.forEach(script => {
                const originalScriptContent = script.textContent;
                const searchString = 'window.location.href';
                const replacementString = `\'../group/${groupId}\'`;

                // 使用正则表达式替换匹配到的字符串
                const modifiedScriptContent = originalScriptContent.replace(new RegExp(searchString, 'g'), replacementString);

                // 将修改后的脚本内容运行
                eval(modifiedScriptContent);
            })
                .catch(error => {
                    console.error('请求HTML文件时出现错误：', error);
                });


        });
}

// 公告页面


function editBoards(shareKey) {
    // 编辑公告页面
    // 隐藏left-column并显示notice-column  
    noticePage();// 左半部分切换到通知页面（方便编辑公告）

    Hide(document.querySelector('.right-column'));
    Show(document.querySelector('.edit-boards'));// 显示编辑公告页面



    // 发送请求获取公告列表  
    fetch(`${url}/filter/a/board?shareKey=${shareKey}`)
        .then(response => response.json())
        .then(boardData => {
            // 创建公告框（班级历史公告放在通知栏的公告分类中，此处只显示最近的公告） 

            swal.fire({
                title: '编辑公告',
                html: '···公告编辑器···<br>✓ 自动获取最新公告 <br>✓ 保存历史公告记录 <br>✓ 每半分钟自动保存 <br>✓ 快捷查看成员班内数据、昵称对话 <br>× 暂不支持发布，请手动复制发布 <br>× 暂不支持@补全，正在对接成员列表'

            });
            const newBoard = document.createElement('div');
            newBoard.innerHTML = `
                    <div class="board">
                        <div class="board-title">${boardData.className}</div>
                        <input class="board-content"></input>
                        <div class="board-footer">
                            <div class="board-footer-left">
                                <div class="board-footer-left-item">${boardData.createTime}</div>
                                <div class="board-footer-left-item">${boardData.author}</div>
                                <div class="board-footer-left-item">自动保存：暂无</div>
                            </div>
                        </div>
                    </div>
                `;
            newBoard.querySelector('.board-content').value = boardData.content;
            document.querySelector('.edit-boards').appendChild(newBoard);
            // 每半分钟保存一次到服务器  
            setInterval(() => {
                const content = newBoard.querySelector('.board-content').value;
                sendRequest({ content: content }, 'board');
            }, 30 * 1000);
        });
}
// 隐藏left-column并显示notice-column  
