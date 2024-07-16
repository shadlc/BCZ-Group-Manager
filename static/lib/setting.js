let cache_second_input = document.getElementById('cache_second_input');
    let real_time_cache_favorite_true = document.getElementById('real_time_cache_favorite_true');
    let real_time_cache_favorite_false = document.getElementById('real_time_cache_favorite_false');
    let daily_record_input = document.getElementById('daily_record_input');
    let main_token_input = document.getElementById('main_token_input');
    let output_file_input = document.getElementById('output_file_input');
    let past_cache_second = "";
    let past_real_time_cache_favorite = "";
    let past_daily_record = "";
    let past_main_token = "";
    let past_output_file = "";
    function initSettingPage(second) {
      getConfig()
      .then((result)=>{
        if (!result) return;
        document.querySelectorAll('.loading-text').forEach((e)=>{
          e.classList.add('hide');
        });
        document.querySelectorAll('.container').forEach((e)=>{
          e.classList.remove('hide');
        });
      });
    }

    // 获取配置
    function getConfig() {
      return fetch('configure')
      .then(response => response.json())
      .then(data => {
        if (data.retcode != 0) {
          notify(data.msg);
          return;
        }
        past_cache_second = data.data.cache_second;
        cache_second_input.value = past_cache_second;
        past_real_time_cache_favorite = data.data.real_time_cache_favorite;
        if (data.data.real_time_cache_favorite) {
          real_time_cache_favorite_true.checked = true;
        } else {
          real_time_cache_favorite_false.checked = true;
        }
        past_daily_record = data.data.daily_record;
        daily_record_input.value = past_daily_record;
        past_main_token = data.data.main_token;
        main_token_input.value = past_main_token;
        past_output_file = data.data.output_file;
        output_file_input.value = past_output_file;
        return true;
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }

    // 修改配置
    function saveConfig() {
      showModal('确保设置无误？该操作不可逆', '修改配置', ()=>{
        if (past_main_token != main_token_input.value) {
          showModal('此次操作修改了授权令牌，请确认无误', '', ()=>{
            postConfig();
          })
        } else {
          postConfig();
        }
      })
    }

    // 发送修改配置请求
    function postConfig() {
      let payload = {};
      let cache_second = cache_second_input.value;
      let real_time_cache_favorite = document.querySelector('input[name=real_time_cache_favorite]:checked')?.value == 'true' ? true : false;
      let daily_record = daily_record_input.value;
      let main_token = main_token_input.value;
      let output_file = output_file_input.value;
      if (past_cache_second != cache_second) {
        payload.cache_second = cache_second;
        past_cache_second = cache_second;
      }
      if (past_real_time_cache_favorite != real_time_cache_favorite) {
        payload.real_time_cache_favorite = real_time_cache_favorite;
        past_real_time_cache_favorite = real_time_cache_favorite;
      }
      if (past_daily_record != daily_record) {
        payload.daily_record = daily_record;
        past_daily_record = daily_record;
      }
      if (past_main_token != main_token) {
        payload.main_token = main_token;
        past_main_token = main_token;
      }
      if (past_output_file != output_file) {
        payload.output_file = output_file;
        past_output_file = output_file;
      }
      return fetch('configure', {
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
        return true;
      })
      .catch(error => {
        console.error('请求错误:', error);
        notify('请求错误:' + error);
      });
    }
