// 全自动管理器监控页面
// 横排，每一列一个班级（33%main+x-scroll），第一块板显示班级管理状态，第二块板编辑策略启动顺序，然后是加入、退出、踢出通知
function initMonitorPage(){
    // 初始化策略页面
    return fetch('./monitor_status')
       .then(response => response.json())
       .then(data => {
            // 显示班级管理状态
       });
            
}
