document.addEventListener("DOMContentLoaded", () => {
  const pageTitle = document.getElementById("page-title");
  const urlParams = new URLSearchParams(window.location.search);
  const title = urlParams.get("title");
  pageTitle.textContent = title || "分類內容";
});

function goBack() {
  window.history.back();
}
