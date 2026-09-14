// nav-star.js — 给导航里的 ⭐ FlowKit 项加闪烁动画（melody 菜单是纯文本，动画靠 class 注入）
(function () {
  function init() {
    var links = document.querySelectorAll('nav a.site-page, #page-header a');
    for (var i = 0; i < links.length; i++) {
      var t = links[i].textContent || '';
      if (t.indexOf('FlowKit') !== -1 && !links[i].classList.contains('nav-star')) {
        links[i].classList.add('nav-star');
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
  document.addEventListener('pjax:success', init); // melody pjax 兼容
})();
