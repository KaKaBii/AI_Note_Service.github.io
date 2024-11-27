document.getElementById("start-recording").addEventListener("click", async () => {
  //alert("錄音功能尚未實作，這裡可連接語音轉文字服務。");
  try {
    // 呼叫 getUserMedia 獲取麥克風權限
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    alert("麥克風權限已授予，可以錄音！");
    console.log("Stream:", stream);

    // 停止使用流以釋放資源
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
  } catch (error) {
    console.error("麥克風權限錯誤:", error);
    alert(`麥克風權限錯誤：${error.message}`);
  }
});

document.getElementById("next-page").addEventListener("click", () => {
  window.location.href = "../templates/class.html";
});

// JavaScript 用於切換按鈕列表的顯示/隱藏
function toggleButtons() {
  const buttonList = document.getElementById('nameList1');
  if (buttonList.style.display === 'none' || buttonList.style.display === '') {
      buttonList.style.display = 'flex'; // 顯示按鈕列表和輸入框
      buttonList.style.flexDirection = 'column'; // 垂直排列按鈕
      fetchNameList(); // 只有顯示按鈕時才清單更新
  } else {
      buttonList.style.display = 'none'; // 隱藏按鈕列表和輸入框
  }
}

// 清單從後端源取按鈕
function fetchNameList() {
  console.log('Fetching name list...');
  fetch('/fetchNameList')
      .then(response => response.json())
      .then(data => {
          console.log('Name list fetched:', data);
          const buttonList = document.getElementById('nameList1');
          if (buttonList) {
              buttonList.innerHTML = '<input type="text" id="filterInput" class="filter-input" placeholder="輸入姓名進行篩選" oninput="filterNameList()">'; // 保留輸入框並清空之前的按鈕
              let addNewButton = document.getElementById('addNewButton');
              if (!addNewButton) {
                  addNewButton = document.createElement('button');
                  addNewButton.id = 'addNewButton';
                  addNewButton.textContent = '新增姓名';
                  addNewButton.className = 'add-name-button';
                  addNewButton.onclick = () => addNewName();
                  buttonList.appendChild(addNewButton);
              }
              let found = false;
              data.forEach(name => {
                  if (name.toLowerCase().includes(document.getElementById('filterInput').value.trim().toLowerCase())) {
                      found = true;
                      const button = document.createElement('button');
                      button.textContent = name;
                      button.onclick = () => SwitchIndivisual(name); // 添加 SwitchIndivisual 函數
                      buttonList.appendChild(button);
                  }
              });
              console.log('Found matching names:', found);
              addNewButtonIfNoneFound(found); // 在更新按鈕列表後檢查是否需要顯示新增按鈕
          }
      })
      .catch(error => console.error('Error fetching name list:', error));
}

// 根據輸入框的值進行篩選
function filterNameList() {
  const filterValue = document.getElementById('filterInput').value.trim().toLowerCase();
  console.log('Filtering name list with value:', filterValue);
  const buttons = document.querySelectorAll('#nameList1 button');
  let found = false;
  buttons.forEach(button => {
      if (button.textContent.toLowerCase().includes(filterValue)) {
          button.style.display = 'block';
          found = true;
      } else {
          button.style.display = 'none';
      }
  });
  console.log('Found any matching buttons:', found);
  addNewButtonIfNoneFound(found);
}

// 添加 "新增" 按鈕如果未找到結果
function addNewButtonIfNoneFound(found = false) {
  console.log('Checking if need to add new button. Found:', found);
  const addNewButton = document.getElementById('addNewButton');
  if (addNewButton) {
      if (!found) {
          console.log('No matching names found. Displaying add new button.');
          addNewButton.style.display = 'block';
      } else {
          console.log('Matching names found. Hiding add new button.');
          addNewButton.style.display = 'none';
      }
  }
  else{
    console.log('addNewButton does not exist.');
  }
}

// 新增姓名至資料庫
function addNewName() {
  const newName = document.getElementById('filterInput').value.trim();
  if (newName) {
      console.log('Adding new name to database:', newName);
      fetch('/addName', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: newName })
      })
      .then(response => {
          if (response.ok) {
              console.log(`Successfully added: ${newName}`);
              alert('新增成功');
              fetchNameList(); // 更新列表
          } else {
              console.error('Failed to add name');
              alert('新增失敗，請重試');
          }
      })
      .catch(error => {
          console.error('Error adding name:', error);
          alert('新增失敗，請重試');
      });
  }
}

// SwitchIndivisual 函數示例
function SwitchIndivisual(name) {
  const toggleHeader = document.getElementById('toggleHeader');
  if (toggleHeader) {
      console.log(`Switching to individual: ${name}`);
      // 更改首頁的 toggle header 名稱
      toggleHeader.textContent = name;
  }
} 
