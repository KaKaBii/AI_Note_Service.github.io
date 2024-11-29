// 當頁面加載時獲取逐字稿列表
document.addEventListener('DOMContentLoaded', () => {
    const pageTitle = document.getElementById('toggleHeader');
    fetchTranscriptsByPerson(pageTitle.textContent);

    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadRecord();  // 確保有選擇文件後再上傳
        }
        else{
            console.log('沒有選擇檔案');
        }
    });
});

// 錄音功能
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

// 下一頁
document.getElementById("next-page").addEventListener("click", () => {
    console.log('Navigating to class.html');
    window.location.href = '/classify'; // 指向 Flask 路由
});

// 觸發上傳錄音檔按鈕
function triggerFileInput() {
    if (event) {
        event.preventDefault(); // 阻止默認的表單提交行為
    }
    const fileInput = document.getElementById('file-input');
    fileInput.click();
    //console.log('文件選擇窗口已打開');
}

//上傳錄音檔
function uploadRecord() {
    //console.log('執行 uploadRecord');
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) {
        alert('請選擇要上傳的檔案');
        return;
    }

    //前端檢查文件類型
    // const allowedExtensions = ['wav', 'mp3'];
    // const fileExtension = file.name.split('.').pop().toLowerCase();

    // if (!allowedExtensions.includes(fileExtension)) {
    //     alert('不支持的文件類型，請選擇 WAV 或 MP3 格式的文件');
    //     return;
    // }

    const formData = new FormData();
    formData.append('file', file);
    
    const personName = document.getElementById('toggleHeader').textContent.trim();
    formData.append('user', personName)
    fetch(`/uploadRecord?name=${personName}`, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            alert('檔案上傳成功');
            fetchTranscriptsByPerson(personName); // 上傳後更新逐字稿顯示
        } else {
            return response.json().then(data => {
                alert(`檔案上傳失敗：${data.message}`);
            });
        }
    })
    .catch(error => {
        console.error('上傳過程中發生錯誤:', error);
        alert('上傳過程中發生錯誤，請再試一次');
    });
}

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
                    addNewButton.style.display = 'none';
                    addNewButton.onclick = () => addNewName();
                    buttonList.appendChild(addNewButton);
                }
                else{
                    addNewButton.style.display = 'none';
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
        if(button.textContent.trim().toLowerCase() == filterValue){
            found = true; // 找到完全匹配的值
        }
        } else {
            button.style.display = 'none';
        }

    });
    
    // 如果輸入框沒有內容，僅隱藏「新增」按鈕，並退出函式
    if (filterValue === '') {
        console.log('Input is empty. Hiding add new button.');
        addNewButtonIfNoneFound(true); // 隱藏新增按鈕
        return;
    }
    console.log('Found any matching buttons:', found);
    addNewButtonIfNoneFound(found);
}

