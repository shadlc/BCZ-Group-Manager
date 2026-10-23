let origin_auth_token = '';
let group_id = '';
    let today = new Date();
    let current_week = today.getWeek();
    current_week = today.getFullYear() + "-W" + ("0" + current_week).slice(-2);
    function initGroupDetails(current_group_id) {
      if (current_group_id == group_id)
        return;
      group_id = current_group_id;

      showModal('正在加载数据，请稍候...', '加载中');
      queryFilterState();

      
      getGroupDetailsOption()
      .then(()=>{
        let week_select = document.getElementById("week_select");
        week_select.value = current_week;
        return queryGroupDetails(group_id);
      })
      .then((result)=>{
        if (result) {
          let loading_text = document.querySelector('.loading-text');
          loading_text.classList.add('hide');
          document.querySelector('.member-info-container').classList.remove('hide');
        }
        hideAllModals();
      });
    }

    // 打开关闭公告模态框
    function toggleNoticeModal(event) {
      if (event?.target) {
        if (event?.target.id != 'notice_modal') {
          return;
        }
      }
      let modal = document.getElementById('notice_modal');
      let modal_content = modal.children[0];
      let status = modal.getAttribute('data-status');
      modal.setAttribute('data-status', '');
      if (status == 'show') {
        modal_content.style.transform = 'scale(0.9)';
        modal.style.opacity = 0;
        setTimeout(()=>{
          modal.classList.add('hide');
          modal.setAttribute('data-status', 'hidden');
        }, 500);
      } else if (status == 'hidden') {
        modal.classList.remove('hide');
        modal_content.style.transform = 'scale(0.9)';
        modal.style.opacity = 0;
        setTimeout(()=>{
          modal_content.style.transform = 'scale(1)';
          modal.style.opacity = 1;
        }, 1);
        setTimeout(()=>{
          modal.setAttribute('data-status', 'show');
        }, 500);
      }
    }

    // 打开关闭小班设置模态框
    function toggleSettingModal(event) {
      if (event?.target) {
        if (event?.target.id != 'setting_modal') {
          return;
        }
      }
      let modal = document.getElementById('setting_modal');
      let modal_content = modal.children[0];
      let status = modal.getAttribute('data-status');
      modal.setAttribute('data-status', '');
      if (status == 'show') {
        modal_content.style.transform = 'scale(0.9)';
        modal.style.opacity = 0;
        setTimeout(()=>{
          modal.classList.add('hide');
          modal.setAttribute('data-status', 'hidden');
        }, 500);
      } else if (status == 'hidden') {
        modal.classList.remove('hide');
        modal_content.style.transform = 'scale(0.9)';
        modal.style.opacity = 0;
        setTimeout(()=>{
          modal_content.style.transform = 'scale(1)';
          modal.style.opacity = 1;
        }, 1);
        setTimeout(()=>{
          modal.setAttribute('data-status', 'show');
        }, 500);
      }
    }

    function addWhitelist(){
      // 添加白名单
      // 向后台查询当前小班的白名单
      fetch('../get_whitelist', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id': group_id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let modal_content = '<table class="simple-table"><tr><th>id</th><th>昵称</th><th>操作</th></tr>'
        for (let i in data.data) {
          let member = data.data[i];
          modal_content += `
          <tr>
            <td>`+member[0]+`</td>
            <td>`+member[1]+`</td>
            <td><a href="javascript:void(0)" onclick="removeWhitelist('`+member[0]+`')">移除</a></td>
          </tr>
          `;
        }
        modal_content += '</table>';
        modal_content += '<div class="input-group"><input type="text" id="add_whitelist_input" placeholder="请输入要添加的id"><button class="btn" onclick="addWhitelistSubmit()">添加</button></div>';
        showModal(modal_content, '当前小班白名单')
      });
    }
    function addWhitelistSubmit(){
      // 向后台添加白名单
      let input = document.getElementById('add_whitelist_input');
      let id = input.value.trim();
      if (id == '') {
        notify('请输入要添加的id');
        return;
      }
      fetch('../add_whitelist', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id': group_id,
          'id': id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        notify(data.msg);
        queryGroupDetails();
        hideAllModals();
      })
    }
    function removeWhitelist(id){
      // 向后台移除白名单
      fetch('../remove_whitelist', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id': group_id,
          'id': id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        notify(data.msg);
        queryGroupDetails();
        hideAllModals();
      })
    }


    function StopFilter() {
      // 停止筛选
      showModal('正在停止筛选...<br>将在本轮【等待结束后】停止<br>可以关闭本窗口', '停止中');
      fetch('./stop_filter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},  
        body: JSON.stringify({
          'group_id': group_id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        notify(data.msg);
        // 将筛选按钮改成启动
        let filter_btn = document.querySelector('#filter_btn');
        filter_btn.textContent = '启动筛选';
        filter_btn.onclick = toggleFilterModal;
        hideAllModals();
      })
    }
    function queryFilterState()
    {
      // 读取筛选状态
      fetch('./query_filter_state', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},  
        body: JSON.stringify({
          'group_id': group_id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let filter_btn = document.querySelector('#filter_btn');
        if (data.data) {
          filter_btn.textContent = '停止筛选';
          filter_btn.onclick = StopFilter;
        } else {
          filter_btn.textContent = '启动筛选';
          filter_btn.onclick = toggleFilterModal;
        }
      })
    }




    function selectStrategyAndStart(strategy_id){
      // 用于在ToggleFilterModal中选择筛选策略并启动，暂时废弃
      showModal('正在启动筛选...<br>可以关闭本信息', '启动中');
      fetch('./start_filter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id': group_id,
          'strategy_id': strategy_id
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        notify(data.msg);
        // 将筛选按钮改成停止
        let filter_btn = document.querySelector('#filter_btn');
        filter_btn.textContent = '停止筛选';
        filter_btn.onclick = StopFilter;
        hideAllModals();
      })

    }
    function toggleFilterModal() {
      // 读取策略，然后显示选择窗口
      fetch('../get_strategy_list', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
      }).then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let modal_content = '<div id="strategy_list"><table class="simple-table"><tr><th>名称</th><th>子条目名称</th></tr>'
        
        for (let i in data.data) {
          let strategy = data.data[i];
          sub_item_name = ''
          for (let j in strategy.subItems){
            // console.log(strategy)
            sub_item_name += strategy.subItems[j].name + '<br>';
          }
          // console.log(i)
          modal_content += `
          <tr class="btn" onclick="pushStrategyList('${i}','${strategy.name}')">
            <td>`+strategy.name+`</td>
            <td>`+sub_item_name+`</td>
          </tr>
          `;
        }
        modal_content += '</table>';
        // 每选择一个策略，push一个div到下面的链中，最后一起发送出去
        modal_content += '<p>接受198人完成筛选，下面是已选策略链：</p><div class="center" id="strategy_list_container"></div>';
        // 添加启动时间，用输入框，提交时再检查是否合法
        modal_content += '<div class="input-group"><input type="text" id="start_time_input" style="width: 15rem; " placeholder="启动时间 如08:30 立即启动不填"></div>';
        // 发送按钮
        modal_content += '<button class="center btn" onclick="startFilter()">启动</button></div>'; 
        showModal(modal_content, '请选择筛选策略')
      });
    }
    function pushStrategyList(strategy_id, strategy_name){
      // 向下面的链中添加一个div
      let container = document.querySelector('#strategy_list_container');
      let strategy_div = document.createElement('div');
      strategy_div.setAttribute('class','strategy-item');
      let strategy_info = document.createElement('span');
      strategy_div.id = strategy_id;
      strategy_info.textContent = `${strategy_name}(点击删除)`;
      // 被点击时删除自身
      strategy_info.onclick = function(){
        this.parentNode.parentNode.removeChild(this.parentNode);
      }
      strategy_div.appendChild(strategy_info);
      container.appendChild(strategy_div)
    }
    function startFilter(){
      // 向后台发送筛选策略
      let strategy_list = document.querySelectorAll('.strategy-item');
      let strategy_id_list = [];
      for (let i = 0; i < strategy_list.length; i++) {
        strategy_id_list.push(strategy_list[i].id);
      }
      console.log(strategy_id_list  )
      if (strategy_id_list.length == 0) {
        notify('请选择筛选策略');
        return;
      }
      // 只需发送hour和minute
      scheduled_time = document.getElementById('start_time_input').value.split(':');
      let scheduled_hour = parseInt(scheduled_time[0]); 
      let scheduled_minute = parseInt(scheduled_time[1]);
      showModal('正在启动筛选...<br>可以关闭本信息', '启动中');
      fetch('./start_filter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id': group_id,
          'strategy_id_list': strategy_id_list,
          'scheduled_hour': scheduled_hour,  
          'scheduled_minute': scheduled_minute
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        notify(data.msg);
        // 将筛选按钮改成停止
        let filter_btn = document.querySelector('#filter_btn');
        filter_btn.textContent = '停止筛选';
        filter_btn.onclick = StopFilter;
        hideAllModals();
      })
    }

    // 获取小班信息
    function queryGroupDetails() {
      let loading_text = document.querySelector('.loading-text');
      let week_select = document.querySelector('#week_select');
      let payload = {
        'id': group_id,
        'week': week_select.value,
      }
      return fetch('../query_group_details', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          loading_text.innerHTML = data.msg;
          notify(data.msg);
          return;
        }
        let group = data.data[0];
        origin_auth_token = group.auth_token;
        if (group.token_invalid) {
          notify('当前小班授权令牌已失效，请设置新的授权令牌');
        }
        setGroupInfo(group);
        getAcceptedFilter(group);//包含setMemberInfo
        // 确保WebSocket连接已初始化
        if (!ws) {
          initWebSocket();
        }
        return true;
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
        loading_text.innerHTML = error;
      });
    }

    // 获取筛选选项
    function getGroupDetailsOption() {
      return fetch('../get_group_details_option')
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let week = data.data.week;
        let week_select = document.querySelector('#week_select');
        for(let key in week) {
          let option = document.createElement('option');
          option.value = key;
          option.text = week[key];
          week_select.add(option);
        }
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 事件触发搜索
    function eventSearch(event) {
      if (event.key === "Enter" || event.type === 'blur') {
        queryGroupDetails(event?.target?.value);
      }
    }

    // 通过数据设置展示小班信息
    function setGroupInfo(group) {
      document.querySelector('input[name=record_select][value="'+group.daily_record+'"]').checked = true;
      document.getElementById('late_time_input').value = group.late_daka_time;
      document.getElementById('auth_token_input').value = group.auth_token;
      let container = document.querySelector('.group-info-container');
      let week_count_limit = 1400;
      if (group.week == current_week) {
        weekday = today.getDay();
        if (weekday == 0) {
          weekday = 7;
        }
        week_count_limit = group.count_limit * weekday;
      }
      let comment_content = '';
      for (let i in group.members) {
        let member = group.members[i];
        if (!member.group_nickname) {
          continue;
        }
        comment_content += `
        <div class="comment">
            <div class="avatar">
              <img src="`+member.avatar+`" />
            </div>
            <div class="member-commit">
              <span>`+member.nickname+`: </span>
              <span>`+member.group_nickname+`</span>
            </div>
            
          </div>
        `;
      }
      if (group.notice == '') {
        group.notice = '<span class="center">暂无公告</span>';
      }
      let group_content = `
        <span class="gloss"></span>
        <span class="eraser" onclick="slideLeft(event)"></span>
        <div class="group brief transparent">
          <div class="info-table">
            <div class="avatar" onclick="rotate(event)">
              <img src="https://vol-v6.bczcdn.com`+group.avatar+`" />
              <img src="`+group.avatar_frame+`" />
            </div>
            <div class="group-info">
              <span>`+group.name+`</span>
            </div>
            <div class="group-detail">
              <span>班长: `+group.leader+`(`+group.leader_id+`)</span>
              <span>人数`+group.member_count+`/`+group.count_limit+`, 完成率`
                + Math.round(group.finishing_rate * 100)+`%, `
                + (group.member_count - group.today_daka_count) +`人未打卡</span>
              <span>当前周总打卡数: `+group.total_times+`/`+week_count_limit+`, `
                + (group.absence_count) +`人缺卡, `
                + group.late_count +`人晚卡</span>
              <span>`+group.introduction+`</span>
            </div>
          </div>
        </div>
        <img class="rank-flag" src="../img/s`+group.rank+`.png" onclick="sway(event)" />
        <div class="tiny-notice" onclick="toggleNoticeModal()">
          <span>公告</span>
        </div>
        <div id="notice_modal" class="modal hide" data-status="hidden" onclick="toggleNoticeModal(event)">
          <div class="modal-content notice">
            <span class="modal-close-btn" onclick="toggleNoticeModal()"></span>
            <div class="modal-title">小班公告</div>
            <div class="modal-body">
              <div class="modal-text">`+group.notice+`</div>
              <div class="modal-comment">
                `+comment_content+`
              </div>
            </div>
          </div>
        </div>
      `;
      let info_div = document.createElement('div');
      info_div.className = 'blackboard';
      info_div.innerHTML = group_content;
      container.innerHTML = '';
      container.insertBefore(info_div, container.firstChild);
    }
    let ws = null;
    let objectInfos = {};
    
    function initWebSocket() {
      // 关闭已存在的连接
      if (ws) {
        ws.close();
      }
      
      // 创建新的WebSocket连接
      ws = new WebSocket('ws://' + window.location.host + '/ws');
      
      ws.onopen = function() {
        console.log('WebSocket连接已建立');
      };
      
      ws.onmessage = function(event) {
        let data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onerror = function(error) {
        console.error('WebSocket错误:', error);
      };
      
      ws.onclose = function() {
        console.log('WebSocket连接已关闭');
        // 尝试重连
        setTimeout(initWebSocket, 3000);
      };
    }
    
    function handleWebSocketMessage(event) {
      console.log(event);
      const data = event.data;
      switch(event.type) {
        case 'filter_start':
          // 筛选器组启动/进入下一个筛选任务
          break;
        case 'object_info':
          // 获取到对象信息
          // 合并info和member_info数据
          const combinedInfo = { ...data.info, ...data.member_info };
          updateObjectInfo(data.shareKey, data.uniqueId, combinedInfo);
          break;
        case 'filter_verdict':
          // 筛选器判断结果
          updateObjectInfo(data.shareKey, data.uniqueId, {'verdict': data})
          break;
        case 'object_quit':
          updateObjectInfo(data.shareKey, data.uniqueId, {'status': '已退出'})
          break;
        case 'object_add_remove_queue':
          // 对象被加入准备移除队列
          updateObjectInfo(data.shareKey, data.uniqueId, {'status': '准备移除'})
          break;
        case 'object_removed':
          // 对象被移除
          updateObjectInfo(data.shareKey, data.uniqueId, {'status': '已移除'})
          deleteObject(data.uniqueId);
          break;
        case 'filter_status_change':
          // 筛选器状态切换
          break;
        case 'filter_progress':
          // 筛选进度条变更
          updateProgressBars(data);
          break;
        case 'filter_sleep':
          // 下一轮筛选前睡眠
          break;
        case 'filter_stop':
          // 筛选器组被强行停止
          break;
        case 'log':
          // 日志消息
          break;
      }
    }

    function deleteObject(uniqueId) {
      // 给元素增加渐隐动画，然后删除
      const ele = document.getElementById(`object-info-${uniqueId}`);
      ele.style.animation = 'fade-out 0.5s ease-in-out forwards';
      setTimeout(() => {
        ele.remove();
        delete objectInfos[uniqueId];
      }, 500);
    }
    
    function updateProgressBars(data) {
      console.log(data);
      // 更新总进度条（累计接受人数/班级人数上限）
      const totalProgressBar = document.getElementById('total-progress-bar');
      const countLimit = data.count_limit; // 班级人数上限
      const progress = (data.accepted_count / countLimit) * 100;
      totalProgressBar.style.width = progress + '%';
      totalProgressBar.textContent = `累计接受${data.accepted_count}/上限${countLimit}`;
      
      // 更新二级进度条（累计已处理对象数/总对象数）
      const secondaryProgressBar = document.getElementById('current-progress-bar');
      const secondaryProgress = (data.processed_count / data.total_count) * 100;
      secondaryProgressBar.style.width = secondaryProgress + '%';
      secondaryProgressBar.textContent = `已处理${data.processed_count}/当前人数${data.total_count}`;
    }
    
    function updateObjectInfo(shareKey, uniqueId, info) {
      // 存储对象信息
      if (!objectInfos[uniqueId]) {
        objectInfos[uniqueId] = {};
      }
      // 采用update的方式合并更新
      for (const key in info) {
        objectInfos[uniqueId][key] = info[key];
      }
      
      // 更新或创建信息框
      renderObjectInfo(uniqueId);
    }
    
    function renderObjectInfo(uniqueId) {
      const objectInfo = objectInfos[uniqueId];
      const container = document.getElementById('objects-info-container');
      
      // 检查是否已存在该对象的信息框
      let infoBox = document.getElementById(`object-info-${uniqueId}`);
      
      if (!infoBox) {
        // 创建新的信息框
        infoBox = document.createElement('div');
        infoBox.id = `object-info-${uniqueId}`;
        infoBox.className = 'object-info-box';
        container.appendChild(infoBox);
      }
      
      // 构建信息框内容
      let content = '';
      
      // 第一行：头像、名称和ID
      content += `
        <div class="object-info-header">
          <div class="avatar">
            <img src="${objectInfo.info?.avatar || 'img/default_avatar_new2.png'}" />
          </div>
          <div class="object-info-name">
            <span class="name">${objectInfo.info?.name || '未获取'}</span>
            <span class="uniqueId">${uniqueId}</span>
          </div>
        </div>
      `;
      
      // 第二行：标签
      content += `
        <div class="object-info-tags">
          ${objectInfo.info?.is_primary_student == 1 ? '<span class="tag primary-student">在学小学词书</span>' : ''}
          ${objectInfo.info?.blacklisted == 1 ? '<span class="tag blacklisted">在王者联黑</span>' : ''}
        </div>
      `;
      
      // 第三行：状态和操作区
      content += `
        <div class="object-info-status">
          <span class="status">${objectInfo.status || '未获取'}</span>
          <div class="object-info-actions">
            <button class="btn small" onclick="emergencyCancelRemove('${uniqueId}')">紧急取消移除</button>
            <button class="btn small" onclick="undoRemoveAndAddWhitelist('${uniqueId}')">撤销移除并添加白名单</button>
          </div>
        </div>
      `;
      
      // 第四行：打卡信息
      content += `
        <div class="object-info-daka">
          <span>本周打卡: ${objectInfo.info?.drop_this_week || '未获取'}</span>
          <span>上周打卡: ${objectInfo.info?.drop_last_week || '未获取'}</span>
        </div>
      `;
      
      // 第五行：加权平均打卡时间
      content += `
        <div class="object-info-wanka">
          <span>加权平均打卡时间: ${objectInfo.info?.wanka_index || '未获取'}</span>
        </div>
      `;
      
      // 第6-11行：所在群组
      content += `
        <div class="object-info-groups">
          ${renderGroups(objectInfo.info?.groups || [])}
        </div>
      `;
      
      infoBox.innerHTML = content;
    }
    
    function renderGroups(groups) {
      let content = '';
      // 最多6个群组
      groups.forEach(group => {
        content += `
          <div class="group-item">
            <div class="group-avatar">
              <img src="${group.group_avatar || 'img/default0.png'}" />
            </div>
            <div class="group-info">
              <span class="group-name">${group.group_name || '未获取'} (${group.rank || '未获取段位'})</span>`;
              if (group.join_days && group.daka_days){ content += `
                <span class="group-stats">加入${group.join_days}天，打卡${group.daka_days}天，个人完成率${group.finishing_rate}%</span>`;
              } else { content += `
                <span class="group-stats">班级完成率${group.finishing_rate}%</span>`;
              } content += `
            </div>
          </div>
        `;
      });
      
      return content;
    }
    
    function emergencyCancelRemove(uniqueId) {
      // 紧急取消移除功能（暂未实现）
      console.log('紧急取消移除:', uniqueId);
      notify('紧急取消移除功能暂未实现');
    }
    
    function undoRemoveAndAddWhitelist(uniqueId) {
      // 撤销移除并添加白名单功能（暂未实现）
      console.log('撤销移除并添加白名单:', uniqueId);
      notify('撤销移除并添加白名单功能暂未实现');
    }
    
    // 初始化WebSocket连接
    window.onload = function() {
      initWebSocket();
    };
    function reCheckStrategyVerdict(member_id, group_id, strategy_id) {
      // 在弹窗中按下重新检测按钮后触发
      // 1.获取策略列表并询问用户选择策略
      if (strategy_id == null) {
        fetch('../get_strategy_list', {
          method: 'GET',
          headers: {'Content-Type': 'application/json'},
        }).then(response => response.json())
        .then(data => {
          if (data.retcode != 0) {
            notify(data.msg);
            return;
          }
          let modal_content = '<table class="simple-table"><tr><th>名称</th><th>子条目名称</th></tr>'
          for (let i in data.data) {
            let strategy = data.data[i];
            sub_item_name = ''
            for (let j in strategy.subItems){
              sub_item_name += strategy.subItems[j].name + '<br>';
            }
            modal_content += `
            <tr class="btn" onclick="reCheckStrategyVerdict(`+member_id+`, `+group_id+`, '`+i+`')">
              <td>`+strategy.name+`</td>
              <td>`+sub_item_name+`</td>
            </tr>
            `;
          }
          modal_content += '</table>';
          showModal(modal_content, '请选择 重新检测 策略')
        });
      }
      else{
        showModal('正在重新检测，请稍候...', '重新检测中');
        let payload = {
          'group_id': group_id,
          'unique_id': member_id,
          'strategy_id': strategy_id
        }
        return fetch('../recheck_strategy_verdict', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
          if (data.retcode != 0) {
            return;
          }
          notify('重新检测成功', 500);
          notify(data.msg, 5000);
          hideAllModals();
        })
        .catch(error => {
          console.error('请求错误:', error);
          notify('请求错误:' + error);
          hideAllModals();
        });
      }
    }
    function getAcceptedFilter(group) {
      payroll = [];
      for (let i in group.members) {
        payroll.push(group.members[i].id);
      }
      return fetch('../query_today_filter_log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          'group_id_list': payroll,
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          return;
        }
        setMemberInfo(group, data.data);
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    } 
    function getStrategyVerdictDetailsAndShowModal(modal_content, member_id, modal_title, refreshable, accepted_filter) {
      // 向后台请求策略详情
      let payload = {
        // 'week': current_week,
       'unique_id': member_id,
      }
      return fetch('../query_strategy_verdict_details', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          return;
        }
        let strategy_verdict_details = data.data;
        for (let i in strategy_verdict_details) {
          let strategy_verdict = strategy_verdict_details[i];
          if (strategy_verdict[2] == null) {
            strategy_verdict[2] = '';
          }
          modal_content+=`<tr><td>`+strategy_verdict[0]+`</td><td>`+strategy_verdict[1]+`</td><td>`+strategy_verdict[2]+`</td></tr>`;
        }
        
        if (refreshable){
          modal_content += `<tr><td></td><td class="btn center" onclick="reCheckStrategyVerdict(`+member_id+`, `+group_id+`)">重新检测</td></tr>`;
          // console.log(modal_content)
        }
        modal_content += '</table>';
        showModal(modal_content, modal_title);
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 通过数据设置展示成员信息
    function setMemberInfo(group, accepted_filter) {
      let container = document.querySelector('.details-container');
      container.innerHTML = '';
      let member_count = Object.keys(group.members).length;
      let member_filter = document.getElementById('member_filter');
      if (member_count >= 10) {
        member_filter.classList.remove('hide');
      } else {
        member_filter.classList.add('hide');
      }
      // console.log(accepted_filter)
      for (let i in group.members) {
        let member = group.members[i];
        let group_nickname_span = '';
        let badges = '';
        let display_left = document.querySelector('input[name="display_left"]:checked').value;
        if (member.group_nickname) {
          group_nickname_span += '<span>' + member.group_nickname + '</span>';
        }
        
        if (accepted_filter[member.id] == '1') {
          badges += '<span class="badge green-border">已接受</span>';
        }
        else if (accepted_filter[member.id] == '0') {
          badges += '<span class="badge red-border">未知</span>';
        }
        else if (accepted_filter[member.id] == '-1') {
          badges += '<span class="badge green-border">白名单</span>';
        }
        else{
          badges += '<span class="badge yellow-border">准备踢出</span>';
        }

        if (!member.data_time && display_left == 'true') {
          badges += '<span class="badge border">已离开</span>';
        } else if (!member.data_time && display_left == 'false') {
          continue;
        }
        if (member.data_time && group.week == current_week && member.completed_time == ''
            && document.getElementById('display_absence').checked) {
          badges += '<span class="badge blue-border">' + '今日未打卡' + '</span>';
        } else if (member.data_time && group.week == current_week && group.late_daka_time != ''
                   && member.completed_time > group.late_daka_time 
                   && document.getElementById('display_late').checked) {
          badges += '<span class="badge purple-border">' + '今日晚卡' + '</span>';
        }
        if (group.week == current_week && member.today_study_cheat == '是'
            && document.getElementById('display_cheat').checked) {
          badges += '<span class="badge red-border">今日作弊</span>';
        }
        if (member.late && document.getElementById('display_late').checked) {
          badges += '<span class="badge yellow-border">晚卡' + member.late + '次</span>';
        }
        if (member.absence && document.getElementById('display_absence').checked) {
          badges += '<span class="badge red-border">漏卡' + member.absence + '次</span>';
        }
        if (badges == '' && !document.getElementById('display_all').checked) {
          continue;
        }
        let member_content = `
          <div class="avatar">
            <img src="`+member.avatar+`" />
          </div>
          <div class="member-info">
            <span>`+member.nickname+` (`+member.completed_times+`/`+member.duration_days+`)</span>
            <span>`+member.id+`</span>
            `+group_nickname_span+`
          </div>
          <div class="member-extra">
            `+badges+`
          </div>
        `;
        let member_table = document.createElement('div');
        var refreshable = true;
        member_table.className = 'member info-table';
        member_table.innerHTML = member_content;
        let modal_content = '打卡记录为空';
        if (group.week == current_week || Object.keys(member.daka).length != 0) {
          modal_content = '<table class="simple-table"><tr><th>日期</th><th>打卡时间</th><th>词数/判定</th></tr>';
          for (let date in member.daka) {
            let daka_time = member.daka[date].time ? member.daka[date].time : '未打卡';
            let today_word_count = member.daka[date].count;
            modal_content += '<tr><td>'+date+'</td><td>'+daka_time+'</td><td>'+today_word_count+'</td></tr>';
          }
          if (member.data_time && group.week == current_week) {
            let daka_time = member.completed_time ? member.completed_time : '未打卡';
            modal_content += '<tr><td>'+member.today_date+'</td><td>'+daka_time+'</td><td>'+member.today_word_count+'</td></tr>';
          } else if (!member.data_time) {
            modal_content += '<tr><td></td><td>已离开</td><td></td></tr>';
            refreshable = false;
          }
          
        } else if (!member.data_time) {
          continue;
        }
        if (refreshable)
          member_table.onclick = () => {
              getStrategyVerdictDetailsAndShowModal(modal_content, member.id, '打卡详情', true);
          }
        else {
          member_table.onclick = () => {
              getStrategyVerdictDetailsAndShowModal(modal_content, member.id, '打卡详情', false);
          }
        }
        container.appendChild(member_table, container.lastChild);
      }
      if (container.innerHTML == '') {
        if (group.exception) {
          container.innerHTML = '<line class="center">当前小班已不可用~ 请在设置内删除</line>';
          container.innerHTML += '<line class="center">'+group.exception+'</line>';
        } else if (group.total_times) {
          container.innerHTML = '<line class="center">没有符合筛选条件的同学~</br> ヾ(≧▽≦*)o</line>';
        } else {
          container.innerHTML = '<line class="center">本周记录数据为空~</br>o((>ω< ))o</line>';
        }
      }
    }

    // 保存小班配置
    function saveConfig() {
      showModal('确保设置无误？该操作不可逆', '修改配置', ()=>{
        let record_enabled = document.querySelector('input[name=record_select]:checked')?.value;
        let late_daka_time = document.getElementById('late_time_input')?.value;
        let auth_token = document.getElementById('auth_token_input')?.value;
        if (origin_auth_token != auth_token) {
          showModal('此次操作修改了授权令牌，请确认无误', '', ()=>{
            postObserveGroup({
              'id': group_id,
              'daily_record': record_enabled,
              'late_daka_time': late_daka_time,
              'auth_token': auth_token
            });
          })
          origin_auth_token = auth_token;
        } else {
            postObserveGroup({
              'id': group_id,
              'daily_record': record_enabled,
              'late_daka_time': late_daka_time
            });
        }
      })
    }

    // 更改小班请求
    function postObserveGroup(payload) {
      return fetch('../observe_group', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => response.json())
      .then(data => {
        notify(data.msg);
        if (data.retcode != 0) {
          return;
        }
        toggleSettingModal();
        return true;
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 删除小班请求
    function deleteGroup() {
      showModal('真的要删除此小班吗？该操作不可逆', '警告', ()=>{
        postObserveGroup({
          'id': group_id,
          'valid': 0
        }).then(()=>{
          location.href = '../';
        });
      });
    }

    // 筛选成员
    function memberFilter(event) {
      let element = event.target;
      let filter = element.value;
      document.querySelectorAll('.member').forEach((e)=>{
        if (e.innerText.includes(filter)) {
          e.classList.remove('hide');
        } else {
          e.classList.add('hide');
        }
      });
    }
    
    // 添加WebSocket消息展示的样式
    function addWebSocketStyles() {
      return;
      let style = document.createElement('style');
      style.textContent = `
        /* 进度条样式 */
        .progress-container {
          margin: 10px 0;
          padding: 10px;
          background: #f5f5f5;
          border-radius: 4px;
        }
        .progress-bar {
          height: 20px;
          background: #4CAF50;
          border-radius: 10px;
          transition: width 0.3s ease;
        }
        .progress-text {
          margin-top: 5px;
          font-size: 12px;
          color: #666;
        }
        
        /* 操作区样式 */
        .action-area {
          margin: 10px 0;
          padding: 10px;
          background: #f9f9f9;
          border-radius: 4px;
          border: 1px solid #ddd;
        }
        .action-area button {
          margin-right: 10px;
          padding: 5px 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: #fff;
          cursor: pointer;
        }
        .action-area button:hover {
          background: #f0f0f0;
        }
        
        /* 对象信息框样式 */
        #object_info_container {
          margin-top: 20px;
        }
        .object-info-box {
          margin-bottom: 15px;
          padding: 15px;
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .object-info-header {
          display: flex;
          align-items: center;
          margin-bottom: 10px;
        }
        .object-info-header .avatar {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          overflow: hidden;
          margin-right: 15px;
        }
        .object-info-header .avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .object-info-name .name {
          display: block;
          font-weight: bold;
          font-size: 16px;
          margin-bottom: 5px;
        }
        .object-info-name .uniqueId {
          font-size: 12px;
          color: #666;
        }
        
        /* 标签样式 */
        .object-info-tags {
          margin-bottom: 10px;
        }
        .tag {
          display: inline-block;
          padding: 3px 8px;
          border-radius: 12px;
          font-size: 12px;
          margin-right: 8px;
        }
        .tag.primary-student {
          background: #e8f5e8;
          color: #2e7d32;
        }
        .tag.blacklisted {
          background: #ffebee;
          color: #c62828;
        }
        
        /* 状态和操作区样式 */
        .object-info-status {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
          padding: 10px;
          background: #f5f5f5;
          border-radius: 4px;
        }
        .object-info-actions button {
          padding: 3px 8px;
          font-size: 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: #fff;
          cursor: pointer;
          margin-left: 5px;
        }
        .object-info-actions button:hover {
          background: #f0f0f0;
        }
        
        /* 打卡信息样式 */
        .object-info-daka {
          margin-bottom: 10px;
          font-size: 14px;
        }
        .object-info-daka span {
          margin-right: 20px;
        }
        
        /* 加权平均打卡时间样式 */
        .object-info-wanka {
          margin-bottom: 10px;
          font-size: 14px;
        }
        
        /* 群组信息样式 */
        .object-info-groups {
          margin-top: 10px;
        }
        .group-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          padding: 8px;
          background: #f9f9f9;
          border-radius: 4px;
        }
        .group-avatar {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          overflow: hidden;
          margin-right: 10px;
        }
        .group-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .group-info .group-name {
          display: block;
          font-weight: bold;
          font-size: 13px;
          margin-bottom: 3px;
        }
        .group-info .group-stats {
          font-size: 11px;
          color: #666;
        }
      `;
      document.head.appendChild(style);
    }
    
    // 初始化时添加样式
    addWebSocketStyles();
