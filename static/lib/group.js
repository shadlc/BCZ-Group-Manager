
  function initGroupPage() {
    getInfo_1()
    .then((info)=>{
      if (!info) return;
      getGroupList();
    });
  }
  // 获取配置信息
  function getInfo_1() {
    return fetch('configure')
    .then(response => response.json())
    .then(data => {
      if (data.retcode != 0) {
        notify(data.msg);
        return;
      }
      return data.data;
    })
    .catch(error => {
      console.error('请求错误:', error);
      notify('请求错误:' + error);
    });
  }

  // 调整小班页面显示
  function toggle_group_display(show) {
    if (show) {
      document.querySelectorAll('.loading-text').forEach((e)=>{
        e.classList.add('hide');
      });
      document.querySelectorAll('#group_filter').forEach((e)=>{
        e.classList.remove('hide');
      });
      document.querySelectorAll('.group').forEach((e)=>{
        e.classList.remove('hide');
      });
    } else {
      document.querySelectorAll('.loading-text').forEach((e)=>{
        e.classList.remove('hide');
      });
      document.querySelectorAll('#group_filter').forEach((e)=>{
        e.classList.add('hide');
      });
      document.querySelectorAll('.group').forEach((e)=>{
        e.classList.add('hide');
      });
    }
  }

  // 获取小班信息
  function getGroupList(cache_all=false) {
    toggle_group_display(show=false);
    let url = 'observe_group';
    if (cache_all) {
      url += '?cache_all=' + cache_all
    }
    return fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.retcode != 0) {
        notify(data.msg);
        return;
      }
      let groups = data.data;
      document.getElementById('group_button').innerText = '小班列表(' + groups.length + ')';
      document.querySelectorAll('.group:not(.empty-group)').forEach((e)=>{
        e.remove();
      });
    //   let container = document.querySelector('.wall-container .group-page');
      let container = document.querySelector('.group-page');
      let empty_group = document.querySelector('.empty-group');
      let group_count = Object.keys(groups).length;
      let group_filter = document.getElementById('group_filter');
      if (group_count >= 10) {
        group_filter.classList.remove('hide');
      } else {
        group_filter.classList.add('hide');
      }
      for (let i in groups) {
        let group = groups[i];
        let favorite_checked = '';
        if (group.favorite) {
          favorite_checked = 'checked';
        }
        let group_content = `
          <div class="info-table">
            <div class="avatar">
              <img src="https://vol-v6.bczcdn.com`+group.avatar+`" />
              <img src="`+group.avatar_frame+`" />
            </div>
            <div class="group-info">
              <span>`+group.name+`</span>
              <span>`+group.today_daka_count+`/`+group.member_count+`已打卡</span>
            </div>
          </div>
          <div class="door">
            <div class="door-glass"></div>
            <div class="door-knob"></div>
            <img class="rank-flag" src="img/s`+group.rank+`.png"/>
          </div>
          <span class="group-favorite `+favorite_checked+`" onclick="addFavorite(event, '`+group.name+`', '`+group.id+`')" >★</span>
        `
        let group_div = document.createElement('div');
        group_div.className = 'group';
        if (group.valid == 2) {
          // notify('小班'+group.name+'的数据获取失败! \n原因为: '+group.exception);
          group_div.className += ' invalid';
        }
        group_div.innerHTML = group_content;
        group_div.addEventListener('click', (e)=>{
        if (e?.target) {
          if (e?.target.classList.contains('group-favorite')) {
            return;
          }
        }
        SwitchRight('group-detail-page')
        initGroupDetails(group.id);
        });
        container.insertBefore(group_div, empty_group);
      }
      toggle_group_display(show=true);
      return true;
    })
    .catch(error => {
      console.error('请求错误:', error);
      notify('请求错误:' + error);
    });
  }

  // 打开关闭小班搜索模态框
  function toggleGroupSearchModal(event) {
    if (event?.target) {
      if (event?.target.id != 'group_search_modal') {
        return;
      }
    }
    let modal = document.getElementById('group_search_modal');
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

  // 搜索小班
  function searchGroups() {
    let search_text = document.getElementById('group_search_input').value;
    let container = document.getElementById('group_result');
    let result_span = document.querySelector('#group_result>span');
    let url = 'search_group';
    if (isNaN(search_text) && search_text.length == 16) {
      url += '?share_key=' + search_text;
    } else if (search_text.length) {
      url += '?uid=' + search_text;
    } else {
      notify('搜索条件不能为空(*/ω＼*)');
      return;
    }
    container.innerHTML = 
      `
        <span class="loading-text">
          <div class="loader">
            <span></span>
            <span></span>
            <span></span>
          </div>
          数据获取中，请稍后...
        </span>
      `;
    fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.retcode != 0) {
        container.innerHTML = '<span>空空如也~</span>';
        notify(data.msg);
        return;
      }
      document.querySelector('#group_result>span')?.remove();
      let groups = data.data;
      container.innerHTML = '';
      for (let i in groups) {
        let group = groups[i];
        let badges = '';
        if (group.leader === true) {
          badges += '<span class="badge green-border">班长</span>';
        } else if (group.leader === false) {
          badges += '<span class="badge blue-border">成员</span>';
        }
        let group_content = `
          <div class="info-table">
            <div class="avatar">
              <img src="https://vol-v6.bczcdn.com`+group.avatar+`" />
              <img src="`+group.avatar_frame+`" />
            </div>
            <div class="group-info">
              <span>`+group.name+`</span>
              <span>小班ID: `+group.id+`</span>
            </div>
            <div class="group-detail">
              <span>人数`+group.member_count+`/`+group.count_limit+`, 完成率`+Math.round(group.finishing_rate * 100)+`%</span>
              <span>`+group.introduction+`</span>
            </div>
            <div class="group-extra">
              `+badges+`
            </div>
          </div>
        `
        let group_div = document.createElement('div');
        group_div.className = 'group brief';
        group_div.innerHTML = group_content;
        group_div.addEventListener('click', ()=>{
          addObserveGroup(group);
        });
        container.appendChild(group_div);
      }
      if (container.innerHTML == '') {
        container.innerHTML = '<span>空空如也~</span>';
      }
      return true;
    })
    .catch(error => {
      console.error('请求错误:', error);
      notify('请求错误:' + error);
      container.innerHTML = '<span>空空如也~</span>';
    });
  }

  // 事件触发搜索
  function eventSearch(event) {
    if (event.key === "Enter") {
      searchGroups(event?.target?.value);
    }
  }

  // 添加关注小班
  function addObserveGroup(group) {
    let content = `
      <line>是否添加此小班?</line>
      <div class="modal-text">`
        + `\n小班名称: ` + group.name
        + `\n小班ID: ` + group.id
        + `\n分享码: ` + group.share_key
        + `</div>`;
    showModal(content, '添加小班', ()=>{
      let payload = {'share_key': group.share_key};
      fetch('observe_group', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        notify(data.msg);
      });
    });
  }

  // 收藏小班
  function addFavorite(event, group_name, group_id) {
    let element = event.target;
    let content = `<line>是否收藏小班[`+group_name+`]?</line><line>收藏后即可显示在最上端</line>`;
    let favorite = 1;
    if (element.classList.contains('checked')) {
      content = `<line>是否取消收藏小班[`+group_name+`]?`;
      favorite = 0;
    }
    showModal(content, '收藏小班', ()=>{
      let payload = {'id': group_id, 'favorite': favorite};
      fetch('observe_group', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        notify(data.msg);
      });
    });
  }

  // 筛选小班
  function groupFilter(event) {
    let element = event.target;
    let filter = element.value;
    document.querySelectorAll('.group:not(.empty-group)').forEach((e)=>{
      if (e.innerText.includes(filter)) {
        e.classList.remove('hide');
      } else {
        e.classList.add('hide');
      }
    });
  }

  // 刷新全部小班数据
  function refresh_data() {
    showModal('是否为当前页面全部小班获取最新数据?', '刷新全部', ()=>{
      getGroupList(true);
    });
  }
