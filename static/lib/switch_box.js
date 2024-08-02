
// var historyLeft = [];
var historyRight = [];

//动画切换函数
// function SwitchLeft(elementShow)
// // 切换左半栏，同时记录历史记录
// {
//     if (historyLeft.length > 0) {
//         document.getElementById(historyLeft[historyLeft.length - 1]).style.animation = 'Fade 0.8s forwards';
//     }
//     document.getElementById(elementShow).classList.remove('hide');
//     document.getElementById(elementShow).style.animation = 'Show 0.8s forwards';
//     historyLeft.push(elementShow);
// }
function SwitchRight(elementShow)
// 这个是右半边
{//console.log(elementShow)
    if (historyRight.length > 0) {
        // console.log(historyRight[historyRight.length - 1])
        elementHide = document.getElementById(historyRight[historyRight.length - 1]);
        elementHide.style.animation = 'Fade 0.8s forwards';
        elementHide.classList.add('back');

    }
    document.getElementById(elementShow).classList.remove('hide');
    document.getElementById(elementShow).classList.remove('back');
    document.getElementById(elementShow).style.animation = 'Show 0.8s forwards';
    // 记录历史记录
    historyRight.push(elementShow);
}
function SwitchPop()
// 弹出历史记录，若没有才退回到上一页
{
    if (historyRight.length === 1) {
        // 浏览器返回上一页
        // window.history.back();
        $newCard('No history to pop...');
        return;
    }
    // 测试：将history_Right数据用→连接成字符串
    // var historyStr = historyRight.join('→');
    // $newCard(historyStr);

    // if (historyLeft.length > 1) {
    //     // 反向动画切换
    //     document.getElementById(historyLeft[historyLeft.length - 1]).style.animation = 'FadeRevert 0.8s forwards';
    //     historyLeft.pop();
    //     document.getElementById(historyLeft[historyLeft.length - 1]).classList.remove('hide');
    //     document.getElementById(historyLeft[historyLeft.length - 1]).style.animation = 'ShowRevert 0.8s forwards';
    // }
    // if (historyRight.length > 1) {
        document.getElementById(historyRight[historyRight.length - 1]).style.animation = 'FadeRevert 0.8s forwards';
        document.getElementById(historyRight[historyRight.length - 1]).classList.add('back');
        historyRight.pop();
        document.getElementById(historyRight[historyRight.length - 1]).classList.remove('back');
        document.getElementById(historyRight[historyRight.length - 1]).style.animation = 'ShowRevert 0.8s forwards';
    // }
}

// window.onpopstate = function (event) {
// 监听浏览器的后退事件
    // if (historyRight.top === 'stragety-column')
    // // 正在strategy页面，弹出swal2弹窗询问是否保存 
    // {
    //     swal2.fire({
    //         title: '策略已修改',
    //         text: '策略已修改，是否要保存当前的更改？',
    //         showCancelButton: true,
    //         confirmButtonColor: '#3085d6',
    //         cancelButtonColor: '#d33',
    //         confirmButtonText: '是',
    //         cancelButtonText: '否'
    //     }).then((result) => {
    //         if (result.isConfirmed) {
    //             saveCurrentStrategy();
    //         } else if (result.isDenied) {

    //         }
    //     });
    // }
    // else {
    //     // 其他页面，弹出历史记录弹窗，如果没有才上一页
    //     if (historyLeft.length === 0 && historyRight.length === 0) {
            // SwitchPop();
        // }
    // }

// };