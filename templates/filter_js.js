

/* <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.min.css">

    <script src="https://cdn.bootcdn.net/ajax/libs/jquery/3.5.1/jquery.min.js">//swal2需要</script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/8.11.8/sweetalert2.all.min.js"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js">//折线图绘制</script> */






//初始化部分

var initData = null;
// Establish WebSocket connection
const url = 'ws://192.168.1.101:8080';
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
    var accessToken = initData.accountCount;
    if (accountCount == 0) swal2.fire("错误", "没有可用的账号，请先创建账号", "error");
    setCookie(main_access_token);
    var xhr = new XMLHttpRequest();

    xhr.open('GET', 'https://social.baicizhan.com/api/deskmate/home_page', true);
    setHeader(xhr);

    xhr.onload = function () {
        if (xhr.status === 200) {
            var userData = JSON.parse(xhr.responseText);
            loadUserAvatar(userData.avatarUrl);
        }
    };
    xhr.send();

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
function loadUserAvatar(avatarUrl) {
    var img = document.getElementById('useravatar');
    img.src = avatarUrl;
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
                    sendRequest({"uniqueId": uniqueId, 'action':'switch' },'switch');
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
                    sendRequest({"uniqueId": uniqueId, 'action': 'delete' }, 'delete');
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
                sendRequest({ "uniqueId":uniqueId, "accessToken":accessToken, "action":"add" }, 'add');
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

