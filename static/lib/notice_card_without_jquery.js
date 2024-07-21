message_data = {}
function touchend_mouseup(uuid, e){
    e.preventDefault(); // 阻止默认事件，比如滚动条滚动  

    let data = message_data[uuid];
    console.log(data);
    let newCard = data.newCard;
    // 还原框大小
    newCard.style.transform = 'scale(1)';
    newCard.style.transition = 'transform 0.2s ease-in-out';
    // 设定滑动阈值，比如50%的宽度 

    cardWidth = data.cardWidth; // 获取卡片宽度
    if (Math.abs(data.swipeDistance) < cardWidth * 0.1) { // 如果滑动距离很小，则认为是点击事件，打开详情页  
        if (data.top == 0) {
            data.top = 1;
            // 将背景色改成aaffff66
            newCard.style.backgroundColor = '#aaaaaa99';

            //停止动画
            data.animation.reverse();
            data.animation.onfinish = function () {};
        } else {
            data.top = 0;
            newCard.style.backgroundColor = '#aaaaaa33';
            data.animation.reverse();
            data.animation.onfinish  = function () {
                // 淡出通知框  
                setTimeout(function () {
                    newCard.animate([
                        { opacity: 0 }
                    ], {
                        duration: 500,
                        fill: 'forwards'
                    }).onfinish = function () {
                        // 删除通知框
                        newCard.remove();
                        delete message_data[uuid];
                    };
                }, 0);
            };
        }
    }

    if (data.isSwiping && Math.abs(data.swipeDistance) > cardWidth * 0.3) { // 如果滑动距离超过阈值  
        // 滑动淡出，然后删除通知框  
        let dist = data.swipeDistance > 0 ? cardWidth : -cardWidth; // 右滑，消失到右边  
        newCard.animate([
            { marginLeft: `${dist}px`, marginRight: `${-dist}px`, opacity: 0 }
        ], {
            duration: 500,
            fill: 'forwards'
        }).onfinish = function () {
            // 删除通知框  
            delete message_data[uuid];
            newCard.remove();
        };
    } else { // 如果滑动距离不超过阈值  
        // 回到原位并恢复动画效果  
        newCard.animate([
            { marginLeft: 0, marginRight: 0, opacity: 1 }
        ], {
            duration: 500,
            easing: 'ease-in',
            fill: 'forwards'
        });
    }
    data.isSwiping = false; // 标记为不是滑动状态  
}

function touchmove_mousemove(uuid, e) {
    console.log(1);
    data = message_data[uuid];
    if (!data.isSwiping) return; // 如果不是滑动状态，直接返回  
    newCard = data.newCard;
    e.preventDefault(); // 阻止默认事件，比如滚动条滚动  
    mouseEndX = e.clientX; // 获取鼠标结束的X坐标

    data.swipeDistance = mouseEndX - data.mouseStartX; // 计算滑动距离  

    // 改变通知框margin，达到左右滑动的效果，同时有消失的动画效果  
    // 这个地方有大问题，应该就只差这个地方，没办法还是用jquery吧，调完其他再说
    // 问题：newCard的marginLeft和marginRight和opacity字段有变化，但是没有效果，就算开发工具手动设置也没有，像锁死了一样
    newCard.style.marginLeft = data.swipeDistance + 'px';
    newCard.style.marginRight = -data.swipeDistance + 'px';
    newCard.style.opacity = 1 - Math.abs(data.swipeDistance / cardWidth);

    // 有可能鼠标超过了newCard的高度，此时收不到mouseup，此时newCard通过动画返回原位
    mouseY = e.clientY; // 获取鼠标的Y坐标

    if (mouseY > data.cardBottom || mouseY < data.cardTop) {
        data.isSwiping = false; // 标记为不是滑动状态  
        newCard.animate([
            { marginLeft: 0, marginRight: 0, opacity: 1 }
        ], {
            duration: 500,
            easing: 'ease-in-out',
            fill: 'forwards'
        });
    }
}

