let origin_auth_token = '';
let group_id = '';
    let today = new Date();
    let current_week = today.getWeek();
    current_week = today.getFullYear() + "-W" + ("0" + current_week).slice(-2);
    function initGroupDetails(current_group_id) {
      if (current_group_id == group_id)
        return;
      group_id = current_group_id;
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
      });
      bindScrollToTopBtn(document.querySelector('.member-info-container'));
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
        setMemberInfo(group);
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

    // 通过数据设置展示成员信息
    function setMemberInfo(group) {
      let container = document.querySelector('.details-container');
      container.innerHTML = '';
      let member_count = Object.keys(group.members).length;
      let member_filter = document.getElementById('member_filter');
      if (member_count >= 10) {
        member_filter.classList.remove('hide');
      } else {
        member_filter.classList.add('hide');
      }
      for (let i in group.members) {
        let member = group.members[i];
        // console.log(member);
        let group_nickname_span = '';
        let badges = '';
        let display_left = document.querySelector('input[name="display_left"]:checked').value;
        if (member.group_nickname) {
          group_nickname_span += '<span>' + member.group_nickname + '</span>';
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
        member_table.className = 'member info-table';
        member_table.innerHTML = member_content;
        let modal_content = '打卡记录为空';
        if (group.week == current_week || Object.keys(member.daka).length != 0) {
          modal_content = '<table class="simple-table"><tr><th>日期</th><th>打卡时间</th><th>单词数</th></tr>';
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
          }
          modal_content += '</table>';
        } else if (!member.data_time) {
          continue;
        }
        member_table.onclick = () => {
          showModal(modal_content, '打卡详情');
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
