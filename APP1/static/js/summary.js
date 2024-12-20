// 切換按鈕列表顯示隱藏
function toggleButtons() {
    const buttonList = document.getElementById('nameList1');
    if (buttonList.style.display === 'none' || buttonList.style.display === '') {
        buttonList.style.display = 'flex'; // 顯示按鈕列表和輸入框
        buttonList.style.flexDirection = 'column'; // 垂直排列按鈕
        fetchNameList(); // 只有顯示按鈕時才更新清單
    } else {
        buttonList.style.display = 'none'; // 隱藏按鈕列表和輸入框
    }
}
  
// 月分清單從後端獲取
// function fetchMonthList() {
//     console.log('Fetching month list...');
//     fetch('/fetchMonthList')
//         .then(response => response.json())
//             .then(data => {
//                 console.log('Month list fetched:', data);
//                 const monthList = document.getElementById('monthList');
//                 if (monthList) {
//                     data.forEach(month => {
//                         const label = document.createElement('label');
//                         label.textContent = month;
//                         monthList.appendChild(label);
//                     });
//                 }
//             })
//         .catch(error => console.error('Error fetching name list:', error));
// }

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
        
        // 更新總結報告
        fetchSummaryContent();
    }
} 

// 用於獲取逐字稿的函數
function fetchSummaryContent() {
    const userName = document.getElementById('toggleHeader').textContent.trim();
    console.log(`Fetching summary content for: ${userName}`);
    
    fetch(`/fetchSummaryContent?person=${encodeURIComponent(userName)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch summary content');
            }
            return response.json(); // 返回 JSON 數據
        })
        .then(data => {
            console.log('summary content data received:', data);
            const container = document.getElementById('summaryContent-container');
            if (container) {  // 確保元素存在
                container.innerHTML = ''; //清空
                if (data.length > 0) {
                    data.forEach((transcriptObj, index) => {
                        console.log(`Rendering summary content ${index + 1}:`, transcriptObj);
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
                else{
                    container.innerHTML = '<p>未找到符合的總結報告</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('獲取總結報告時發生錯誤');
        });
}

// 當頁面加載時獲取逐字稿列表
document.addEventListener('DOMContentLoaded', () => {
    // fetchSummaryContent();
    fetchMonthList();
    // 更新總結報告
    fetchSummaryContent();
});

function fetchMonthList() {
    console.log('Fetching month list...');
    const userName = document.getElementById('toggleHeader').textContent.trim();
    fetch(`/fetchMonthList?person=${encodeURIComponent(userName)}`)
        .then(response => response.json())
            .then(data => {
                console.log('Month list fetched:', data);
                const monthList = document.getElementById('monthList');
                if (monthList) {
                    data.forEach(month => {
                        const label = document.createElement('option');
                        label.textContent = month;
                        monthList.appendChild(label);
                    });
                }
            })
        .catch(error => console.error('Error fetching name list:', error));
}

function generateSummary(name, month){
    console.log('Generating summary for:', name, month);
    fetch(`/generateSummaryContent?person=${encodeURIComponent(name)}&month=${encodeURIComponent(month)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to generate summary');
            }
            return response.json();
        })
        .then(data => {
            console.log('Summary generated:', data);
            alert('總結報告已生成');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('生成總結報告時發生錯誤');
        });
}

async function submitForm() {
    const monthList = document.getElementById('monthList');
    const selectedMonth = monthList.options[monthList.selectedIndex];
    const name = document.getElementById('toggleHeader').textContent.trim();
    if (selectedMonth && selectedMonth.value) {
        console.log('Submitting form for month:', selectedMonth.textContent);
        await generateSummary(name, selectedMonth.textContent);
        fetchSummaryContent();

    } else {
        alert('請選擇一個月份');
    }
}

function goBack() {
    window.history.back();
}