function touchstart_mousedown(uuid, e) {
    e.preventDefault(); // 阻止默认事件，比如滚动条滚动  
    console.log(0);
    data = message_data[uuid];
    newCard = data.newCard;

    data.mouseStartX = e.clientX; // 记录鼠标开始的X坐标      
    // 缩小一圈，模拟卡片的缩放效果  
    newCard.style.transform = 'scale(0.9)';
    newCard.style.transition = 'transform 0.3s ease-in-out';
    data.isSwiping = true; // 标记为正在滑动 
    rect = newCard.getBoundingClientRect(); // 刷新一下元素的宽高，因为transform会改变宽高
    // rect={
    //     width: newCard.offsetWidth,
    //     top: newCard.offsetTop,
    //     bottom: newCard.offsetTop + newCard.offsetHeight
    // }
    data.cardWidth = rect.width;
    data.cardTop = rect.top;
    data.cardBottom = rect.bottom;
}
function new_card_disappear(uuid, e) {
    // 线的宽度逐渐减少到0%  
    data = message_data[uuid];
    let newCard = data.newCard;
    let noticeLine = newCard.querySelector('.notice-line');
    data.animation = noticeLine.animate([
        { width: '0%' }
    ], {
        duration: delay,
        fill: 'forwards',
        easing: 'ease-in-out'
    })
    data.animation.onfinish = function () {
        // 淡出通知框  
        setTimeout(function () {
            newCard.animate([
                { opacity: 0 }
            ], {
                duration: 500,
                fill: 'forwards'
            }).onfinish = function () {
                // 删除通知框
                newCard.remove();
                delete message_data[uuid];
            };
        }, 0);
    };
};

function $newCard(msg) {
    // 获取msg有多少个<br>
    let lines = msg.split('<br>');
    let height = 30; // 计算高度
    for (let i = 0; i < lines.length; i++) {
        lines[i] = lines[i].trim();
        // 以每15个字符为一行，计算高度
        height += Math.ceil(lines[i].length / 15) * 20;
    }

    // 创建新的notice类的框  
    let newCard = document.createElement('div');
    newCard.innerHTML = /*最外层的div并不是真正的card，转换jquery对象时还有一层*/`
        <div>
            <div class="notice-line" style="width: 100%; height: 3px; background: black; position: relative; top: 0; left: 0;"></div>
            <div class="notice" style="height: ${height}px; position: relative; touch-action: none; background-color: #aaaaaa33; cursor:pointer; ">
                ${msg}
            </div>
        </div>
    `;
    document.querySelector('.notice-wall').appendChild(newCard);

    // 添加触摸事件监听器  
    // 随机生成信息uuid
    let uuid = Math.random().toString(10);
    message_data[uuid] = {
        newCard: newCard,
        touchStartX: 0,
        mouseStartX: 0,
        isSwiping: false,
        swipeDistance: 0,
        cardTop: 0,
        cardBottom: 0,
        cardWidth: 0,
        top: 0,
        animation: null
    };

    newCard.addEventListener('touchstart', (e) => {
        touchstart_mousedown(uuid, e);
    }, false);

    newCard.addEventListener('mousedown', (e) => {
        touchstart_mousedown(uuid,e);
    });

    newCard.addEventListener('touchmove', (e) => {
        touchmove_mousemove(uuid,e);
    }, false);

    newCard.addEventListener('mousemove', (e) => {
        touchmove_mousemove(uuid,e);
    });

    newCard.addEventListener('touchend', (e) => {
        touchend_mouseup(uuid,e);
    }, false);

    newCard.addEventListener('mouseup', (e) => {
        touchend_mouseup(uuid,e);
    });

    //延迟时间获取方式：通知末尾可能有(..s)的显示时间，获取即可
    try {
        let delay = msg.match(/\((\d.+)s\)/)[1];
        delay = delay.replace('s', '') * 1000;
    } catch (error) {
        try {
            let delay = msg.match(/\((-\d.+)s\)/)[1];
            delay = delay.replace('s', '') * 1000;
        } catch (error) {
            delay = msg.length * 60;
        }
    }
    newCard.style.opacity = '1';
    newCard.animate([
        { marginLeft: '10px', marginRight: '-10px', opacity: 0.5 }
    ], {
        duration: 200,
        fill: 'forwards'
    }).onfinish = function () {
        newCard.animate([
            { marginLeft: 0, marginRight: 0, opacity: 1 }
        ], {
            duration: 200,
            fill: 'forwards'
        }).onfinish  = function () { new_card_disappear(uuid); }
    };
}
