currentStrategy = {};
strategies = {};
currentStrategyHashId = null;
strategycontainer = null;
function initStrategyPage(){
    // 初始化策略页面
    return fetch(`../get_strategy_list`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
    .then(data => {
        strategies = data.data;
        strategycontainer = document.querySelector('.strategy-detail');
        // 初始化策略列表
        strategy_list_content = '';
        for (let key in strategies) {
            const strategy = strategies[key];
            strategy_list_content += `
                <div class="center-tag btn" id="${key}" onclick="showStrategyInfo(this.id)">${strategy.name}</div>
            `;
        }
        document.querySelector('.strategy-list').innerHTML = strategy_list_content;
        // 显示第一个策略
        for (let key in strategies) {
            showStrategyInfo(key, true);
            break;
        }
        return data;
    });
}
function addStrategy() {
    // 新建策略

    //（后台数据）  
    const newStrategy = {
        name: "新策略",
        weekDays: ["周一", "周三"],
        timesStart: "09:00",
        timesEnd: "10:00",
        subItemsCount: 2,
        subItems: [
            {
                name: "子条目1",
                operation: "接受",
                minPeople: 199,
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

    strategies.push(newStrategy);

    // 更新按钮
    newButton = document.createElement('div');
    newButton.innerHTML = `
        <div class="center-tag btn" id="${newStrategy.name}" onclick="showStrategyInfo(this.id)">${newStrategy.name} </div>
    `;
    document.getElementById('operation').appendChild(newButton);

    // 更新页面显示
    showStrategyInfo(newStrategy);
}
function hashStrategy(strategy) {
    // 像hash_strategy发送策略数据，返回hashId
    return fetch(`../hash_strategy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(strategy)
    }).then(response => response.json())
    .then(data => {
        // 将data.data转为string，作为hashId
        const hashId = data.data;
        return hashId;
    });
}
function copyCurrentStrategy(hashId) {
    // 复制当前策略
    if (hashId == null) {
        saveCurrentStrategy(true);
        return;
    }
    fetch(`../copy_strategy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            strategy_id: currentStrategyHashId,
        })
    }).then(response => response.json())
    .then(data => {
        copied_strategy = {...strategies[hashId]};
        copied_strategy.name = '复制的' + copied_strategy.name;
        
        hashStrategy(copied_strategy).then(copied_strategy_id => {
            strategies[copied_strategy_id] = copied_strategy;

            // 添加按钮
            const newButton = document.createElement('div');
            newButton.innerHTML = `
                <div class="center-tag btn" id="${copied_strategy_id}" onclick="showStrategyInfo(this.id)">${copied_strategy.name} </div>
            `;
            document.querySelector('.strategy-list').appendChild(newButton);

            // 更新页面显示，含按钮更新
            showStrategyInfo(copied_strategy_id, true);
        });
    });
}
function deleteCurrentStrategy(confirmed = false) {
    // 删除当前策略

    // 警告
    if (!confirmed) showModal('确认删除策略？此操作不可恢复<div class="center-tag btn" onclick="deleteCurrentStrategy(true)">确认删除</div> <div class="center-tag btn" onclick="hideModal()">取消</div>', '警告');
    

    else {
        // 如果是最后一个策略，则不允许删除
        if (Object.keys(strategies).length == 1) {
            notify('策略列表中至少要有一个策略', 1000);
            return;
        }
        showModal('删除中...', '此窗口可关闭');
        delete strategies[currentStrategyHashId];
        fetch(`../save_strategy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                previous_strategy_id: currentStrategyHashId
            })
        }).then(response => {
            if (response.ok){
                notify('保存成功', 1000);
                initStrategyPage();
                hideAllModals();
            }
        });
    }
}
function addSubItem() {
    // 在策略中添加子条目，仍属于策略部分

    // 添加后台数据
    const subItem = {
        name: "子条目",
        operation: "accept",
        conditions: [

        ]
    };

    currentStrategy.subItems.push(subItem);

    const subItemInfo = document.createElement('div');
    subItemInfo.innerHTML = `
        <div class="card subItem">
            <div class="tag name">
                <input class="subItem-name" type="text" value="${subItem.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag btn" onclick="addCondition('${subItem.name}')">添加条件</div>
                <div class="center-tag btn" onclick="copySubItem('${subItem.name}')">复制</div>
                <div class="center-tag btn" onclick="deleteSubItem('${subItem.name}', false)">删除</div>
            </div>
            <div class="tag">剩<input type="number" class="minPeople" value="${subItem.minPeople || '199'}">人时可执行</div>
            <div class="tag">操作：<select class="operation" style="height: 2rem">
                    <option value="accept">接受</option>
                    <option value="reject">移出</option>
                </select>
            </div>
            <div class="tag">记录：<select class="logCondition" style="height: 2rem">
                    <option value=-1>无</option>
                    <option value=0>子条目</option>
                    <option value=1>通过条件</option>
                    <option value=2>不通过条件</option>
                </select>
            </div>
        </div>
    `;
    subItemInfo.querySelector('.operation').value = 'accept';
    subItemInfo.querySelector('.logCondition').value = '0';

    const subItemCard = document.createElement('div');
    subItemCard.id = `${subItem.name}`;

    const subItemDetail = document.createElement('div');
    subItemInfo.style.width = '35%'
    subItemCard.style.width = '65%'
    subItemDetail.classList.add('subItem-detail');
    subItemDetail.appendChild(subItemInfo);
    subItemDetail.appendChild(subItemCard);
    strategycontainer.appendChild(subItemDetail);
}


function showStrategyInfo(strategyHashId, no_save = false) {
    

    if (currentStrategyHashId == strategyHashId) return;
    if (!no_save) {
        saveCurrentStrategy().then(() => {
            showStrategyInfo(strategyHashId, true);
        });
        return;
    }

    // 更改按钮样式
    strategy_list = document.querySelector('.strategy-list');

    strategy_list.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
    strategy_list.querySelector(`[id='${strategyHashId}']`).classList.add('active');

    // 更改全局变量

    currentStrategyHashId = strategyHashId;
    currentStrategy = strategies[strategyHashId]

    // 清空column内容
    strategycontainer.innerHTML = '';


    // 创建并添加策略名的card  (包括操作按钮)

    
    document.querySelector('.strategy-info').innerHTML = `
        <div class="card strategy" id="${currentStrategy.name}">
            <div class="tag">
                <input class="strategy-name" type="text" value="${currentStrategy.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag btn" onclick="addSubItem()">添加子条目</div>
                <div class="center-tag btn" onclick="copyCurrentStrategy()">复制策略</div>
                <div class="center-tag btn" onclick="deleteCurrentStrategy()">删除本策略</div>
                <div class="center-tag btn" onclick="saveCurrentStrategy()">保存本策略</div>
            </div>
        </div>
    `;
    // 星期、时间暂未实现
    // <div class="frame settings">
    // <div class="center-tag btn" onclick="showWeekDays()">
    //     设置星期：${currentStrategy.weekDays}
    // </div>
    // <div class="center-tag btn" onclick="showTimes()">
    //     运行时间：${currentStrategy.timesStart}-${currentStrategy.timesEnd}
    // </div>
    // </div>
    
    

    // 创建并添加每个子条目的card  
    currentStrategy.subItems.forEach((subItem) => {

        // 添加子条目卡片
        const subItemInfo = document.createElement('div');
        subItemInfo.innerHTML = `
            <div class="card subItem">
            <div class="tag name">
                <input class="subItem-name" type="text" value="${subItem.name}">
            </div>
            <div class="tag actions">
                <div class="center-tag btn" onclick="addCondition('${subItem.name}')">添加条件</div>
                <div class="center-tag btn" onclick="copySubItem('${subItem.name}')">复制</div>
                <div class="center-tag btn" onclick="deleteSubItem('${subItem.name}', false)">删除</div>
            </div>
            <div class="tag">剩<input type="number" class="minPeople" value="${subItem.minPeople || '199'}">人时可执行</div>
            <div class="tag">操作：<select class="operation" style="height: 2rem">
                    <option value="accept">接受</option>
                    <option value="reject">移出</option>
                </select>
            </div>
            <div class="tag">记录：<select class="logCondition" style="height: 2rem">
                    <option value=-1>无</option>
                    <option value=0>子条目</option>
                    <option value=1>通过条件</option>
                    <option value=2>不通过条件</option>
                </select>
            </div>
        </div>
        `;
        subItemInfo.querySelector('.operation').value = subItem.operation;
        subItemInfo.querySelector('.logCondition').value = subItem.logCondition;

        const subItemCard = document.createElement('div');
        subItemCard.id = `${subItem.name}`;

        subItem.conditions.forEach((Condition) => {
            // 创建tag元素  
            const ConditionTag = document.createElement('div');
            ConditionTag.innerHTML = `
                <div class="tag condition">
                    <div class="tag">
                        <select id="conditionName">
                            <option value="deskmate_days">同桌天数</option>
                            <option value="completed_time_stamp">今日已打卡0/1</option>
                            <option value="today_study_cheat">今日作弊0/1</option>
                            <option value="max_combo_expectancy">期望连卡天数</option>
                            <option value="finishing_rate">本班总榜完成率</option>
                            <option value="dependable_frame">小队头像框</option>
                            <!-- (3靠谱4未知1萌新0不靠谱) -->
                            <option value="blacklisted">在王者黑名单</option>
                            <option value="modified_nickname">班内已改昵称</option>
                            <option value="drop_last_week">上周漏卡天数</option>
                            <option value="drop_this_week">本周漏卡天数</option>
                            <option value="duration_days">加入天数</option>
                            <option value="completed_times">完成天数</option>
                            <!--还没实现 <option value="late_last_week">上周晚卡天数</option> -->
                            <!-- <option value="late_this_week">本周晚卡天数</option> -->
                        </select>
                    </div>
                    <div class="tag">
                        <select id="operator">
                            <option>></option>
                            <option><</option>
                            <option>==</option>
                            <option>!=</option>
                            <option>>=</option>
                            <option><=</option>
                        </select>
                    </div>
                    <div class="tag value">
                        <input id="conditionValue" type="number" class="conditionValue">
                    </div>
                    <div class="tag actions">
                        <div class="btn" onclick="deleteCondition(this)">删除</div>
                    </div>
                </div>
            `;
            // 将tag添加到subItem
            subItemCard.appendChild(ConditionTag);
            // 设置名称默认值
            ConditionTag.querySelector('#conditionName').value = Condition.name;
            
            // 设置操作符默认值
            ConditionTag.querySelector('#operator').value = Condition.operator;
            
            // 设置值默认值
            if (Condition.name == 'today_study_cheat'){
                conditionValue = ConditionTag.querySelector('#conditionValue')
                if (Condition.value == '是'){
                    conditionValue.value = 1
                }else{  
                    conditionValue.value = 0
                }
            }else{
                ConditionTag.querySelector('#conditionValue').value = Condition.value;
            }
        });
        const subItemDetail = document.createElement('div');
        subItemDetail.classList.add('subItem-detail');
        subItemInfo.style.width = '35%'
        subItemCard.style.width = '65%'
        subItemDetail.appendChild(subItemInfo);
        subItemDetail.appendChild(subItemCard);
        // 将子条目名称卡片添加到容器  
        strategycontainer.appendChild(subItemDetail);

    });
}

// 以下是 子条目 实现细节
function copySubItem(subItemName) {
// 复制子条目
    copied_name = `复制的${subItemName}`
    const subItem = {
        name: copied_name,
        minPeople: 199
    }

    // 复制子条目卡片  

    const subItemInfo = document.createElement('div');
    subItemInfo.innerHTML = `
    <div class="card subItem">
        <div class="tag name">
            <input class="subItem-name" type="text" value="${subItem.name}">
        </div>
        <div class="tag actions">
            <div class="center-tag btn" onclick="addCondition('${subItem.name}')">添加条件</div>
            <div class="center-tag btn" onclick="copySubItem('${subItem.name}')">复制</div>
            <div class="center-tag btn" onclick="deleteSubItem('${subItem.name}', false)">删除</div>
        </div>
        <div class="tag">剩<input type="number" class="minPeople" value="${subItem.minPeople || '199'}">人时可执行</div>
        <div class="tag">操作：<select class="operation" style="height: 2rem">
                <option value="accept">接受</option>
                <option value="reject">移出</option>
            </select>
        </div>
        <div class="tag">记录：<select class="logCondition" style="height: 2rem">
                <option value=-1>无</option>
                <option value=0>子条目</option>
                <option value=1>通过条件</option>
                <option value=2>不通过条件</option>
            </select>
        </div>
    </div>
    `;
    subItemInfo.querySelector('.operation').value = 'accept';
    subItemInfo.querySelector('.logCondition').value = '0';
    const subItemCard = document.createElement('div');
    subItemCard.id = `${copied_name}`;
    
    const subItemDetail = document.createElement('div');
    subItemDetail.classList.add('subItem-detail');
    subItemInfo.style.width = '35%'
    subItemCard.style.width = '65%'
    subItemDetail.appendChild(subItemInfo);
    subItemDetail.appendChild(subItemCard);

    // 将子条目名称卡片添加到容器  
    strategycontainer.appendChild(subItemDetail);
}
function deleteSubItem(subItemName, confirmed) {
// 删除子条目
    // 警告
    if (!confirmed)
        showModal(`是否删除子条目${subItemName}？此操作无法撤销<br><div class="center-tag btn" onclick="deleteSubItem('${subItemName}', true)">确认删除</div><div class="center-tag btn" onclick="hideAllModals()">取消</div>`, '警告');
    else {
        // 实际上#subItemName是子条目condition框，所以要找1级父节点
        document.querySelector(`#${subItemName}`).parentNode.remove();
        hideAllModals();
    };
}
function addCondition(subItemName) {
// 添加条件

    // 前台：添加条件Tag 
    const ConditionTag = document.createElement('div');
    ConditionTag.innerHTML = `
        <div class="tag condition">
            <div class="tag">
                <select id="conditionName">
                    <option value="deskmate_days">同桌天数</option>
                    <option value="completed_time_stamp">今日已打卡0/1</option>
                    <option value="today_study_cheat">今日作弊0/1</option>
                    <option value="max_combo_expectancy">期望连卡天数</option>
                    <option value="finishing_rate">本班总榜完成率</option>
                    <option value="dependable_frame">小队头像框</option>
                    <!-- (3靠谱4未知1萌新0不靠谱) -->
                    <option value="blacklisted">在王者黑名单</option>
                    <option value="modified_nickname">班内已改昵称</option>
                    <option value="drop_last_week">上周漏卡天数</option>
                    <option value="drop_this_week">本周漏卡天数</option>
                    <option value="duration_days">加入天数</option>
                    <option value="completed_times">完成天数</option>
                    <!--还没实现 <option value="late_last_week">上周晚卡天数</option> -->
                    <!-- <option value="late_this_week">本周晚卡天数</option> -->
                </select>
            </div>
            <div class="tag">
                <select id="operator">
                    <option>></option>
                    <option><</option>
                    <option>==</option>
                    <option>!=</option>
                    <option>>=</option>
                    <option><=</option>
                </select>
            </div>
            <div class="tag value">
                <input id="conditionValue" type="number" class="conditionValue">
            </div>
            <div class="tag actions">
                <div class="btn" onclick="deleteCondition(this)">删除</div>
            </div>
        </div>
    `;
    // 将tag添加到subItem
    document.getElementById(subItemName).appendChild(ConditionTag);
    // 设置名称默认值
    ConditionTag.querySelector('#conditionName').value = 'deskmate_days';
    
    // 设置操作符默认值
    ConditionTag.querySelector('#operator').value = '>';
    
    // 设置值默认值
    ConditionTag.querySelector('#conditionValue').value = 0;
}



//以下是 条件 实现细节
function deleteCondition(button) {
    // 删除条件
    button.parentNode.parentNode.remove();
}




function saveCurrentStrategy(copy_current_strategy = false) {
    // currentStrategyDiv = document.querySelector('.strategy-info');
    currentStrategy = {
        name : document.querySelector('.strategy-name').value,
        subItems: []
    };
    const subItems = document.querySelectorAll('.subItem-detail');
    subItems.forEach((subItem) => {
        let subItemData = {
            name: subItem.querySelector('.subItem-name').value,
            minPeople: subItem.querySelector('.minPeople').value,
            operation: subItem.querySelector('.operation').value,
            logCondition: subItem.querySelector('.logCondition').value,
            conditions: []
        };
        const conditions = subItem.querySelectorAll('.condition');
        conditions.forEach((condition) => {
            let conditionData = {
                name: condition.querySelector('#conditionName').value,
                operator: condition.querySelector('#operator').value,
                value: condition.querySelector('#conditionValue').value
            };
            if (conditionData.name == 'today_study_cheat'){
                if (conditionData.value == 1){
                    conditionData.value = '是';
                }else{
                    conditionData.value = '否';
                }
            }
            subItemData.conditions.push(conditionData);
        });
        currentStrategy.subItems.push(subItemData);
    });
    
    return hashStrategy(currentStrategy).then( hashId => {
        if (hashId === currentStrategyHashId) {
            notify("策略未修改，无需保存", 500);
            if (copy_current_strategy) copyCurrentStrategy(hashId);
            return;
        } // 未修改，不保存
        delete strategies[currentStrategyHashId];
        strategies[hashId] = currentStrategy;

        showModal('保存修改中，请稍候...<br>此页面可关闭', '提示');
        // 发送到服务器
        return fetch(`../save_strategy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_dict: currentStrategy,
                previous_strategy_id: currentStrategyHashId
            })
        }).then(response => {
            if (response.ok){
                notify('保存成功');
                if (copy_current_strategy) showModal(`复制成功，将要复制策略名称${currentStrategy.name}`, '提示');
                else showModal('保存成功，即将重新加载', '提示');
                // 刷新页面
                setTimeout(() => {
                    initStrategyPage().then((data) => {
                        if (copy_current_strategy) copyCurrentStrategy(hashId);
                        hideAllModals();
                    });
                }, 1000);
            }
        }).catch(error => {
            notify(`保存失败：${error}`);
            hideAllModals();
        });
    });
}

function confirmAndSaveCurrentStrategy() {
    // 确认保存当前策略
    showModal(`是否保存当前策略？不保存请直接刷新页面<br><div class="center-tag btn" onclick="saveCurrentStrategy()">保存</div><div class="center-tag btn" onclick="hideAllModals()">取消</div>`, '提示');

}
