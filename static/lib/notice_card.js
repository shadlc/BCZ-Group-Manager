
function $newCard(msg) {
            // 获取msg有多少个<br>
            lines = msg.split('<br>')
            height = 30; // 计算高度
            for (var i = 0; i < lines.length; i++) {
                lines[i] = lines[i].trim();
                // 以每15个字符为一行，计算高度
                height += Math.ceil(lines[i].length / 15) * 20;
            }
            

            // 创建新的notice类的框  
            const newCard = document.createElement('div');
            newCard.innerHTML = /*最外层的div并不是真正的card，转换jquery对象时还有一层*/`
                <div>
                    <div class="notice-line" style="width: 100%; height: 3px; background: black; position: relative; top: 0; left: 0;"></div>
                    <div class="notice" style="height: ${height}px; position: relative; touch-action: none; background-color: #aaaaaa33; cursor:pointer; ">
                        ${msg}
                    </div>
                </div>
            `;
            var $newCard = $(newCard);
            $newCard.appendTo('.notice-wall');

            // 添加触摸事件监听器  
            var touchStartX = 0;
            var mouseStartX = 0;
            var isSwiping = false;
            var cardWidth = $newCard.width();
            var swipeDistance = 0;
            var cardY = $newCard.offset().top + height; // 获取通知框的Y坐标 + 高度
            var top = 0;
            

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
                    // console.log('点击事件');
                    if (top == 0) {
                        top = 1
                        // 将背景色改成aaffff66

                        $newCard.css('background-color', '#aaaaaa99');
                        // 停止当前线的动画
                        $newCard.find('.notice-line').stop();
                        // 线的宽度逐渐增加到100%  
                        $newCard.find('.notice-line').animate({
                            width: '100%'
                        });
                    }
                    else {
                        top = 0
                        $newCard.css('background-color', '#aaaaaa33');
                        $newCard.find('.notice-line').animate({
                            width: '0%'
                        }, delay, function () {
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
                    }
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
            //延迟时间获取方式：通知末尾可能有(..s)的显示时间，获取即可
            try {
                var delay = msg.match(/\((\d.+)s\)/)[1];
                delay = delay.replace('s', '') * 1000;
                // console.log(delay);
            } catch (error) {
                try{
                    var delay = msg.match(/\((-\d.+)s\)/)[1];
                    delay = delay.replace('s', '') * 1000;
                    // console.log(delay);
                }
                catch (error) {
                    delay = msg.length * 120;
                }
            }
            console.log(delay);
            // 如果delay不是数字，则设置为msg*60

            if (isNaN(delay)) {
                delay = msg.length * 120;
            }
            if (delay == 99999000) {
                // 错误代码
                showModal('错误', '出现了错误，请检查');
                showModal('错误发生时间', new Date().toLocaleString());
            }
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
                    // 线的宽度逐渐减少到0%  
                    $newCard.find('.notice-line').animate({
                        width: '0%'
                    }, delay, function () {
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