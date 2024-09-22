// 全自动管理器监控页面
// 横排，每一列一个班级（33%main+x-scroll），第一块板显示班级管理状态，第二块板编辑策略启动顺序，然后是加入、退出、踢出通知
function initStrategyPage(){
    // 初始化策略页面
    return fetch(`../get_activated_groups`, {
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