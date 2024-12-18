// 切換按鈕列表顯示隱藏
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

// 顯示對應的分類後逐字稿
async function toggleList(containerId, categoryType) {
    const container = document.getElementById(containerId);

    if (container) {
        if (container.style.display === 'none') {
            try {
                // 等待分類內容數據加載
                const personName = document.getElementById('toggleHeader').textContent.trim();
                const data = await fetchClassifiedContent(personName, categoryType);
                
                // 根據 data 動態新增逐字稿內容
                container.innerHTML = ''; // 清空原有內容
                if (data.length > 0) {
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

                        container.appendChild(transcriptDiv);
                    })
                }
                else {
                    container.innerHTML = '<p>未找到符合條件的逐字稿。</p>';
                }
            container.style.display = 'block'; // 顯示列表
            } 
            catch (error) {
                console.error('Error fetching classified content:', error);
                alert('加載分類內容失敗，請稍後重試。');
            }
        }
        else {
            container.style.display = 'none'; // 隱藏列表
        }    
    } 
}

// 回到首頁
function navigateToRoot() {
    // 保存用戶名稱到 sessionStorage
    const userName = document.getElementById('toggleHeader').textContent.trim();
    sessionStorage.setItem('userName', userName); 

    // 當點擊分類按鈕時，會導向對應的分類頁面
    window.location.href = `/`;
}

