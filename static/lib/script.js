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
function notify(content) {
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
  }, 3000);
}

// 展示模态框
function showModal(content='', title='') {
  document.querySelectorAll('.modal').forEach((modal)=>{
    if (modal.id == '') {
      modal.remove();
    }
  });
  let modal_content = `
    <div class="modal-content notice">
      <span class="modal-close-btn" onclick="toggleModal()"></span>
      <div class="modal-title">`+title+`</div>
      <div class="modal-body">`+content+`</div>
    </div>
  `
  let modal = document.createElement('div');
  modal.className = 'modal hide';
  modal.setAttribute('data-status', 'hidden');
  modal.onclick = (event) =>{toggleModal(event)};
  modal.innerHTML = modal_content;
  document.body.appendChild(modal, document.body.lastChild);
  toggleModal();
}

// 打开关闭模态框
function toggleModal(event) {
  if (event?.target) {
    if (!event?.target.classList.contains('modal')) {
      return;
    }
  }
  document.querySelectorAll('.modal').forEach((modal)=>{
    if (modal.id != '') {
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
