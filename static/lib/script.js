function initCloud(cloud_num) {
  // 初始化云层
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

function generateCloud(cloud_type) {
  // 生成单个云朵
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

function sortTable(element) {
  // 输入表格的一个表头元素,以这个表头对表进行排序
  let index = Array.from(element.parentNode.children).indexOf(element);
  let table = element.parentNode.parentNode;
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
    Array.from(table.children[1].children).forEach((e) => {
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
  let row_count = table.rows.length;
  for (let i = 1; i < row_count; i++) {
    let cell = table.rows[i].cells[index].innerHTML;
    td_arr.push(cell);
  }

  let is_all_numbers = td_arr.every((str) => !isNaN(Number(str)));
  if (is_all_numbers) {
    td_arr = td_arr.map((str) => Number(str));
  }

  for (let i = 0; i < row_count - 2; i++) {
    for (let j = 0; j < row_count - 2 - i; j++) {
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
      if (table.rows[i].cells[index].innerHTML == td_arr[item]) {
        table.insertBefore(table.rows[i], table.rows[parseInt(item) + 1]);
        continue;
      }
    }
  }
}

function notify(content) {
  // 弹窗提示
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
