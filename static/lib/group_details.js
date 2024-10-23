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
        queryFilterLog('1');
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
    function eventFilterSearch(event) {
      if (event.key === "Enter" || event.type === 'blur') {
        queryFilterLog(event?.target?.value);
      }
    }
    function queryFilterLog(option = '1') {
      // 向后端请求筛选日志
      filter_page_num = document.querySelector('.filter-page-num');
      // filter_page_num的内容是 当前页/总页数
      let page_num = parseInt(filter_page_num.textContent.split('/')[0]);
      let page_max = parseInt(filter_page_num.textContent.split('/')[1]);
      if (option === '') {
        return;
      } else if (option == '-') {
        page_num --;
      } else if (option == '+') {
        page_num ++;
      } else if (option !== null && !isNaN(option)) {
        if (option < 0) {
          page_num = page_max + 1 + parseInt(option);
        } else {
          page_num = parseInt(option);
        }
      }
      if (page_num > page_max) {
        page_num = page_max;
      }
      else if (page_num < 1) {
        page_num = 1;
      }
      page_count = parseInt(document.querySelector('#filter-page-count').value)
      
      let payload = {
        'group_id': group_id,
        'count_start': (page_num - 1) * page_count,
        'count_limit': page_count,
      }
      fetch('../query_filter_log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload) 
      })
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          return;
        }
        let result = data.data;
        result.data.unshift(['时间','策略名','人数','累计筛选','累计接受','接受名单','踢出名单','退出名单']);
      
        // 将result最前面加上分页信息
        
        page_max = result.page_max;
        page_num = result.page_num;

        filter_page_num.style="margin-right: 0.2rem; width: ${(page_num.toString().length * 8) + 'px'}"
        filter_page_num.oninput="this.style.width = (this.value.length * 8) + 'px'"
        filter_page_num.onkeypress="eventFilterSearch(event)"
        filter_page_num.onblur="eventFilterSearch(event)"
        filter_page_num.textContent = `${page_num}/${page_max}`;
        
        
        let table = document.getElementById("filter_log_table");
        // 如果没有数据，则提示为空
        if (result.data.length == 0) {
          table.innerHTML = '<br><span class="center">暂无筛选数据</span><br><br>';
          return;
        }
        else {
          table.innerHTML = '';
          fillDataToTable(result.data, table);
        }
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }
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