// 切換個案
function SwitchIndivisual(name) {
    const toggleHeader = document.getElementById('toggleHeader');
    if (toggleHeader) {
        console.log(`Switching to individual: ${name}`);
        // 更改首頁的 toggle header 名稱
        toggleHeader.textContent = name;

        // 保存用戶名稱到 sessionStorage
        const userName = document.getElementById('toggleHeader').textContent.trim();
        localStorage.setItem('userName', userName); 
        
        // 獲取該個案的逐字稿
        //fetchTranscriptsByPerson(name);
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
                    
                data.forEach(name => {
                if (name.toLowerCase().includes(document.getElementById('filterInput').value.trim().toLowerCase())) {
                    found = true;
                    const button = document.createElement('button');
                    button.textContent = name;
                    button.onclick = () => SwitchIndivisual(name); // 添加 SwitchIndivisual 函數
                    buttonList.appendChild(button);
                }
                });
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

}

// 用於獲取逐字稿的函數
function fetchClassifiedContent(personName, categoryType) {
    return fetch(`/fetchClassifiedContent?person=${encodeURIComponent(personName)}&type=${encodeURIComponent(categoryType)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch classified content');
            }
            return response.json(); // 返回 JSON 數據
        })
        .catch(error => {
            console.error('Error:', error);
            alert('獲取分類內容時發生錯誤');
            return []; // 返回空數據
        });
}

// // 用於獲取逐字稿的函數
// function fetchClassifiedContent(personName, categoryType) {
//     console.log(`Fetching transcripts for: ${personName}`);
//     fetch(`/fetchClassifiedContent`)
//         .then(response => {
//             console.log(`Response status: ${response.status}`);
//             return response.json();
//         })
//         .then(data => {
//             console.log('Transcripts data received:', data);
//             const container = document.getElementById('transcripts-container');
            
//             if (container) {  // 確保元素存在
//                 container.innerHTML = ''; //清空
//                 data.forEach((transcriptObj, index) => {
//                     console.log(`Rendering transcript ${index + 1}:`, transcriptObj);
//                     const transcriptDiv = document.createElement('div');
//                     transcriptDiv.className = 'transcript';

//                     // 添加 timestamp
//                     const timestampDiv = document.createElement('div');
//                     timestampDiv.className = 'transcript-timestamp';
//                     timestampDiv.textContent = transcriptObj.timestamp;
//                     transcriptDiv.appendChild(timestampDiv);

//                     // 添加 transcript 內容
//                     const contentDiv = document.createElement('div');
//                     contentDiv.className = 'transcript-content';

//                     // 使用 innerHTML 並將換行符號 \n 替換為 <br>
//                     const formattedContent = transcriptObj.content.replace(/\n/g, '<br>');
//                     contentDiv.innerHTML = formattedContent;

//                     transcriptDiv.appendChild(contentDiv);
                    
//                     // 添加點擊事件以便直接編輯
//                     contentDiv.onclick = () => {
//                         // 設置為可編輯並獲取焦點
//                         contentDiv.contentEditable = "true";
//                         contentDiv.focus();

//                         // 修改按鈕為"確認"
//                         editButton.textContent = '確認';
//                         editButton.className = 'confirm-button blue';

//                         // 在內容上失去焦點時，保存變更
//                         contentDiv.onblur = () => {
//                             // 如果當前按鈕還是“確認”，則需要執行確認邏輯
//                             if (editButton.textContent === '確認') {
//                                 const newContent = contentDiv.innerHTML.replace(/<br>/g, '\n');
                                
//                                 // 檢查內容是否已修改
//                                 if (newContent === transcriptObj.content) {
//                                     // 如果內容沒有改變
//                                     //alert('內容沒有變更');
//                                     // 取消可編輯狀態
//                                     contentDiv.contentEditable = "false";

//                                     // 將按鈕改回"編輯"
//                                     editButton.textContent = '編輯';
//                                     editButton.className = 'edit-button green';

//                                     // 恢復按鈕的默認樣式
//                                     editButton.style.border = '';
//                                     editButton.style.outline = '';
//                                     return; // 不繼續發送請求
//                                 }

//                                 // 發送 fetch 請求
//                                 fetch('/editTranscript', {
//                                     method: 'POST',
//                                     headers: {
//                                         'Content-Type': 'application/json'
//                                     },
//                                     body: JSON.stringify({
//                                         timestamp: transcriptObj.timestamp,
//                                         newContent: newContent
//                                     })
//                                 })
//                                 .then(response => {
//                                     if (response.ok) {
//                                         console.log('Transcript successfully edited');
//                                         alert('逐字稿編輯成功');
//                                         // 取消可編輯狀態
//                                         contentDiv.contentEditable = "false";

//                                         // 更新顯示的內容
//                                         contentDiv.innerHTML = newContent.replace(/\n/g, '<br>');

//                                         // 將按鈕改回"編輯"
//                                         editButton.textContent = '編輯';
//                                         editButton.className = 'edit-button green';
//                                     } else {
//                                         console.error('Failed to edit transcript');
//                                         alert('逐字稿編輯失敗，請重試');
//                                     }
//                                 })
//                                 .catch(error => {
//                                     console.error('Error editing transcript:', error);
//                                     alert('編輯過程中發生錯誤，請重試');
//                                 });
//                             }
//                         };
//                     };

//                     // 編輯和刪除按鈕容器
//                     const buttonContainer = document.createElement('div');
//                     buttonContainer.className = 'button-container';
//                     buttonContainer.style.display = 'none';
//                     transcriptDiv.appendChild(buttonContainer);

//                     // 編輯按鈕
//                     const editButton = document.createElement('button');
//                     editButton.textContent = '編輯';
//                     editButton.className = 'edit-button green';
//                     editButton.onclick = () => {
//                         if (editButton.textContent === '編輯') {
//                             // 設置為可編輯並獲取焦點
//                             contentDiv.contentEditable = "true";
//                             contentDiv.focus();

//                             // 修改按鈕為"確認"
//                             editButton.textContent = '確認';
//                             editButton.className = 'confirm-button blue';
//                         } else {
//                             // 如果按鈕顯示"確認"，則保存更改並發送請求
//                             const newContent = contentDiv.innerHTML.replace(/<br>/g, '\n');
                            
//                             // 檢查內容是否已修改
//                             if (newContent === transcriptObj.content) {
//                                 // 如果內容沒有改變
//                                 alert('內容沒有變更');
//                                 // 取消可編輯狀態
//                                 contentDiv.contentEditable = "false";

//                                 // 將按鈕改回"編輯"
//                                 editButton.textContent = '編輯';
//                                 editButton.className = 'edit-button green';

//                                 // 恢復按鈕的默認樣式
//                                 editButton.style.border = '';
//                                 editButton.style.outline = '';
//                                 return; // 不繼續發送請求
//                             }
                            
//                             // 發送 fetch 請求
//                             fetch('/editTranscript', {
//                                 method: 'POST',
//                                 headers: {
//                                     'Content-Type': 'application/json'
//                                 },
//                                 body: JSON.stringify({
//                                     timestamp: transcriptObj.timestamp,
//                                     newContent: newContent
//                                 })
//                             })
//                             .then(response => {
//                                 if (response.ok) {
//                                     console.log('Transcript successfully edited');
//                                     alert('逐字稿編輯成功');
//                                     // 取消可編輯狀態
//                                     contentDiv.contentEditable = "false";

//                                     // 更新顯示的內容
//                                     contentDiv.innerHTML = newContent.replace(/\n/g, '<br>');

//                                     // 將按鈕改回"編輯"
//                                     editButton.textContent = '編輯';
//                                     editButton.className = 'edit-button green';
//                                 } else {
//                                     console.error('Failed to edit transcript');
//                                     alert('逐字稿編輯失敗，請重試');
//                                 }
//                             })
//                             .catch(error => {
//                                 console.error('Error editing transcript:', error);
//                                 alert('編輯過程中發生錯誤，請重試');
//                             });
//                         }
//                     };
//                     buttonContainer.appendChild(editButton);

//                     // 刪除按鈕
//                     const deleteButton = document.createElement('button');
//                     deleteButton.textContent = '刪除';
//                     deleteButton.className = 'delete-button red';
//                     deleteButton.onclick = () => deleteTranscript(transcriptObj.timestamp);
//                     buttonContainer.appendChild(deleteButton);

//                     // 滑鼠移入顯示編輯和刪除按鈕
//                     transcriptDiv.addEventListener('mouseenter', () => {
//                         buttonContainer.style.display = 'block';
//                     });

//                     // 滑鼠移出隱藏編輯和刪除按鈕
//                     transcriptDiv.addEventListener('mouseleave', () => {
//                         buttonContainer.style.display = 'none';
//                     });

//                     container.appendChild(transcriptDiv);
//                 });
//             } else {
//                 console.error("Element with ID 'text-container' not found.");
//             }
//         })
//         .catch(error => console.error('Error fetching transcripts:', error));
// }