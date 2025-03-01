// 增加获取周数函数
Date.prototype.getWeek = function() {
    const currentDate = new Date(this.getFullYear(), this.getMonth(), this.getDate());
    const startOfYear = new Date(this.getFullYear(), 0, 1);
    const startDay = (startOfYear.getDay() || 7) - 1;
    const startOfFirstWeek = new Date(this.getFullYear(), 0, 1 - startDay);
    const diffInMilliseconds = currentDate - startOfFirstWeek;
    const diffInDays = diffInMilliseconds / (1000 * 60 * 60 * 24);
    return Math.ceil((diffInDays + 1) / 7);
};
Date.prototype.getISOWeek = function () {
  const currentDate = new Date(this.getFullYear(), this.getMonth(), this.getDate());
  currentDate.setHours(0, 0, 0, 0);
  currentDate.setDate(currentDate.getDate() + 4 - (currentDate.getDay() || 7));
  const yearStart = new Date(currentDate.getFullYear(), 0, 1);
  const weekNumber = Math.ceil(((currentDate - yearStart) / 86400000 + 1) / 7);
  return weekNumber;
};
Date.prototype.getISOYear = function () {
  const currentDate = new Date(this.getFullYear(), this.getMonth(), this.getDate());
  currentDate.setDate(currentDate.getDate() + 4 - (currentDate.getDay() || 7));
  return currentDate.getFullYear();
};

// 初始化云层
function initCloud(cloud_num) {
  const cloud_array = Array.from({ length: cloud_num }, () =>
    generateCloud(Math.round(Math.random()))
  );
  const cloud_container = document.getElementById("cloud_container");
  const windowHeight = window.innerHeight * 0.3;
  const windowWidth = window.innerWidth * 2;
  cloud_array.forEach((cloud) => {
    cloud.style.top = `${Math.random() * windowHeight}px`;
    cloud.style.left = `${(Math.random() - 0.25) * windowWidth}px`;
    if (Math.round(Math.random())) {
      cloud.style.transform = "scaleX(-1)";
    }
    let duration = Math.floor(Math.random() * 20) + 30;
    if (cloud.style.left > windowWidth) {
      cloud.style.animation =
        "swing-left " + duration + "s ease-in-out infinite alternate";
    } else if (cloud.style.left < 0) {
      cloud.style.animation =
        "swing-right " + duration + "s ease-in-out infinite alternate";
    } else if (Math.round(Math.random())) {
      cloud.style.animation =
        "swing-left " + duration + "s ease-in-out infinite alternate";
    } else {
      cloud.style.animation =
        "swing-right " + duration + "s ease-in-out infinite alternate";
    }
    cloud_container.appendChild(cloud);
  });
}

// 生成单个云朵
function generateCloud(cloud_type) {
  let cloud_content = `
    <span class="cloud-border">
    <span></span><span></span><span></span><span></span><span></span>
    </span>
    <span class="cloud-body">
    <span></span><span></span><span></span><span></span><span></span>
    </span>
`;
  let cloud = document.createElement("div");
  cloud.innerHTML = cloud_content;
  if (cloud_type) {
    cloud.className = "cloud-one";
  } else {
    cloud.className = "cloud-two";
  }
  return cloud;
}

// 把数据插入到表中
function fillDataToTable(table_data, table) {
  let thead = table.createTHead();
  var row = thead.insertRow();
  for (var i = 0; i < table_data[0].length; i++) {
    var th = document.createElement("th");
    th.innerHTML = table_data[0][i];
    row.appendChild(th);
  }
  table.appendChild(thead);

  document.querySelectorAll('th').forEach((th)=>{
    th.style.cursor = 'pointer';
    th.onclick = (e)=>{
      sortTable(e.target);
    }
  });

  let tbody = document.createElement("tbody");
  for (let i = 1; i < table_data.length; i++) {
    let row = tbody.insertRow(-1);
    for (let j = 0; j < table_data[i].length; j++) {
      let cell = row.insertCell(j);
      cell.innerHTML = table_data[i][j];
    }
  }
  table.appendChild(tbody);
}

// 输入表格的一个表头元素,以这个表头对表进行排序
function sortTable(element) {
  let index = Array.from(element.parentNode.children).indexOf(element);
  let table = element.parentNode.parentNode.parentNode;
  let tbody = table.children[1];
  let order = "asc";

  if (element.classList.contains("desc")) {
    element.classList.remove("desc");
    element.classList.add("asc");
    order = "asc";
    element.innerHTML = element.innerHTML.replace("▲", "▼");
  } else if (element.classList.contains("asc")) {
    element.classList.add("desc");
    element.classList.remove("asc");
    order = "desc";
    element.innerHTML = element.innerHTML.replace("▼", "▲");
  } else {
    Array.from(tbody.children[0].children).forEach((e) => {
      if (e.tagName === "TH") {
        e.classList.remove("asc");
        e.classList.remove("desc");
        e.innerHTML = e.innerHTML.replace(/▼|▲/g, "");
      }
    });
    element.classList.add("asc");
    element.innerHTML = element.innerHTML + "▼";
  }

  let td_arr = [];
  let row_count = tbody.rows.length;
  for (let i = 0; i < row_count; i++) {
    let cell = tbody.rows[i].cells[index].innerHTML;
    td_arr.push(cell);
  }

  let is_all_numbers = td_arr.every((str) => !isNaN(Number(str)));
  if (is_all_numbers) {
    td_arr = td_arr.map((str) => Number(str));
  }

  for (let i = 0; i < row_count - 1; i++) {
    for (let j = 0; j < row_count - 1 - i; j++) {
      if (order == "asc") {
        if (td_arr[j] < td_arr[j + 1]) {
          let temp = td_arr[j];
          td_arr[j] = td_arr[j + 1];
          td_arr[j + 1] = temp;
        }
      } else {
        if (td_arr[j] > td_arr[j + 1]) {
          let temp = td_arr[j];
          td_arr[j] = td_arr[j + 1];
          td_arr[j + 1] = temp;
        }
      }
    }
  }

  for (let item in td_arr) {
    for (let i = item; i < row_count; i++) {
      if (tbody.rows[i].cells[index].innerHTML == td_arr[item]) {
        tbody.insertBefore(tbody.rows[i], tbody.rows[parseInt(item)]);
        continue;
      }
    }
  }
}