// 添加 "新增" 按鈕如果未找到結果
function addNewButtonIfNoneFound(found = false) {
  //console.log('Checking if need to add new button. Found:', found);
  const addNewButton = document.getElementById('addNewButton');
  if (addNewButton) {
      if (!found) {
          console.log('No matching names found. Displaying add new button.');
          addNewButton.style.display = 'block';
      } else {
          //console.log('Matching names found. Hiding add new button.');
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

// 切換個案
function SwitchIndivisual(name) {
  const toggleHeader = document.getElementById('toggleHeader');
  if (toggleHeader) {
      console.log(`Switching to individual: ${name}`);
      // 更改首頁的 toggle header 名稱
      toggleHeader.textContent = name;
      fetchTranscriptsByPerson(name);
  }
} 

// 用於獲取逐字稿的函數
function fetchTranscriptsByPerson(personName) {
    console.log(`Fetching transcripts for: ${personName}`);
    fetch(`/fetchTranscripts?person=${personName}`)
        .then(response => {
            console.log(`Response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('Transcripts data received:', data);
            const container = document.getElementById('transcripts-container');
            
            if (container) {  // 確保元素存在
                container.innerHTML = ''; //清空
                data.forEach((transcriptObj, index) => {
                    console.log(`Rendering transcript ${index + 1}:`, transcriptObj);
                    const transcriptDiv = document.createElement('div');
                    transcriptDiv.className = 'transcript';

                    // 添加 timestamp
                    const timestampDiv = document.createElement('div');
                    timestampDiv.className = 'transcript-timestamp';
                    timestampDiv.textContent = transcriptObj.timestamp;
                    transcriptDiv.appendChild(timestampDiv);

                    // 添加 transcript 內容
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'transcript-content';

                    // 使用 innerHTML 並將換行符號 \n 替換為 <br>
                    const formattedContent = transcriptObj.content.replace(/\n/g, '<br>');
                    contentDiv.innerHTML = formattedContent;

                    transcriptDiv.appendChild(contentDiv);

                    // 編輯和刪除按鈕容器
                    const buttonContainer = document.createElement('div');
                    buttonContainer.className = 'button-container';
                    buttonContainer.style.display = 'none';
                    transcriptDiv.appendChild(buttonContainer);

                    // 編輯按鈕
                    const editButton = document.createElement('button');
                    editButton.textContent = '編輯';
                    editButton.className = 'edit-button green';
                    editButton.onclick = () => editTranscript(transcriptObj, contentDiv);
                    buttonContainer.appendChild(editButton);

                    // 刪除按鈕
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = '刪除';
                    deleteButton.className = 'delete-button red';
                    deleteButton.onclick = () => deleteTranscript(transcriptObj.timestamp);
                    buttonContainer.appendChild(deleteButton);

                    // 滑鼠移入顯示編輯和刪除按鈕
                    transcriptDiv.addEventListener('mouseenter', () => {
                        buttonContainer.style.display = 'block';
                    });

                    // 滑鼠移出隱藏編輯和刪除按鈕
                    transcriptDiv.addEventListener('mouseleave', () => {
                        buttonContainer.style.display = 'none';
                    });

                    container.appendChild(transcriptDiv);
                });
                // 添加輸入框和上傳按鈕的包裝區塊
                const inputContainer = document.createElement('div');
                inputContainer.className = 'filter-input';

                // 輸入框
                const transcriptInput = document.createElement('textarea');
                transcriptInput.id = 'transcript-input';
                transcriptInput.placeholder = '輸入逐字稿內容...';
                transcriptInput.className = 'transcript-input';
                inputContainer.appendChild(transcriptInput);

                // 上傳按鈕
                const uploadButton = document.createElement('button');
                uploadButton.textContent = '上傳';
                uploadButton.className = 'btn upload-button blue';
                uploadButton.onclick = uploadTranscript;
                inputContainer.appendChild(uploadButton);

                container.appendChild(inputContainer);
            } else {
                console.error("Element with ID 'text-container' not found.");
            }
        })
        .catch(error => console.error('Error fetching transcripts:', error));
}

// 用於新增逐字稿的函數
function uploadTranscript(){
    console.log('Uploading transcript...');
    const transcriptInput = document.getElementById('transcript-input');
    const personName = document.getElementById('toggleHeader').textContent.trim();

    if (transcriptInput && personName) {
        const transcriptContent = transcriptInput.value.trim();
        if (transcriptContent) {
            fetch(`/uploadTranscript?name=${personName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: personName,
                    content: transcriptContent
                })
            })
            .then(response => {
                console.log(`Response status: ${response.status}`);
                if (response.ok) {
                    console.log('Transcript successfully uploaded');
                    alert('逐字稿上傳成功');
                    fetchTranscriptsByPerson(personName); // 上傳後更新逐字稿顯示
                } else {
                    console.error('Failed to upload transcript');
                    alert('逐字稿上傳失敗，請重試');
                }
            })
            .catch(error => {
                console.error('Error uploading transcript:', error);
                alert('上傳過程中發生錯誤，請重試');
            });
        } else {
            alert('請輸入逐字稿內容後再上傳');
        }
    } else {
        console.error('Transcript input or person name is missing.');
    }
}

// 用於編輯逐字稿的函數
function editTranscript(transcriptObj, contentDiv) {
    const newContent = prompt('編輯逐字稿內容：', transcriptObj.content);
    if (newContent !== null) {
        fetch('/editTranscript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: transcriptObj.timestamp,
                newContent: newContent
            })
        })
        .then(response => {
            if (response.ok) {
                console.log('Transcript successfully edited');
                alert('逐字稿編輯成功');
                contentDiv.textContent = newContent;
            } else {
                console.error('Failed to edit transcript');
                alert('逐字稿編輯失敗，請重試');
            }
        })
        .catch(error => {
            console.error('Error editing transcript:', error);
            alert('編輯過程中發生錯誤，請重試');
        });
    }
}

// 用於刪除逐字稿的函數
function deleteTranscript(timestamp) {
    if (confirm('確定要刪除這條逐字稿嗎？')) {
        fetch('/deleteTranscript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: timestamp
            })
        })
        .then(response => {
            if (response.ok) {
                console.log('Transcript successfully deleted');
                alert('逐字稿刪除成功');
                fetchTranscriptsByPerson(document.getElementById('toggleHeader').textContent.trim()); // 刪除後重新加載逐字稿
            } else {
                console.error('Failed to delete transcript');
                alert('逐字稿刪除失敗，請重試');
            }
        })
        .catch(error => {
            console.error('Error deleting transcript:', error);
            alert('刪除過程中發生錯誤，請重試');
        });
    }
}
