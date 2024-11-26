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