// 给元素添加摇摆动画
function sway(event) {
  let element = event.target;
  if (element.classList.contains("sway")) {
    return;
  }
  setTimeout(()=>{
    element.classList.add('sway');
  },1)
  setTimeout(()=>{
    element.classList.remove('sway');
  },1000)
}

// 给元素添加旋转动画
function rotate(event) {
  let element = event.target;
  if (element.classList.contains("rotate")) {
    return;
  }
  setTimeout(()=>{
    element.classList.add('rotate');
  },1)
  setTimeout(()=>{
    element.classList.remove('rotate');
  },1000)
}

// 给元素添加左滑动画
function slideLeft(event) {
  let element = event.target;
  if (element.classList.contains("slideLeft")) {
    return;
  }
  setTimeout(()=>{
    element.classList.add('slideLeft');
  },1)
  setTimeout(()=>{
    element.classList.remove('slideLeft');
  },1000)
}

// 弹窗提示
function notify(content, delay=5000) {
  if (!document.getElementById('notify_container')) {
    let notify_container = document.createElement('div');
    notify_container.id = 'notify_container';
    document.body.appendChild(notify_container, document.body.lastChild);
  }
  const container = document?.getElementById("notify_container");
  if (!container) {
    alert(content);
    return;
  }
  const notification = document.createElement("div");
  notification.classList.add("notification", "fade-in");
  notification.textContent = content;
  container.appendChild(notification);
  setTimeout(() => {
    notification.classList.remove("fade-in");
    notification.classList.add("fade-out");
    setTimeout(() => {
      container.removeChild(notification);
    }, 800);
  }, delay);
}

// 展示模态框
function showModal(content='', title='', callback=null) {
  let timestamp = Date.now();
  let modal_content = document.createElement('div');
  modal_content.className = 'modal-content';
  let modal_close_btn = document.createElement('span');
  modal_close_btn.className = 'modal-close-btn';
  modal_close_btn.onclick = ()=>{toggleModal(null, 'modal-' + timestamp)};
  modal_content.appendChild(modal_close_btn, null);
  let modal_title = document.createElement('div');
  modal_title.className = 'modal-title';
  modal_title.innerHTML = title;
  modal_content.appendChild(modal_title, null);
  let modal_body = document.createElement('div');
  modal_body.className = 'modal-body';
  modal_body.innerHTML = content;
  modal_content.appendChild(modal_body, null);
  let modal_footer = document.createElement('div');
  modal_footer.className = 'modal-footer';
  modal_content.appendChild(modal_footer, null);

  let modal = document.createElement('div');
  modal.className = 'modal hide';
  modal.id = 'modal-' + timestamp;
  modal.setAttribute('data-status', 'hidden');
  modal.onclick = (event) =>{toggleModal(event, 'modal-' + timestamp)};
  modal.appendChild(modal_content, null);
  document.body.appendChild(modal, null);

  if (callback) {
    let confirm_btn = document.createElement('div');
    confirm_btn.className = 'btn';
    confirm_btn.innerText = '确认';
    confirm_btn.onclick = (event) =>{toggleModal(null, 'modal-' + timestamp);callback(event)};
    let deny_btn = document.createElement('div');
    deny_btn.className = 'btn';
    deny_btn.innerText = '取消';
    deny_btn.onclick = ()=>{toggleModal(null, 'modal-' + timestamp)};
    modal_footer.appendChild(confirm_btn, null);
    modal_footer.insertBefore(deny_btn, null);
  }
  toggleModal(null, 'modal-' + timestamp);
}

// 打开关闭模态框
function toggleModal(event, modal_id='') {
  if (event?.target) {
    if (!event?.target.classList.contains('modal')) {
      return;
    }
  }
  let modal_pattern = '.modal';
  if (modal_id) {
    modal_pattern += '#' + modal_id;
  }
  document.querySelectorAll(modal_pattern).forEach((modal)=>{
    if (modal_id == '' && modal.id != '') {
      return;
    }
    let modal_content = modal.children[0];
    let status = modal.getAttribute('data-status');
    modal.setAttribute('data-status', '');
    if (status == 'show') {
      modal_content.style.transform = 'scale(0.9)';
      modal.style.opacity = 0;
      setTimeout(()=>{
        modal.classList.add('hide');
        modal.setAttribute('data-status', 'hidden');
        modal.remove();
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
  })
}

// 为元素绑定返回顶部按钮
function bindScrollToTopBtn(element) {
  let scroll_to_top_btn = document.createElement('div');
  scroll_to_top_btn.id = 'scroll_top_btn';
  scroll_to_top_btn.title = '回到顶部';
  scroll_to_top_btn.innerText = '▲';
  document.body.appendChild(scroll_to_top_btn, document.body.lastChild);
  element.onscroll = () => {
    if (element.scrollTop > element.clientHeight * 1.5) {
      document.getElementById("scroll_top_btn").classList.add('show');
    } else {
      document.getElementById("scroll_top_btn").classList.remove('show');
    }
  }
  scroll_to_top_btn.onclick = () => {
    element.scrollTo({top: 0, behavior: "smooth" });
  };

}