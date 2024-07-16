let page_num = 0
    let page_max = 0
    let observe_groups = [];

    function initDataPage(){
      getInfo_2()
      .then((result)=>{
        if (!result) return;
        return getSearchOption();
      })
      .then(()=>{
        return queryMemberTable();
      })
      .then(()=>{
        document.querySelectorAll('.data-page').forEach((e)=>{
          e.classList.remove('hide');
        });
        document.querySelectorAll('.loading-text').forEach((e)=>{
          e.classList.add('hide');
        });
        document.querySelectorAll('.blackboard').forEach((e)=>{
          e.classList.remove('hide');
        });
        document.querySelectorAll('.data-container').forEach((e)=>{
          e.classList.remove('hide');
        });
      });
      bindScrollToTopBtn(document.querySelector('.data-page'));
    }

    // 获取数据查询信息
    function getInfo_2() {
      return fetch('get_data_info')
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let info = data.data;
        let status_text = document.querySelector('#status_text');
        let status_content = '';
        if (info.token_valid) {
          let observe_group_count = 0;
          for (let i in info.groups) {
            if (info.groups[i].daily_record) {
              observe_group_count += 1
            }
          }
          observe_groups = info.groups;
          status_content = `
            <line>运行状况: 已持续记录`+info.running_days+`天</line>
            <line>数据统计: 记录数据共`+info.count+`条</line>
            <line>授权用户: `+info.name+`(`+info.uid+`)</line>
            <line>监控小班: `+observe_group_count+`个<u onclick="show_observe_groups()">[详情]</u></line>
          `;
        } else {
          status_content = `
            <line>运行状况: 已持续记录`+info.running_days+`天</line>
            <line>授权用户: 授权失效! 请及时处理, 否则无法正常记录!</line>
          `;
        }
        status_text.innerHTML = status_content;
        return true;
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
        let status_text = document.querySelector('#status_text');
        status_text.innerHTML = '';
      });
    }

    // 展示关注小班
    function show_observe_groups() {
      let content =  '<div class="start scroll-auto">';
      for (let i in observe_groups) {
        let group = observe_groups[i];
        content += ' <line><a href="group/'+group.id+'">'+group.name+'</a>'
        if (group.daily_record) {
          content += '<b class="float-right">已开启</b>';
        } else {
          content += '<b class="float-right">未开启</b>';
        }
        content += '</line>';
      }
        content += '</div>';
      showModal(content, '每日记录状态');
    }

    // 获取筛选选项
    function getSearchOption() {
      return fetch('get_search_option')
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let groups = data.data.groups;
        let group_id_select = document.querySelector('#group_id_select');
        for(let item in groups) {
          let option = document.createElement('option');
          option.value = groups[item][0];
          option.text = groups[item][1];
          group_id_select.add(option);
        }
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 通过内容生成请求体
    function buildPayload(page=true) {
      let group_id = document.getElementById('group_id_select').value;
      let group_name = document.getElementById('group_name_input').value;
      let sdate = document.getElementById('sdate_select').value;
      let edate = document.getElementById('edate_select').value;
      let cheat = document.getElementById('cheat_select').value;
      let completed_time = document.getElementById('completed_time_select').value;
      let user_id = document.getElementById('user_id_input').value;
      let nickname = document.getElementById('nickname_input').value;
      let payload = {
        'group_id': group_id,
        'group_name': group_name,
        'sdate': sdate,
        'edate': edate,
        'cheat': cheat,
        'completed_time': completed_time,
        'user_id': user_id,
        'nickname': nickname,
      }
      if (page) {
        let page_count = document.getElementById('page_count').value;
        payload.page_num = page_num
        payload.page_count = parseInt(page_count)
      }
      return payload
    }

    // 重置搜索条件
    function resetSearch() {
      document.getElementById('group_id_select').value = '';
      document.getElementById('group_name_input').value = '';
      document.getElementById('sdate_select').value = '';
      document.getElementById('edate_select').value = '';
      document.getElementById('cheat_select').value = '';
      document.getElementById('completed_time_select').value = '';
      document.getElementById('user_id_input').value = '';
      document.getElementById('nickname_input').value = '';
    }

    // 事件触发搜索
    function eventSearch(event) {
      if (event.key === "Enter" || event.type === 'blur') {
        queryMemberTable(event?.target?.value);
      }
    }

    // 用户信息表查询
    function queryMemberTable(option=null) {
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
      let payload = buildPayload()
      return fetch('query_member_table', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => {
        return response.json();
      })
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        let result = data.data;
        let count = result.count;
        page_max = result.page_max;
        page_num = result.page_num;
        document.querySelectorAll('.page-count').forEach((e)=>{
          e.innerHTML = `
            <input type="text" value= "${page_num}"
              style="margin-right: 0.2rem; width: ${(page_num.toString().length * 8) + 'px'}"
              oninput="this.style.width = (this.value.length * 8) + 'px'"
              onkeypress="eventSearch(event)"
              onblur="eventSearch(event)"
            />/${page_max}
          `
        });
        let table_data = result.data;
        let table = document.getElementById("user_info_table");
        table.innerHTML = '';
        fillDataToTable(table_data, table);
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 下载数据
    function downloadMemberTable(event) {
      let element = event.target;
      if (element.classList.contains('disabled')) {
        notify('点太快了，休息一下吧~');
        return;
      }
      element.classList.add('disabled');
      notify('正在下载中...请稍后...');
      payload = buildPayload(page=false)
      fetch('download', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      .then(response => {
        const contentType = response.headers.get("Content-Type");
        if (contentType.includes("application/json")) {
          return response.json()
          .then(data => {
            notify(data?.msg);
          });
        } else {
          return response.blob()
          .then(data => {
            const link = document.createElement('a');
            const dispositionHeader = response.headers.get('Content-Disposition');
            const filename = decodeURIComponent(dispositionHeader.split("UTF-8''").pop());
            link.href = URL.createObjectURL(data);
            link.download = filename;
            link.click();
          });
        }
      })
      .catch(error => {
        notify('下载出错! ' + error);
        console.error(error);
      })
      .finally(() => {
        element.classList.remove('disabled');
      });
    }